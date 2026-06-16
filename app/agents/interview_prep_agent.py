"""Interview Prep agent.

Shares the retrieval pipeline with the RAG agent but always uses interview-prep framing.
"""

from __future__ import annotations

from app.agents import rag_resource_agent
from app.models.chat_models import RagQueryResponse

AGENT_NAME = "interview_prep"


def run(query: str, top_k: int = 4, role: str | None = None) -> RagQueryResponse:
    return rag_resource_agent.run(query, mode="interview_prep", top_k=top_k, role=role)
