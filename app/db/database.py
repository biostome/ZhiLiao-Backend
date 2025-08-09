from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None


def get_engine() -> Optional[AsyncEngine]:
    global _engine
    if _engine is not None:
        return _engine
    if not settings.database_url:
        return None
    try:
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        return _engine
    except Exception as exc:
        logger.warning("Database engine init failed, DB features disabled: %s", exc)
        return None