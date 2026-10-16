from maadhyam_api.m10.firestore_rest import transactional
"""Firestore-only persistence, with transactional compare-and-swap updates."""
import os
from functools import lru_cache
from google.cloud import firestore
from fastapi import HTTPException, Request
from maadhyam_api.config import get_settings

@lru_cache(maxsize=1)
def client():
    settings = get_settings()
    project = settings.google_cloud_project
    if not project and not os.getenv("FIRESTORE_EMULATOR_HOST"):
        raise RuntimeError("Set GOOGLE_CLOUD_PROJECT or FIRESTORE_EMULATOR_HOST")
    credentials = None
    if settings.google_application_credentials:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(settings.google_application_credentials)
    return firestore.Client(project=project or "maadhyam-local", credentials=credentials)

def request_database(request: Request):
    settings = get_settings()
    if settings.firestore_transport == 'user-rest':
        from maadhyam_api.m10.firestore_rest import RestDatabase
        authorization = request.headers.get('Authorization', '')
        if not authorization.startswith('Bearer '):
            raise HTTPException(401, 'Authentication required')
        return RestDatabase(settings.google_cloud_project, authorization[7:].strip())
    return client()


class FirestoreRepository:
    def __init__(self, db=None):
        self.db = db if db is not None else client()

    def collection(self, owner):
        return self.db.collection("users").document(owner).collection("applications")

    def create(self, owner, record, record_id=None):
        ref = self.collection(owner).document(record_id) if record_id else self.collection(owner).document()
        data = {**record, "id": ref.id, "owner_user_id": owner}
        ref.create(data)
        return data

    def get(self, owner, record_id):
        doc = self.collection(owner).document(record_id).get()
        if not doc.exists:
            raise HTTPException(404, "Application not found")
        return doc.to_dict()

    def list(self, owner):
        return [d.to_dict() for d in self.collection(owner).stream()]

    def update(self, owner, record_id, expected_revision, transform):
        ref = self.collection(owner).document(record_id)
        transaction = self.db.transaction()
        @transactional
        def commit(tx):
            doc = ref.get(transaction=tx)
            if not doc.exists:
                raise HTTPException(404, "Application not found")
            previous = doc.to_dict()
            if previous["revision"] != expected_revision:
                raise HTTPException(409, "Revision conflict; reload before saving")
            changes = transform(previous)
            tx.update(ref, changes)
            return {**previous, **changes}
        return commit(transaction)

    def delete(self, owner, record_id, expected_revision):
        ref = self.collection(owner).document(record_id)
        transaction = self.db.transaction()
        @transactional
        def commit(tx):
            doc = ref.get(transaction=tx)
            if not doc.exists:
                raise HTTPException(404, "Application not found")
            if doc.to_dict()["revision"] != expected_revision:
                raise HTTPException(409, "Revision conflict; reload before deleting")
            tx.delete(ref)
        commit(transaction)
