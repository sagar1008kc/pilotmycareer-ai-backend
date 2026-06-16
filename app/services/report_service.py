"""Persist AI reports and usage logs to Supabase (config gated).

All functions are no-ops unless ``SUPABASE_PERSIST=true`` and the service role is configured,
so the API works fully without persistence. Usage logs never store raw resume/JD content.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.models.common import ResponseMeta
from app.services import supabase_service

logger = get_logger("app.services.report")


def persistence_enabled() -> bool:
    return settings.supabase_persist and supabase_service.is_configured()


def save_report(
    user_id: str,
    agent: str,
    content: dict[str, Any],
    *,
    title: str | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> dict[str, Any] | None:
    """Insert an ai_reports row. Returns the row, or ``None`` when disabled."""
    if not persistence_enabled():
        return None
    return supabase_service.insert_row(
        "ai_reports",
        {
            "user_id": user_id,
            "agent": agent,
            "title": title,
            "content": content,
            "model": model,
            "provider": provider,
        },
    )


def log_usage(user_id: str, agent: str, meta: ResponseMeta, status: str = "ok") -> None:
    """Insert an ai_usage_logs row with token/latency metadata (no raw content)."""
    if not persistence_enabled():
        return
    supabase_service.insert_row(
        "ai_usage_logs",
        {
            "user_id": user_id,
            "request_id": meta.request_id,
            "agent": agent or meta.agent,
            "model": meta.model,
            "provider": meta.provider,
            "prompt_tokens": meta.usage.prompt_tokens,
            "completion_tokens": meta.usage.completion_tokens,
            "total_tokens": meta.usage.total_tokens,
            "latency_ms": meta.latency_ms,
            "status": status,
        },
    )
