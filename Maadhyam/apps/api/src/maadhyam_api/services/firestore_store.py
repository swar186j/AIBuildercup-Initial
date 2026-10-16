
"""Owner-scoped Firestore persistence with revision protection."""

from datetime import datetime, timezone
from functools import lru_cache
from uuid import uuid4

from fastapi import HTTPException
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore

from maadhyam_api.config import get_settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def get_store():
    settings = get_settings()

    if not settings.google_cloud_project:
        raise HTTPException(
            status_code=503,
            detail="Cloud persistence is not configured",
        )

    client = firestore.Client(
        project=settings.google_cloud_project,
        database=settings.firestore_database_id,
    )

    return FirestoreStore(client)


class FirestoreStore:
    def __init__(self, client):
        self.client = client

    def collection(self, uid: str):
        return (
            self.client.collection("users")
            .document(uid)
            .collection("applications")
        )

    def create(self, uid: str, fields: dict, client_id=None):
        record_id = client_id or uuid4().hex
        ref = self.collection(uid).document(record_id)

        now = utc_now()
        record = {
            **fields,
            "id": record_id,
            "owner_uid": uid,
            "revision": 1,
            "created_at": now,
            "updated_at": now,
            "planner_state": {},
            "assessment_history": [],
        }

        try:
            ref.create(record)
        except AlreadyExists:
            if not client_id:
                raise HTTPException(409, "Application already exists")

            existing = self.get(uid, record_id)

            if (
                existing.get("service_type") != fields.get("service_type")
                or existing.get("application_type")
                != fields.get("application_type")
            ):
                raise HTTPException(
                    409,
                    "Existing application has different details",
                )

            return existing

        return record

    def list(self, uid: str):
        items = [
            doc.to_dict()
            for doc in self.collection(uid).limit(100).stream()
        ]
        return sorted(
            items,
            key=lambda item: item.get("updated_at", ""),
            reverse=True,
        )

    def get(self, uid: str, record_id: str):
        snapshot = self.collection(uid).document(record_id).get()

        if not snapshot.exists:
            raise HTTPException(404, "Application not found")

        return snapshot.to_dict()

    def update(
        self,
        uid: str,
        record_id: str,
        expected_revision: int,
        fields: dict,
    ):
        ref = self.collection(uid).document(record_id)
        transaction = self.client.transaction()

        @firestore.transactional
        def commit(tx):
            snapshot = ref.get(transaction=tx)

            if not snapshot.exists:
                raise HTTPException(404, "Application not found")

            previous = snapshot.to_dict()

            if previous.get("revision") != expected_revision:
                raise HTTPException(
                    409,
                    "Revision conflict; reload before saving",
                )

            changes = {
                **fields,
                "revision": expected_revision + 1,
                "updated_at": utc_now(),
            }

            tx.update(ref, changes)
            return {**previous, **changes}

        return commit(transaction)

    def delete(
        self,
        uid: str,
        record_id: str,
        expected_revision: int,
    ):
        ref = self.collection(uid).document(record_id)
        transaction = self.client.transaction()

        @firestore.transactional
        def commit(tx):
            snapshot = ref.get(transaction=tx)

            if not snapshot.exists:
                raise HTTPException(404, "Application not found")

            if snapshot.to_dict().get("revision") != expected_revision:
                raise HTTPException(
                    409,
                    "Revision conflict; reload before deleting",
                )

            tx.delete(ref)

        commit(transaction)
