"""LinkedIn optimizer models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.common import ResponseMeta


class LinkedInOptimizeRequest(BaseModel):
    profile_text: str = Field(min_length=30, description="Current LinkedIn profile text")
    target_role: str | None = None


class LinkedInOptimizeResponse(ResponseMeta):
    headline: str = ""
    about: str = ""
    suggestions: list[str] = Field(default_factory=list)
