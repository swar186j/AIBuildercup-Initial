"""Milestone 1B regression and configuration tests."""
from fastapi import HTTPException
from starlette.testclient import TestClient

from maadhyam_api.config import Settings
from maadhyam_api.main import create_app


def test_default_settings():
    settings = Settings()
    assert settings.app_name
    assert "http://localhost:5173" in settings.cors_origins


def test_existing_routes_remain_compatible():
    with TestClient(create_app()) as client:
        assert client.get("/api/health").json() == {
            "status": "healthy", "application": "Maadhyam", "version": "0.1.0"
        }
        assert len(client.get("/api/services").json()["services"]) == 3


def test_cors_preflight():
    with TestClient(create_app()) as client:
        response = client.options(
            "/api/services",
            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_http_error_shape():
    app = create_app()

    @app.get("/api/test-not-found")
    def test_endpoint():
        raise HTTPException(status_code=404, detail="Not found")

    with TestClient(app) as client:
        response = client.get("/api/test-not-found")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "http_error", "message": "Not found"}}


def test_validation_error_shape():
    app = create_app()

    @app.get("/api/test-validation")
    def test_endpoint(count: int):
        return {"count": count}

    with TestClient(app) as client:
        response = client.get("/api/test-validation?count=not-a-number")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]


def test_unexpected_error_does_not_leak_details():
    app = create_app()

    @app.get("/api/test-failure")
    def test_endpoint():
        raise RuntimeError("private backend details")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/test-failure")
    assert response.status_code == 500
    assert "private backend details" not in response.text
    assert response.json()["error"]["code"] == "internal_error"
