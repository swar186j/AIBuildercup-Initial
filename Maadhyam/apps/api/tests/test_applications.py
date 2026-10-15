"""Run from apps/api: uv run pytest tests/test_applications.py -q"""
import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import app
import maadhyam_api.persistence as persistence


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, 'DB_PATH', tmp_path / 'test.sqlite3')
    return TestClient(app)


def test_application_lifecycle(client):
    created = client.post('/api/applications', json={'service': 'passport', 'kind': 'fresh', 'payload': {'demo': True}})
    assert created.status_code == 201
    app = created.json()
    assert app['revision'] == 1
    assert len(client.get('/api/applications').json()) == 1
    updated = client.put(f"/api/applications/{app['id']}", json={
        'revision': 1, 'status': 'in-progress', 'payload': {'step': 2}
    })
    assert updated.status_code == 200
    assert updated.json()['revision'] == 2
    assert client.put(f"/api/applications/{app['id']}", json={
        'revision': 1, 'status': 'completed', 'payload': {}
    }).status_code == 409
    assert len(client.get(f"/api/applications/{app['id']}/history").json()) == 2
    assert client.delete(f"/api/applications/{app['id']}").status_code == 204
    assert client.get(f"/api/applications/{app['id']}").status_code == 404
