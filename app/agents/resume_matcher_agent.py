"""Evidence-based Resume Analyzer agent.

Deterministic analysis owns cleaning, validation, evidence scoring, and score caps. The LLM
only refines resume edits and optimized text, with deterministic fallbacks when unavailable.
"""

from __future__ import annotations

from app.models.resume_models import ResumeMatchResponse
from app.services import llm_service, prompt_service, resume_analysis_service

AGENT_NAME = "resume_match"


def _fallback_rewrite_suggestions(analysis: dict) -> list[dict[str, str]]:
    missing_requirements = list(analysis.get("missing_requirements", []))
    suggestions: list[dict[str, str]] = []
    for item in missing_requirements[:3]:
        requirement = str(item.get("requirement", "the missing requirement"))
        suggestions.append(
            {
                "section": "experience",
                "current_issue": f"No clear evidence for: {requirement}",
                "improved_bullet": (
                    "Add a truthful bullet such as: "
                    '"Used [tool] to [process/responsibility] with [team], improving [metric/outcome]."'
                ),
                "reason": "This gives the analyzer concrete action, tool, scope, and outcome evidence.",
            }
        )
    if not suggestions:
        suggestions.append(
            {
                "section": "experience",
                "current_issue": "Bullets can be more evidence-rich.",
                "improved_bullet": (
                    "Rewrite a relevant bullet as: "
                    '"Built [project/system] using [tool] to solve [problem], resulting in [metric/outcome]."'
                ),
                "reason": "Specific examples carry more weight than keyword mentions.",
            }
        )
    return suggestions


def _fallback_optimized_resume(analysis: dict) -> str:
    sections = dict(analysis.get("resume_sections", {}))
    parts = [
        "SUMMARY",
        sections.get("summary")
        or "Candidate summary: add a concise target-role summary grounded in your real experience.",
        "",
        "SKILLS",
        sections.get("skills")
        or "Add truthful tools, languages, platforms, and methods you have used.",
        "",
        "EXPERIENCE",
        sections.get("experience")
        or "- Add bullets with action + [tool] + [responsibility] + [metric/outcome].",
    ]
    if sections.get("projects"):
        parts.extend(["", "PROJECTS", sections["projects"]])
    if sections.get("education"):
        parts.extend(["", "EDUCATION", sections["education"]])
    return "\n".join(parts).strip()


def _fallback_payload(analysis: dict) -> dict:
    return {
        "summary": analysis.get("summary", ""),
        "top_resume_fixes": list(analysis.get("top_resume_fixes", [])),
        "matched_evidence": list(analysis.get("matched_evidence", [])),
        "missing_requirements": list(analysis.get("missing_requirements", [])),
        "resume_rewrite_suggestions": _fallback_rewrite_suggestions(analysis),
        "optimized_resume_text": _fallback_optimized_resume(analysis),
    }


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def run(resume_text: str, job_description: str) -> ResumeMatchResponse:
    analysis = resume_analysis_service.evidence_score(resume_text, job_description)
    fallback = _fallback_payload(analysis)

    system, user = prompt_service.resume_match_prompt(
        cleaned_resume_text=str(analysis.get("cleaned_resume_text", "")),
        cleaned_job_description=str(analysis.get("cleaned_job_description", "")),
        deterministic_score=int(analysis.get("overall_score", 0)),
        score_breakdown=dict(analysis.get("score_breakdown", {})),
        input_quality=dict(analysis.get("input_quality", {})),
        extracted_job_requirements=dict(analysis.get("job_requirements", {})),
        extracted_resume_sections=dict(analysis.get("resume_sections", {})),
        matched_evidence=list(analysis.get("matched_evidence", [])),
        missing_requirements=list(analysis.get("missing_requirements", [])),
    )
    data, result = llm_service.generate_json(system, user, fallback=fallback, timeout_seconds=20.0)

    top_resume_fixes = _as_list(data.get("top_resume_fixes")) or fallback["top_resume_fixes"]
    matched_evidence = _as_list(data.get("matched_evidence")) or fallback["matched_evidence"]
    missing_requirements = _as_list(data.get("missing_requirements")) or fallback["missing_requirements"]
    rewrite_suggestions = (
        _as_list(data.get("resume_rewrite_suggestions"))
        or fallback["resume_rewrite_suggestions"]
    )
    optimized_resume_text = str(
        data.get("optimized_resume_text") or fallback["optimized_resume_text"]
    )
    summary = str(data.get("summary") or fallback["summary"])

    return ResumeMatchResponse(
        agent=AGENT_NAME,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        input_quality=dict(analysis.get("input_quality", {})),
        overall_score=int(analysis.get("overall_score", 0)),
        score_label=str(analysis.get("score_label", "Weak match")),
        score_breakdown=dict(analysis.get("score_breakdown", {})),
        summary=summary,
        top_resume_fixes=top_resume_fixes,
        matched_evidence=matched_evidence,
        missing_requirements=missing_requirements,
        resume_rewrite_suggestions=rewrite_suggestions,
        optimized_resume_text=optimized_resume_text,
        score=int(analysis.get("overall_score", 0)),
        matched_skills=list(analysis.get("matched_skills", [])),
        missing_skills=list(analysis.get("missing_skills", [])),
        recommended_edits=top_resume_fixes,
        explanation=summary,
    )
