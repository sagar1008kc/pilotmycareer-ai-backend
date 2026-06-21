from pathlib import Path

from app.agents import resume_matcher_agent
from app.models.common import Usage
from app.models.resume_models import ResumeMatchResponse
from app.services.llm_service import LLMResult

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _load(name: str) -> str:
    return (EXAMPLES / name).read_text(encoding="utf-8")


def test_resume_match_structured_output(client):
    payload = {
        "resume_text": _load("sample_resume.txt"),
        "job_description": _load("sample_job_description.txt"),
    }
    res = client.post("/api/v1/resume/match", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert 0 <= body["overall_score"] <= 100
    assert body["score"] == body["overall_score"]
    assert body["score_label"] in {
        "Weak match",
        "Moderate match",
        "Strong match",
        "Excellent match",
    }
    assert set(body["score_breakdown"]) == {
        "skills",
        "experience",
        "tools",
        "impact",
        "keywords",
        "formatting",
    }
    assert body["input_quality"]["resume_looks_valid"] is True
    assert body["input_quality"]["jd_looks_valid"] is True
    assert body["top_resume_fixes"]
    assert body["matched_evidence"]
    assert body["missing_requirements"] is not None
    assert body["resume_rewrite_suggestions"]
    assert body["optimized_resume_text"]
    assert isinstance(body["matched_skills"], list)
    assert isinstance(body["missing_skills"], list)
    assert body["recommended_edits"]
    assert "interview_questions" not in body
    assert body["agent"] == "resume_match"
    assert body["request_id"]
    # Mock provider used when no OPENAI_API_KEY.
    assert body["provider"] in {"mock", "openai"}
    # The resume and JD share core backend skills.
    assert "python" in body["matched_skills"]


def test_resume_match_validation(client):
    res = client.post("/api/v1/resume/match", json={"resume_text": "x", "job_description": "y"})
    assert res.status_code == 422


def test_resume_match_score_is_deterministic(client):
    payload = {
        "resume_text": _load("sample_resume.txt"),
        "job_description": _load("sample_job_description.txt"),
    }
    first = client.post("/api/v1/resume/match", json=payload).json()["score"]
    second = client.post("/api/v1/resume/match", json=payload).json()["score"]
    assert first == second


def test_copied_jd_pasted_into_resume_caps_score(client):
    jd = _load("sample_job_description.txt")
    payload = {
        "resume_text": jd,
        "job_description": jd,
    }
    res = client.post("/api/v1/resume/match", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert body["input_quality"]["copied_jd_detected"] is True
    assert body["overall_score"] <= 40
    assert body["input_quality"]["resume_warning"]


def test_very_short_resume_caps_score(client):
    payload = {
        "resume_text": (
            "SUMMARY\nPython developer.\nSKILLS\nPython, FastAPI, PostgreSQL, Redis, Docker."
        ),
        "job_description": _load("sample_job_description.txt"),
    }
    res = client.post("/api/v1/resume/match", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert body["overall_score"] <= 55
    assert body["input_quality"]["resume_warning"]


def test_invalid_resume_text_returns_warning(client):
    payload = {
        "resume_text": (
            "This paragraph is about weekend cooking, travel preferences, and favorite books. "
            "It contains enough words to pass transport validation, but it has no resume "
            "sections, no work history, and no project evidence."
        ),
        "job_description": _load("sample_job_description.txt"),
    }
    res = client.post("/api/v1/resume/match", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert body["input_quality"]["resume_looks_valid"] is False
    assert body["input_quality"]["resume_warning"]
    assert body["overall_score"] <= 35


def test_keyword_only_resume_does_not_get_high_score(client):
    payload = {
        "resume_text": (
            "SUMMARY\nBackend keywords.\nSKILLS\nPython FastAPI PostgreSQL Redis Docker "
            "Kubernetes AWS Kafka Terraform GraphQL microservices observability pytest asyncio."
        ),
        "job_description": _load("sample_job_description.txt"),
    }
    res = client.post("/api/v1/resume/match", json=payload)
    assert res.status_code == 200
    body = res.json()

    assert body["overall_score"] <= 55
    assert body["score_breakdown"]["experience"] < 15


def test_llm_failure_returns_deterministic_fallback(monkeypatch):
    def failing_generate_json(system, user, *, fallback, timeout_seconds=20.0):
        return dict(fallback), LLMResult(
            text="",
            provider="openai",
            model="error",
            usage=Usage(),
        )

    monkeypatch.setattr(resume_matcher_agent.llm_service, "generate_json", failing_generate_json)

    result = resume_matcher_agent.run(_load("sample_resume.txt"), _load("sample_job_description.txt"))
    assert result.provider == "openai"
    assert result.model == "error"
    assert result.top_resume_fixes
    assert result.resume_rewrite_suggestions
    assert result.optimized_resume_text


def test_resume_match_response_model_validates(client):
    payload = {
        "resume_text": _load("sample_resume.txt"),
        "job_description": _load("sample_job_description.txt"),
    }
    body = client.post("/api/v1/resume/match", json=payload).json()

    parsed = ResumeMatchResponse.model_validate(body)
    assert parsed.overall_score == parsed.score
    assert parsed.agent == "resume_match"
