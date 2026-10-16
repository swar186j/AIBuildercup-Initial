import pytest
from fastapi import HTTPException
from google.api_core.exceptions import AlreadyExists
from maadhyam_api.m10.firestore_rest import RestDatabase, encode, decode, transactional
from maadhyam_api.m10.repository import FirestoreRepository


class Response:
    def __init__(self, status, value):
        self.status_code, self.value = status, value
    def json(self):
        return self.value


class Session:
    def __init__(self):
        self.docs = {}
        self.calls = []
        self.clock = 0
    def request(self, method, url, **kwargs):
        assert kwargs['timeout'] == 15 and kwargs['allow_redirects'] is False
        assert kwargs['headers']['Authorization'] == 'Bearer fictional-token'
        path = url.split('/v1/', 1)[1]
        self.calls.append((method, path, kwargs))
        if method == 'POST':
            writes = kwargs['json']['writes']
            for write in writes:
                name = write.get('update', {}).get('name') or write['delete']
                old = self.docs.get(name)
                condition = write['currentDocument']
                if condition.get('exists') is False and old:
                    return Response(400, {'error': {'status': 'FAILED_PRECONDITION'}})
                if 'updateTime' in condition and (not old or old['updateTime'] != condition['updateTime']):
                    return Response(400, {'error': {'status': 'FAILED_PRECONDITION'}})
            for write in writes:
                name = write.get('update', {}).get('name') or write['delete']
                if 'delete' in write:
                    self.docs.pop(name, None)
                else:
                    self.clock += 1
                    value = write['update'].copy()
                    if 'updateMask' in write:
                        value['fields'] = {**self.docs[name]['fields'], **value['fields']}
                    value['updateTime'] = f'2026-10-16T00:00:{self.clock:02d}Z'
                    self.docs[name] = value
            return Response(200, {})
        if 'params' in kwargs:
            return Response(200, {'documents': [v for k, v in self.docs.items() if k.rsplit('/', 1)[0] == path]})
        return Response(200, self.docs[path]) if path in self.docs else Response(404, {})


def test_roundtrip_nested_metadata():
    value = {'none': None, 'yes': True, 'int': 7, 'float': 2.3, 'text': 'fictional', 'list': [None, {'nested': ['a']}], 'empty': {}}
    assert decode(encode(value)) == value


def test_repository_create_revision_conflict_delete_and_owner_paths():
    session = Session()
    db = RestDatabase('fictional-project', 'fictional-token', session)
    repo = FirestoreRepository(db)
    repo.create('a', {'revision': 1, 'nested': {'yes': True}}, 'record-123')
    with pytest.raises(AlreadyExists):
        repo.create('a', {'revision': 1}, 'record-123')
    assert repo.list('b') == []
    assert repo.get('a', 'record-123')['nested'] == {'yes': True}
    assert repo.update('a', 'record-123', 1, lambda value: {'revision': 2})['revision'] == 2
    with pytest.raises(HTTPException) as exc:
        repo.update('a', 'record-123', 1, lambda value: {'revision': 3})
    assert exc.value.status_code == 409
    repo.delete('a', 'record-123', 2)
    assert repo.list('a') == []


def test_commit_precondition_rejects_change_after_read():
    session = Session()
    db = RestDatabase('fictional-project', 'fictional-token', session)
    ref = db.collection('users').document('a').collection('settings').document('household')
    ref.create({'revision': 1})
    tx = db.transaction()
    ref.get(transaction=tx)
    tx.update(ref, {'revision': 2})
    session.docs[ref.name]['updateTime'] = 'changed-concurrently'
    with pytest.raises(HTTPException) as exc:
        tx.commit()
    assert exc.value.status_code == 409
    assert ref.get().to_dict()['revision'] == 1


def test_missing_document_first_settings_save():
    db = RestDatabase('fictional-project', 'fictional-token', Session())
    ref = db.collection('users').document('a').collection('settings').document('planner')
    @transactional
    def save(tx):
        assert not ref.get(transaction=tx).exists
        tx.set(ref, {'revision': 1, 'completed': []})
    save(db.transaction())
    assert ref.get().to_dict() == {'revision': 1, 'completed': []}


@pytest.mark.parametrize('status, expected', [(401, 401), (403, 403), (500, 503), (302, 503)])
def test_provider_errors_are_redacted(status, expected):
    class Failure:
        def request(self, *args, **kwargs):
            return Response(status, {'error': {'message': 'SECRET_PROVIDER_DETAILS'}})
    db = RestDatabase('fictional-project', 'fictional-token', Failure())
    with pytest.raises(HTTPException) as exc:
        db.request('GET')
    assert exc.value.status_code == expected
    assert 'SECRET' not in exc.value.detail


def test_keyless_auth_enforces_project_issuer_and_subject(monkeypatch):
    from google.oauth2 import id_token
    from maadhyam_api.config import get_settings
    from maadhyam_api.m10.auth import authenticated_user
    monkeypatch.setenv('MAADHYAM_FIRESTORE_TRANSPORT', 'user-rest')
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'fictional-project')
    get_settings.cache_clear()
    claims = {'iss': 'https://securetoken.google.com/fictional-project', 'sub': 'fictional-a'}
    def verify(token, request, audience):
        assert audience == 'fictional-project' and token == 'signed-token'
        return claims
    monkeypatch.setattr(id_token, 'verify_firebase_token', verify)
    try:
        assert authenticated_user('Bearer signed-token') == 'fictional-a'
        claims['iss'] = 'https://attacker.example'
        with pytest.raises(HTTPException) as exc:
            authenticated_user('Bearer signed-token')
        assert exc.value.status_code == 401
        claims['iss'] = 'https://securetoken.google.com/fictional-project'
        claims['sub'] = ''
        with pytest.raises(HTTPException):
            authenticated_user('Bearer signed-token')
    finally:
        get_settings.cache_clear()
