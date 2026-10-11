from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json() == {
        "status": "healthy", "application": "Draft1", "version": "0.1.0"
    }

def test_root():
    assert client.get("/").status_code == 200

def test_reject_wrong_file_type():
    response = client.post(
        "/api/evidence/submit",
        data={"scheme": "ESIC", "applicant_name": "Test User"},
        files={"document": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
