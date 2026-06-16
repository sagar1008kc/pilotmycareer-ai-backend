"""Resume Optimizer agent."""

from __future__ import annotations

from app.models.resume_models import ResumeOptimizeResponse
from app.services import llm_service, prompt_service

AGENT_NAME = "resume_optimize"


def run(resume_text: str, job_title: str | None, job_description: str | None) -> ResumeOptimizeResponse:
    fallback = {
        "optimized_text": resume_text.strip(),
        "highlights": [
            "Lead bullets with strong action verbs and quantified outcomes.",
            "Tailor keywords to the target role for ATS compatibility.",
            "Move the most relevant experience to the top.",
        ],
    }
    system, user = prompt_service.resume_optimize_prompt(resume_text, job_title, job_description)
    data, result = llm_service.generate_json(system, user, fallback=fallback)

    return ResumeOptimizeResponse(
        agent=AGENT_NAME,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        optimized_text=str(data.get("optimized_text", "")),
        highlights=list(data.get("highlights", [])),
    )
