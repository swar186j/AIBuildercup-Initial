import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore
from m10_support import test_app as make_app


@pytest.fixture
def client(monkeypatch):
    # The adapter executes transactions synchronously; revision checks are real.
    monkeypatch.setattr(firestore, 'transactional', lambda fn: fn)
    app, _ = make_app()
    with TestClient(app, headers={'Authorization': 'Bearer test-a'}) as client:
        yield client


def create(client):
    response = client.post('/api/applications', json={'client_id': 'LOCAL-test-draft-123'})
    assert response.status_code == 201
    return response.json()


def test_create_retry_save_reload_and_delete(client):
    item = create(client)
    assert create(client)['id'] == item['id']
    assert len(client.get('/api/applications').json()) == 1
    path = '/api/applications/' + item['id']
    result = client.patch(path, json={'revision': 1, 'current_step': 2, 'status': 'in-progress'})
    assert result.status_code == 200
    assert result.json()['revision'] == 2
    assert result.json()['progress_history'][-1]['current_step'] == 2
    replay = client.post('/api/applications', json={'client_id': item['id'], 'current_step': 0})
    assert replay.json()['revision'] == 2
    assert replay.json()['current_step'] == 2
    assert client.get(path).json()['current_step'] == 2
    assert client.patch(path, json={'revision': 1, 'current_step': 0}).status_code == 409
    assert client.delete(path + '?revision=1').status_code == 409
    assert client.delete(path + '?revision=2').status_code == 204
    assert client.get(path).status_code == 404


def test_accounts_cannot_read_update_or_delete_each_other(client):
    item = create(client)
    path = '/api/applications/' + item['id']
    other = {'Authorization': 'Bearer test-b'}
    assert client.get('/api/applications', headers=other).json() == []
    assert client.get(path, headers=other).status_code == 404
    assert client.patch(path, headers=other, json={'revision': 1, 'status': 'completed'}).status_code == 404
    assert client.delete(path + '?revision=1', headers=other).status_code == 404
    assert client.get(path).json()['revision'] == 1


def test_new_planner_dependencies_conflicts_cascade_and_reset(client):
    path = '/api/applications/workspace/planner'
    assert client.get(path).json() == {'completed': [], 'revision': 0}
    def update(revision, task, completed=True):
        return client.put(path, json={'revision': revision, 'task_id': task, 'completed': completed})
    assert update(0, 'vault').status_code == 409
    for revision, task in enumerate(['journey', 'vault', 'details', 'differences', 'next']):
        assert update(revision, task).status_code == 200
    assert update(0, 'journey').status_code == 409
    assert update(5, 'vault', False).json()['completed'] == ['journey']
    assert client.get(path, headers={'Authorization': 'Bearer test-b'}).json()['completed'] == []
    assert client.delete(path + '?revision=5').status_code == 409
    assert client.delete(path + '?revision=6').json()['completed'] == []
    assert client.get(path).json()['revision'] == 7


def test_confirmed_migration_is_idempotent_and_account_scoped(client):
    payload = {'records': [{'client_id': 'LOCAL-old-draft-123'}], 'migration_id': 'migration-123', 'confirmed': False}
    assert client.post('/api/applications/migrate', json=payload).status_code == 400
    payload['confirmed'] = True
    first = client.post('/api/applications/migrate', json=payload).json()
    second = client.post('/api/applications/migrate', json=payload).json()
    assert first == second
    assert first['local_data_deleted'] is False
    assert len(client.get('/api/applications').json()) == 1
    other = client.post('/api/applications/migrate', headers={'Authorization': 'Bearer test-b'}, json=payload).json()
    assert other['application_ids'] != first['application_ids']


def test_planner_section_and_assessment_history(client):
    item = create(client)
    path = '/api/applications/' + item['id']
    assert client.patch(path + '/planner', json={'revision': 1, 'task_id': 'vault', 'completed': True}).status_code == 409
    assert client.patch(path + '/planner', json={'revision': 1, 'task_id': 'journey', 'completed': True}).status_code == 200
    assert client.patch(path + '/household', json={'revision': 2, 'value': {'members': []}}).status_code == 200
    result = client.post(path + '/assessments', json={'revision': 3, 'value': {'summary': 'fictional test'}})
    assert result.status_code == 200
    assert result.json()['assessment_history'][0]['recorded_at']
    assert client.patch(path + '/owner', json={'revision': 4, 'value': {}}).status_code == 404


@pytest.mark.parametrize('payload', [{'owner_user_id': 'b'}, {'revision': 1, 'status': None}, {'revision': 1, 'current_step': -1}])
def test_invalid_patch_cannot_corrupt_record(client, payload):
    item = create(client)
    assert client.patch('/api/applications/' + item['id'], json=payload).status_code == 422


def test_missing_auth_rejected(client):
    assert client.get('/api/applications', headers={'Authorization': ''}).status_code == 401
