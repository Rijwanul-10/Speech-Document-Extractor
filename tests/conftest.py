"""
Pytest Fixtures.

Configures test fixtures, FastAPITestClient, and mock provider settings
for automated testing.
"""

import pytest
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Ensure mock providers are active for all tests."""
    monkeypatch.setenv("SPEECH_PROVIDER", "mock")
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    get_settings.cache_clear()
