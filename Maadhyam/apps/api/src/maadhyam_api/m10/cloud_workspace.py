from maadhyam_api.m10.firestore_rest import transactional
"""Authenticated, private file storage and revisioned household settings."""
import hashlib
import json
from typing import Literal
from urllib.parse import quote
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from maadhyam_api.m10.file_storage import FileStorage, record_storage
from maadhyam_api.m10.auth import authenticated_user
from maadhyam_api.m10.models import utc_now
from maadhyam_api.m10.repository import request_database

router = APIRouter(prefix='/workspace', tags=['cloud workspace'])
MAX_BYTES = 10 * 1024 * 1024


def database(request: Request):
    return request_database(request)


def bucket():
    return FileStorage()


class Metadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Literal['identity','address','birth','education','employment','other'] = 'other'
    categories: list[Literal['identity','address','birth','education','employment','other']] = Field(default_factory=list, max_length=6)
    documentType: str = Field(default='', max_length=120)
    holder: Literal['self','parent-guardian','spouse','other'] = 'self'
    householdMemberId: str | None = Field(default=None, max_length=128)
    associationConsent: bool | None = None
    printedName: str | None = Field(default=None, max_length=200)
    dateOfBirth: str | None = Field(default=None, max_length=10)
    expiryDate: str | None = Field(default=None, max_length=10)
    residentialAddress: str | None = Field(default=None, max_length=1000)


class DocumentPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=1)
    metadata: Metadata
    status: Literal['needs-review','reviewed']


class StorageMigration(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=1)
    confirmed: bool = False


class Member(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=200)
    relationship: Literal['self','parent','guardian','spouse','child','sibling','other']
    dependsOnMemberIds: list[str] = Field(default_factory=list, max_length=30)
    dependsOnDocumentIds: list[str] = Field(default_factory=list, max_length=100)
    relationshipEvidenceDocumentIds: list[str] = Field(default_factory=list, max_length=100)


class HouseholdPatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision: int = Field(ge=0)
    members: list[Member] = Field(min_length=1, max_length=30)

    @model_validator(mode='after')
    def valid_members(self):
        ids = {member.id for member in self.members}
        if len(ids) != len(self.members) or not any(m.id == 'applicant' and m.relationship == 'self' for m in self.members):
            raise ValueError('Household requires unique members and the applicant')
        if any(m.relationship == 'self' and m.id != 'applicant' for m in self.members):
            raise ValueError('Only applicant may have relationship self')
        if any(any(dep not in ids or dep == m.id for dep in m.dependsOnMemberIds) for m in self.members):
            raise ValueError('Invalid household member dependency')
        return self


def documents(db, user):
    return db.collection('users').document(user).collection('vault')


def document_ref(db, user, document_id):
    import re
    if not re.fullmatch(r'[A-Za-z0-9-]{8,128}', document_id):
        raise HTTPException(422, 'Invalid document ID')
    return documents(db, user).document(document_id)


def record(ref):
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(404, 'Document not found')
    return snapshot.to_dict()


@router.get('/documents')
def list_documents(user=Depends(authenticated_user), db=Depends(database), files=Depends(bucket)):
    return [item.to_dict() for item in documents(db, user).stream()]


@router.put('/documents/{document_id}', status_code=201)
def upload_document(document_id: str, file: UploadFile = File(...), metadata: str = Form(...),
                          user=Depends(authenticated_user), db=Depends(database), files=Depends(bucket)):
    ref = document_ref(db, user, document_id)
    try:
        parsed = Metadata.model_validate(json.loads(metadata))
    except (ValueError, ValidationError):
        raise HTTPException(422, 'Invalid document metadata') from None
    try:
        data = file.file.read(MAX_BYTES + 1)
    finally:
        file.file.close()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(413, 'File must contain 1 byte to 10 MB')
    mime = file.content_type
    signatures = {'application/pdf': b'%PDF-', 'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}
    if mime not in signatures or not data.startswith(signatures[mime]):
        raise HTTPException(415, 'Only valid PDF, PNG and JPEG files are supported')
    digest = hashlib.sha256(data).hexdigest()
    existing = ref.get()
    if existing.exists:
        saved = existing.to_dict()
        if saved.get('sha256') != digest or saved.get('deleting'):
            raise HTTPException(409, 'Document ID already belongs to another upload or pending deletion')
        return saved
    key = f'users/{quote(user, safe="")}/vault/{document_id}'
    files.upload(key, data, mime)
    value = {'id': document_id, 'filename': (file.filename or 'document')[:255], 'mime': mime,
             'size': len(data), 'sha256': digest, 'object_key': key, 'storage_provider': getattr(files, 'provider', 'supabase'),
             'metadata': parsed.model_dump(exclude_none=True), 'status': 'needs-review', 'revision': 1, 'added_at': utc_now()}
    try:
        ref.create(value)
    except AlreadyExists:
        value = record(ref)
        if value.get('sha256') != digest:
            raise HTTPException(409, 'Concurrent upload conflict') from None
    return value


@router.get('/documents/{document_id}/content')
def download_document(document_id: str, user=Depends(authenticated_user), db=Depends(database), files=Depends(bucket)):
    value = record(document_ref(db, user, document_id))
    if value.get('deleting'):
        raise HTTPException(409, 'Document deletion is pending')
    if value.get('mime') not in ('application/pdf', 'image/png', 'image/jpeg'):
        raise HTTPException(422, 'Invalid stored document type')
    data = record_storage(files, value).download(f'users/{quote(user, safe="")}/vault/{document_id}')
    return Response(data, media_type=value['mime'], headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.patch('/documents/{document_id}')
def update_document(document_id: str, payload: DocumentPatch, user=Depends(authenticated_user), db=Depends(database)):
    ref = document_ref(db, user, document_id)
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        if not snapshot.exists:
            raise HTTPException(404, 'Document not found')
        before = snapshot.to_dict()
        if before['revision'] != payload.revision or before.get('deleting'):
            raise HTTPException(409, 'Document changed; reload before saving')
        changes = {'metadata': payload.metadata.model_dump(exclude_none=True), 'status': payload.status, 'revision': payload.revision + 1}
        tx.update(ref, changes)
        return {**before, **changes}
    return commit(db.transaction())


@router.delete('/documents/{document_id}', status_code=204)
def delete_document(document_id: str, revision: int = Query(ge=1), user=Depends(authenticated_user), db=Depends(database), files=Depends(bucket)):
    ref = document_ref(db, user, document_id)
    @transactional
    def lock(tx):
        snapshot = ref.get(transaction=tx)
        if not snapshot.exists:
            raise HTTPException(404, 'Document not found')
        before = snapshot.to_dict()
        if before['revision'] != revision:
            raise HTTPException(409, 'Document changed; reload before deleting')
        tx.update(ref, {'deleting': True})
        return before
    value = lock(db.transaction())
    record_storage(files, value).delete(f'users/{quote(user, safe="")}/vault/{document_id}')
    if value.get('migration_source_retained') == 'supabase' and isinstance(files, FileStorage):
        # Explicit document deletion also removes its retained migration original.
        files.for_provider('supabase').delete(f'users/{quote(user, safe="")}/vault/{document_id}')
    @transactional
    def finish(tx):
        snapshot = ref.get(transaction=tx)
        if snapshot.exists and snapshot.to_dict().get('deleting') and snapshot.to_dict()['revision'] == revision:
            tx.delete(ref)
    finish(db.transaction())


@router.post('/documents/{document_id}/migrate-storage')
def migrate_document_storage(document_id: str, payload: StorageMigration, user=Depends(authenticated_user),
                             db=Depends(database), files=Depends(bucket)):
    if not payload.confirmed:
        raise HTTPException(400, 'Explicit file migration confirmation required')
    if not isinstance(files, FileStorage) or files.provider != 'gcs':
        raise HTTPException(503, 'Google Cloud Storage migration is not configured')
    ref = document_ref(db, user, document_id)
    before = record(ref)
    if before['revision'] != payload.revision or before.get('deleting'):
        raise HTTPException(409, 'Document changed; reload before migration')
    if before.get('storage_provider') == 'gcs':
        return before
    key = f'users/{quote(user, safe="")}/vault/{document_id}'
    data = record_storage(files, before).download(key)
    if not data or len(data) > MAX_BYTES or hashlib.sha256(data).hexdigest() != before['sha256']:
        raise HTTPException(409, 'Source file integrity check failed; original preserved')
    if before.get('mime') not in ('application/pdf', 'image/png', 'image/jpeg'):
        raise HTTPException(422, 'Invalid stored document type')
    files.upload(key, data, before['mime'])
    if hashlib.sha256(files.active.download(key)).hexdigest() != before['sha256']:
        raise HTTPException(502, 'Copied file integrity check failed; original preserved')
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        if not snapshot.exists:
            raise HTTPException(409, 'Document was deleted during migration')
        current = snapshot.to_dict()
        if current['revision'] != payload.revision or current.get('deleting'):
            raise HTTPException(409, 'Document changed during migration; reload before retry')
        changes = {'storage_provider': 'gcs', 'migration_source_retained': 'supabase',
            'revision': current['revision'] + 1, 'storage_migrated_at': utc_now()}
        tx.update(ref, changes)
        return {**current, **changes}
    return commit(db.transaction())


@router.post('/documents/{document_id}/finalize-storage-migration')
def finalize_storage_migration(document_id: str, payload: StorageMigration, user=Depends(authenticated_user),
                               db=Depends(database), files=Depends(bucket)):
    if not payload.confirmed:
        raise HTTPException(400, 'Explicit retained-original deletion confirmation required')
    if not isinstance(files, FileStorage) or files.provider != 'gcs':
        raise HTTPException(503, 'Google Cloud Storage migration is not configured')
    ref = document_ref(db, user, document_id)
    before = record(ref)
    if before['revision'] != payload.revision or before.get('deleting'):
        raise HTTPException(409, 'Document changed; reload before finalizing migration')
    if before.get('storage_provider') != 'gcs':
        raise HTTPException(409, 'Verify migration to Google Cloud Storage first')
    if not before.get('migration_source_retained'):
        return before
    key = f'users/{quote(user, safe="")}/vault/{document_id}'
    if hashlib.sha256(files.active.download(key)).hexdigest() != before['sha256']:
        raise HTTPException(409, 'Google Cloud file integrity check failed; original preserved')
    files.for_provider('supabase').delete(key)
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        if not snapshot.exists:
            raise HTTPException(409, 'Document was deleted during finalization')
        current = snapshot.to_dict()
        if current['revision'] != payload.revision or current.get('deleting'):
            raise HTTPException(409, 'Document changed during finalization; reload before retry')
        changes = {'migration_source_retained': None, 'revision': current['revision'] + 1}
        tx.update(ref, changes)
        return {**current, **changes}
    return commit(db.transaction())


@router.get('/household')
def get_household(user=Depends(authenticated_user), db=Depends(database)):
    snapshot = db.collection('users').document(user).collection('settings').document('household').get()
    return snapshot.to_dict() if snapshot.exists else {'members': [], 'revision': 0}


@router.put('/household')
def save_household(payload: HouseholdPatch, user=Depends(authenticated_user), db=Depends(database)):
    ref = db.collection('users').document(user).collection('settings').document('household')
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        before = snapshot.to_dict() if snapshot.exists else {'revision': 0}
        if before['revision'] != payload.revision:
            raise HTTPException(409, 'Household changed in another session; reload before saving')
        value = {'members': [m.model_dump() for m in payload.members], 'revision': payload.revision + 1, 'updated_at': utc_now()}
        tx.set(ref, value)
        return value
    return commit(db.transaction())
