from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging


logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()

    def add_cron_job(self, func: Callable, cron_expr: str, name: str) -> None:
        trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(func, trigger=trigger, name=name, max_instances=1, coalesce=True, replace_existing=True)
        logger.info("Scheduler job registered: %s (%s)", name, cron_expr)

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")


scheduler = Scheduler()