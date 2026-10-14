"""M4–M9 fictional-document API integration tests. No real identity data or Gemini calls.

Place in apps/api/tests/ and run: uv run pytest tests/test_passport_integration.py -v
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient
from maadhyam_api.main import app

client = TestClient(app)
API = '/api/intelligence'


def fake_doc(id, kind, name='', dob='', address='', *, holder='self', reviewed=True, categories=None):
    return dict(id=id, documentType=kind, printedName=name, dateOfBirth=dob,
                residentialAddress=address, holder=holder, reviewed=reviewed,
                categories=categories or [])


@pytest.fixture
def fictional_passport_docs():
    return [
        fake_doc('demo-aadhaar', 'Aadhaar (fictional)', 'Rahul Kumar Sharma', '2000-05-12',
                 '10 Sample Road, Pune', categories=['identity', 'address']),
        fake_doc('demo-pan', 'PAN (fictional)', 'Rahul K Sharma', '2000-05-12',
                 categories=['identity']),
        fake_doc('demo-birth', 'Birth Certificate (fictional)', 'Rahul Kumar Sharma',
                 '2000-12-05', categories=['birth']),
    ]


def assess(docs, **kwargs):
    response = client.post(API + '/analyze', json={'documents': docs, **kwargs})
    assert response.status_code == 200, response.text
    return response.json()


def ids(result, key):
    return {item['id'] for item in result[key]}


def assert_dependency_graph_valid(result):
    tasks = {t['id']: t for t in result['tasks']}
    for t in tasks.values():
        assert all(dep in tasks for dep in t['dependsOn']), t
        assert t['id'] not in t['dependsOn'], t
    def visit(node, visiting, visited):
        assert node not in visiting, f'Dependency cycle at {node}'
        if node in visited:
            return
        visiting.add(node)
        for dep in tasks[node]['dependsOn']:
            visit(dep, visiting, visited)
        visiting.remove(node)
        visited.add(node)
    visited = set()
    for node in tasks:
        visit(node, set(), visited)


def test_e2e_01_fictional_three_documents_detect_two_conflicts(fictional_passport_docs):
    result = assess(fictional_passport_docs, assistanceType='fresh', applicantAgeGroup='adult')
    assert result['documentCount'] == 3
    assert result['reviewedSelfDocuments'] == 3
    assert {'printedName-conflict', 'dateOfBirth-conflict'} <= ids(result, 'findings')
    assert {'resolve-printedName', 'resolve-dateOfBirth'} <= ids(result, 'tasks')
    assert 'residentialAddress-conflict' not in ids(result, 'findings')
    assert result['readyForOfficialSubmission'] is False
    assert_dependency_graph_valid(result)


def test_e2e_02_review_gate_removes_unverified_conflict(fictional_passport_docs):
    fictional_passport_docs[1]['reviewed'] = False
    fictional_passport_docs[2]['reviewed'] = False
    result = assess(fictional_passport_docs)
    assert result['reviewedSelfDocuments'] == 1
    assert 'review-documents' in ids(result, 'tasks')
    assert 'printedName-conflict' not in ids(result, 'findings')
    assert 'dateOfBirth-conflict' not in ids(result, 'findings')


def test_e2e_03_reviewing_records_updates_analysis(fictional_passport_docs):
    for doc in fictional_passport_docs[1:]:
        doc['reviewed'] = False
    before = assess(fictional_passport_docs)
    for doc in fictional_passport_docs[1:]:
        doc['reviewed'] = True
    after = assess(fictional_passport_docs)
    assert 'printedName-conflict' not in ids(before, 'findings')
    assert 'printedName-conflict' in ids(after, 'findings')
    assert 'review-documents' not in ids(after, 'tasks')


def test_e2e_04_fixing_name_clears_only_name_conflict(fictional_passport_docs):
    fictional_passport_docs[1]['printedName'] = 'Rahul Kumar Sharma'
    result = assess(fictional_passport_docs)
    assert 'printedName-conflict' not in ids(result, 'findings')
    assert 'dateOfBirth-conflict' in ids(result, 'findings')
    assert 'resolve-printedName' not in ids(result, 'tasks')


def test_e2e_05_fixing_dob_clears_only_dob_conflict(fictional_passport_docs):
    fictional_passport_docs[2]['dateOfBirth'] = '2000-05-12'
    result = assess(fictional_passport_docs)
    assert 'dateOfBirth-conflict' not in ids(result, 'findings')
    assert 'printedName-conflict' in ids(result, 'findings')


def test_e2e_06_all_metadata_aligned_still_not_officially_approved(fictional_passport_docs):
    fictional_passport_docs[1]['printedName'] = 'Rahul Kumar Sharma'
    fictional_passport_docs[2]['dateOfBirth'] = '2000-05-12'
    result = assess(fictional_passport_docs)
    assert not [f for f in result['findings'] if f['type'] == 'conflict']
    assert result['readyForOfficialSubmission'] is False
    assert 'official-review' in ids(result, 'tasks')


def test_e2e_07_family_name_does_not_create_self_conflict(fictional_passport_docs):
    fictional_passport_docs[1]['printedName'] = 'Rahul Kumar Sharma'
    fictional_passport_docs.append(fake_doc('demo-mother', 'Parent ID (fictional)',
                                            'Anita Sharma', holder='parent-guardian',
                                            categories=['identity']))
    result = assess(fictional_passport_docs)
    assert 'printedName-conflict' not in ids(result, 'findings')
    assert 'family-proof' in ids(result, 'tasks')
    assert 'parent-guardian' in result['familyHolders']
    assert result['reviewedSelfDocuments'] == 3


def test_e2e_08_family_only_documents_not_applicant_proof():
    result = assess([fake_doc('demo-parent', 'Parent ID (fictional)', 'Anita Sharma',
                              holder='parent-guardian', categories=['identity','address','birth'])])
    assert result['reviewedSelfDocuments'] == 0
    assert 'verify-self' in ids(result, 'tasks')
    assert {'check-identity', 'check-address', 'check-birth'} <= ids(result, 'tasks')


@pytest.mark.parametrize('assistance,age,expected', [
    ('reissue', 'adult', 'review-reissue'),
    ('fresh', 'minor', 'review-minor'),
    ('correction', 'adult', 'official-review'),
])
def test_e2e_09_scenario_branching(fictional_passport_docs, assistance, age, expected):
    result = assess(fictional_passport_docs, assistanceType=assistance, applicantAgeGroup=age)
    assert expected in ids(result, 'tasks')
    assert_dependency_graph_valid(result)


def test_e2e_10_planner_official_review_precedes_visit(fictional_passport_docs):
    result = assess(fictional_passport_docs)
    tasks = {t['id']: t for t in result['tasks']}
    assert 'official-review' in tasks['prepare-visit']['dependsOn']
    assert 'resolve-printedName' in tasks['official-review']['dependsOn']
    assert 'resolve-dateOfBirth' in tasks['official-review']['dependsOn']


def test_e2e_11_what_if_is_conservative_not_submission_approval(fictional_passport_docs):
    result = assess(fictional_passport_docs)
    assert result['whatIf']['allConflictsResolved']['remainingReviewTasks'] >= 1
    assert result['readyForOfficialSubmission'] is False


def test_e2e_12_local_assistant_uses_current_conflict_assessment(fictional_passport_docs):
    response = client.post(API + '/chat', json={
        'documents': fictional_passport_docs, 'question': 'Explain the name mismatch and DOB discrepancy',
        'useGemini': False,
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['mode'] == 'local-explainable'
    assert {'printedName-conflict','dateOfBirth-conflict'} <= ids(payload['assessment'], 'findings')
    assert 'passportindia.gov.in' in payload['sourceUrl']


def test_e2e_13_local_assistant_document_counts_match_analysis(fictional_passport_docs):
    response = client.post(API + '/chat', json={
        'documents': fictional_passport_docs, 'question': 'How many documents are in my vault?',
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload['assessment']['documentCount'] == 3
    assert '3 documents' in payload['answer']


def test_e2e_14_gemini_consent_denied_even_with_documents(fictional_passport_docs):
    response = client.post(API + '/chat', json={
        'documents': fictional_passport_docs, 'question': 'Can I apply now?',
        'useGemini': True, 'fictionalDataConfirmed': False,
    })
    assert response.status_code == 403


def test_e2e_15_no_automatic_correction_or_submission(fictional_passport_docs):
    first = assess(fictional_passport_docs)
    second = assess(fictional_passport_docs)
    assert first == second
    assert all(t['status'] == 'pending' for t in first['tasks'])
    assert first['readyForOfficialSubmission'] is False


def test_e2e_16_no_official_deadline_fabrication(fictional_passport_docs):
    result = assess(fictional_passport_docs, targetDate='2026-10-16')
    assert 'No official processing deadline' in result['deadlineNote']


def test_e2e_17_duplicate_document_ids_are_rejected(fictional_passport_docs):
    """Regression: duplicate IDs must not silently overwrite evidence references."""
    duplicate = [fictional_passport_docs[0], dict(fictional_passport_docs[0])]
    response = client.post(API + '/analyze', json={'documents': duplicate})
    assert response.status_code == 422


def test_e2e_18_payload_rejects_nonfictional_holder_enum(fictional_passport_docs):
    fictional_passport_docs[0]['holder'] = 'government-verified'
    response = client.post(API + '/analyze', json={'documents': fictional_passport_docs})
    assert response.status_code == 422
