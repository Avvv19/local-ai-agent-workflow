"""
Application settings loaded from environment variables.

Uses pydantic-settings for type-safe env var loading.
All secrets come from .env (never hardcoded).
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # LangSmith
    langchain_tracing_v2: str = Field(default="true", alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="document-automation", alias="LANGCHAIN_PROJECT")

    # Storage
    db_path: str = Field(default="data/audit.db", alias="DB_PATH")

    # App
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    confidence_threshold: float = Field(default=0.85, alias="CONFIDENCE_THRESHOLD")
    max_retry_attempts: int = Field(default=3, alias="MAX_RETRY_ATTEMPTS")

    class Config:
        env_file = ".env"
        populate_by_name = True


settings = Settings()
