"""Deterministic resume <-> job description matching.

Produces a reproducible score and skill lists without calling an LLM. The LLM is used only
later for narrative explanation and suggestions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Curated skill vocabulary. Multi-word phrases are matched as substrings; single tokens are
# matched on word boundaries. Extend freely.
SKILL_VOCAB: tuple[str, ...] = (
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "ruby", "php",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq",
    "fastapi", "flask", "django", "node.js", "express", "react", "next.js", "vue", "angular",
    "docker", "kubernetes", "terraform", "ansible", "aws", "gcp", "azure", "ci/cd", "github actions",
    "rest", "rest apis", "graphql", "grpc", "microservices", "distributed systems", "asyncio",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas", "numpy",
    "data pipelines", "etl", "streaming", "spark", "airflow", "observability", "pytest",
    "unit testing", "agile", "scrum", "leadership", "mentoring", "communication",
    "system design", "scalability", "security", "jwt", "oauth", "linux",
)

_STOPWORDS = {
    "and", "the", "for", "with", "you", "our", "are", "will", "your", "this", "that", "have",
    "from", "all", "any", "can", "has", "was", "but", "not", "who", "how", "why", "into",
    "experience", "team", "work", "role", "build", "design", "strong", "years",
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9.+#/-]{1,}")


@dataclass
class MatchResult:
    score: int
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    extra_keywords: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return text.lower()


def extract_skills(text: str) -> set[str]:
    """Extract known skills from text using the curated vocabulary."""
    norm = _normalize(text)
    found: set[str] = set()
    for skill in SKILL_VOCAB:
        if " " in skill or any(c in skill for c in "+#./"):
            if skill in norm:
                found.add(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", norm):
                found.add(skill)
    return found


def _keywords(text: str) -> set[str]:
    words = {w.lower() for w in _WORD_RE.findall(text)}
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def match_resume_to_job(resume_text: str, job_description: str) -> MatchResult:
    """Compute a reproducible match score and skill breakdown.

    Score blends curated-skill coverage (weighted) with general keyword overlap.
    """
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)

    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    skill_coverage = len(matched) / len(job_skills) if job_skills else 0.0

    resume_kw = _keywords(resume_text)
    job_kw = _keywords(job_description)
    kw_overlap = len(resume_kw & job_kw) / len(job_kw) if job_kw else 0.0

    # Weight curated skills more heavily than generic keyword overlap.
    raw = 0.7 * skill_coverage + 0.3 * kw_overlap
    score = max(0, min(100, round(raw * 100)))

    extra = sorted((resume_kw & job_kw) - resume_skills)[:15]

    return MatchResult(
        score=score,
        matched_skills=matched,
        missing_skills=missing,
        extra_keywords=extra,
    )
