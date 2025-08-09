# Task Management Service

A FastAPI-based backend service for storing, managing, and retrieving tasks, exposing a clean REST API for web/mobile frontends and other services.

## Tech Stack
- Framework: FastAPI
- ORM: SQLAlchemy 2.x
- Validation: Pydantic v2
- DB: SQLite by default (PostgreSQL recommended for production)
- Tests: pytest + FastAPI TestClient
- Deployment: Docker (uvicorn)

## Project Layout
- `app/models.py`: ORM models (Task/Label/TaskDependency)
- `app/schemas.py`: Pydantic schemas (I/O, filters)
- `app/routers/tasks.py`: Task CRUD, list with filters/pagination/sort, integrations
- `app/routers/relations.py`: Dependency endpoints (predecessor/successor/parallel/mutex)
- `app/main.py`: FastAPI entrypoint
- `scripts/*.sh`: One-liner scripts (setup/test/dev/docker)
- `tests/test_tasks.py`: Test cases
- `docs/er.mmd`: Mermaid ER diagram
- `docs/sequence_ingest.mmd`: Ingestion sequence diagram

## Quickstart (macOS/Linux)
1) Setup
```
bash scripts/setup.sh
```
2) Run tests
```
bash scripts/test.sh
```
3) Start dev server
```
bash scripts/dev.sh
```
Open API docs at `http://127.0.0.1:8000/docs`.

## Run without scripts
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker
- Build
```
bash scripts/docker-build.sh  # or: docker build -t task-manager:latest .
```
- Run
```
bash scripts/docker-run.sh    # or: docker run -p 8000:8000 task-manager:latest
```
- Use PostgreSQL
```
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
bash scripts/docker-run.sh
```

## Configuration
- `DATABASE_URL`: DB connection string
  - Default: `sqlite:///./task_manager.db`
  - PostgreSQL: `postgresql+psycopg://user:pass@host:5432/db`

## API Overview (prefix: /api/v1)
- Tasks
  - POST `/tasks`: create one
  - POST `/tasks/batch`: create many
  - GET `/tasks`: list with filtering/pagination/sorting
  - GET `/tasks/{task_id}`: get one
  - PATCH `/tasks/{task_id}`: update
  - DELETE `/tasks/{task_id}`: delete
- Relations
  - POST `/relations/tasks/{task_id}/predecessors` (body: `{ "other_task_id" }`)
  - DELETE `/relations/tasks/{task_id}/predecessors`
  - POST `/relations/tasks/{task_id}/successors`
  - DELETE `/relations/tasks/{task_id}/successors`
  - POST `/relations/tasks/{task_id}/parallel`
  - DELETE `/relations/tasks/{task_id}/parallel`
  - POST `/relations/tasks/{task_id}/mutex`
  - DELETE `/relations/tasks/{task_id}/mutex`
- Integrations
  - POST `/tasks/integrations/ingest`: bulk ingest
  - GET `/tasks/integrations/graph`: export task graph (for optimizer agent)

## Query params (GET /tasks)
- `q`, `status` (todo|in_progress|done), `priority` (red|yellow|green), `label`
- `channel`, `subcategory`, `assigned_to_user_id`, `created_by_user_id`
- `due_before`, `due_after` (ISO datetime)
- `sort_by` (created_at|due_at|priority|status|title) default created_at
- `sort_order` (asc|desc) default desc
- `limit` (1..200, default 20), `offset` (default 0)

Example:
```
curl "http://127.0.0.1:8000/api/v1/tasks?label=backend&sort_by=title&sort_order=asc&limit=10"
```

## Examples
- Create a task
```
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
        "title": "My first task",
        "priority": "yellow",
        "status": "todo",
        "labels": ["backend", "urgent"],
        "channel": "work",
        "subcategory": "feature",
        "assigned_to_user_id": "u1",
        "created_by_user_id": "u2"
      }'
```
- Create dependency (A -> B)
```
curl -X POST http://127.0.0.1:8000/api/v1/relations/tasks/{B_ID}/predecessors \
  -H "Content-Type: application/json" \
  -d '{"other_task_id": "{A_ID}"}'
```
- Export graph
```
curl http://127.0.0.1:8000/api/v1/tasks/integrations/graph
```

## Diagrams
- ER diagram (Mermaid): `docs/er.mmd`
- Ingestion sequence (Mermaid): `docs/sequence_ingest.mmd`

## Testing
```
bash scripts/test.sh
# or manual
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

## Troubleshooting
- `ModuleNotFoundError: No module named 'app'`
  - Set `PYTHONPATH=.` when running pytest or uvicorn.
- Port in use
  - Change port: `bash scripts/dev.sh 8001`
- SQLite file location
  - Default at project root: `task_manager.db`
- DB migrations
  - For production, use Alembic (not included by default).