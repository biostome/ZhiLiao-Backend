import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential
from app.models.source_item import SourceItem
from app.models.task import Task
from app.config import settings

logger = logging.getLogger(__name__)


PROMPT = (
    "You are an expert task planner. Read the input news/post and generate a concise actionable task. "
    "Return a JSON with keys: title, description, priority (low|medium|high), tags (array). "
)


def _fallback_generate(item: SourceItem) -> Task:
    title = item.title[:120]
    description = (item.summary or item.title)[:1000]
    return Task(
        source_id=item.id,
        title=title,
        description=description,
        priority="medium",
        source_url=item.url,
        source_type="rss",
        tags=["auto"],
    )


@retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
async def generate_task(item: SourceItem) -> Task:
    try:
        # Lazy import to avoid hard dependency
        import json
        from litellm import acompletion

        content = f"{PROMPT}\nInput:\nTitle: {item.title}\nSummary: {item.summary}\nURL: {item.url}"
        response = await acompletion(
            model=settings.model_name,
            messages=[{"role": "user", "content": content}],
            timeout=15,
        )
        text = response.choices[0].message["content"]
        data = None
        try:
            data = json.loads(text)
        except Exception:
            # Some models wrap JSON in code fences
            import re
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                data = json.loads(match.group(0))
        if not data:
            raise ValueError("Model did not return JSON")

        priority = data.get("priority", "medium")
        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        return Task(
            source_id=item.id,
            title=data.get("title") or item.title,
            description=data.get("description") or (item.summary or item.title),
            priority=priority,
            source_url=item.url,
            source_type="rss",
            tags=list(data.get("tags") or []),
        )
    except Exception as exc:
        logger.debug("LLM generation failed, using fallback: %s", exc)
        return _fallback_generate(item)


async def generate_tasks(items: List[SourceItem]) -> List[Task]:
    import asyncio

    tasks = [generate_task(item) for item in items]
    return await asyncio.gather(*tasks)