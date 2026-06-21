"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings sourced from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Pilot My Career AI Backend"
    app_env: str = "local"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    # LLM
    llm_provider: Literal["openai", "grok", "gemini", "claude", "mock"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Auth
    auth_mode: Literal["dev", "supabase"] = "supabase"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_service_role_key: str = ""

    # Persistence
    supabase_persist: bool = False

    # Optional infra
    database_url: str = ""
    redis_url: str = ""

    # Vector
    vector_provider: Literal["local", "qdrant"] = "local"
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Comma-separated origins allowed for browser requests."""
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
