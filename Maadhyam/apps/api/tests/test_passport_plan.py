"""M5/M6 behavior tests. Put in apps/api/tests and run uv run pytest tests/test_passport_plan.py -q."""
import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import app

client = TestClient(app)
URL = '/api/intelligence/passport-plan'


def doc(id, **kw):
    return {'id': id, 'reviewed': True, 'holder': 'self', **kw}


def plan(documents=None, **kw):
    response = client.post(URL, json={'documents': documents or [], **kw})
    assert response.status_code == 200, response.text
    return response.json()['passportPlan']


@pytest.mark.parametrize('scenario,expected', [
    ('fresh', 'identity-details'), ('reissue', 'existing-passport'),
    ('correction', 'change-evidence'), ('documents', 'present-address'),
    ('police', 'verification-process'),
])
def test_scenario_specific_checklist(scenario, expected):
    data = plan(assistanceType=scenario)
    assert expected in {item['id'] for item in data['checklist']}
    assert data['scenario'] == scenario


def test_reviewed_self_category_is_only_candidate_not_accepted():
    data = plan([doc('aadhaar-demo', categories=['identity', 'address'])], applicantAgeGroup='adult')
    by_id = {i['id']:i for i in data['checklist']}
    assert by_id['identity-details']['candidateDocumentIds'] == ['aadhaar-demo']
    assert by_id['present-address']['candidateDocumentIds'] == ['aadhaar-demo']
    assert by_id['identity-details']['officialAcceptanceVerified'] is False
    assert by_id['birth-details']['candidateDocumentIds'] == []


def test_unreviewed_document_is_not_a_candidate():
    data = plan([{'id':'pending', 'reviewed':False, 'holder':'self', 'categories':['identity']}])
    assert data['checklist'][0]['candidateDocumentIds'] == []
    assert 'Unreviewed applicant documents' in data['preparationBlockers']


def test_family_held_document_is_not_applicant_evidence():
    data = plan([{'id':'parent', 'reviewed':True, 'holder':'parent-guardian', 'categories':['identity']}])
    assert data['checklist'][0]['candidateDocumentIds'] == []
    assert 'Family relationship and evidence acceptance not verified' in data['preparationBlockers']


def test_minor_has_extra_guardian_check():
    data = plan(applicantAgeGroup='minor')
    assert 'minor-guardian' in {i['id'] for i in data['checklist']}


def test_adult_does_not_get_minor_check():
    data = plan(applicantAgeGroup='adult')
    assert 'minor-guardian' not in {i['id'] for i in data['checklist']}


def test_conflict_yields_non_prescriptive_correction_options():
    data = plan([doc('a', printedName='Rahul Sharma'), doc('b', printedName='Rahul K Sharma')])
    options = next(x for x in data['resolutionOptions'] if x['field'] == 'printedName')
    assert len(options['alternatives']) == 3
    assert options['chosenCorrection'] is None
    assert all(not a['automaticallyApproved'] for a in options['alternatives'])
    assert 'Unresolved evidence discrepancies or extraction quality' in data['preparationBlockers']


def test_matching_dob_formats_do_not_create_correction_option():
    data = plan([doc('a', dateOfBirth='2000-05-12'), doc('b', dateOfBirth='12/05/2000')])
    assert not any(o['field']=='dateOfBirth' for o in data['resolutionOptions'])


def test_invalid_dob_is_a_blocker():
    data = plan([doc('a', dateOfBirth='31/02/2000')])
    assert 'Unresolved evidence discrepancies or extraction quality' in data['preparationBlockers']


def test_no_evidence_and_age_unknown_are_blockers():
    data = plan()
    assert 'No reviewed applicant-held evidence' in data['preparationBlockers']
    assert 'Applicant age group not specified' in data['preparationBlockers']


def test_ordered_tasks_are_exposed_and_preserved():
    payload = client.post(URL, json={'documents': [doc('a')], 'assistanceType':'fresh'}).json()
    assert payload['passportPlan']['orderedTaskIds'] == payload['assessment']['executionOrder']


def test_never_claims_official_acceptance_or_eligibility():
    data = plan([doc('a', categories=['identity','birth','address'])], applicantAgeGroup='adult')
    assert data['officialEligibilityDetermined'] is False
    assert data['officialAcceptanceDetermined'] is False
    assert all(item['officialAcceptanceVerified'] is False for item in data['checklist'])
    assert data['sourceUrl'].startswith('https://')


def test_duplicate_ids_still_rejected():
    response = client.post(URL, json={'documents':[doc('ABC'),doc(' abc ')]})
    assert response.status_code == 422


def test_existing_analyze_endpoint_still_available():
    response = client.post('/api/intelligence/analyze', json={'documents':[]})
    assert response.status_code == 200
    assert 'tasks' in response.json()
