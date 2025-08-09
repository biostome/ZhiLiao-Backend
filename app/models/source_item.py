from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class SourceItem(BaseModel):
    id: str
    title: str
    url: HttpUrl
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    raw: dict = {}