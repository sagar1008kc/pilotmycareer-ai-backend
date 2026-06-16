"""Guardrails for the Mental Fitness Support agent.

The agent is supportive and educational only. This service detects potential crisis signals so
the response can surface professional resources. It is intentionally conservative: it never
diagnoses and always errs toward providing help resources.
"""

from __future__ import annotations

import re

DISCLAIMER = (
    "This is supportive, educational guidance only and is not a substitute for professional "
    "medical or mental-health care. If you are in crisis, please contact a professional or one "
    "of the resources below."
)

CRISIS_RESOURCES = [
    "988 Suicide & Crisis Lifeline (US): call or text 988",
    "Crisis Text Line: text HOME to 741741 (US)",
    "International Association for Suicide Prevention directory: https://www.iasp.info/resources/Crisis_Centres/",
    "If you are in immediate danger, call your local emergency number.",
]

_CRISIS_PATTERNS = [
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bsuicid",
    r"\bself[\s-]?harm\b",
    r"\bhurt myself\b",
    r"\bwant to die\b",
    r"\bno reason to live\b",
    r"\bcan't go on\b",
    r"\bharm myself\b",
]

_CRISIS_RE = re.compile("|".join(_CRISIS_PATTERNS), re.IGNORECASE)


def detect_crisis(text: str) -> bool:
    """Return True if the text contains potential crisis signals."""
    if not text:
        return False
    return bool(_CRISIS_RE.search(text))
