import asyncio
import json
import logging
import logging.config
import os
import uuid
from datetime import datetime, timezone

import aio_pika
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Column
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID

# ── Logging ────────────────────────────────────────────────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"level": "INFO", "handlers": ["console"]},
}
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/appdb",
)
QUEUE_NAME = "tasks_queue"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ── DB ─────────────────────────────────────────────────────────────────────────

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), nullable=False, default="pending")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Handlers ───────────────────────────────────────────────────────────────────

async def handle_create_order(payload: dict, session: AsyncSession) -> None:
    task_id = uuid.UUID(payload["task_id"])
    order_id = uuid.UUID(payload["order_id"])

    # Idempotency check
    existing_order = await session.get(Order, order_id)
    if existing_order:
        logger.info("Order %s already exists — skipping (idempotent)", order_id)
    else:
        order = Order(id=order_id, status="completed")
        session.add(order)

    task = await session.get(Task, task_id)
    if task:
        task.status = "completed"
    await session.commit()
    logger.info("create_order processed — task=%s order=%s", task_id, order_id)


async def handle_delete_order(payload: dict, session: AsyncSession) -> None:
    task_id = uuid.UUID(payload["task_id"])

    task = await session.get(Task, task_id)
    if task:
        task.status = "failed"
    await session.commit()
    logger.info("delete_order processed — task=%s", task_id)


# ── Message consumer ───────────────────────────────────────────────────────────

async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        retry_count = int(message.headers.get("x-retry-count", 0))
        try:
            payload = json.loads(message.body)
            action = payload.get("action")
            logger.info("Received message action=%s retry=%d", action, retry_count)

            async with AsyncSessionLocal() as session:
                if action == "create_order":
                    await handle_create_order(payload, session)
                elif action == "delete_order":
                    await handle_delete_order(payload, session)
                else:
                    logger.warning("Unknown action: %s — discarding", action)

        except Exception as exc:
            logger.error("Error processing message: %s", exc, exc_info=True)
            if retry_count < MAX_RETRIES:
                logger.info("Requeueing message (retry %d/%d)", retry_count + 1, MAX_RETRIES)
                channel = message.channel
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=message.body,
                        headers={"x-retry-count": retry_count + 1},
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key=QUEUE_NAME,
                )
            else:
                logger.error("Max retries reached — discarding message")


async def main() -> None:
    logger.info("Worker starting…")
    await init_db()

    for attempt in range(1, 11):
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            break
        except Exception as exc:
            logger.warning("RabbitMQ not ready (attempt %d/10): %s", attempt, exc)
            await asyncio.sleep(5)
    else:
        logger.error("Could not connect to RabbitMQ after 10 attempts")
        return

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        logger.info("Worker listening on queue '%s'", QUEUE_NAME)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_message(message)


if __name__ == "__main__":
    asyncio.run(main())
