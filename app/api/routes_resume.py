"""Resume matcher and optimizer endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.agents import resume_matcher_agent, resume_optimizer_agent
from app.api.deps import finalize, start_timer
from app.core.security import get_current_user
from app.models.common import AuthUser
from app.models.resume_models import (
    ResumeMatchRequest,
    ResumeMatchResponse,
    ResumeOptimizeRequest,
    ResumeOptimizeResponse,
)
from app.services import report_service

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/match", response_model=ResumeMatchResponse)
async def resume_match(
    payload: ResumeMatchRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> ResumeMatchResponse:
    timer = start_timer(request)
    result = resume_matcher_agent.run(payload.resume_text, payload.job_description)
    finalize(result, timer, user.user_id)
    report_service.save_report(
        user.user_id,
        result.agent or "resume_match",
        result.model_dump(),
        title="Resume match report",
        model=result.model,
        provider=result.provider,
    )
    return result


@router.post("/optimize", response_model=ResumeOptimizeResponse)
async def resume_optimize(
    payload: ResumeOptimizeRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> ResumeOptimizeResponse:
    timer = start_timer(request)
    result = resume_optimizer_agent.run(
        payload.resume_text, payload.job_title, payload.job_description
    )
    finalize(result, timer, user.user_id)
    report_service.save_report(
        user.user_id,
        result.agent or "resume_optimize",
        result.model_dump(),
        title="Resume optimization",
        model=result.model,
        provider=result.provider,
    )
    return result
