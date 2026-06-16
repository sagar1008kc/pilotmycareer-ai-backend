"""Aggregate API router mounted under the configured API prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    routes_chat,
    routes_health,
    routes_linkedin,
    routes_rag,
    routes_reports,
    routes_resume,
    routes_wellness,
)

api_router = APIRouter()
api_router.include_router(routes_health.router)
api_router.include_router(routes_chat.router)
api_router.include_router(routes_resume.router)
api_router.include_router(routes_linkedin.router)
api_router.include_router(routes_wellness.router)
api_router.include_router(routes_rag.router)
api_router.include_router(routes_reports.router)
