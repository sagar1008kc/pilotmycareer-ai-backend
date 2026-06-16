"""General dashboard chat endpoint that routes to the right agent via LangGraph."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.agents.graph import get_graph
from app.api.deps import finalize, start_timer
from app.core.security import get_current_user
from app.models.chat_models import ChatRequest, ChatResponse
from app.models.common import AuthUser, Usage

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    user: AuthUser = Depends(get_current_user),
) -> ChatResponse:
    timer = start_timer(request)

    graph = get_graph()
    state = graph.invoke(
        {
            "message": payload.message,
            "page_context": payload.page_context,
            "resume_text": payload.resume_text,
            "job_description": payload.job_description,
            "request_id": getattr(request.state, "request_id", None),
        }
    )

    data = state.get("data") or {}
    usage = Usage(**data.get("usage", {})) if isinstance(data.get("usage"), dict) else Usage()

    result = ChatResponse(
        agent=state.get("agent", "general"),
        intent=state.get("intent", "general"),
        response=state.get("response", ""),
        data=data or None,
        provider=state.get("provider", "system"),
        model=state.get("model", "n/a"),
        usage=usage,
    )
    finalize(result, timer, user.user_id)
    return result
