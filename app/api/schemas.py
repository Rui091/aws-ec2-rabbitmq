import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


TaskStatus = Literal["pending", "completed", "failed"]
OrderStatus = Literal["pending", "completed", "failed"]


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: TaskStatus
    created_at: datetime


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: OrderStatus


class TaskCreate(BaseModel):
    pass


class MessagePayload(BaseModel):
    action: Literal["create_order", "delete_order"]
    task_id: uuid.UUID
    order_id: uuid.UUID | None = None
