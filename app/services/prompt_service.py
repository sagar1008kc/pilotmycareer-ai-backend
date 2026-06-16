"""Centralized system/user prompt builders for each agent."""

from __future__ import annotations

MAX_CHARS = 14000


def _clip(text: str, limit: int = MAX_CHARS) -> str:
    return text[:limit]


def resume_match_prompt(resume_text: str, job_description: str, score: int,
                        matched: list[str], missing: list[str]) -> tuple[str, str]:
    system = (
        "You are an ATS-aware career coach. A deterministic engine already computed the match "
        "score and skill lists. Use them as ground truth. Return JSON only with keys: "
        '"recommended_edits" (string[]), "interview_questions" (string[]), '
        '"explanation" (string). Do not restate the score.'
    )
    user = (
        f"Match score: {score}\n"
        f"Matched skills: {', '.join(matched) or 'none'}\n"
        f"Missing skills: {', '.join(missing) or 'none'}\n\n"
        f"RESUME:\n{_clip(resume_text)}\n\n"
        f"JOB DESCRIPTION:\n{_clip(job_description)}"
    )
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
