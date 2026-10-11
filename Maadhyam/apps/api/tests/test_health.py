from fastapi.testclient import TestClient
from maadhyam_api.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "application": "Maadhyam",
        "version": "0.1.0",
    }