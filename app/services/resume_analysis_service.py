"""Evidence-based resume analysis utilities for resume/JD matching."""

from __future__ import annotations

import html
import math
import re
from collections import Counter
from typing import Any

MAX_INPUT_CHARS = 20_000

SKILL_VOCAB: tuple[str, ...] = (
    "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#", "ruby", "php",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq",
    "fastapi", "flask", "django", "node.js", "express", "react", "next.js", "vue", "angular",
    "docker", "kubernetes", "terraform", "ansible", "aws", "gcp", "azure", "ci/cd",
    "github actions", "rest", "rest apis", "graphql", "grpc", "microservices",
    "distributed systems", "asyncio", "machine learning", "deep learning", "nlp", "pytorch",
    "tensorflow", "pandas", "numpy", "data pipelines", "etl", "streaming", "spark", "airflow",
    "observability", "pytest", "unit testing", "agile", "scrum", "leadership", "mentoring",
    "communication", "system design", "scalability", "security", "jwt", "oauth", "linux",
)

_STOPWORDS = {
    "about", "above", "after", "again", "against", "also", "am", "and", "any", "are", "as",
    "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "will", "with", "you", "your", "yours",
}

_ACTION_VERBS = {
    "achieved", "architected", "automated", "built", "created", "cut", "delivered",
    "designed", "developed", "drove", "enabled", "implemented", "improved", "increased",
    "launched", "led", "managed", "migrated", "optimized", "owned", "reduced", "shipped",
    "scaled", "secured", "streamlined", "supported", "mentored",
}

_GENERIC_PHRASES = (
    "gain experience",
    "familiar with",
    "responsible for",
    "passionate about",
    "hard worker",
    "team player",
    "detail oriented",
    "self starter",
)

_RESUME_SECTION_ALIASES = {
    "summary": {"summary", "profile", "professional summary", "objective"},
    "skills": {"skills", "technical skills", "technologies", "core competencies"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "projects": {"projects", "selected projects", "personal projects"},
    "education": {"education", "academic background"},
    "certifications": {"certifications", "certificates", "licenses"},
}

_JD_SECTION_ALIASES = {
    "responsibilities": {"responsibilities", "what you'll do", "what you will do", "role"},
    "required": {"required qualifications", "requirements", "required skills", "must have"},
    "preferred": {"preferred qualifications", "nice to have", "bonus", "preferred skills"},
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9.+#/-]{1,}")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def normalize_text(text: str) -> str:
    """Normalize whitespace and casing for deterministic text comparison."""
    text = html.unescape(text or "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip().lower()


def _strip_sensitive_noise(text: str) -> str:
    text = html.unescape(text or "")[:MAX_INPUT_CHARS]
    text = re.sub(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", "", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text, flags=re.I)
    text = re.sub(r"\b(?:linkedin|github)\.com/\S+", "", text, flags=re.I)
    text = re.sub(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}", "", text)
    text = re.sub(
        r"\b\d{1,5}\s+[A-Za-z0-9 .'-]+(?:street|st\.|road|rd\.|avenue|ave\.|lane|ln\.|drive|dr\.)\b",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def _dedupe_lines(lines: list[str]) -> list[str]:
    counts: Counter[str] = Counter()
    cleaned: list[str] = []
    for raw in lines:
        line = raw.strip(" \t-*•")
        if not line:
            if cleaned and cleaned[-1]:
                cleaned.append("")
            continue
        key = normalize_text(line)
        counts[key] += 1
        if counts[key] <= 2:
            cleaned.append(line)
    return cleaned


def clean_resume_text(text: str) -> str:
    """Remove contact data and repeated noise while preserving resume evidence."""
    text = _strip_sensitive_noise(text)
    lines = _dedupe_lines(text.splitlines())
    return "\n".join(lines).strip()


def clean_job_description(text: str) -> str:
    """Remove job-page boilerplate while preserving role requirements."""
    text = _strip_sensitive_noise(text)
    boilerplate = re.compile(
        r"(equal opportunity|eeo|reasonable accommodation|background check|privacy policy|"
        r"terms of use|cookie|benefits include|about us|our company|we are proud|"
        r"all qualified applicants|without regard to|apply now|share this job)",
        re.I,
    )
    lines = [line for line in _dedupe_lines(text.splitlines()) if not boilerplate.search(line)]
    return "\n".join(lines).strip()


def _tokens(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOPWORDS]


def _keywords(text: str) -> set[str]:
    return {w for w in _tokens(text) if len(w) > 3}


def _sentences(text: str) -> list[str]:
    parts = [normalize_text(s).strip(" -*•") for s in _SENTENCE_RE.split(text)]
    return [s for s in parts if len(s.split()) >= 5]


def _has_metric(text: str) -> bool:
    return bool(re.search(r"(\d+[%+]?|\$[\d,.]+|\b(?:million|thousand|k|m|x)\b)", text, re.I))


def _has_action(text: str) -> bool:
    words = set(_tokens(text))
    return bool(words & _ACTION_VERBS)


def _has_generic_phrase(text: str) -> bool:
    norm = normalize_text(text)
    return any(phrase in norm for phrase in _GENERIC_PHRASES)


def extract_skills(text: str) -> set[str]:
    """Extract known skills and tools from text using a curated vocabulary."""
    norm = normalize_text(text)
    found: set[str] = set()
    for skill in SKILL_VOCAB:
        if " " in skill or any(c in skill for c in "+#./"):
            if skill in norm:
                found.add(skill)
        elif re.search(rf"\b{re.escape(skill)}\b", norm):
            found.add(skill)
    return found


def detect_resume_like(text: str) -> bool:
    norm = normalize_text(text)
    sections = sum(1 for aliases in _RESUME_SECTION_ALIASES.values() for a in aliases if a in norm)
    has_resume_terms = bool(re.search(r"\b(resume|experience|skills|education|projects|engineer|analyst|manager)\b", norm))
    has_bullets = len(re.findall(r"(^|\n)\s*[-•*]", text)) >= 2
    return len(_tokens(text)) >= 35 and ((sections >= 2) or (has_resume_terms and has_bullets))


def detect_jd_like(text: str) -> bool:
    norm = normalize_text(text)
    jd_terms = re.search(
        r"\b(responsibilities|requirements|qualifications|required|preferred|you will|we are hiring|"
        r"experience with|years of experience|nice to have)\b",
        norm,
    )
    return len(_tokens(text)) >= 35 and bool(jd_terms)


def detect_copied_jd(resume_text: str, jd_text: str) -> bool:
    resume_sentences = set(_sentences(resume_text))
    jd_sentences = set(_sentences(jd_text))
    if jd_sentences:
        sentence_overlap = len(resume_sentences & jd_sentences) / len(jd_sentences)
        if sentence_overlap >= 0.25 and len(resume_sentences & jd_sentences) >= 2:
            return True

    resume_words = Counter(_tokens(resume_text))
    jd_words = Counter(_tokens(jd_text))
    shared = set(resume_words) & set(jd_words)
    if not shared or len(jd_words) < 20:
        return False
    dot = sum(resume_words[w] * jd_words[w] for w in shared)
    resume_mag = math.sqrt(sum(v * v for v in resume_words.values()))
    jd_mag = math.sqrt(sum(v * v for v in jd_words.values()))
    cosine = dot / (resume_mag * jd_mag) if resume_mag and jd_mag else 0.0
    containment = len(shared) / len(set(jd_words))
    return cosine >= 0.82 or (containment >= 0.72 and len(shared) >= 25)


def extract_resume_sections(text: str) -> dict[str, str]:
    sections = {name: "" for name in _RESUME_SECTION_ALIASES}
    current = "summary"
    buffer: dict[str, list[str]] = {name: [] for name in sections}
    for raw in text.splitlines():
        line = raw.strip()
        heading = normalize_text(line).strip(":")
        matched = next(
            (name for name, aliases in _RESUME_SECTION_ALIASES.items() if heading in aliases),
            None,
        )
        if matched:
            current = matched
            continue
        if line:
            buffer.setdefault(current, []).append(line)
    return {name: "\n".join(parts).strip() for name, parts in buffer.items()}


def _classify_jd_section(line: str, current: str) -> str:
    heading = normalize_text(line).strip(":")
    for name, aliases in _JD_SECTION_ALIASES.items():
        if heading in aliases:
            return name
    return current


def _requirement_from_line(line: str) -> str:
    return line.strip(" \t-*•:;")


def extract_job_requirements(text: str) -> dict[str, list[str]]:
    requirements: dict[str, list[str]] = {"required": [], "preferred": [], "responsibilities": []}
    current = "responsibilities"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        new_section = _classify_jd_section(line, current)
        if new_section != current and normalize_text(line).strip(":") in _JD_SECTION_ALIASES[new_section]:
            current = new_section
            continue
        current = new_section
        req = _requirement_from_line(line)
        if len(req.split()) >= 3:
            requirements.setdefault(current, []).append(req)
    if not requirements["required"]:
        requirements["required"] = requirements["responsibilities"][:5]
    return requirements


def _best_evidence(requirement: str, resume_lines: list[str], copied_jd: bool) -> tuple[str, str] | None:
    req_words = _keywords(requirement)
    if not req_words:
        return None
    best_line = ""
    best_score = 0.0
    for line in resume_lines:
        line_words = _keywords(line)
        if not line_words:
            continue
        overlap = len(req_words & line_words) / len(req_words)
        quality = 0.0
        if _has_action(line):
            quality += 0.25
        if _has_metric(line):
            quality += 0.25
        if extract_skills(line):
            quality += 0.15
        if _has_generic_phrase(line):
            quality -= 0.25
        score = overlap + quality
        if score > best_score:
            best_score = score
            best_line = line
    if not best_line or best_score < 0.18:
        return None
    if copied_jd and normalize_text(best_line) in set(_sentences(requirement)):
        return None
    confidence = "high" if best_score >= 0.75 and _has_action(best_line) else "medium" if best_score >= 0.38 else "low"
    return best_line, confidence


def _score_label(score: int) -> str:
    if score >= 85:
        return "Excellent match"
    if score >= 70:
        return "Strong match"
    if score >= 45:
        return "Moderate match"
    return "Weak match"


def _formatting_score(text: str, sections: dict[str, str]) -> int:
    present = sum(1 for key in ("summary", "skills", "experience", "projects", "education") if sections.get(key))
    bullets = len(re.findall(r"(^|\n)\s*[-•*]", text))
    score = min(6, present) + min(4, bullets)
    return min(10, score)


def _has_experience_evidence(sections: dict[str, str]) -> bool:
    evidence = "\n".join([sections.get("experience", ""), sections.get("projects", "")])
    return len(_tokens(evidence)) >= 25 and (_has_action(evidence) or _has_metric(evidence))


def evidence_score(resume_text: str, jd_text: str) -> dict[str, Any]:
    """Compute weighted, evidence-based resume/JD alignment with quality caps."""
    clean_resume = clean_resume_text(resume_text)
    clean_jd = clean_job_description(jd_text)
    resume_valid = detect_resume_like(clean_resume)
    jd_valid = detect_jd_like(clean_jd)
    copied = detect_copied_jd(clean_resume, clean_jd)

    resume_sections = extract_resume_sections(clean_resume)
    job_requirements = extract_job_requirements(clean_jd)
    all_requirements = job_requirements.get("required", []) + job_requirements.get("responsibilities", [])
    preferred_requirements = job_requirements.get("preferred", [])
    resume_lines = [line.strip(" -*•") for line in clean_resume.splitlines() if len(line.strip()) > 3]

    resume_skills = extract_skills(clean_resume)
    jd_skills = extract_skills(clean_jd)
    matched_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)

    matched_evidence: list[dict[str, str]] = []
    missing_requirements: list[dict[str, str]] = []
    strong_matches = 0
    medium_or_better = 0
    for requirement in all_requirements:
        best = _best_evidence(requirement, resume_lines, copied)
        if best:
            evidence, confidence = best
            matched_evidence.append(
                {
                    "jd_requirement": requirement,
                    "resume_evidence": evidence,
                    "confidence": confidence,
                }
            )
            if confidence == "high":
                strong_matches += 1
            if confidence in {"high", "medium"}:
                medium_or_better += 1
        else:
            missing_requirements.append(
                {
                    "requirement": requirement,
                    "importance": "required",
                    "reason": "No concrete resume evidence found for this requirement.",
                    "suggested_resume_line": "",
                }
            )
    for requirement in preferred_requirements:
        best = _best_evidence(requirement, resume_lines, copied)
        if best:
            evidence, confidence = best
            matched_evidence.append(
                {
                    "jd_requirement": requirement,
                    "resume_evidence": evidence,
                    "confidence": confidence,
                }
            )
        else:
            missing_requirements.append(
                {
                    "requirement": requirement,
                    "importance": "preferred",
                    "reason": "Preferred requirement is not clearly represented in the resume.",
                    "suggested_resume_line": "",
                }
            )

    req_count = max(1, len(all_requirements))
    skill_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 0.0
    keyword_ratio = len(_keywords(clean_resume) & _keywords(clean_jd)) / len(_keywords(clean_jd)) if _keywords(clean_jd) else 0.0
    tool_ratio = len(matched_skills) / len(jd_skills) if jd_skills else 0.0
    evidence_ratio = medium_or_better / req_count
    strong_ratio = strong_matches / req_count
    impact_lines = [line for line in resume_lines if _has_metric(line) and _has_action(line)]
    impact_ratio = min(1.0, len(impact_lines) / 3)

    breakdown = {
        "skills": round(25 * skill_ratio),
        "experience": round(25 * evidence_ratio),
        "tools": round(15 * tool_ratio),
        "impact": round(15 * impact_ratio),
        "keywords": round(10 * min(keyword_ratio, 0.85)),
        "formatting": _formatting_score(clean_resume, resume_sections),
    }
    total = sum(breakdown.values())

    caps: list[int] = []
    resume_warning = ""
    jd_warning = ""
    if copied:
        caps.append(40)
        resume_warning = "The resume appears to contain copied job-description language; score is capped."
    if not resume_valid:
        caps.append(35)
        resume_warning = resume_warning or "The resume text does not look like a complete resume."
    if not jd_valid:
        caps.append(0)
        jd_warning = "The job description does not contain enough recognizable role requirements."
    if len(_tokens(clean_resume)) < 70 or not _has_experience_evidence(resume_sections):
        caps.append(55)
        resume_warning = resume_warning or "The resume is too short or lacks concrete work/project evidence."
    if not matched_evidence and total > 45:
        caps.append(45)
    if total > 95 and (strong_ratio < 0.85 or impact_ratio < 0.8):
        caps.append(95)
    if total == 100 and (strong_ratio < 0.95 or len(missing_requirements) > 0):
        caps.append(99)

    if caps:
        total = min(total, min(caps))
    total = max(0, min(100, total))

    summary = (
        f"The resume shows {_score_label(total).lower()} alignment based on concrete evidence, "
        f"with {len(matched_evidence)} matched requirement(s) and {len(missing_requirements)} gap(s)."
    )
    top_fixes = []
    if missing_skills:
        top_fixes.append("Add truthful project or work examples for: " + ", ".join(missing_skills[:5]) + ".")
    if not impact_lines:
        top_fixes.append("Add measurable outcomes, scale, latency, revenue, quality, or efficiency metrics.")
    if missing_requirements:
        top_fixes.append("Address the highest-priority missing requirement with a specific resume bullet.")
    if not top_fixes:
        top_fixes.append("Tighten bullets by pairing each action with tools, scope, and measurable outcomes.")

    return {
        "cleaned_resume_text": clean_resume,
        "cleaned_job_description": clean_jd,
        "input_quality": {
            "resume_looks_valid": resume_valid,
            "jd_looks_valid": jd_valid,
            "copied_jd_detected": copied,
            "resume_warning": resume_warning,
            "jd_warning": jd_warning,
        },
        "overall_score": total,
        "score_label": _score_label(total),
        "score_breakdown": breakdown,
        "summary": summary,
        "top_resume_fixes": top_fixes,
        "matched_evidence": matched_evidence[:12],
        "missing_requirements": missing_requirements[:12],
        "resume_rewrite_suggestions": [],
        "optimized_resume_text": "",
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_keywords": sorted((_keywords(clean_resume) & _keywords(clean_jd)) - resume_skills)[:15],
        "resume_sections": resume_sections,
        "job_requirements": job_requirements,
    }
