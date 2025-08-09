from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Label, Task
from ..schemas import (
    BatchCreateRequest,
    GraphEdge,
    GraphNode,
    GraphResponse,
    TaskCreate,
    TaskOut,
    TaskQueryParams,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_or_create_labels(session: Session, label_names: list[str]) -> list[Label]:
    if not label_names:
        return []
    # Normalize label names
    normalized = [name.strip() for name in label_names if name and name.strip()]
    if not normalized:
        return []
    existing = session.scalars(select(Label).where(Label.name.in_(normalized))).all()
    existing_by_name = {l.name: l for l in existing}
    result: list[Label] = []
    for name in normalized:
        if name in existing_by_name:
            result.append(existing_by_name[name])
        else:
            label = Label(name=name)
            session.add(label)
            result.append(label)
    return result


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        channel=payload.channel,
        subcategory=payload.subcategory,
        assigned_to_user_id=payload.assigned_to_user_id,
        created_by_user_id=payload.created_by_user_id,
        start_at=payload.start_at,
        due_at=payload.due_at,
    )
    task.labels = _get_or_create_labels(db, payload.labels)
    db.add(task)
    db.flush()
    db.refresh(task)
    return task


@router.post("/batch", response_model=List[TaskOut])
def create_tasks_batch(payload: BatchCreateRequest, db: Session = Depends(get_db)):
    created: list[Task] = []
    for item in payload.tasks:
        task = Task(
            title=item.title,
            description=item.description,
            priority=item.priority,
            status=item.status,
            channel=item.channel,
            subcategory=item.subcategory,
            assigned_to_user_id=item.assigned_to_user_id,
            created_by_user_id=item.created_by_user_id,
            start_at=item.start_at,
            due_at=item.due_at,
        )
        task.labels = _get_or_create_labels(db, item.labels)
        db.add(task)
        created.append(task)
    db.flush()
    for t in created:
        db.refresh(t)
    return created


@router.get("", response_model=List[TaskOut])
def list_tasks(
    q: str | None = None,
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    label: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    assigned_to_user_id: str | None = Query(default=None),
    created_by_user_id: str | None = Query(default=None),
    due_before: str | None = Query(default=None),
    due_after: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Task).options(joinedload(Task.labels))

    filters = []
    if q:
        like = f"%{q}%"
        filters.append(or_(Task.title.ilike(like), Task.description.ilike(like)))
    if status:
        filters.append(Task.status == status)
    if priority:
        filters.append(Task.priority == priority)
    if channel:
        filters.append(Task.channel == channel)
    if subcategory:
        filters.append(Task.subcategory == subcategory)
    if assigned_to_user_id:
        filters.append(Task.assigned_to_user_id == assigned_to_user_id)
    if created_by_user_id:
        filters.append(Task.created_by_user_id == created_by_user_id)
    if due_before:
        filters.append(Task.due_at != None)
        filters.append(Task.due_at <= due_before)  # type: ignore
    if due_after:
        filters.append(Task.due_at != None)
        filters.append(Task.due_at >= due_after)  # type: ignore

    if filters:
        stmt = stmt.where(and_(*filters))

    if label:
        # join via association
        from ..models import TaskLabel, Label as LabelModel
        stmt = (
            stmt.join(TaskLabel, Task.id == TaskLabel.c.task_id)
            .join(LabelModel, LabelModel.id == TaskLabel.c.label_id)
            .where(LabelModel.name == label)
        )

    # Sorting
    sort_column = {
        "created_at": Task.created_at,
        "due_at": Task.due_at,
        "priority": Task.priority,
        "status": Task.status,
        "title": Task.title,
    }.get(sort_by, Task.created_at)

    if sort_order.lower() == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    stmt = stmt.limit(limit).offset(offset)

    results = db.execute(stmt).unique().scalars().all()
    return results


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    labels = data.pop("labels", None)
    for key, value in data.items():
        setattr(task, key, value)

    if labels is not None:
        task.labels = _get_or_create_labels(db, labels)

    db.add(task)
    db.flush()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    return None


# Integration endpoints
@router.post("/integrations/ingest", response_model=List[TaskOut])
def ingest_tasks(payload: BatchCreateRequest, db: Session = Depends(get_db)):
    return create_tasks_batch(payload, db)


@router.get("/integrations/graph", response_model=GraphResponse)
def graph(db: Session = Depends(get_db)):
    tasks = db.scalars(select(Task)).all()
    from ..models import TaskDependency

    edges = db.scalars(select(TaskDependency)).all()

    nodes = [
        GraphNode(id=t.id, title=t.title, priority=t.priority, status=t.status) for t in tasks
    ]
    graph_edges = [
        GraphEdge(src_task_id=e.src_task_id, dst_task_id=e.dst_task_id, relation_type=e.relation_type)
        for e in edges
    ]
    return GraphResponse(nodes=nodes, edges=graph_edges)