import logging
from typing import List, Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.models.task import Task, PublishResult

logger = logging.getLogger(__name__)


class TaskManagerClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def list_existing(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/tasks"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=self.headers)
            r.raise_for_status()
            return r.json() if r.content else []

    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(3))
    async def publish(self, task: Task) -> PublishResult:
        url = f"{self.base_url}/tasks"
        payload = {
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "source_url": str(task.source_url),
            "source_type": task.source_type,
            "tags": task.tags,
            "created_at": task.created_at.isoformat(),
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(url, headers=self.headers, json=payload)
            if r.status_code in (200, 201):
                data = r.json()
                return PublishResult(published=True, task_manager_id=str(data.get("id")))
            else:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
                logger.warning("Publish failed (%s): %s", r.status_code, detail)
                return PublishResult(published=False, reason=str(detail))


async def publish_tasks(tasks: List[Task]) -> List[PublishResult]:
    if not settings.task_mgr_base_url or not settings.task_mgr_api_key:
        logger.info("Task Manager config missing; skipping publish for %d tasks", len(tasks))
        return [PublishResult(published=False, reason="no_task_mgr_config") for _ in tasks]

    client = TaskManagerClient(settings.task_mgr_base_url, settings.task_mgr_api_key)

    # Optional: dedupe with remote if it exposes titles/urls
    try:
        existing = await client.list_existing()
        existing_keys = set()
        for e in existing:
            title = (e.get("title") or "").strip().lower()
            url = (e.get("source_url") or "").strip().lower()
            if title:
                existing_keys.add((title, url))
    except Exception as exc:
        logger.debug("Failed to list existing tasks: %s", exc)
        existing_keys = set()

    results: List[PublishResult] = []
    for t in tasks:
        key = (t.title.strip().lower(), str(t.source_url).strip().lower())
        if key in existing_keys:
            logger.info("Skip publish (exists remotely): %s", t.title)
            results.append(PublishResult(published=False, reason="exists"))
            continue
        results.append(await client.publish(t))
    return results