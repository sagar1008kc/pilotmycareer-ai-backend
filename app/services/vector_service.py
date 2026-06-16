"""Lightweight retrieval for the RAG / interview-prep agent.

The local provider performs a deterministic keyword-overlap search over a small in-memory
knowledge base. A Qdrant-backed provider can be added later behind the same ``search`` API.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import settings

_WORD_RE = re.compile(r"[a-zA-Z]{3,}")


@dataclass
class Document:
    title: str
    text: str


# Small seed knowledge base. Replace/extend with real content or a vector DB later.
KNOWLEDGE_BASE: list[Document] = [
    Document(
        title="STAR method for behavioral interviews",
        text=(
            "Use the STAR method to answer behavioral questions: describe the Situation, the "
            "Task you were responsible for, the Action you took, and the Result you achieved. "
            "Quantify results whenever possible and keep answers under two minutes."
        ),
    ),
    Document(
        title="Answering 'Tell me about yourself'",
        text=(
            "Structure 'tell me about yourself' as present, past, future: what you do now, "
            "relevant experience that led here, and why you are excited about this role. Keep it "
            "to 60-90 seconds and tailor it to the job."
        ),
    ),
    Document(
        title="Technical interview preparation",
        text=(
            "For technical interviews, practice data structures and algorithms, explain your "
            "thought process out loud, clarify requirements before coding, discuss tradeoffs, "
            "and test your solution with edge cases. Review system design fundamentals for "
            "senior roles."
        ),
    ),
    Document(
        title="Salary negotiation basics",
        text=(
            "When negotiating salary, research market ranges, let the employer state a number "
            "first when possible, anchor on total compensation, and respond to offers with "
            "gratitude plus a researched counter. Never accept on the spot if you need time."
        ),
    ),
    Document(
        title="Resume best practices",
        text=(
            "Strong resumes lead with measurable impact, use action verbs, tailor keywords to "
            "the job description for ATS, keep to one or two pages, and avoid generic duties. "
            "Quantify achievements with numbers and outcomes."
        ),
    ),
    Document(
        title="Handling layoffs and career transitions",
        text=(
            "After a layoff, focus on what you can control: update your resume and LinkedIn, "
            "build a target company list, activate your network, and maintain a routine. "
            "Frame the transition positively and emphasize transferable skills."
        ),
    ),
]


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)}


def search(query: str, top_k: int = 4) -> list[tuple[Document, float]]:
    """Return the top_k documents ranked by keyword overlap with the query."""
    if settings.vector_provider == "qdrant":
        # Placeholder: Qdrant integration goes here behind the same interface.
        pass

    q_tokens = _tokens(query)
    if not q_tokens:
        return []
    scored: list[tuple[Document, float]] = []
    for doc in KNOWLEDGE_BASE:
        d_tokens = _tokens(doc.title + " " + doc.text)
        overlap = len(q_tokens & d_tokens)
        if overlap:
            score = overlap / len(q_tokens)
            scored.append((doc, round(score, 3)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]
