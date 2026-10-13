"""Extraction must require explicit fictional-document confirmation."""
from fastapi.testclient import TestClient
from maadhyam_api.main import create_app


def test_extraction_rejects_without_demo_confirmation():
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/ai/extract-document",
            files={"file": ("demo.pdf", b"%PDF-1.4\nfictional", "application/pdf")},
        )
    assert response.status_code == 403
    assert "fictional demo" in response.json()["error"]["message"]
