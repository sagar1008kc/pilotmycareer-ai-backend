"""Resume + JD Matcher agent.

Deterministic scoring (no LLM) produces the score and skill lists. The LLM only writes the
narrative explanation, recommended edits, and interview questions, with deterministic
fallbacks when the LLM is unavailable.
"""

from __future__ import annotations

from app.models.resume_models import ResumeMatchResponse
from app.services import llm_service, prompt_service, scoring_service

AGENT_NAME = "resume_match"


def _fallback_edits(missing: list[str], matched: list[str]) -> dict:
    edits: list[str] = []
    if missing:
        edits.append(
            "Add concrete experience or keywords for: " + ", ".join(missing[:6]) + "."
        )
    if matched:
        edits.append(
            "Quantify impact for your strengths (" + ", ".join(matched[:4]) + ") with metrics."
        )
    edits.append("Mirror the job description's terminology to improve ATS matching.")
    edits.append("Lead each bullet with an action verb and a measurable result.")

    questions = [
        "Walk me through a project where you used "
        + (matched[0] if matched else "your core skills")
        + ".",
        "How would you ramp up on "
        + (missing[0] if missing else "a technology new to you")
        + "?",
        "Describe a time you improved a system's performance or reliability.",
        "Tell me about a challenging stakeholder situation and how you handled it.",
    ]
    return {"recommended_edits": edits, "interview_questions": questions}


def run(resume_text: str, job_description: str) -> ResumeMatchResponse:
    match = scoring_service.match_resume_to_job(resume_text, job_description)

    fallback_extra = _fallback_edits(match.missing_skills, match.matched_skills)
    coverage_word = (
        "strong" if match.score >= 70 else "moderate" if match.score >= 45 else "limited"
    )
    fallback = {
        "recommended_edits": fallback_extra["recommended_edits"],
        "interview_questions": fallback_extra["interview_questions"],
        "explanation": (
            f"The resume shows {coverage_word} alignment with the role "
            f"({match.score}/100). Matched skills: "
            f"{', '.join(match.matched_skills) or 'none detected'}. "
            f"Key gaps: {', '.join(match.missing_skills) or 'none detected'}."
        ),
    }

    system, user = prompt_service.resume_match_prompt(
        resume_text, job_description, match.score, match.matched_skills, match.missing_skills
    )
    data, result = llm_service.generate_json(system, user, fallback=fallback)

    return ResumeMatchResponse(
        agent=AGENT_NAME,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        score=match.score,
        matched_skills=match.matched_skills,
        missing_skills=match.missing_skills,
        recommended_edits=list(data.get("recommended_edits", [])),
        interview_questions=list(data.get("interview_questions", [])),
        explanation=str(data.get("explanation", "")),
    )
