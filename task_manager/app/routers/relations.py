from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import RelationTypeEnum, Task, TaskDependency
from ..schemas import RelationOp

router = APIRouter(prefix="/relations", tags=["relations"])


def _ensure_tasks(db: Session, a_id: str, b_id: str) -> tuple[Task, Task]:
    a = db.get(Task, a_id)
    b = db.get(Task, b_id)
    if not a or not b:
        raise HTTPException(status_code=404, detail="Task not found")
    return a, b


@router.post("/tasks/{task_id}/predecessors", status_code=201)
def add_predecessor(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, payload.other_task_id, task_id)
    dep = TaskDependency(src_task_id=payload.other_task_id, dst_task_id=task_id, relation_type=RelationTypeEnum.precedes)
    db.add(dep)
    try:
        db.flush()
    except Exception:
        raise HTTPException(status_code=409, detail="Relation already exists")
    return {"ok": True}


@router.delete("/tasks/{task_id}/predecessors")
def remove_predecessor(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, payload.other_task_id, task_id)
    dep = db.scalar(
        select(TaskDependency).where(
            and_(
                TaskDependency.src_task_id == payload.other_task_id,
                TaskDependency.dst_task_id == task_id,
                TaskDependency.relation_type == RelationTypeEnum.precedes,
            )
        )
    )
    if not dep:
        raise HTTPException(status_code=404, detail="Relation not found")
    db.delete(dep)
    return {"ok": True}


@router.post("/tasks/{task_id}/successors", status_code=201)
def add_successor(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = TaskDependency(src_task_id=task_id, dst_task_id=payload.other_task_id, relation_type=RelationTypeEnum.precedes)
    db.add(dep)
    try:
        db.flush()
    except Exception:
        raise HTTPException(status_code=409, detail="Relation already exists")
    return {"ok": True}


@router.delete("/tasks/{task_id}/successors")
def remove_successor(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = db.scalar(
        select(TaskDependency).where(
            and_(
                TaskDependency.src_task_id == task_id,
                TaskDependency.dst_task_id == payload.other_task_id,
                TaskDependency.relation_type == RelationTypeEnum.precedes,
            )
        )
    )
    if not dep:
        raise HTTPException(status_code=404, detail="Relation not found")
    db.delete(dep)
    return {"ok": True}


@router.post("/tasks/{task_id}/parallel", status_code=201)
def mark_parallel(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = TaskDependency(src_task_id=task_id, dst_task_id=payload.other_task_id, relation_type=RelationTypeEnum.parallel)
    db.add(dep)
    try:
        db.flush()
    except Exception:
        raise HTTPException(status_code=409, detail="Relation already exists")
    return {"ok": True}


@router.delete("/tasks/{task_id}/parallel")
def unmark_parallel(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = db.scalar(
        select(TaskDependency).where(
            and_(
                TaskDependency.src_task_id == task_id,
                TaskDependency.dst_task_id == payload.other_task_id,
                TaskDependency.relation_type == RelationTypeEnum.parallel,
            )
        )
    )
    if not dep:
        raise HTTPException(status_code=404, detail="Relation not found")
    db.delete(dep)
    return {"ok": True}


@router.post("/tasks/{task_id}/mutex", status_code=201)
def mark_mutex(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = TaskDependency(src_task_id=task_id, dst_task_id=payload.other_task_id, relation_type=RelationTypeEnum.mutex)
    db.add(dep)
    try:
        db.flush()
    except Exception:
        raise HTTPException(status_code=409, detail="Relation already exists")
    return {"ok": True}


@router.delete("/tasks/{task_id}/mutex")
def unmark_mutex(task_id: str, payload: RelationOp, db: Session = Depends(get_db)):
    _ensure_tasks(db, task_id, payload.other_task_id)
    dep = db.scalar(
        select(TaskDependency).where(
            and_(
                TaskDependency.src_task_id == task_id,
                TaskDependency.dst_task_id == payload.other_task_id,
                TaskDependency.relation_type == RelationTypeEnum.mutex,
            )
        )
    )
    if not dep:
        raise HTTPException(status_code=404, detail="Relation not found")
    db.delete(dep)
    return {"ok": True}