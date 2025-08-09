from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .db import engine
from .models import Base
from .routers.tasks import router as tasks_router
from .routers.relations import router as relations_router

app = FastAPI(title="Task Management Service", version="0.1.0")


@app.on_event("startup")
def on_startup():
    # Create tables if not exist. In production, prefer Alembic migrations.
    Base.metadata.create_all(bind=engine)


app.include_router(tasks_router, prefix="/api/v1")
app.include_router(relations_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)