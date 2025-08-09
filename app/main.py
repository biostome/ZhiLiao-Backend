import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logging import configure_logging
from app.utils.scheduler import scheduler
from app.services.collector.rss_collector import RSSCollector
from app.services.ai.generator import generate_tasks
from app.services.ai.filter import TaskFilter
from app.services.ai.audit import Auditor
from app.services.verifier.verifier import verify_tasks
from app.services.publisher.publisher import publish_tasks
from app.db.database import get_engine
from app.db.crud import init_db, upsert_normalized_task


logger = logging.getLogger(__name__)


COLLECTORS = []
if settings.rss_feeds:
    COLLECTORS.append(RSSCollector(settings.rss_feeds))


async def run_pipeline(limit: int = 50, dry_run: bool = False) -> dict:
    # 1. Collect
    collected_items = []
    for c in COLLECTORS:
        items = await c.fetch(limit=limit)
        collected_items.extend(items)

    # 2. Generate via LLM (with fallback)
    tasks = await generate_tasks(collected_items)

    # 3. Filter duplicates
    task_filter = TaskFilter()
    tasks = await task_filter.filter_duplicates(tasks)

    # 4. Audit
    auditor = Auditor(auto_approve=True)
    tasks = await auditor.review(tasks)

    # 5. Verify
    tasks = await verify_tasks(tasks)

    # 6. Optional: persist normalized tasks
    engine = get_engine()
    await init_db(engine)
    if engine:
        for t in tasks:
            await upsert_normalized_task(engine, t)

    # 7. Publish
    publish_results = []
    if not dry_run:
        publish_results = await publish_tasks(tasks)

    return {
        "collected": len(collected_items),
        "generated": len(tasks),
        "published": sum(1 for r in publish_results if r.published) if publish_results else 0,
        "skipped": sum(1 for r in publish_results if not r.published) if publish_results else 0,
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    logger.info("Starting app in env=%s", settings.env)

    # Initialize DB if configured
    await init_db(get_engine())

    # Register scheduler job
    async def scheduled_job():
        try:
            result = await run_pipeline(limit=50, dry_run=False)
            logger.info("Scheduled run result: %s", result)
        except Exception as exc:
            logger.exception("Scheduled job failed: %s", exc)

    scheduler.add_cron_job(lambda: asyncio.create_task(scheduled_job()), settings.scheduler_cron, name="ingest_publish")
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title="Task Collector & Publisher", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    return settings.safe_dict()


@app.post("/ingest/run")
async def ingest_run(payload: Optional[dict] = Body(default=None)):
    payload = payload or {}
    limit = int(payload.get("limit", 50))
    dry_run = bool(payload.get("dry_run", False))
    result = await run_pipeline(limit=limit, dry_run=dry_run)
    return JSONResponse(content=result)