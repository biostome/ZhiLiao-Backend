from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .models import PriorityEnum, StatusEnum, RelationTypeEnum


class LabelOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class LabelIn(BaseModel):
    name: str


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    priority: PriorityEnum = PriorityEnum.yellow
    status: StatusEnum = StatusEnum.todo

    channel: Optional[str] = None
    subcategory: Optional[str] = None

    assigned_to_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None

    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None

    labels: list[str] = Field(default_factory=list, description="List of label names")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    channel: Optional[str] = None
    subcategory: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    labels: Optional[list[str]] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    priority: PriorityEnum
    status: StatusEnum
    channel: Optional[str]
    subcategory: Optional[str]
    assigned_to_user_id: Optional[str]
    created_by_user_id: Optional[str]
    start_at: Optional[datetime]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    labels: list[LabelOut]

    class Config:
        from_attributes = True


class TaskQueryParams(BaseModel):
    q: Optional[str] = None
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    label: Optional[str] = None
    channel: Optional[str] = None
    subcategory: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    sort_by: Optional[Literal[
        "created_at",
        "due_at",
        "priority",
        "status",
        "title",
    ]] = "created_at"
    sort_order: Optional[Literal["asc", "desc"]] = "desc"
    limit: int = 20
    offset: int = 0


class BatchCreateRequest(BaseModel):
    tasks: list[TaskCreate]


class GraphNode(BaseModel):
    id: str
    title: str
    priority: PriorityEnum
    status: StatusEnum


class GraphEdge(BaseModel):
    src_task_id: str
    dst_task_id: str
    relation_type: RelationTypeEnum


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class RelationOp(BaseModel):
    other_task_id: str