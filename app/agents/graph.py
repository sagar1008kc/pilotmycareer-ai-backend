"""LangGraph supervisor workflow.

A single graph routes a request to exactly one agent based on the classified intent. Feature
endpoints call agent ``run`` functions directly; the ``/chat`` endpoint uses this graph to
classify and route. The compiled graph is cached.
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.agents import (
    linkedin_optimizer_agent,
    mental_fitness_agent,
    rag_resource_agent,
    resume_matcher_agent,
    resume_optimizer_agent,
    supervisor_agent,
)
from app.agents.state import AgentState


def _supervisor_node(state: AgentState) -> dict:
    intent = state.get("intent") or supervisor_agent.classify(
        state.get("message", ""), state.get("page_context")
    )
    return {"intent": intent}


def _need(text: str) -> dict:
    return {"response": text, "data": {}, "provider": "system", "model": "n/a"}


def _resume_match_node(state: AgentState) -> dict:
    resume = state.get("resume_text")
    jd = state.get("job_description")
    if not resume or not jd:
        return {"agent": "resume_match", **_need(
            "Please provide both your resume text and the job description to run a match."
        )}
    res = resume_matcher_agent.run(resume, jd)
    return {
        "agent": res.agent,
        "response": res.explanation,
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _resume_optimize_node(state: AgentState) -> dict:
    resume = state.get("resume_text") or state.get("message", "")
    if not resume:
        return {"agent": "resume_optimize", **_need("Please share your resume text to optimize.")}
    res = resume_optimizer_agent.run(resume, None, state.get("job_description"))
    return {
        "agent": res.agent,
        "response": "Here is an optimized version of your resume.",
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _linkedin_node(state: AgentState) -> dict:
    profile = state.get("resume_text") or state.get("message", "")
    res = linkedin_optimizer_agent.run(profile, None)
    return {
        "agent": res.agent,
        "response": res.headline,
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _wellness_node(state: AgentState) -> dict:
    res = mental_fitness_agent.run(state.get("message", ""), None)
    return {
        "agent": res.agent,
        "response": res.reflection,
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _rag_node(state: AgentState) -> dict:
    res = rag_resource_agent.run(state.get("message", ""), mode="resource", top_k=4, role=None)
    return {
        "agent": res.agent,
        "response": res.answer,
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _interview_node(state: AgentState) -> dict:
    res = rag_resource_agent.run(state.get("message", ""), mode="interview_prep", top_k=4, role=None)
    return {
        "agent": res.agent,
        "response": res.answer,
        "data": res.model_dump(),
        "provider": res.provider,
        "model": res.model,
    }


def _general_node(state: AgentState) -> dict:
    return {
        "agent": "general",
        "response": (
            "I can help with resume matching, resume and LinkedIn optimization, interview prep, "
            "career resources, and wellness check-ins. What would you like to work on?"
        ),
        "data": {},
        "provider": "system",
        "model": "n/a",
    }


_ROUTE = {
    "resume_match": "resume_match",
    "resume_optimize": "resume_optimize",
    "linkedin": "linkedin",
    "wellness": "wellness",
    "rag": "rag",
    "interview_prep": "interview_prep",
    "general": "general",
}


def _route(state: AgentState) -> str:
    return _ROUTE.get(state.get("intent", "general"), "general")


@lru_cache
def get_graph():
    """Build and compile the supervisor graph (cached)."""
    builder = StateGraph(AgentState)
    builder.add_node("supervisor", _supervisor_node)
    builder.add_node("resume_match", _resume_match_node)
    builder.add_node("resume_optimize", _resume_optimize_node)
    builder.add_node("linkedin", _linkedin_node)
    builder.add_node("wellness", _wellness_node)
    builder.add_node("rag", _rag_node)
    builder.add_node("interview_prep", _interview_node)
    builder.add_node("general", _general_node)

    builder.set_entry_point("supervisor")
    builder.add_conditional_edges("supervisor", _route, _ROUTE)
    for node in _ROUTE.values():
        builder.add_edge(node, END)

    return builder.compile()
