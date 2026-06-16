"""AI Resource / RAG agent (also serves interview-prep mode)."""

from __future__ import annotations

from app.models.chat_models import RagQueryResponse, RagSource
from app.services import llm_service, prompt_service, vector_service

AGENT_NAME = "rag"


def run(query: str, mode: str, top_k: int, role: str | None) -> RagQueryResponse:
    hits = vector_service.search(query, top_k=top_k)
    sources = [
        RagSource(title=doc.title, snippet=doc.text, score=score) for doc, score in hits
    ]
    context = "\n\n".join(f"[{doc.title}]\n{doc.text}" for doc, _ in hits)

    if sources:
        fallback_answer = (
            f"{sources[0].snippet} "
            "(Based on the most relevant resource in the knowledge base.)"
        )
    else:
        fallback_answer = (
            "I don't have a specific resource for that yet. As a general tip, break the problem "
            "into concrete steps and practice articulating your reasoning out loud."
        )

    system, user = prompt_service.rag_prompt(query, mode, context, role)
    data, result = llm_service.generate_json(system, user, fallback={"answer": fallback_answer})

    return RagQueryResponse(
        agent=AGENT_NAME if mode == "resource" else "interview_prep",
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        answer=str(data.get("answer", "")),
        sources=sources,
    )
