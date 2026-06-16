"""LinkedIn optimizer endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.agents import linkedin_optimizer_agent
from app.api.deps import finalize, start_timer
from app.core.security import get_current_user
from app.models.common import AuthUser
from app.models.linkedin_models import LinkedInOptimizeRequest, LinkedInOptimizeResponse
from app.services import report_service

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.post("/optimize", response_model=LinkedInOptimizeResponse)
async def linkedin_optimize(
    payload: LinkedInOptimizeRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> LinkedInOptimizeResponse:
    timer = start_timer(request)
    result = linkedin_optimizer_agent.run(payload.profile_text, payload.target_role)
    finalize(result, timer, user.user_id)
    report_service.save_report(
        user.user_id,
        result.agent or "linkedin",
        result.model_dump(),
        title="LinkedIn optimization",
        model=result.model,
        provider=result.provider,
    )
    return result
