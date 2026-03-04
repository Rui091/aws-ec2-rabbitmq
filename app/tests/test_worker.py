"""
Unit tests for the Worker message-processing logic.
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Column
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Re-import worker internals (standalone module)
import importlib, sys, types

# Provide a minimal stub so aio_pika doesn't need a real broker
aio_pika_stub = types.ModuleType("aio_pika")
aio_pika_stub.connect_robust = AsyncMock()
aio_pika_stub.Message = MagicMock()
aio_pika_stub.DeliveryMode = MagicMock()

class _AioABC(types.ModuleType):
    AbstractIncomingMessage = object
    AbstractChannel = object

aio_pika_stub.abc = _AioABC("aio_pika.abc")
sys.modules.setdefault("aio_pika", aio_pika_stub)
sys.modules.setdefault("aio_pika.abc", aio_pika_stub.abc)

from app.worker.main import handle_create_order, handle_delete_order, Task, Order, Base  # noqa: E402

TEST_DB_URL = "sqlite+aiosqlite:///./test_worker.db"
engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="module", autouse=True)
async def setup_worker_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_handle_create_order():
    async with SessionLocal() as session:
        task_id = uuid.uuid4()
        order_id = uuid.uuid4()

        # Pre-create task as pending
        task = Task(id=task_id, status="pending")
        session.add(task)
        await session.commit()

        payload = {"task_id": str(task_id), "order_id": str(order_id)}
        await handle_create_order(payload, session)

        await session.refresh(task)
        assert task.status == "completed"


@pytest.mark.asyncio
async def test_handle_create_order_idempotent():
    """Calling handle_create_order twice with the same order_id must not fail."""
    async with SessionLocal() as session:
        task_id = uuid.uuid4()
        order_id = uuid.uuid4()

        task = Task(id=task_id, status="pending")
        session.add(task)
        await session.commit()

        payload = {"task_id": str(task_id), "order_id": str(order_id)}
        await handle_create_order(payload, session)
        await handle_create_order(payload, session)

        await session.refresh(task)
        assert task.status == "completed"


@pytest.mark.asyncio
async def test_handle_delete_order():
    async with SessionLocal() as session:
        task_id = uuid.uuid4()

        task = Task(id=task_id, status="pending")
        session.add(task)
        await session.commit()

        payload = {"task_id": str(task_id)}
        await handle_delete_order(payload, session)

        await session.refresh(task)
        assert task.status == "failed"
