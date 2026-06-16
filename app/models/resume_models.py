"""Resume matcher and optimizer models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.common import ResponseMeta


class ResumeMatchRequest(BaseModel):
    resume_text: str = Field(min_length=30, description="Plain-text resume content")
    job_description: str = Field(min_length=30, description="Plain-text job description")


class ResumeMatchResponse(ResponseMeta):
    score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommended_edits: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    explanation: str = ""


class ResumeOptimizeRequest(BaseModel):
    resume_text: str = Field(min_length=30)
    job_title: str | None = None
    job_description: str | None = None


class ResumeOptimizeResponse(ResponseMeta):
    optimized_text: str = ""
    highlights: list[str] = Field(default_factory=list)
