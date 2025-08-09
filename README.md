# 任务管理服务（Task Management Service）

本仓库包含后端服务 `task_manager`，提供任务的存储、管理、检索与依赖关系等 REST API，基于 FastAPI 构建。

- 技术栈：FastAPI + SQLAlchemy + Pydantic + SQLite（默认）/ PostgreSQL（生产推荐）
- 详细文档：请查看 `task_manager/README.md`（中文）与 `task_manager/README_EN.md`（English）

---

## 快速开始

1) 进入服务目录并初始化环境（macOS/Linux）
```bash
cd task_manager
bash scripts/setup.sh
```

2) 运行测试
```bash
bash scripts/test.sh  # 预期看到 3 passed
```

3) 启动开发服务
```bash
bash scripts/dev.sh
# 打开 http://127.0.0.1:8000/docs 查看 API 文档
```

---

## 直接运行（不使用脚本）
```bash
cd task_manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Docker
- 构建镜像
```bash
cd task_manager
bash scripts/docker-build.sh  # 或：docker build -t task-manager:latest .
```
- 运行容器
```bash
bash scripts/docker-run.sh  # 或：docker run -p 8000:8000 task-manager:latest
# 打开 http://127.0.0.1:8000/docs 查看 API 文档
```

---

## 更多
- 中文文档：`task_manager/README.md`
- English: `task_manager/README_EN.md`
