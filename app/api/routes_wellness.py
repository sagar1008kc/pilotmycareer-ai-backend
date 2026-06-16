"""Mental fitness support endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.agents import mental_fitness_agent
from app.api.deps import finalize, start_timer
from app.core.security import get_current_user
from app.models.common import AuthUser
from app.models.wellness_models import WellnessCheckinRequest, WellnessCheckinResponse

router = APIRouter(prefix="/wellness", tags=["wellness"])


@router.post("/checkin", response_model=WellnessCheckinResponse)
async def wellness_checkin(
    payload: WellnessCheckinRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> WellnessCheckinResponse:
    timer = start_timer(request)
    result = mental_fitness_agent.run(payload.message, payload.answers)
    finalize(result, timer, user.user_id)
    # Note: wellness content is intentionally NOT persisted as a report by default.
    return result
