from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import get_db
from app.models import Base


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db():
    # Use a temporary SQLite file to persist across connections for the test session
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp.name}"
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator:
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_and_get_task(client: TestClient):
    r = client.post(
        "/api/v1/tasks",
        json={
            "title": "Task A",
            "description": "desc",
            "priority": "red",
            "status": "todo",
            "labels": ["backend", "urgent"],
            "channel": "work",
            "subcategory": "feature",
            "assigned_to_user_id": "u1",
            "created_by_user_id": "u2",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    task_id = data["id"]
    assert data["title"] == "Task A"
    assert len(data["labels"]) == 2

    r2 = client.get(f"/api/v1/tasks/{task_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == task_id


def test_filters_and_pagination(client: TestClient):
    # Create multiple tasks
    payload = {
        "tasks": [
            {"title": "Task B", "priority": "yellow", "labels": ["backend"], "channel": "work"},
            {"title": "Task C", "priority": "green", "labels": ["frontend"], "channel": "life"},
            {"title": "Task D", "priority": "red", "labels": ["backend"], "channel": "work"},
        ]
    }
    r = client.post("/api/v1/tasks/batch", json=payload)
    assert r.status_code == 200

    # Filter by label
    r = client.get("/api/v1/tasks", params={"label": "backend", "sort_by": "title", "sort_order": "asc"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    titles = [t["title"] for t in data]
    assert titles == sorted(titles)

    # Pagination
    r = client.get("/api/v1/tasks", params={"limit": 2, "offset": 0})
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_relations(client: TestClient):
    # Create two tasks
    a = client.post("/api/v1/tasks", json={"title": "A"}).json()
    b = client.post("/api/v1/tasks", json={"title": "B"}).json()

    # A precedes B (A -> B)
    r = client.post(f"/api/v1/relations/tasks/{b['id']}/predecessors", json={"other_task_id": a["id"]})
    assert r.status_code == 201

    # Duplicate should be 409
    r = client.post(f"/api/v1/relations/tasks/{b['id']}/predecessors", json={"other_task_id": a["id"]})
    assert r.status_code == 409

    # Graph should contain edge
    graph = client.get("/api/v1/tasks/integrations/graph").json()
    assert any(e for e in graph["edges"] if e["src_task_id"] == a["id"] and e["dst_task_id"] == b["id"])  # noqa

    # Remove relation
    r = client.request("DELETE", f"/api/v1/relations/tasks/{b['id']}/predecessors", json={"other_task_id": a["id"]})
    assert r.status_code == 200

    # Ensure removed
    graph = client.get("/api/v1/tasks/integrations/graph").json()
    assert not any(e for e in graph["edges"] if e["src_task_id"] == a["id"] and e["dst_task_id"] == b["id"])  # noqa