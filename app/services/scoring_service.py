"""Deterministic resume <-> job description matching.

Compatibility wrapper around the evidence-based resume analyzer. New code should use
``resume_analysis_service.evidence_score`` when it needs the full analyzer payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services import resume_analysis_service


@dataclass
class MatchResult:
    score: int
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    extra_keywords: list[str] = field(default_factory=list)
    score_breakdown: dict[str, int] = field(default_factory=dict)
    input_quality: dict[str, Any] = field(default_factory=dict)


def extract_skills(text: str) -> set[str]:
    """Extract known skills from text using the curated vocabulary."""
    return resume_analysis_service.extract_skills(text)


def match_resume_to_job(resume_text: str, job_description: str) -> MatchResult:
    """Compute a reproducible weighted match score and compatibility skill lists."""
    analysis = resume_analysis_service.evidence_score(resume_text, job_description)
    return MatchResult(
        score=int(analysis["overall_score"]),
        matched_skills=list(analysis.get("matched_skills", [])),
        missing_skills=list(analysis.get("missing_skills", [])),
        extra_keywords=list(analysis.get("extra_keywords", [])),
        score_breakdown=dict(analysis.get("score_breakdown", {})),
        input_quality=dict(analysis.get("input_quality", {})),
    )
