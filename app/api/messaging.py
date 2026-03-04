import json
import logging
import os
import uuid

import aio_pika

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = "tasks_queue"


async def get_rabbitmq_channel() -> aio_pika.abc.AbstractChannel:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.declare_queue(QUEUE_NAME, durable=True)
    return channel


async def publish_message(channel: aio_pika.abc.AbstractChannel, payload: dict) -> None:
    body = json.dumps(payload, default=str).encode()
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=QUEUE_NAME,
    )
    logger.info("Published message: %s", payload)
