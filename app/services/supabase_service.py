"""Lazy, optional Supabase access using the backend-only service role key.

This module never raises at import time. Callers must check `is_configured()` (or rely on
the helpers returning ``None``) so the API works fully even when Supabase is not configured.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.supabase")


def is_configured() -> bool:
    return settings.supabase_configured


@lru_cache
def _service_client() -> Any | None:
    """Return a cached service-role Supabase client, or ``None`` if unavailable."""
    if not settings.supabase_configured:
        return None
    try:
        from supabase import create_client

        return create_client(settings.supabase_url, settings.supabase_service_role_key)
    except Exception:  # pragma: no cover - defensive: missing dep / bad config
        logger.exception("Failed to create Supabase service client")
        return None


def _user_client(access_token: str) -> Any | None:
    """Return a client scoped to the user's token so RLS policies apply."""
    if not (settings.supabase_url and settings.supabase_anon_key):
        return None
    try:
        from supabase import create_client

        client = create_client(settings.supabase_url, settings.supabase_anon_key)
        client.postgrest.auth(access_token)
        return client
    except Exception:  # pragma: no cover
        logger.exception("Failed to create Supabase user client")
        return None


def fetch_user_profile(user_id: str) -> dict[str, Any] | None:
    """Read profile + entitlements for plan/limit enrichment (best effort)."""
    client = _service_client()
    if client is None:
        return None
    try:
        profile_res = (
            client.table("profiles")
            .select("plan, role")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        ent_res = (
            client.table("entitlements")
            .select("plan_key, unlimited")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        profile = getattr(profile_res, "data", None) or {}
        ent = getattr(ent_res, "data", None) or {}
        return {**profile, **ent}
    except Exception:  # pragma: no cover - enrichment is best effort
        logger.warning("Profile enrichment failed", extra={"user_id": user_id})
        return None


def insert_row(table: str, row: dict[str, Any]) -> dict[str, Any] | None:
    """Insert a row using the service role. Returns the inserted row or ``None``."""
    client = _service_client()
    if client is None:
        return None
    try:
        res = client.table(table).insert(row).execute()
        data = getattr(res, "data", None)
        return data[0] if data else None
    except Exception:
        logger.exception("Insert failed", extra={"agent": table})
        return None


def fetch_user_reports(access_token: str, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """Read the user's own ai_reports rows (RLS-scoped via the user token)."""
    client = _user_client(access_token)
    if client is None:
        return []
    try:
        res = (
            client.table("ai_reports")
            .select("id, agent, title, content, model, provider, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return getattr(res, "data", None) or []
    except Exception:
        logger.warning("Report history read failed", extra={"user_id": user_id})
        return []
