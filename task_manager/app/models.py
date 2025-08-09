from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PriorityEnum(str, enum.Enum):
    red = "red"
    yellow = "yellow"
    green = "green"


class StatusEnum(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class RelationTypeEnum(str, enum.Enum):
    precedes = "precedes"  # A -> B means A must be done before B
    parallel = "parallel"
    mutex = "mutex"


# Association table for many-to-many Task <-> Label
TaskLabel = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", String(36), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", String(36), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("task_id", "label_id", name="uq_task_label"),
)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    priority: Mapped[PriorityEnum] = mapped_column(Enum(PriorityEnum), default=PriorityEnum.yellow, index=True)
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum), default=StatusEnum.todo, index=True)

    channel: Mapped[str | None] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100), index=True)

    assigned_to_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(64), index=True)

    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow
    )

    labels: Mapped[list[Label]] = relationship(
        "Label",
        secondary=TaskLabel,
        lazy="selectin",
        backref="tasks",
        cascade="save-update",
    )

    # Relationships for dependencies
    outgoing_edges: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.src_task_id",
        cascade="all, delete-orphan",
        back_populates="src_task",
        lazy="selectin",
    )

    incoming_edges: Mapped[list["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.dst_task_id",
        cascade="all, delete-orphan",
        back_populates="dst_task",
        lazy="selectin",
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    src_task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    dst_task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[RelationTypeEnum] = mapped_column(Enum(RelationTypeEnum), index=True)

    src_task: Mapped[Task] = relationship("Task", foreign_keys=[src_task_id], back_populates="outgoing_edges")
    dst_task: Mapped[Task] = relationship("Task", foreign_keys=[dst_task_id], back_populates="incoming_edges")

    __table_args__ = (
        UniqueConstraint("src_task_id", "dst_task_id", "relation_type", name="uq_dependency_edge"),
    )