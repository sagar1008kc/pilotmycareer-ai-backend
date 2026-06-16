"""Supervisor: classify intent and route to the correct agent.

Rule-based classification using ``page_context`` and keywords runs first; the LLM is used as a
fallback when rules are inconclusive. Falls back to mock-safe heuristics with no key.
"""

from __future__ import annotations

import re

from app.agents.state import VALID_INTENTS
from app.services import llm_service, prompt_service

# Map common frontend page hints to intents.
PAGE_CONTEXT_MAP = {
    "resume_match": "resume_match",
    "resume-match": "resume_match",
    "resume_optimize": "resume_optimize",
    "resume-optimizer": "resume_optimize",
    "linkedin": "linkedin",
    "linkedin-optimizer": "linkedin",
    "wellness": "wellness",
    "mental-fitness": "wellness",
    "interview": "interview_prep",
    "interview-prep": "interview_prep",
    "resources": "rag",
    "rag": "rag",
}

_KEYWORD_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bmatch\b.*\bjob\b|\bjob description\b|\bjd\b|\bfit\b", re.I), "resume_match"),
    (re.compile(r"\boptimi[sz]e\b.*\bresume\b|\brewrite\b.*\bresume\b", re.I), "resume_optimize"),
    (re.compile(r"\blinkedin\b", re.I), "linkedin"),
    (re.compile(r"\binterview\b", re.I), "interview_prep"),
    (re.compile(r"\bstress|anxious|burn ?out|overwhelm|mental|wellbeing|well-being|cope\b", re.I), "wellness"),
    (re.compile(r"\bresume\b", re.I), "resume_optimize"),
]


def classify(message: str, page_context: str | None) -> str:
    if page_context:
        mapped = PAGE_CONTEXT_MAP.get(page_context.strip().lower())
        if mapped:
            return mapped

    for pattern, intent in _KEYWORD_RULES:
        if pattern.search(message):
            return intent

    # LLM fallback (returns mock-safe 'general' when no key configured).
    system, user = prompt_service.intent_prompt(message, page_context)
    data, _ = llm_service.generate_json(system, user, fallback={"intent": "general"})
    intent = str(data.get("intent", "general"))
    return intent if intent in VALID_INTENTS else "general"
