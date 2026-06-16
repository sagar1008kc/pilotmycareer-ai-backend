"""Mental Fitness Support agent.

Supportive and educational only. Never diagnoses; surfaces crisis resources when crisis
signals are detected and always attaches a disclaimer.
"""

from __future__ import annotations

from app.models.wellness_models import WellnessCheckinResponse
from app.services import llm_service, prompt_service, safety_service

AGENT_NAME = "wellness"


def _content_from(message: str | None, answers: dict[str, str] | None) -> str:
    if message:
        return message
    if answers:
        return "\n".join(f"{k}: {v}" for k, v in answers.items())
    return ""


def run(message: str | None, answers: dict[str, str] | None) -> WellnessCheckinResponse:
    content = _content_from(message, answers)
    crisis = safety_service.detect_crisis(content)

    fallback = {
        "reflection": (
            "Thank you for checking in. It's completely understandable to feel this way, and "
            "noticing how you feel is a meaningful first step."
        ),
        "suggestions": [
            "Take a few slow breaths and name one small, manageable next step.",
            "Reach out to someone you trust to talk things through.",
            "Keep a simple daily routine to create a sense of stability.",
            "Consider speaking with a licensed professional for ongoing support.",
        ],
    }
    system, user = prompt_service.wellness_prompt(content)
    data, result = llm_service.generate_json(system, user, fallback=fallback)

    return WellnessCheckinResponse(
        agent=AGENT_NAME,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        reflection=str(data.get("reflection", "")),
        suggestions=list(data.get("suggestions", [])),
        crisis_flag=crisis,
        crisis_resources=safety_service.CRISIS_RESOURCES if crisis else [],
        disclaimer=safety_service.DISCLAIMER,
    )
