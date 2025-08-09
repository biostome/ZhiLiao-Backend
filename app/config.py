from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.getenv("ENV_FILE", ".env"), env_file_encoding="utf-8", extra="ignore")

    env: str = Field("dev", alias="ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Scheduler
    scheduler_cron: str = Field("*/10 * * * *", alias="SCHEDULER_CRON")

    # Task Manager API
    task_mgr_base_url: Optional[str] = Field(default=None, alias="TASK_MGR_BASE_URL")
    task_mgr_api_key: Optional[str] = Field(default=None, alias="TASK_MGR_API_KEY")

    # Data sources
    rss_feeds: List[str] = Field(default_factory=list, alias="RSS_FEEDS")

    # Optional infra
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # LLM via LiteLLM
    model_provider: str = Field("openai", alias="MODEL_PROVIDER")
    model_name: str = Field("gpt-4o-mini", alias="MODEL_NAME")

    # Provider keys are read from env by LiteLLM; include common ones for clarity
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    @field_validator("rss_feeds", mode="before")
    @classmethod
    def parse_rss_csv(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    def safe_dict(self) -> dict:
        data = self.model_dump()
        if data.get("task_mgr_api_key"):
            data["task_mgr_api_key"] = "***"
        if data.get("openai_api_key"):
            data["openai_api_key"] = "***"
        return data


settings = Settings()