"""Application settings via pydantic-settings."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "saengibu-portal"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://saengibu:saengibu@localhost:5432/saengibu",
        description="PostgreSQL async DSN",
    )

    # Session / CSRF
    session_secret: str = Field(
        "change-me-to-a-long-random-secret-at-least-32-chars-for-jwt",
        min_length=32,
    )
    session_cookie_name: str = "saengibu_session"
    csrf_cookie_name: str = "csrf_token"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 24
    cookie_secure: bool = True  # HTTPS only — dev에서는 override
    cookie_domain: str | None = None
    cookie_samesite: str = "strict"  # 'strict' | 'lax'

    # Google OAuth
    google_client_id: str = Field("", description="Google OAuth 2.0 Client ID")

    # 학교 이메일 도메인 화이트리스트 (콤마 구분). 비어 있으면 모든 도메인 허용(개발용).
    allowed_email_domains: str = ""

    # CORS (프록시 사용 시 비워둠)
    cors_origins: str = ""

    # AI (외부 LLM 사용 여부 — 기본은 외부 차단)
    llm_external_enabled: bool = False
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    llm_default_model: str = "claude-sonnet-4-6"

    # Rules version
    rules_version: str = "2026-03"

    @property
    def allowed_domains_list(self) -> list[str]:
        return [d.strip().lower() for d in self.allowed_email_domains.split(",") if d.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
