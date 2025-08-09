import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from app.db.models import Base


async def init_db(engine: Optional[AsyncEngine]) -> None:
    if not engine:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def upsert_normalized_task(engine: Optional[AsyncEngine], task) -> None:
    if not engine:
        return
    # Simplified upsert using INSERT ... ON CONFLICT requires explicit DDL; here we do best-effort replace
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                delete from task_normalized where source_id = :source_id;
                insert into task_normalized (source_id, title, description, priority, status, source_url, source_type, tags, verified, created_at)
                values (:source_id, :title, :description, :priority, :status, :source_url, :source_type, :tags, :verified, :created_at);
                """
            ),
            {
                "source_id": task.source_id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
                "source_url": str(task.source_url),
                "source_type": task.source_type,
                "tags": json.dumps(task.tags),
                "verified": task.verified,
                "created_at": task.created_at,
            },
        )