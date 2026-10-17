"""Authenticated private Vault. File bytes never enter Firestore or AI."""
import hashlib
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.concurrency import run_in_threadpool

from maadhyam_api.services.firebase_auth import require_uid
from maadhyam_api.services.document_store import get_document_store

router = APIRouter(prefix='/documents', tags=['documents'])
MAX_BYTES = 10 * 1024 * 1024
Category = Literal['identity', 'address', 'birth', 'education', 'employment', 'other']


class Metadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: Category = 'other'
    categories: list[Category] = Field(default_factory=list, max_length=6)
    documentType: str = Field(default='Unclassified', max_length=120)
    holder: Literal['self', 'parent-guardian', 'spouse', 'other'] = 'self'
    householdMemberId: str | None = Field(default=None, max_length=128)
    associationConsent: bool = False
    printedName: str = Field(default='', max_length=200)
    dateOfBirth: str = Field(default='', max_length=10)
    expiryDate: str = Field(default='', max_length=10)
    residentialAddress: str = Field(default='', max_length=1000)

    @field_validator('dateOfBirth', 'expiryDate')
    @classmethod
    def date_valid(cls, value):
        from datetime import date
        if value and date.fromisoformat(value).isoformat() != value:
            raise ValueError('Use YYYY-MM-DD')
        return value


class UploadMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    metadata: Metadata = Field(default_factory=Metadata)
    status: Literal['needs-review', 'reviewed'] = 'needs-review'
    originalLocalAddedAt: str | None = Field(default=None,max_length=40)

    @field_validator('originalLocalAddedAt')
    @classmethod
    def local_timestamp(cls,value):
        from datetime import datetime,timezone
        if value is None:
            return None
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None or parsed > datetime.now(timezone.utc):
            raise ValueError('Original local timestamp must be a past UTC timestamp')
        return parsed.astimezone(timezone.utc).isoformat()


class DocumentPatch(UploadMetadata):
    revision: int = Field(ge=1)


DocumentId = Path(pattern=r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')


@router.post('', status_code=201)
async def upload_document(
    document_id: str = Form(...), cloud_storage_consent: bool = Form(False),
    fields: str = Form('{}'), file: UploadFile = File(...),
    uid: str = Depends(require_uid), store=Depends(get_document_store),
):
    try:
        if not cloud_storage_consent:
            raise HTTPException(403, 'Explicit cloud storage consent is required')
        try:
            if str(UUID(document_id)) != document_id:
                raise ValueError()
            parsed = UploadMetadata.model_validate_json(fields)
        except (ValueError, ValidationError):
            raise HTTPException(422, 'Invalid document ID or metadata') from None
        filename = file.filename or ''
        if not filename or len(filename) > 200 or any(c in filename for c in ('/', '\\', '\x00', '\r', '\n')):
            raise HTTPException(422, 'Invalid filename')
        extension = filename.rsplit('.', 1)[-1].lower()
        expected = {'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}.get(extension)
        if not expected or file.content_type != expected:
            raise HTTPException(415, 'Only matching PDF, PNG and JPEG files are supported')
        chunks, size = [], 0
        while chunk := await file.read(65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise HTTPException(413, 'File exceeds 10 MiB')
            chunks.append(chunk)
        data = b''.join(chunks)
        if not data:
            raise HTTPException(400, 'File is empty')
        signatures = {'application/pdf': b'%PDF-', 'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8\xff'}
        if not data.startswith(signatures[expected]):
            raise HTTPException(415, 'File signature does not match MIME type')
        fields = {**parsed.model_dump(mode='json'), 'filename': filename, 'contentType': expected,
                  'sizeBytes': size, 'sha256': hashlib.sha256(data).hexdigest()}
        return await run_in_threadpool(store.upload, uid, document_id, fields, data)
    finally:
        await file.close()


@router.get('')
def list_documents(uid: str = Depends(require_uid), store=Depends(get_document_store)):
    return store.list(uid)


@router.get('/{document_id}')
def get_document(document_id: str = DocumentId, uid: str = Depends(require_uid), store=Depends(get_document_store)):
    return store.get(uid, document_id)


@router.get('/{document_id}/file')
def download_document(document_id: str = DocumentId, uid: str = Depends(require_uid), store=Depends(get_document_store)):
    record, data = store.download(uid, document_id)
    return Response(data, media_type=record['contentType'], headers={
        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
        'Content-Disposition': 'attachment',
    })


@router.patch('/{document_id}')
def patch_document(payload: DocumentPatch, document_id: str = DocumentId,
                   uid: str = Depends(require_uid), store=Depends(get_document_store)):
    return store.patch(uid, document_id, payload.revision, payload.model_dump(exclude={'revision','originalLocalAddedAt'}, mode='json'))


@router.delete('/{document_id}', status_code=204)
def delete_document(document_id: str = DocumentId, revision: int = Query(ge=1),
                    uid: str = Depends(require_uid), store=Depends(get_document_store)):
    store.delete(uid, document_id, revision)


@router.delete('')
def clear_documents(uid: str = Depends(require_uid), store=Depends(get_document_store)):
    # Snapshot only this UID; concurrent new uploads are not silently deleted.
    deleted, failed = [], []
    for record in store.list(uid):
        try:
            store.delete(uid, record['id'], record['revision'])
            deleted.append(record['id'])
        except Exception:
            failed.append(record['id'])
    return {'deleted': deleted, 'failed': failed}
