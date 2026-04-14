"""Application settings via pydantic-settings."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "saengibu-portal"
    environment: str = "development"

    database_url: str = Field(..., description="PostgreSQL DSN")
    redis_url: str = Field("redis://localhost:6379/0")

    jwt_secret: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 24

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    llm_default_model: str = "claude-sonnet-4-6"

    embedding_model: str = "jhgan/ko-sroberta-multitask"

    rules_version: str = "2026-03"


@lru_cache
def get_settings() -> Settings:
    return Settings()
