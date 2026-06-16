"""Shared pytest fixtures.

Forces dev auth + mock LLM so tests run with no external dependencies.
"""

from __future__ import annotations

import os

os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("SUPABASE_PERSIST", "false")

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


@pytest.fixture(scope="session")
def client() -> TestClient:
    # Clear cached settings so the env above is picked up.
    get_settings.cache_clear()
    from app.main import create_app

    return TestClient(create_app())
