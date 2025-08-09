## 任务管理系统 · 使用文档

### 简介
- 独立后端服务，提供任务的存储、管理、检索与接口对接
- 技术栈：FastAPI + SQLAlchemy + Pydantic + SQLite（默认）/ PostgreSQL（推荐生产）
- 目录结构：
  - `app/models.py`：ORM 模型（任务/标签/依赖）
  - `app/schemas.py`：Pydantic 模型（入参/出参/查询）
  - `app/routers/tasks.py`：任务 CRUD、筛选分页、集成接口
  - `app/routers/relations.py`：依赖关系接口（前置/后续/并行/互斥）
  - `app/main.py`：FastAPI 入口
  - `scripts/*.sh`：开箱即用脚本（setup/test/dev/docker）
  - `tests/test_tasks.py`：测试用例

---

### 快速开始
1) 准备环境（macOS/Linux）
```
bash scripts/setup.sh
```
2) 运行测试
```
bash scripts/test.sh
```
显示 `3 passed` 即成功。

3) 启动开发服务
```
bash scripts/dev.sh
```
打开接口文档：`http://127.0.0.1:8000/docs`

---

### 直接运行（不使用脚本）
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Docker 部署
- 构建镜像
```
bash scripts/docker-build.sh  # 或 docker build -t task-manager:latest .
```
- 运行容器
```
bash scripts/docker-run.sh    # 或 docker run -p 8000:8000 task-manager:latest
```
- 访问文档：`http://127.0.0.1:8000/docs`
- 使用 PostgreSQL：
```
export DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
bash scripts/docker-run.sh
```

---

### 配置
- 环境变量
  - `DATABASE_URL`：数据库连接字符串
    - 默认：`sqlite:///./task_manager.db`
    - PostgreSQL 示例：`postgresql+psycopg://user:pass@host:5432/db`

---

### API 概览（REST）
前缀：`/api/v1`

- 任务 CRUD
  - POST `/tasks` 创建任务（单）
  - POST `/tasks/batch` 批量创建
  - GET `/tasks` 列表查询（分页/排序/过滤）
  - GET `/tasks/{task_id}` 查询单条
  - PATCH `/tasks/{task_id}` 更新
  - DELETE `/tasks/{task_id}` 删除

- 任务关系（预留接口）
  - POST `/relations/tasks/{task_id}/predecessors` 添加前置（body: `{ "other_task_id" }`）
  - DELETE `/relations/tasks/{task_id}/predecessors` 删除前置
  - POST `/relations/tasks/{task_id}/successors` 添加后续
  - DELETE `/relations/tasks/{task_id}/successors` 删除后续
  - POST `/relations/tasks/{task_id}/parallel` 标记并行
  - DELETE `/relations/tasks/{task_id}/parallel` 取消并行
  - POST `/relations/tasks/{task_id}/mutex` 标记互斥
  - DELETE `/relations/tasks/{task_id}/mutex` 取消互斥

- 集成接口
  - POST `/tasks/integrations/ingest` 批量导入任务
  - GET `/tasks/integrations/graph` 导出任务图（供依赖优化智能体）

---

### 查询参数（GET /tasks）
- `q`：标题/描述模糊搜索
- `status`：`todo|in_progress|done`
- `priority`：`red|yellow|green`
- `label`：按标签过滤
- `channel`、`subcategory`：分类过滤
- `assigned_to_user_id`、`created_by_user_id`
- `due_before`、`due_after`：截止时间范围（ISO 时间）
- `sort_by`：`created_at|due_at|priority|status|title`（默认 `created_at`）
- `sort_order`：`asc|desc`（默认 `desc`）
- `limit`（默认 20，1~200）、`offset`（默认 0）

示例：
```
curl "http://127.0.0.1:8000/api/v1/tasks?label=backend&sort_by=title&sort_order=asc&limit=10"
```

---

### 示例请求
- 创建任务
```
curl -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
        "title": "My first task",
        "description": "desc",
        "priority": "yellow",
        "status": "todo",
        "labels": ["backend", "urgent"],
        "channel": "work",
        "subcategory": "feature",
        "assigned_to_user_id": "u1",
        "created_by_user_id": "u2"
      }'
```
- 批量创建
```
curl -X POST http://127.0.0.1:8000/api/v1/tasks/batch \
  -H "Content-Type: application/json" \
  -d '{
        "tasks": [
          {"title": "Task A", "priority": "red", "labels": ["backend"]},
          {"title": "Task B", "priority": "green", "labels": ["frontend"]}
        ]
      }'
```
- 建立依赖（A -> B）
```
# 令 A 为 B 的前置
curl -X POST http://127.0.0.1:8000/api/v1/relations/tasks/{B_ID}/predecessors \
  -H "Content-Type: application/json" \
  -d '{"other_task_id": "{A_ID}"}'
```
- 导出任务图
```
curl http://127.0.0.1:8000/api/v1/tasks/integrations/graph
```

---

### 测试
- 运行全部测试
```
bash scripts/test.sh
```
- 直接用 pytest（需激活 venv 并设置 PYTHONPATH）
```
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

---

### 常见问题（Troubleshooting）
- `ModuleNotFoundError: No module named 'app'`
  - 没有设置 `PYTHONPATH`。按如下方式执行：`PYTHONPATH=. pytest -q` 或 `PYTHONPATH=. uvicorn app.main:app --reload`
- 端口被占用
  - 修改启动端口：`bash scripts/dev.sh 8001`
- SQLite 数据文件
  - 默认生成在项目根目录：`task_manager.db`
- 数据迁移
  - PoC 阶段使用自动建表。生产建议引入 Alembic 管理迁移。

---

### 备注
- 本服务仅管理数据和提供 API，不负责任务内容生成或自动优化依赖关系。
- 接口文档在运行时可访问：`/docs` 与 `/redoc`。