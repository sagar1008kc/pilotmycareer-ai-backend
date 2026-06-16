"""Health check endpoint (no auth)."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": __version__,
        "provider": settings.llm_provider,
        "auth_mode": settings.auth_mode,
    }
