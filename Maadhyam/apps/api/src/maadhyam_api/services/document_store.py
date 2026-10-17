"""UID-scoped Firestore metadata and generation-protected private GCS objects.

Reserve metadata before object creation. Retries recover pending uploads using a
content checksum. A deleting tombstone blocks updates/uploads until both removals
finish. No global cleanup or public URLs. All transactions precede GCS side effects.
"""
from functools import lru_cache

from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from google.cloud import firestore, storage

from maadhyam_api.config import get_settings


@lru_cache(maxsize=1)
def get_document_store():
    settings = get_settings()
    if not settings.google_cloud_project or not settings.document_bucket:
        raise HTTPException(503, 'Cloud Vault is not configured')
    if settings.firestore_database_id != 'maadhyam':
        raise HTTPException(503, 'Cloud Vault requires the named maadhyam database')
    return DocumentStore(firestore.Client(project=settings.google_cloud_project, database='maadhyam'),
                         storage.Client(project=settings.google_cloud_project).bucket(settings.document_bucket))


class DocumentStore:
    def __init__(self, client, bucket):
        self.client, self.bucket = client, bucket

    def collection(self, uid):
        return self.client.collection('users').document(uid).collection('documents')

    def get(self, uid, document_id):
        snapshot = self.collection(uid).document(document_id).get()
        if not snapshot.exists:
            raise HTTPException(404, 'Document not found')
        return snapshot.to_dict()

    def list(self, uid):
        return [doc.to_dict() for doc in self.collection(uid).stream()]

    def mutate(self, uid, document_id, transform):
        ref = self.collection(uid).document(document_id)
        @firestore.transactional
        def commit(tx):
            snapshot = ref.get(transaction=tx)
            previous = snapshot.to_dict() if snapshot.exists else None
            changes = transform(previous)
            if changes is None:
                tx.delete(ref)
            else:
                # Server timestamps are read back after acknowledgment.
                tx.set(ref, changes)
            return changes
        result = commit(self.client.transaction())
        return self.get(uid, document_id) if result is not None else None

    def upload(self, uid, document_id, fields, data):
        path = f'users/{uid}/documents/{document_id}/original'
        def reserve(previous):
            if previous:
                if previous['storageStatus'] == 'deleting' or any(previous.get(key) != value for key,value in fields.items()):
                    raise HTTPException(409, 'Document ID already has different content or is deleting')
                return previous
            return {**fields, 'id': document_id, 'revision': 1, 'storagePath': path,
                    'storageStatus': 'pending', 'createdAt': firestore.SERVER_TIMESTAMP,
                    'updatedAt': firestore.SERVER_TIMESTAMP}
        record = self.mutate(uid, document_id, reserve)
        if record['storageStatus'] == 'ready':
            # Verify the object still exists before reporting an idempotent success.
            self.bucket.blob(path, generation=int(record['generation'])).reload(timeout=20)
            return record
        blob = self.bucket.blob(path)
        try:
            blob.metadata = {'sha256': fields['sha256']}
            blob.upload_from_string(data, content_type=fields['contentType'], if_generation_match=0, timeout=20)
        except PreconditionFailed:
            blob.reload(timeout=20)
            if (blob.metadata or {}).get('sha256') != fields['sha256'] or blob.size != len(data):
                raise HTTPException(409, 'Existing file differs; original retained') from None
        generation = str(blob.generation)
        def finish(previous):
            if not previous or previous['storageStatus'] == 'deleting':
                raise HTTPException(409, 'Upload interrupted by deletion; retry after reconciliation')
            if previous['storageStatus'] == 'ready':
                return previous
            return {**previous, 'generation': generation, 'storageStatus': 'ready', 'uploadedAt': firestore.SERVER_TIMESTAMP,
                    'revision': previous['revision'] + 1, 'updatedAt': firestore.SERVER_TIMESTAMP}
        # If final write fails the pending record remains recoverable; do not
        # remove an object that a concurrent successful retry may now reference.
        try:
            return self.mutate(uid, document_id, finish)
        except HTTPException:
            # A delete may finish while upload is in flight. Remove only this
            # exact object generation when no ready record references it.
            try:
                current = self.get(uid, document_id)
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
                current = None
            if current is None or current['storageStatus'] == 'deleting':
                try:
                    self.bucket.blob(path).delete(if_generation_match=int(generation), timeout=20)
                except NotFound:
                    pass
            raise

    def patch(self, uid, document_id, revision, fields):
        def change(previous):
            if not previous:
                raise HTTPException(404, 'Document not found')
            if previous['revision'] != revision or previous['storageStatus'] != 'ready':
                raise HTTPException(409, 'Revision conflict or document is not ready; refresh before saving')
            changes={**fields}
            if 'metadata' in changes:
                changes['metadata']={**previous['metadata'],**changes['metadata']}
            return {**previous, **changes, 'revision': revision + 1, 'updatedAt': firestore.SERVER_TIMESTAMP}
        return self.mutate(uid, document_id, change)

    def download(self, uid, document_id):
        record = self.get(uid, document_id)
        if record['storageStatus'] != 'ready':
            raise HTTPException(409, 'Document is not ready')
        try:
            data = self.bucket.blob(record['storagePath'], generation=int(record['generation'])).download_as_bytes(
                if_generation_match=int(record['generation']), timeout=20)
        except NotFound:
            raise HTTPException(409, 'File is unavailable; retry or restore the original') from None
        return record, data

    def delete(self, uid, document_id, revision):
        def mark(previous):
            if not previous:
                return None  # Idempotent; never touch an unowned GCS object.
            if previous['revision'] != revision:
                raise HTTPException(409, 'Revision conflict; refresh before deleting')
            return {**previous, 'storageStatus': 'deleting', 'updatedAt': firestore.SERVER_TIMESTAMP}
        record = self.mutate(uid, document_id, mark)
        if record is None:
            return
        blob = self.bucket.blob(record['storagePath'])
        try:
            if not record.get('generation'):
                blob.reload(timeout=20)
            generation = int(record.get('generation') or blob.generation)
            blob.delete(if_generation_match=generation, timeout=20)
        except NotFound:
            pass
        def finish(previous):
            if previous and (previous['storageStatus'] != 'deleting' or previous['revision'] != revision):
                raise HTTPException(409, 'Document changed during deletion')
            return None
        self.mutate(uid, document_id, finish)
