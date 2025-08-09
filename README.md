# 任务收集与发布系统（对接任务管理系统）

本项目实现一个可扩展的“任务收集与发布系统”，用于持续从互联网数据源采集信息，经由 LLM 解析生成任务，筛选/审核/验证后，通过任务管理系统 API 进行发布。

### 核心能力
- 数据采集：RSS、HTTP、API（可扩展数据源）
- AI 任务生成：支持 LiteLLM 统一接入（OpenAI、Claude、Gemini、Qwen、Mistral 等），并提供本地回退逻辑
- 任务筛选与审核：去重、规则审核、AI 审核（可选）
- 任务验证：URL 存活性验证、接口数据有效性校验（扩展点）
- 任务发布：通过任务管理系统 REST API 发布，支持批量/实时
- 异步与调度：FastAPI + asyncio，内置 APScheduler 定时调度
- 可观测性：结构化日志，预留 Prometheus 指标扩展点

---

### 目录结构
```
app/
  main.py
  config.py
  utils/
    logging.py
    http.py
    scheduler.py
  models/
    task.py
    source_item.py
  services/
    collector/
      base.py
      rss_collector.py
    ai/
      generator.py
      filter.py
      audit.py
    verifier/
      verifier.py
    publisher/
      publisher.py
  db/
    database.py
    models.py
    crud.py
scripts/
  run_worker.py
requirements.txt
Dockerfile
docker-compose.yml
.env.example
```

---

### 快速开始（本地）
1) 准备环境
- Python 3.10+
- 可选：Docker / Docker Compose（推荐）

2) 克隆与安装
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

3) 配置环境变量
复制 `.env.example` 为 `.env`，并按需修改：
- `TASK_MGR_BASE_URL`：任务管理系统 API Base URL（必填）
- `TASK_MGR_API_KEY`：API Key 或 Bearer Token（必填）
- `RSS_FEEDS`：以逗号分隔的 RSS 源列表
- `MODEL_PROVIDER`、`MODEL_NAME`、`OPENAI_API_KEY` 等（按需）

4) 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
访问：
- 健康检查：`GET /health`
- 触发一次采集与发布：`POST /ingest/run`

---

### 使用 Docker / Compose（推荐）
```bash
cp .env.example .env
# 修改 .env 中的配置

# 构建与启动
docker compose up --build
```
默认会启动：
- `app`（FastAPI）
- `redis`
- `postgres`（可选，未提供必须表时自动创建）

---

### 配置项（.env）
- 基础
  - `ENV=dev|prod`
  - `LOG_LEVEL=INFO|DEBUG|WARNING|ERROR`
  - `SCHEDULER_CRON=*/10 * * * *` 采集频率（默认每 10 分钟）
- 任务管理系统
  - `TASK_MGR_BASE_URL`
  - `TASK_MGR_API_KEY`
- 数据源
  - `RSS_FEEDS` 逗号分隔列表
- AI 模型（LiteLLM）
  - `MODEL_PROVIDER=openai|anthropic|gemini|qwen|mistral|...`
  - `MODEL_NAME=gpt-4o-mini|claude-3-haiku|gemini-1.5-pro|qwen2.5-7b-instruct|...`
  - `OPENAI_API_KEY`（若使用 OpenAI）
  - 其他厂商密钥见 LiteLLM 文档
- 可选：Redis / DB
  - `REDIS_URL=redis://redis:6379/0`
  - `DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/tasks`

---

### 关键 API
- `POST /ingest/run`：立即采集并发布
  - 可选 body：`{"limit": 50, "dry_run": false}`
- `GET /health`：健康检查
- `GET /config`：当前有效配置（敏感字段已打码）

---

### 扩展数据源
实现 `app/services/collector/base.py` 中的 `DataSource` 抽象类并注册到 `main.py` 的 `COLLECTORS` 列表即可。

---

### 备注
- 若未配置数据库，将以内存/Redis 做去重，发布后不保留历史。
- 若任务管理系统提供 `GET /tasks`，系统会先拉取现有任务标题/URL 以避免重复创建。
- 验证模块默认对来源 URL 进行 `HEAD/GET` 校验，可依据需求增强。

---

### 许可证
MIT
