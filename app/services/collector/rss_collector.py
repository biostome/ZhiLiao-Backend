import asyncio
import logging
from typing import List
import hashlib
import feedparser
from app.models.source_item import SourceItem
from app.services.collector.base import DataSource

logger = logging.getLogger(__name__)


class RSSCollector(DataSource):
    def __init__(self, feeds: List[str]):
        self.feeds = feeds

    async def fetch(self, limit: int = 50) -> List[SourceItem]:
        results: List[SourceItem] = []

        async def fetch_feed(url: str) -> List[SourceItem]:
            try:
                parsed = await asyncio.to_thread(feedparser.parse, url)
                items: List[SourceItem] = []
                for entry in parsed.entries[:limit]:
                    link = entry.get("link") or entry.get("id")
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    if not link or not title:
                        continue
                    sid = hashlib.sha256(link.encode("utf-8")).hexdigest()
                    items.append(SourceItem(id=sid, title=title, url=link, summary=summary, raw=dict(entry)))
                return items
            except Exception as exc:
                logger.warning("Failed to parse RSS feed %s: %s", url, exc)
                return []

        tasks = [fetch_feed(url) for url in self.feeds]
        for items in await asyncio.gather(*tasks):
            results.extend(items)

        logger.info("RSSCollector fetched %d items from %d feeds", len(results), len(self.feeds))
        return results[:limit]