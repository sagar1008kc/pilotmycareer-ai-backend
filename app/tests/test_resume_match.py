from pathlib import Path

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

    assert 0 <= body["score"] <= 100
    assert isinstance(body["matched_skills"], list)
    assert isinstance(body["missing_skills"], list)
    assert body["recommended_edits"]
    assert body["interview_questions"]
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
