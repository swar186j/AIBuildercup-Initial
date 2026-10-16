"""No network or paid inference: provider configuration and production admission."""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from maadhyam_api.config import get_settings
from maadhyam_api.main import create_app
from maadhyam_api.services import gemini_provider, ai_guard


def test_vertex_client_uses_adc_and_bounds(monkeypatch):
    import google.genai
    monkeypatch.setenv("MAADHYAM_GEMINI_VERTEXAI", "true")
    monkeypatch.setenv("MAADHYAM_GOOGLE_CLOUD_PROJECT", "maadhyam-1610")
    get_settings.cache_clear()
    constructor = MagicMock()
    monkeypatch.setattr(google.genai, "Client", constructor)
    try:
        gemini_provider.create_client("must-not-be-used")
        args = constructor.call_args.kwargs
        assert args["vertexai"] is True
        assert args["project"] == "maadhyam-1610"
        assert args["location"] == "global"
        assert "api_key" not in args
        assert args["http_options"].timeout == 30000
        assert args["http_options"].retry_options.attempts == 1
    finally:
        get_settings.cache_clear()


def test_production_ai_requires_auth_and_local_chat_does_not(monkeypatch):
    monkeypatch.setenv("MAADHYAM_PRODUCTION", "true")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            assert client.post("/api/ai/connection-test").status_code == 401
            assert client.post("/api/intelligence/chat", json={"question": "Help"}).status_code == 200
            assert client.post("/api/intelligence/chat", json={"question": "Help", "useGemini": True}).status_code == 401
    finally:
        get_settings.cache_clear()


def test_ai_limit_does_not_invoke_provider(monkeypatch):
    monkeypatch.setenv("MAADHYAM_PRODUCTION", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(ai_guard, "require_uid", lambda token: "fictional-uid")
    from maadhyam_api.routes import gemini
    monkeypatch.setattr(gemini, "check_gemini_connection", lambda *args: "READY")
    monkeypatch.setattr(gemini, "configured", lambda settings: True)
    try:
        with TestClient(create_app()) as client:
            for _ in range(6):
                assert client.post("/api/ai/connection-test").status_code == 200
            response = client.post("/api/ai/connection-test")
            assert response.status_code == 429
            assert response.headers["retry-after"] == "60"
    finally:
        get_settings.cache_clear()


def test_generation_has_finite_output():
    config = gemini_provider.generation_config()
    assert config.max_output_tokens == 2048
    assert config.thinking_config.thinking_budget == 0


def test_missing_adc_is_service_unavailable(monkeypatch):
    import google.genai
    from google.auth.exceptions import DefaultCredentialsError
    from fastapi import HTTPException
    import pytest
    monkeypatch.setenv("MAADHYAM_GEMINI_VERTEXAI", "true")
    monkeypatch.setenv("MAADHYAM_GOOGLE_CLOUD_PROJECT", "maadhyam-1610")
    get_settings.cache_clear()
    monkeypatch.setattr(google.genai, "Client", MagicMock(side_effect=DefaultCredentialsError("private path")))
    try:
        with pytest.raises(HTTPException) as error:
            gemini_provider.create_client()
        assert error.value.status_code == 503
        assert "private path" not in error.value.detail
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("code,status", [(429, 429), (403, 503), (401, 503), (404, 503), (500, 503)])
def test_provider_errors_are_safe_and_actionable(code, status):
    error = RuntimeError("PRIVATE_PROVIDER_DETAILS")
    error.code = code
    response = gemini_provider.provider_http_error(error)
    assert response.status_code == status
    assert "PRIVATE_PROVIDER_DETAILS" not in response.detail


def test_provider_timeout_is_bounded_failure():
    import httpx
    response = gemini_provider.provider_http_error(httpx.ReadTimeout("PRIVATE_PROVIDER_DETAILS"))
    assert response.status_code == 504
    assert "PRIVATE_PROVIDER_DETAILS" not in response.detail
