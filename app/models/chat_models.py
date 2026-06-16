"""Chat and RAG request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import ResponseMeta


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    page_context: str | None = Field(
        default=None,
        description="Frontend page hint used to bias intent routing (e.g. 'resume_match').",
    )
    history: list[ChatMessage] = Field(default_factory=list)
    # Optional payloads so chat can drive a specific agent directly.
    resume_text: str | None = None
    job_description: str | None = None


class ChatResponse(ResponseMeta):
    intent: str = ""
    response: str = ""
    data: dict | None = None


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    mode: Literal["resource", "interview_prep"] = "resource"
    top_k: int = Field(default=4, ge=1, le=20)
    role: str | None = None


class RagSource(BaseModel):
    title: str
    snippet: str
    score: float = 0.0


class RagQueryResponse(ResponseMeta):
    answer: str = ""
    sources: list[RagSource] = Field(default_factory=list)
