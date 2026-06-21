"""Centralized system/user prompt builders for each agent."""

from __future__ import annotations

import json
from typing import Any

MAX_CHARS = 14000


def _clip(text: str, limit: int = MAX_CHARS) -> str:
    return text[:limit]


def resume_match_prompt(
    *,
    cleaned_resume_text: str,
    cleaned_job_description: str,
    deterministic_score: int,
    score_breakdown: dict[str, int],
    input_quality: dict[str, Any],
    extracted_job_requirements: dict[str, list[str]],
    extracted_resume_sections: dict[str, str],
    matched_evidence: list[dict[str, str]],
    missing_requirements: list[dict[str, str]],
) -> tuple[str, str]:
    system = (
        "You are an expert ATS-aware resume analyzer. You compare a candidate resume against "
        "a job description using evidence, not keyword stuffing. You must not invent experience. "
        "You must return valid JSON only."
    )
    payload = {
        "cleaned_resume_text": _clip(cleaned_resume_text),
        "cleaned_job_description": _clip(cleaned_job_description),
        "deterministic_score": deterministic_score,
        "score_breakdown": score_breakdown,
        "input_quality": input_quality,
        "extracted_job_requirements": extracted_job_requirements,
        "extracted_resume_sections": extracted_resume_sections,
        "matched_evidence": matched_evidence,
        "missing_requirements": missing_requirements,
        "required_output_shape": {
            "summary": "string",
            "top_resume_fixes": ["string"],
            "matched_evidence": [
                {
                    "jd_requirement": "string",
                    "resume_evidence": "string",
                    "confidence": "high | medium | low",
                }
            ],
            "missing_requirements": [
                {
                    "requirement": "string",
                    "importance": "required | preferred",
                    "reason": "string",
                    "suggested_resume_line": "string",
                }
            ],
            "resume_rewrite_suggestions": [
                {
                    "section": "summary | skills | experience | projects | education",
                    "current_issue": "string",
                    "improved_bullet": "string",
                    "reason": "string",
                }
            ],
            "optimized_resume_text": "string",
        },
        "rules": [
            "Do not change or override deterministic_score or score_breakdown.",
            "If experience is missing, write template bullets with placeholders like [tool], [metric], [process], [team], [outcome].",
            "Do not fabricate specific numbers, employers, certifications, tools, years, or outcomes.",
            "Do not copy job-description sentences directly into the resume.",
            "Keep optimized_resume_text ATS-friendly, clean, and professional.",
            "Suggestions must be actionable inside a resume editor.",
        ],
    }
    user = json.dumps(payload, ensure_ascii=True)
    return system, user


def resume_optimize_prompt(resume_text: str, job_title: str | None,
                           job_description: str | None) -> tuple[str, str]:
    system = (
        "You are an expert resume writer and ATS-aware coach. Rewrite the resume to be sharp, "
        "metric-driven, and aligned with the target role. Return JSON only with keys: "
        '"optimized_text" (string) and "highlights" (string[] of key improvements).'
    )
    user = (
        f"Target title: {job_title or 'not specified'}\n"
        f"Target job description: {_clip(job_description or 'not provided', 4000)}\n\n"
        f"RESUME:\n{_clip(resume_text)}"
    )
    return system, user


def linkedin_optimize_prompt(profile_text: str, target_role: str | None) -> tuple[str, str]:
    system = (
        "You are a LinkedIn branding expert. Improve the profile for discoverability and impact. "
        'Return JSON only with keys: "headline" (string, <= 220 chars), "about" (string), '
        '"suggestions" (string[]).'
    )
    user = (
        f"Target role: {target_role or 'not specified'}\n\n"
        f"CURRENT PROFILE:\n{_clip(profile_text)}"
    )
    return system, user


def wellness_prompt(content: str) -> tuple[str, str]:
    system = (
        "You are a supportive, educational career-wellness companion. You are NOT a medical "
        "professional and you do NOT diagnose or provide crisis counseling. Be warm, validating, "
        "and practical. Encourage professional help when appropriate. Return JSON only with keys: "
        '"reflection" (string), "suggestions" (string[] of gentle, actionable ideas).'
    )
    user = f"User check-in:\n{_clip(content, 6000)}"
    return system, user


def rag_prompt(query: str, mode: str, context: str, role: str | None) -> tuple[str, str]:
    focus = (
        "Answer as an interview preparation coach with concrete examples and frameworks."
        if mode == "interview_prep"
        else "Answer as a career-resource assistant grounded in the provided context."
    )
    system = (
        f"{focus} Use only the provided context when relevant and be concise. "
        'Return JSON only with keys: "answer" (string).'
    )
    user = (
        f"Target role: {role or 'general'}\n\n"
        f"CONTEXT:\n{_clip(context, 8000)}\n\n"
        f"QUESTION:\n{query}"
    )
    return system, user


def intent_prompt(message: str, page_context: str | None) -> tuple[str, str]:
    system = (
        "Classify the user's request into exactly one intent. Return JSON only with key "
        '"intent" whose value is one of: resume_match, resume_optimize, linkedin, wellness, '
        "rag, interview_prep, general."
    )
    user = f"Page context: {page_context or 'none'}\n\nMessage: {message}"
    return system, user
