"""User-token Firestore transport for hosts without Google service-account keys.

Single-document mutations use atomic commit update-time preconditions, preserving
the existing optimistic revision contract. Firebase Security Rules also apply.
"""
from uuid import uuid4
from urllib.parse import quote
import requests
from fastapi import HTTPException
from google.api_core.exceptions import AlreadyExists
from google.cloud import firestore


def encode(value):
    if value is None:
        return {'nullValue': None}
    if isinstance(value, bool):
        return {'booleanValue': value}
    if isinstance(value, int):
        return {'integerValue': str(value)}
    if isinstance(value, float):
        return {'doubleValue': value}
    if isinstance(value, str):
        return {'stringValue': value}
    if isinstance(value, list):
        return {'arrayValue': {'values': [encode(v) for v in value]}}
    if isinstance(value, dict):
        return {'mapValue': {'fields': {k: encode(v) for k, v in value.items()}}}
    raise ValueError('Unsupported Firestore value')


def decode(value):
    if 'nullValue' in value:
        return None
    if 'integerValue' in value:
        return int(value['integerValue'])
    if 'arrayValue' in value:
        return [decode(v) for v in value['arrayValue'].get('values', [])]
    if 'mapValue' in value:
        return {k: decode(v) for k, v in value['mapValue'].get('fields', {}).items()}
    for key in ('stringValue', 'booleanValue', 'doubleValue', 'timestampValue'):
        if key in value:
            return value[key]
    raise ValueError('Unsupported Firestore response value')


class Snapshot:
    def __init__(self, ref, value=None):
        self.reference = ref
        self.id = ref.id
        self.exists = value is not None
        self.update_time = (value or {}).get('updateTime')
        self.data = {k: decode(v) for k, v in (value or {}).get('fields', {}).items()}

    def to_dict(self):
        return self.data.copy()


class RestDatabase:
    def __init__(self, project, token, session=None):
        if not project or not token:
            raise HTTPException(401, 'Authentication required')
        self.project = project
        self.session = session or requests
        self.headers = {'Authorization': 'Bearer ' + token}
        self.name = f'projects/{project}/databases/(default)/documents'
        self.url = 'https://firestore.googleapis.com/v1/' + self.name

    def request(self, method, path='', *, missing=False, create=False, **kwargs):
        try:
            r = self.session.request(method, self.url + path, headers=self.headers,
                timeout=15, allow_redirects=False, **kwargs)
        except requests.RequestException:
            raise HTTPException(503, 'Cloud persistence unavailable; retry later') from None
        if missing and r.status_code == 404:
            return None
        error_status = ''
        if r.status_code >= 400:
            try:
                error_status = r.json().get('error', {}).get('status', '')
            except ValueError:
                pass
        if error_status == 'FAILED_PRECONDITION':
            if create:
                raise AlreadyExists('Document already exists')
            raise HTTPException(409, 'Revision conflict; reload before saving')
        if create and r.status_code in (409, 412):
            raise AlreadyExists('Document already exists')
        if r.status_code in (409, 412):
            raise HTTPException(409, 'Revision conflict; reload before saving')
        if r.status_code in (401, 403):
            raise HTTPException(r.status_code, 'Cloud authorization failed; sign in again or check owner rules')
        if not 200 <= r.status_code < 300:
            raise HTTPException(503, 'Cloud persistence unavailable; retry later')
        try:
            return r.json()
        except ValueError:
            raise HTTPException(502, 'Cloud persistence returned an invalid response') from None

    def collection(self, name):
        return Collection(self, [name])

    def transaction(self):
        return RestTransaction(self)


def segment(value):
    if not value or '/' in value or value in ('.', '..'):
        raise HTTPException(422, 'Invalid record path')
    return quote(value, safe='')


class Collection:
    def __init__(self, db, parts):
        self.db, self.parts = db, parts

    def document(self, name=None):
        return Reference(self.db, self.parts + [name or str(uuid4())])

    def stream(self):
        token = None
        while True:
            params = {'pageSize': 1000}
            if token:
                params['pageToken'] = token
            data = self.db.request('GET', '/' + '/'.join(segment(p) for p in self.parts), params=params)
            for item in data.get('documents', []):
                yield Snapshot(self.document(item['name'].rsplit('/', 1)[1]), item)
            token = data.get('nextPageToken')
            if not token:
                break


class Reference:
    def __init__(self, db, parts):
        self.db, self.parts = db, parts
        self.id = parts[-1]
        self.path = '/' + '/'.join(segment(p) for p in parts)
        self.name = db.name + '/' + '/'.join(parts)

    def collection(self, name):
        return Collection(self.db, self.parts + [name])

    def get(self, transaction=None):
        value = self.db.request('GET', self.path, missing=True)
        snapshot = Snapshot(self, value)
        if transaction is not None:
            transaction.reads[self.name] = snapshot
        return snapshot

    def create(self, value):
        return self.db.request('POST', ':commit', create=True, json={'writes': [{
            'update': {'name': self.name, 'fields': {k: encode(v) for k, v in value.items()}},
            'currentDocument': {'exists': False}}]})


class RestTransaction:
    def __init__(self, db):
        self.db, self.reads, self.writes = db, {}, []

    def condition(self, ref):
        if ref.name not in self.reads:
            raise RuntimeError('Read before mutation required')
        snap = self.reads[ref.name]
        return {'updateTime': snap.update_time} if snap.exists else {'exists': False}

    def set(self, ref, value):
        self.writes.append({'update': {'name': ref.name, 'fields': {k: encode(v) for k, v in value.items()}},
            'currentDocument': self.condition(ref)})

    def update(self, ref, value):
        self.writes.append({'update': {'name': ref.name, 'fields': {k: encode(v) for k, v in value.items()}},
            'updateMask': {'fieldPaths': list(value)}, 'currentDocument': self.condition(ref)})

    def delete(self, ref):
        self.writes.append({'delete': ref.name, 'currentDocument': self.condition(ref)})

    def commit(self):
        if self.writes:
            self.db.request('POST', ':commit', json={'writes': self.writes})


def transactional(fn):
    def invoke(tx):
        if isinstance(tx, RestTransaction):
            result = fn(tx)
            tx.commit()
            return result
        return firestore.transactional(fn)(tx)
    return invoke
