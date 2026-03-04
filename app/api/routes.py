import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.database import get_db
from app.api.models import Task, Order
from app.api.schemas import TaskOut, OrderOut
from app.api.messaging import get_rabbitmq_channel, publish_message

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Tasks ──────────────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=list[TaskOut], tags=["Tasks"])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task))
    return result.scalars().all()


@router.get("/tasks/{task_id}", response_model=TaskOut, tags=["Tasks"])
async def get_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_202_ACCEPTED, tags=["Tasks"])
async def create_task(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task = Task(id=uuid.uuid4(), status="pending")
    order_id = uuid.uuid4()
    db.add(task)
    await db.commit()
    await db.refresh(task)

    async def _publish():
        try:
            channel = await get_rabbitmq_channel()
            await publish_message(
                channel,
                {"action": "create_order", "task_id": str(task.id), "order_id": str(order_id)},
            )
        except Exception as exc:
            logger.error("Failed to publish create_order message: %s", exc)

    background_tasks.add_task(_publish)
    logger.info("Task created: %s", task.id)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_202_ACCEPTED, tags=["Tasks"])
async def delete_task(
    task_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def _publish():
        try:
            channel = await get_rabbitmq_channel()
            await publish_message(
                channel,
                {"action": "delete_order", "task_id": str(task_id)},
            )
        except Exception as exc:
            logger.error("Failed to publish delete_order message: %s", exc)

    background_tasks.add_task(_publish)
    logger.info("Delete task requested: %s", task_id)
    return {"task_id": str(task_id), "status": "accepted"}


# ── Orders ─────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=list[OrderOut], tags=["Orders"])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order))
    return result.scalars().all()
