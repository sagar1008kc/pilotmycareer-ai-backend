"""AI report history and generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user
from app.models.common import AuthUser
from app.models.report_models import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportHistoryResponse,
    ReportRecord,
)
from app.services import report_service, supabase_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/history", response_model=ReportHistoryResponse)
async def reports_history(
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> ReportHistoryResponse:
    request_id = getattr(request.state, "request_id", None)
    access_token = getattr(request.state, "access_token", "")
    rows: list[dict] = []
    if report_service.persistence_enabled() and access_token:
        rows = supabase_service.fetch_user_reports(access_token, user.user_id)
    reports = [ReportRecord(**row) for row in rows]
    return ReportHistoryResponse(
        reports=reports,
        persisted=report_service.persistence_enabled(),
        request_id=request_id,
    )


@router.post("/generate", response_model=ReportGenerateResponse)
async def reports_generate(
    payload: ReportGenerateRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> ReportGenerateResponse:
    request_id = getattr(request.state, "request_id", None)
    saved = report_service.save_report(
        user.user_id,
        payload.agent,
        payload.content,
        title=payload.title,
    )
    record = ReportRecord(**saved) if saved else ReportRecord(
        agent=payload.agent, title=payload.title, content=payload.content
    )
    return ReportGenerateResponse(
        report=record,
        persisted=saved is not None,
        request_id=request_id,
    )
