"""Optional direct database access via DATABASE_URL.

Primary persistence goes through the Supabase client (``supabase_service``). This module is a
placeholder for cases that need a direct SQL connection (e.g. analytics, batch jobs). It is
inert unless ``DATABASE_URL`` is set and a driver (asyncpg/SQLAlchemy) is installed.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("app.db")


def is_configured() -> bool:
    return bool(settings.database_url)


def get_engine():  # pragma: no cover - optional, enabled when a driver is added
    """Return a SQLAlchemy engine if DATABASE_URL + SQLAlchemy are available."""
    if not is_configured():
        return None
    try:
        from sqlalchemy import create_engine

        return create_engine(settings.database_url, pool_pre_ping=True)
    except Exception:
        logger.exception("Failed to create database engine")
        return None
