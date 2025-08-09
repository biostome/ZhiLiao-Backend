import logging
from typing import List
from app.models.task import Task
from app.utils.http import aiohttp_session

logger = logging.getLogger(__name__)


async def verify_tasks(tasks: List[Task]) -> List[Task]:
    verified: List[Task] = []
    async with aiohttp_session() as session:
        for t in tasks:
            try:
                async with session.head(str(t.source_url), allow_redirects=True) as resp:
                    if 200 <= resp.status < 400:
                        t.verified = True
                        verified.append(t)
                        continue
                # Some sites block HEAD; try GET lightweight
                async with session.get(str(t.source_url), allow_redirects=True) as resp:
                    if 200 <= resp.status < 400:
                        t.verified = True
                        verified.append(t)
                        continue
                logger.debug("Verification failed (%s): %s", resp.status, t.source_url)
            except Exception as exc:
                logger.debug("Verification error: %s (%s)", t.source_url, exc)
    logger.info("Verified %d/%d tasks", len(verified), len(tasks))
    return verified