"""M4–M9 deep regression checks; fictional metadata only. Run: uv run pytest tests/test_intelligence_deep.py -q"""
import pytest
from starlette.testclient import TestClient
from maadhyam_api.main import app

client = TestClient(app)
ANALYZE = '/api/intelligence/analyze'
CHAT = '/api/intelligence/chat'


def doc(id, **kw):
    return {'id': str(id), **kw}


def analyze(documents, **kw):
    response = client.post(ANALYZE, json={'documents': documents, **kw})
    assert response.status_code == 200, response.text
    return response.json()


def task_ids(data):
    return {t['id'] for t in data['tasks']}


def finding_ids(data):
    return {f['id'] for f in data['findings']}


def test_empty_vault_requires_documents():
    result = analyze([])
    assert 'add-documents' in task_ids(result)
    assert 'verify-self' in task_ids(result)
    assert result['documentCount'] == 0
    assert result['readyForOfficialSubmission'] is False


def test_unreviewed_documents_not_trusted():
    result = analyze([doc(1, printedName='One', reviewed=False), doc(2, printedName='Two', reviewed=False)])
    assert 'review-documents' in task_ids(result)
    assert result['reviewedSelfDocuments'] == 0
    assert 'printedName-conflict' not in finding_ids(result)


def test_reviewed_self_document_count():
    result = analyze([doc(1, reviewed=True), doc(2, reviewed=True, holder='spouse'), doc(3, reviewed=False)])
    assert result['documentCount'] == 3
    assert result['reviewedSelfDocuments'] == 1


@pytest.mark.parametrize('field,value_a,value_b', [
    ('printedName', 'Rahul Sharma', 'Rahul Kumar Sharma'),
    ('dateOfBirth', '2000-05-12', '2000-12-05'),
    ('residentialAddress', '10 Main Road', '20 Main Road'),
])
def test_conflicts_are_detected(field, value_a, value_b):
    result = analyze([doc(1, reviewed=True, **{field: value_a}), doc(2, reviewed=True, **{field: value_b})])
    assert field + '-conflict' in finding_ids(result)
    assert 'resolve-' + field in task_ids(result)


@pytest.mark.parametrize('field,a,b', [
    ('printedName', 'Rahul  Sharma', 'rahul sharma'),
    ('printedName', 'Rahul K. Sharma', 'rahul k sharma'),
    ('residentialAddress', '10, Main Road', '10 Main Road'),
])
def test_cosmetic_normalization_does_not_trigger_conflict(field, a, b):
    result = analyze([doc(1, reviewed=True, **{field: a}), doc(2, reviewed=True, **{field: b})])
    assert field + '-conflict' not in finding_ids(result)


@pytest.mark.parametrize('holder', ['parent-guardian', 'spouse', 'other'])
def test_family_documents_do_not_contaminate_self_comparison(holder):
    result = analyze([doc(1, reviewed=True, printedName='Rahul', holder='self'), doc(2, reviewed=True, printedName='Different', holder=holder)])
    assert 'printedName-conflict' not in finding_ids(result)
    assert holder in result['familyHolders']
    assert 'family-proof' in task_ids(result)


def test_family_only_does_not_verify_applicant():
    result = analyze([doc(1, reviewed=True, holder='parent-guardian', categories=['identity'])])
    assert 'verify-self' in task_ids(result)
    assert 'check-identity' in task_ids(result)


@pytest.mark.parametrize('category', ['identity', 'address', 'birth'])
def test_missing_categories_get_check_tasks(category):
    result = analyze([doc(1, reviewed=True)])
    assert 'check-' + category in task_ids(result)


def test_reviewed_category_satisfies_organizational_check_only():
    result = analyze([doc(1, reviewed=True, categories=['identity', 'address', 'birth'])])
    assert not any(x.startswith('check-') for x in task_ids(result))
    assert result['readyForOfficialSubmission'] is False


def test_reissue_requires_specific_review():
    assert 'review-reissue' in task_ids(analyze([], assistanceType='reissue'))


def test_minor_requires_guardian_review():
    assert 'review-minor' in task_ids(analyze([], applicantAgeGroup='minor'))


def test_tasks_have_valid_dependency_references():
    result = analyze([doc(1, reviewed=False), doc(2, reviewed=True, printedName='A'), doc(3, reviewed=True, printedName='B')], applicantAgeGroup='minor')
    ids = task_ids(result)
    for task in result['tasks']:
        assert set(task['dependsOn']).issubset(ids), task
        assert task['id'] not in task['dependsOn']


def test_visit_depends_on_official_review():
    result = analyze([])
    visit = next(t for t in result['tasks'] if t['id'] == 'prepare-visit')
    assert 'official-review' in visit['dependsOn']


def test_conflict_never_asserts_invalid_document():
    result = analyze([doc(1, reviewed=True, printedName='A'), doc(2, reviewed=True, printedName='B')])
    finding = next(f for f in result['findings'] if f['id'] == 'printedName-conflict')
    assert 'does not prove' in finding['disclaimer']


def test_no_automatic_submission_readiness():
    result = analyze([doc(1, reviewed=True, categories=['identity', 'address', 'birth'], printedName='Rahul', dateOfBirth='2000-05-12', residentialAddress='Main Road')])
    assert result['readyForOfficialSubmission'] is False
    assert 'passportindia.gov.in' in result['sourceUrl']


def test_no_fabricated_deadline():
    assert 'No official processing deadline' in analyze([], targetDate='2026-10-16')['deadlineNote']


def test_local_chat_works_without_gemini():
    response = client.post(CHAT, json={'question': 'Show my documents', 'useGemini': False, 'documents': [doc(1, reviewed=True)]})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'local-explainable'
    assert '1 documents' in data['answer']


def test_local_chat_family_context():
    response = client.post(CHAT, json={'question': 'Can I use family documents?', 'documents': [doc(1, holder='spouse')]})
    assert response.status_code == 200
    assert 'spouse' in response.json()['answer']


def test_gemini_requires_explicit_fictional_data_consent():
    response = client.post(CHAT, json={'question': 'Help me', 'useGemini': True, 'fictionalDataConfirmed': False})
    assert response.status_code == 403


@pytest.mark.parametrize('invalid_payload', [
    {'documents': [doc('')]},
    {'documents': [doc(1, holder='unknown')]},
    {'documents': [doc(1, categories=['passport-approved'])]},
    {'documents': [doc(1, printedName='x' * 201)]},
    {'documents': [], 'assistanceType': 'invalid'},
    {'documents': [], 'applicantAgeGroup': 'elderly'},
    {'documents': [doc(i) for i in range(61)]},
])
def test_invalid_inputs_rejected(invalid_payload):
    response = client.post(ANALYZE, json=invalid_payload)
    assert response.status_code == 422


def test_empty_chat_question_rejected():
    assert client.post(CHAT, json={'question': ''}).status_code == 422


def test_oversized_chat_question_rejected():
    assert client.post(CHAT, json={'question': 'x' * 1501}).status_code == 422
