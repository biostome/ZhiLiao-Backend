from typing import List
import logging
from app.models.task import Task

logger = logging.getLogger(__name__)


class Auditor:
    def __init__(self, auto_approve: bool = True) -> None:
        self.auto_approve = auto_approve

    async def review(self, tasks: List[Task]) -> List[Task]:
        reviewed: List[Task] = []
        for t in tasks:
            # Basic rules: title/description length
            if len(t.title.strip()) < 5 or len(t.description.strip()) < 10:
                logger.debug("Rejected by rule (too short): %s", t.title)
                continue
            # Placeholder for more rules or AI-based classification
            reviewed.append(t)
        logger.info("Auditor approved %d tasks", len(reviewed))
        return reviewed