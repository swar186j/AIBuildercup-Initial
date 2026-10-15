"""Prototype-only application lifecycle endpoints; no real citizen data."""
import json
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from maadhyam_api.persistence import connection, decode, now, record_event

router = APIRouter(prefix='/applications', tags=['applications'])
Status = Literal['draft', 'in-progress', 'completed']


class ApplicationCreate(BaseModel):
    service: str = Field(default='passport', min_length=1, max_length=80)
    kind: str = Field(default='fresh', min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class ApplicationUpdate(BaseModel):
    status: Status
    payload: dict[str, Any]
    revision: int = Field(ge=1)


def validate_payload(payload):
    if len(json.dumps(payload)) > 65536:
        raise HTTPException(413, 'Payload exceeds 64 KiB')


@router.post('', status_code=201)
def create_application(body: ApplicationCreate):
    validate_payload(body.payload)
    application_id, timestamp = str(uuid4()), now()
    with connection() as db:
        db.execute('INSERT INTO applications VALUES (?,?,?,?,?,?,?,?)',
                   (application_id, body.service, body.kind, 'draft', json.dumps(body.payload), timestamp, timestamp, 1))
        record_event(db, application_id, 'created')
        return decode(db.execute('SELECT * FROM applications WHERE id=?', (application_id,)).fetchone())


@router.get('')
def list_applications():
    with connection() as db:
        return [decode(row) for row in db.execute('SELECT * FROM applications ORDER BY updated_at DESC')]


@router.get('/{application_id}')
def get_application(application_id: str):
    with connection() as db:
        row = db.execute('SELECT * FROM applications WHERE id=?', (application_id,)).fetchone()
        if row is None:
            raise HTTPException(404, 'Application not found')
        return decode(row)


@router.put('/{application_id}')
def update_application(application_id: str, body: ApplicationUpdate):
    validate_payload(body.payload)
    with connection() as db:
        result = db.execute('''UPDATE applications SET status=?, payload=?, updated_at=?, revision=revision+1
            WHERE id=? AND revision=?''', (body.status, json.dumps(body.payload), now(), application_id, body.revision))
        if result.rowcount == 0:
            exists = db.execute('SELECT 1 FROM applications WHERE id=?', (application_id,)).fetchone()
            raise HTTPException(409 if exists else 404, 'Revision conflict' if exists else 'Application not found')
        record_event(db, application_id, 'updated')
        return decode(db.execute('SELECT * FROM applications WHERE id=?', (application_id,)).fetchone())


@router.get('/{application_id}/history')
def application_history(application_id: str):
    with connection() as db:
        if not db.execute('SELECT 1 FROM applications WHERE id=?', (application_id,)).fetchone():
            raise HTTPException(404, 'Application not found')
        return [dict(row) for row in db.execute('SELECT event, timestamp FROM application_events WHERE application_id=? ORDER BY rowid', (application_id,))]


@router.delete('/{application_id}', status_code=204)
def delete_application(application_id: str):
    with connection() as db:
        db.execute('DELETE FROM application_events WHERE application_id=?', (application_id,))
        result = db.execute('DELETE FROM applications WHERE id=?', (application_id,))
        if result.rowcount == 0:
            raise HTTPException(404, 'Application not found')
