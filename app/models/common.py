"""Shared models used across requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthUser(BaseModel):
    """Authenticated user derived from a Supabase JWT (or dev mock)."""

    user_id: str
    email: str | None = None
    role: str = "authenticated"
    # Optional enrichment from profiles / entitlements (best effort)
    plan: str | None = None
    plan_key: str | None = None
    unlimited: bool | None = None


class Usage(BaseModel):
    """Token usage for an LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ResponseMeta(BaseModel):
    """Metadata attached to every agent response."""

    request_id: str | None = None
    agent: str | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int = 0
    usage: Usage = Field(default_factory=Usage)
