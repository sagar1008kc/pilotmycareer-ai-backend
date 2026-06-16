"""Shared LangGraph state passed between the supervisor and agent nodes."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    message: str
    page_context: str | None
    resume_text: str | None
    job_description: str | None
    request_id: str | None

    # Routing
    intent: str

    # Outputs
    agent: str
    response: str
    data: dict[str, Any]
    provider: str
    model: str


VALID_INTENTS = {
    "resume_match",
    "resume_optimize",
    "linkedin",
    "wellness",
    "rag",
    "interview_prep",
    "general",
}
