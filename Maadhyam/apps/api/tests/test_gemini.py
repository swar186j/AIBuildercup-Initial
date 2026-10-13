"""Tests never call the real Gemini service."""
from fastapi.testclient import TestClient
from maadhyam_api.config import get_settings
from maadhyam_api.main import create_app
from maadhyam_api.routes import gemini


def test_missing_key(monkeypatch):
    # Isolate this test from a developer's real .env file.
    # Never contact Gemini when testing the missing-key path.
    monkeypatch.setattr(gemini, "get_settings", lambda: type("TestSettings", (), {
        "gemini_api_key": "",
        "gemini_model": "test-model",
    })())

    def must_not_call_provider(api_key, model):
        raise AssertionError("Missing-key test must not call Gemini")

    monkeypatch.setattr(gemini, "check_gemini_connection", must_not_call_provider)
    with TestClient(create_app()) as client:
        response = client.post("/api/ai/connection-test")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "http_error"


def test_connection_success(monkeypatch):
    monkeypatch.setenv("MAADHYAM_GEMINI_API_KEY", "fake-key")
    get_settings.cache_clear()
    monkeypatch.setattr(gemini, "check_gemini_connection", lambda key, model: "READY")
    with TestClient(create_app()) as client:
        response = client.post("/api/ai/connection-test")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"
    assert response.json()["reply"] == "READY"
    get_settings.cache_clear()


def test_provider_failure_hides_internal_details(monkeypatch):
    monkeypatch.setenv("MAADHYAM_GEMINI_API_KEY", "fake-key")
    get_settings.cache_clear()
    def fail(key, model):
        raise RuntimeError("private provider details")
    monkeypatch.setattr(gemini, "check_gemini_connection", fail)
    with TestClient(create_app()) as client:
        response = client.post("/api/ai/connection-test")
    assert response.status_code == 502
    assert "private provider details" not in response.text
    get_settings.cache_clear()
