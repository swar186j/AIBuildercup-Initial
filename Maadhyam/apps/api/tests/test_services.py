from fastapi.testclient import TestClient

from maadhyam_api.main import app


def test_services_list():
    with TestClient(app) as client:
        response = client.get("/api/services")

    assert response.status_code == 200

    data = response.json()

    assert len(data["services"]) == 3

    service_ids = [service["id"] for service in data["services"]]

    assert service_ids == [
        "passport",
        "aadhaar",
        "epfo",
    ]

    assert all(
        service["status"] == "planned"
        for service in data["services"]
    )