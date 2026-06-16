"""AI Resource / RAG and interview-prep endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.agents import rag_resource_agent
from app.api.deps import finalize, start_timer
from app.core.security import get_current_user
from app.models.chat_models import RagQueryRequest, RagQueryResponse

from app.models.common import AuthUser

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(
    payload: RagQueryRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> RagQueryResponse:
    timer = start_timer(request)
    result = rag_resource_agent.run(
        payload.query, mode=payload.mode, top_k=payload.top_k, role=payload.role
    )
    finalize(result, timer, user.user_id)
    return result
