import json
import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore
from m10_support import test_app as make_app

PNG = b'\x89PNG\r\n\x1a\nfictional-test-image'
META = {'category': 'identity', 'documentType': 'Fictional ID', 'holder': 'self'}
PATH = '/api/workspace/documents/test-document-123'


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(firestore, 'transactional', lambda fn: fn)
    app, _ = make_app()
    with TestClient(app, headers={'Authorization': 'Bearer test-a'}) as result:
        yield result


def upload(client, data=PNG, mime='image/png'):
    return client.put(PATH, files={'file': ('fictional.png', data, mime)}, data={'metadata': json.dumps(META)})


def test_file_upload_private_download_reload_and_idempotency(client):
    first = upload(client)
    assert first.status_code == 201
    assert first.json()['revision'] == 1
    assert upload(client).json()['id'] == first.json()['id']
    assert len(client.get('/api/workspace/documents').json()) == 1
    response = client.get(PATH + '/content')
    assert response.content == PNG
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert upload(client, PNG + b'changed').status_code == 409


def test_document_owner_isolation(client):
    upload(client)
    other = {'Authorization': 'Bearer test-b'}
    assert client.get('/api/workspace/documents', headers=other).json() == []
    assert client.get(PATH + '/content', headers=other).status_code == 404
    assert client.patch(PATH, headers=other, json={'revision': 1, 'metadata': META, 'status': 'reviewed'}).status_code == 404
    assert client.delete(PATH + '?revision=1', headers=other).status_code == 404


def test_download_and_delete_never_trust_stored_object_key(client):
    from maadhyam_api.m10 import cloud_workspace
    upload(client)
    db = client.app.dependency_overrides[cloud_workspace.database]()
    ref = db.collection('users').document('a').collection('vault').document('test-document-123')
    ref.update({'object_key': 'users/b/vault/other-document'})
    files = client.app.state.test_files
    files.objects['users/b/vault/other-document'] = b'other-user-private-content'
    assert client.get(PATH + '/content').content == PNG
    assert client.delete(PATH + '?revision=1').status_code == 204
    assert files.objects['users/b/vault/other-document'] == b'other-user-private-content'


@pytest.mark.parametrize('data,mime,status', [(b'', 'image/png', 413), (b'bad', 'image/png', 415), (PNG, 'text/html', 415), (b'a' * (10 * 1024 * 1024 + 1), 'image/png', 413)], ids=['empty','signature','mime','oversize'])
def test_file_validation(client, data, mime, status):
    assert upload(client, data, mime).status_code == status


def test_document_metadata_conflicts_and_confirmed_delete(client):
    upload(client)
    result = client.patch(PATH, json={'revision': 1, 'metadata': {**META, 'printedName': 'Fictional Applicant'}, 'status': 'reviewed'})
    assert result.status_code == 200
    assert result.json()['revision'] == 2
    assert client.patch(PATH, json={'revision': 1, 'metadata': META, 'status': 'reviewed'}).status_code == 409
    assert client.delete(PATH + '?revision=1').status_code == 409
    assert client.delete(PATH + '?revision=2').status_code == 204
    assert client.get(PATH + '/content').status_code == 404
    assert client.get('/api/workspace/documents').json() == []
    assert client.app.state.test_files.objects == {}


def test_failed_delete_can_be_retried_without_concurrent_overwrite(client):
    upload(client)
    files = client.app.state.test_files
    files.fail_delete = True
    assert client.delete(PATH + '?revision=1').status_code == 503
    assert client.get('/api/workspace/documents').json()[0]['deleting'] is True
    assert client.patch(PATH, json={'revision': 1, 'metadata': META, 'status': 'reviewed'}).status_code == 409
    files.fail_delete = False
    assert client.delete(PATH + '?revision=1').status_code == 204
    assert files.objects == {}


def test_household_cloud_restore_conflict_and_account_isolation(client):
    path = '/api/workspace/household'
    applicant = {'id': 'applicant', 'label': 'Fictional applicant', 'relationship': 'self'}
    spouse = {'id': 'spouse-1', 'label': 'Fictional spouse', 'relationship': 'spouse'}
    assert client.get(path).json()['revision'] == 0
    payload = {'revision': 0, 'members': [applicant, spouse]}
    assert client.put(path, json=payload).status_code == 200
    assert len(client.get(path).json()['members']) == 2
    assert client.put(path, json=payload).status_code == 409
    assert client.get(path, headers={'Authorization': 'Bearer test-b'}).json()['members'] == []
    assert client.put(path, json={'revision': 1, 'members': [spouse]}).status_code == 422


def test_cloud_endpoints_require_sign_in(client):
    for path in ('/api/workspace/household', '/api/workspace/documents', PATH + '/content'):
        assert client.get(path, headers={'Authorization': ''}).status_code == 401
