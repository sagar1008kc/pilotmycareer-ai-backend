"""Auth dependency tests.

The session ``client`` fixture runs in dev mode (mock user). Here we also exercise the
supabase-mode path to confirm a missing/invalid token is rejected.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_dev_mode_allows_without_token(client):
    res = client.post("/api/v1/wellness/checkin", json={"message": "feeling ok"})
    assert res.status_code == 200


@pytest.fixture
def supabase_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("AUTH_MODE", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    get_settings.cache_clear()
    from app.main import create_app

    yield TestClient(create_app())
    get_settings.cache_clear()


def test_supabase_mode_rejects_missing_token(supabase_client):
    res = supabase_client.post("/api/v1/wellness/checkin", json={"message": "hi"})
    assert res.status_code == 401


def test_supabase_mode_rejects_invalid_token(supabase_client):
    res = supabase_client.post(
        "/api/v1/wellness/checkin",
        json={"message": "hi"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert res.status_code == 401


def test_crisis_detection_flag(client):
    res = client.post(
        "/api/v1/wellness/checkin",
        json={"message": "I feel like I want to end my life"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["crisis_flag"] is True
    assert body["crisis_resources"]
