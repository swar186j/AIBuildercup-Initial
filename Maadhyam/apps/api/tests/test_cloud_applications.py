
"""Isolated HTTP contract tests; no live cloud credentials required."""

from copy import deepcopy

import pytest
from fastapi import Header, HTTPException
from fastapi.testclient import TestClient

from maadhyam_api.main import create_app
from maadhyam_api.routes.applications import get_store, require_uid
from copy import deepcopy
from uuid import uuid4

class MemoryStore:
    def __init__(self):
        self.records = {}

    def create(self, uid, fields, client_id=None):
        key = client_id or uuid4().hex
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


def test_workspace_snapshots_and_revision(client):
    payload = {
        "service_type": "passport",
        "planner_state": {"manual_task_ids": ["journey"], "target_date": "2026-11-15", "generated_plan": {"task_ids": ["resolve-name"]}},
        "household_state": {"members": [{"id": "applicant", "label": "Demo", "relationship": "self", "dependsOnMemberIds": [], "dependsOnDocumentIds": [], "relationshipEvidenceDocumentIds": []}]},
        "assessment_history": [{"captured_at": "2026-10-16T15:00:00Z", "task_count": 1, "finding_count": 1, "task_ids": ["resolve-name"]}],
    }
    response=client.post("/api/applications",json=payload)
    assert response.status_code==201,response.text
    created=response.json();id=created["id"]
    assert created["planner_state"]["generated_plan"]["task_ids"]==["resolve-name"]
    updated=client.patch(f"/api/applications/{id}",json={"revision":1,"planner_state":{"manual_task_ids":["journey","vault"],"target_date":None,"generated_plan":{}}})
    assert updated.status_code==200,updated.text
    assert updated.json()["revision"]==2
    assert client.get(f"/api/applications/{id}").json()["household_state"]["members"][0]["label"]=="Demo"
    assert client.patch(f"/api/applications/{id}",json={"revision":1,"household_state":{"members":[]}}).status_code==409
    assert client.get(f"/api/applications/{id}",headers={"X-Test-UID":"user-b"}).status_code==404


def test_reject_malformed_workspace_fields(client):
    invalid=[
        {"planner_state":{"manual_task_ids":list(map(str,range(101))) }},
        {"planner_state":{"target_date":"tomorrow"}},
        {"household_state":{"members":[{"id":"child","label":"A","relationship":"invalid"}]}},
        {"assessment_history":[{"captured_at":"x","task_count":-1,"finding_count":0,"task_ids":[]}]},
        {"applicant_details":{"long":"x"*110_000}},
    ]
    for payload in invalid:
        assert client.post("/api/applications",json=payload).status_code==422
