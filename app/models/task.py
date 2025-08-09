from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class Task(BaseModel):
    source_id: str = Field(..., description="Unique ID derived from source item (e.g., URL hash)")
    title: str
    description: str
    priority: str = Field(default="medium")
    status: str = Field(default="not_started")
    source_url: HttpUrl
    source_type: str = Field(default="rss")
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False


class PublishResult(BaseModel):
    published: bool
    task_manager_id: Optional[str] = None
    reason: Optional[str] = None