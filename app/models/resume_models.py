"""Resume matcher and optimizer models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.common import ResponseMeta

MAX_RESUME_ANALYZER_INPUT_CHARS = 20_000


def _looks_repetitive(value: str) -> bool:
    normalized = " ".join(value.lower().split())
    if not normalized:
        return True
    words = normalized.split()
    if len(words) >= 30 and len(set(words)) / len(words) < 0.12:
        return True
    chunks = [normalized[i : i + 80] for i in range(0, len(normalized), 80)]
    return len(chunks) >= 5 and len(set(chunks)) <= 2


class ResumeMatchRequest(BaseModel):
    resume_text: str = Field(
        min_length=30,
        max_length=MAX_RESUME_ANALYZER_INPUT_CHARS,
        description="Plain-text resume content",
    )
    job_description: str = Field(
        min_length=30,
        max_length=MAX_RESUME_ANALYZER_INPUT_CHARS,
        description="Plain-text job description",
    )

    @field_validator("resume_text", "job_description")
    @classmethod
    def reject_spammy_input(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Input cannot be empty")
        if _looks_repetitive(value):
            raise ValueError("Input is too repetitive to analyze")
        return value


class InputQuality(BaseModel):
    resume_looks_valid: bool = True
    jd_looks_valid: bool = True
    copied_jd_detected: bool = False
    resume_warning: str = ""
    jd_warning: str = ""


class ScoreBreakdown(BaseModel):
    skills: int = Field(ge=0, le=25)
    experience: int = Field(ge=0, le=25)
    tools: int = Field(ge=0, le=15)
    impact: int = Field(ge=0, le=15)
    keywords: int = Field(ge=0, le=10)
    formatting: int = Field(ge=0, le=10)


class MatchedEvidence(BaseModel):
    jd_requirement: str = ""
    resume_evidence: str = ""
    confidence: Literal["high", "medium", "low"] = "low"


class MissingRequirement(BaseModel):
    requirement: str = ""
    importance: Literal["required", "preferred"] = "required"
    reason: str = ""
    suggested_resume_line: str = ""


class ResumeRewriteSuggestion(BaseModel):
    section: Literal["summary", "skills", "experience", "projects", "education"] = "experience"
    current_issue: str = ""
    improved_bullet: str = ""
    reason: str = ""


class ResumeMatchResponse(ResponseMeta):
    input_quality: InputQuality = Field(default_factory=InputQuality)
    overall_score: int = Field(ge=0, le=100)
    score_label: Literal["Weak match", "Moderate match", "Strong match", "Excellent match"]
    score_breakdown: ScoreBreakdown
    summary: str = ""
    top_resume_fixes: list[str] = Field(default_factory=list)
    matched_evidence: list[MatchedEvidence] = Field(default_factory=list)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list)
    resume_rewrite_suggestions: list[ResumeRewriteSuggestion] = Field(default_factory=list)
    optimized_resume_text: str = ""

    # Temporary backward-compatible fields for existing frontend consumers.
    score: int = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    recommended_edits: list[str] = Field(default_factory=list)
    explanation: str = ""


class ResumeOptimizeRequest(BaseModel):
    resume_text: str = Field(min_length=30)
    job_title: str | None = None
    job_description: str | None = None


class ResumeOptimizeResponse(ResponseMeta):
    optimized_text: str = ""
    highlights: list[str] = Field(default_factory=list)
