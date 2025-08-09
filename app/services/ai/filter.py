import logging
import hashlib
from typing import Iterable, List, Optional

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None

from app.config import settings
from app.models.task import Task

logger = logging.getLogger(__name__)


class TaskFilter:
    def __init__(self, redis_url: Optional[str] = settings.redis_url) -> None:
        self.redis_url = redis_url
        self.client = None

    async def _get_client(self):
        if not self.redis_url or not redis:
            return None
        if self.client is None:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
        return self.client

    @staticmethod
    def _fingerprint(task: Task) -> str:
        h = hashlib.sha256()
        h.update(task.source_url.encode("utf-8"))
        h.update(task.title.strip().lower().encode("utf-8"))
        return h.hexdigest()

    async def filter_duplicates(self, tasks: Iterable[Task]) -> List[Task]:
        keep: List[Task] = []
        client = await self._get_client()
        for t in tasks:
            fp = self._fingerprint(t)
            if client:
                added = await client.sadd("task_fingerprints", fp)
                if added == 0:
                    logger.debug("Duplicate (redis): %s", t.title)
                    continue
            else:
                # Fallback: in-memory set on object
                if not hasattr(self, "_seen"):
                    self._seen = set()  # type: ignore[attr-defined]
                if fp in self._seen:  # type: ignore[attr-defined]
                    logger.debug("Duplicate (memory): %s", t.title)
                    continue
                self._seen.add(fp)  # type: ignore[attr-defined]
            keep.append(t)
        logger.info("Filtered duplicates, remaining %d", len(keep))
        return keep