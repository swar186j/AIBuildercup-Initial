
"""Isolated HTTP contract tests; no live cloud credentials required."""

from copy import deepcopy

import pytest
from fastapi import Header, HTTPException
from fastapi.testclient import TestClient

from maadhyam_api.main import create_app
from maadhyam_api.routes.applications import get_store, require_uid


class MemoryStore:
    def __init__(self):
        self.records = {}

    def create(self, uid, fields, client_id=None):
        key = client_id or "generated000000000000000000000001"
        record = {
            **deepcopy(fields),
            "id": key,
            "revision": 1,
            "owner_uid": uid,
        }
        self.records[(uid, key)] = record
        return deepcopy(record)

    def list(self, uid):
        return [
            deepcopy(value)
            for (owner, _), value in self.records.items()
            if owner == uid
        ]

    def get(self, uid, record_id):
        value = self.records.get((uid, record_id))
        if value is None:
            raise HTTPException(404, "Application not found")
        return deepcopy(value)

    def update(self, uid, record_id, revision, fields):
        previous = self.get(uid, record_id)
        if previous["revision"] != revision:
            raise HTTPException(409, "Revision conflict")
        updated = {
            **previous,
            **deepcopy(fields),
            "revision": revision + 1,
        }
        self.records[(uid, record_id)] = updated
        return deepcopy(updated)

    def delete(self, uid, record_id, revision):
        previous = self.get(uid, record_id)
        if previous["revision"] != revision:
            raise HTTPException(409, "Revision conflict")
        del self.records[(uid, record_id)]


@pytest.fixture
def client():
    api = create_app()
    store = MemoryStore()

    def test_identity(x_test_uid: str = Header(default="user-a")):
        return x_test_uid

    api.dependency_overrides[require_uid] = test_identity
    api.dependency_overrides[get_store] = lambda: store

    with TestClient(api) as browser:
        yield browser

    api.dependency_overrides.clear()


def test_missing_authentication():
    with TestClient(create_app()) as client:
        response = client.get("/api/applications")
    assert response.status_code == 401


def test_application_lifecycle(client):
    created = client.post(
        "/api/applications",
        json={
            "service_type": "passport",
            "applicant_details": {"name": "Synthetic Applicant"},
        },
    )
    assert created.status_code == 201, created.text
    item = created.json()
    record_id = item["id"]

    listed = client.get("/api/applications")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(f"/api/applications/{record_id}")
    assert fetched.status_code == 200

    updated = client.patch(
        f"/api/applications/{record_id}",
        json={"revision": 1, "current_step": 3},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["revision"] == 2

    stale = client.patch(
        f"/api/applications/{record_id}",
        json={"revision": 1, "current_step": 4},
    )
    assert stale.status_code == 409

    deleted = client.delete(
        f"/api/applications/{record_id}?revision=2",
    )
    assert deleted.status_code == 204

    assert client.get(
        f"/api/applications/{record_id}"
    ).status_code == 404


def test_cross_user_isolation(client):
    created = client.post(
        "/api/applications",
        json={"service_type": "passport"},
    )
    record_id = created.json()["id"]

    headers = {"X-Test-UID": "user-b"}

    assert client.get(
        f"/api/applications/{record_id}",
        headers=headers,
    ).status_code == 404

    assert client.get(
        "/api/applications",
        headers=headers,
    ).json() == []

    assert client.delete(
        f"/api/applications/{record_id}?revision=1",
        headers=headers,
    ).status_code == 404


def test_invalid_payload(client):
    response = client.post(
        "/api/applications",
        json={"current_step": -10},
    )
    assert response.status_code == 422
