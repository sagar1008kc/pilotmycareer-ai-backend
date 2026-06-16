"""LinkedIn Optimizer agent."""

from __future__ import annotations

from app.models.linkedin_models import LinkedInOptimizeResponse
from app.services import llm_service, prompt_service

AGENT_NAME = "linkedin"


def run(profile_text: str, target_role: str | None) -> LinkedInOptimizeResponse:
    role = target_role or "your target role"
    fallback = {
        "headline": f"Results-driven professional focused on {role} | Open to opportunities",
        "about": (
            "Experienced professional with a track record of measurable impact. "
            "Passionate about solving meaningful problems and growing with strong teams."
        ),
        "suggestions": [
            "Add a keyword-rich headline aligned with your target role.",
            "Quantify achievements in the About and Experience sections.",
            "Request recommendations from colleagues and managers.",
            "Use a professional photo and a clear, scannable About section.",
        ],
    }
    system, user = prompt_service.linkedin_optimize_prompt(profile_text, target_role)
    data, result = llm_service.generate_json(system, user, fallback=fallback)

    return LinkedInOptimizeResponse(
        agent=AGENT_NAME,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        headline=str(data.get("headline", "")),
        about=str(data.get("about", "")),
        suggestions=list(data.get("suggestions", [])),
    )
