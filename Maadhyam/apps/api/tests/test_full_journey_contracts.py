"""Maadhyam M4-M9 deterministic contract, security and regression tests.

Run from apps/api: uv run pytest tests/test_full_journey_contracts.py -v
These tests use FastAPI TestClient (no Gemini network); mocked-provider tests are labeled.
"""
from __future__ import annotations

import copy
import json
import sys
import types
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import app

API = '/api/intelligence'
client = TestClient(app)


def document(id='aadhaar', *, name='Rahul Kumar Sharma', dob='2000-05-12',
             holder='self', reviewed=True, categories=None, address='Demo Road'):
    return {'id': id, 'documentType': 'Fictional sample', 'printedName': name,
            'dateOfBirth': dob, 'residentialAddress': address,
            'holder': holder, 'reviewed': reviewed,
            'categories': categories if categories is not None else ['identity']}


def post(path, docs=None, **kwargs):
    return client.post(API + path, json={'documents': docs if docs is not None else [], **kwargs})


@pytest.mark.parametrize('scenario', ['fresh', 'reissue', 'correction', 'documents', 'police'])
def test_m5_each_scenario_is_conservative(scenario):
    r = post('/passport-plan', [document()], assistanceType=scenario, applicantAgeGroup='adult')
    assert r.status_code == 200, r.text
    p = r.json()['passportPlan']
    assert p['scenario'] == scenario
    assert p['checklist']
    assert p['officialEligibilityDetermined'] is False
    assert p['officialAcceptanceDetermined'] is False
    assert all(item['officialAcceptanceVerified'] is False for item in p['checklist'])


@pytest.mark.parametrize('scenario', ['fresh', 'reissue', 'correction', 'documents', 'police'])
def test_m5_no_document_cannot_be_assumed_ready(scenario):
    r = post('/passport-plan', [], assistanceType=scenario)
    assert r.status_code == 200
    p = r.json()['passportPlan']
    assert 'No reviewed applicant-held evidence' in p['preparationBlockers']
    assert not any(x['candidateDocumentIds'] for x in p['checklist'])


@pytest.mark.parametrize('holder', ['parent-guardian', 'spouse', 'other'])
def test_m8_family_holder_never_counts_as_self(holder):
    r = post('/passport-plan', [document(holder=holder)])
    assert r.status_code == 200
    data = r.json()
    assert data['assessment']['reviewedSelfDocuments'] == 0
    assert 'No reviewed applicant-held evidence' in data['passportPlan']['preparationBlockers']
    assert not any(x['candidateDocumentIds'] for x in data['passportPlan']['checklist'])


@pytest.mark.parametrize('reviewed', [False, True])
def test_m4_review_gate_for_candidate_evidence(reviewed):
    d = document(reviewed=reviewed, categories=['identity', 'birth', 'address'])
    r = post('/passport-plan', [d], applicantAgeGroup='adult')
    assert r.status_code == 200
    items = r.json()['passportPlan']['checklist']
    assert all(('aadhaar' in x['candidateDocumentIds']) == reviewed for x in items if x['id'] in {'identity-details','birth-details','present-address'})


@pytest.mark.parametrize('dob', ['2000-05-12', '12/05/2000'])
def test_m4_equivalent_dob_formats_no_conflict(dob):
    docs = [document('a', dob='2000-05-12'), document('b', dob=dob)]
    r = post('/analyze', docs)
    assert r.status_code == 200
    assert not any(f['id'] == 'dateOfBirth-conflict' for f in r.json()['findings'])


@pytest.mark.parametrize('bad_dob', ['31/02/2000', '2000-13-01', '05-12-2000', '12/31/2000', '2000-02-30'])
def test_m4_invalid_or_ambiguous_dob_flagged(bad_dob):
    r = post('/analyze', [document(dob=bad_dob)])
    assert r.status_code == 200
    assert any(f['id'] == 'dateOfBirth-invalid' for f in r.json()['findings'])


def test_m4_real_dob_conflict_and_name_conflict_both_detected():
    r = post('/analyze', [document('a'), document('b', name='Rahul K Sharma', dob='2000-05-13')])
    assert r.status_code == 200
    ids = {x['id'] for x in r.json()['findings']}
    assert {'printedName-conflict', 'dateOfBirth-conflict'} <= ids


def test_m4_unreviewed_conflict_does_not_count_as_verified_comparison():
    r = post('/analyze', [document('a'), document('b', name='Rahul K Sharma', reviewed=False)])
    assert r.status_code == 200
    assert 'printedName-conflict' not in {x['id'] for x in r.json()['findings']}


@pytest.mark.parametrize('ids', [('A','a'), (' A ','a'), ('X','x')])
def test_m4_duplicate_document_ids_rejected(ids):
    r = post('/analyze', [document(ids[0]), document(ids[1])])
    assert r.status_code == 422


@pytest.mark.parametrize('invalid_id', ['', '   '])
def test_m4_blank_document_id_rejected(invalid_id):
    assert post('/analyze', [document(invalid_id)]).status_code == 422


@pytest.mark.parametrize('confidence,should_flag', [(0.2,True), (0.84,True), (0.85,False), (1.0,False)])
def test_m4_extraction_confidence_review_threshold(confidence, should_flag):
    d = document()
    d.update(extractionSource='gemini', extractionConfidence=confidence)
    r = post('/analyze', [d])
    assert r.status_code == 200
    assert ('extraction-low-confidence' in {x['id'] for x in r.json()['findings']}) is should_flag


def test_m4_manual_metadata_not_falsely_flagged_low_confidence():
    d = document()
    d.update(extractionSource='manual', extractionConfidence=None)
    assert 'extraction-low-confidence' not in {x['id'] for x in post('/analyze',[d]).json()['findings']}


def test_m6_alternatives_do_not_choose_a_legally_correct_document():
    docs = [document('a'), document('b', name='Rahul K Sharma')]
    r = post('/passport-plan', docs)
    assert r.status_code == 200
    options = r.json()['passportPlan']['resolutionOptions']
    name = next(x for x in options if x['field']=='printedName')
    assert name['chosenCorrection'] is None
    assert len(name['alternatives']) >= 2
    assert all(a['automaticallyApproved'] is False for a in name['alternatives'])


def test_m6_dependency_order_is_topological_and_unique():
    docs = [document('a'), document('b', name='Rahul K Sharma')]
    r = post('/analyze', docs)
    assert r.status_code == 200
    data = r.json()
    order = data['executionOrder']
    assert len(order) == len(set(order)) == len(data['tasks'])
    for task in data['tasks']:
        for dep in task['dependsOn']:
            assert order.index(dep) < order.index(task['id'])


def test_m5_minor_requires_guardian_check_without_approval():
    r = post('/passport-plan', [document()], applicantAgeGroup='minor')
    assert r.status_code == 200
    assert 'minor-guardian' in {x['id'] for x in r.json()['passportPlan']['checklist']}
    assert r.json()['passportPlan']['officialEligibilityDetermined'] is False


def test_m7_what_if_resolves_conflict_but_not_official_acceptance():
    docs = [document('a'), document('b', name='Rahul K Sharma')]
    simulation = {'id':'sim-1','label':'Correct fictional PAN name',
                  'replaceFields': {'b': {'printedName':'Rahul Kumar Sharma'}}}
    r = post('/reasoning', docs, simulations=[simulation])
    assert r.status_code == 200, r.text
    data = r.json()
    assert 'printedName-conflict' in data['baseline']['reviewFindings']
    assert 'printedName-conflict' in data['simulations'][0]['resolvedFindingIds']
    assert data['simulations'][0]['officialAcceptanceVerified'] is False
    assert data['officialEligibilityDetermined'] is False


@pytest.mark.parametrize('bad_sim', [
    {'id':'x','label':'invalid','removeDocumentIds':['unknown']},
    {'id':'x','label':'invalid','markReviewedIds':['unknown']},
    {'id':'x','label':'invalid','replaceFields':{'unknown':{'printedName':'X'}}},
    {'id':'x','label':'invalid','removeDocumentIds':['a'], 'replaceFields':{'a':{'printedName':'X'}}},
])
def test_m7_invalid_what_if_references_rejected(bad_sim):
    assert post('/reasoning', [document('a')], simulations=[bad_sim]).status_code == 422


def test_m7_simulation_does_not_mutate_baseline():
    docs = [document('a'), document('b', name='Rahul K Sharma')]
    saved = copy.deepcopy(docs)
    sim = {'id':'x','label':'hypothesis','replaceFields':{'b':{'printedName':'Rahul Kumar Sharma'}}}
    r = post('/reasoning', docs, simulations=[sim])
    assert r.status_code == 200
    assert docs == saved
    assert 'printedName-conflict' in r.json()['baseline']['reviewFindings']


def test_m8_family_link_is_claim_only():
    docs = [document('self'), document('guardian',holder='parent-guardian')]
    r = post('/reasoning', docs, familyLinks=[{'documentId':'guardian','relation':'parent',
        'claimedByApplicant':True,'relationshipEvidenceDocumentIds':['self']}])
    assert r.status_code == 200, r.text
    evidence = r.json()['familyEvidence']
    assert evidence['officialRelationshipVerified'] is False
    assert evidence['links'][0]['officialRelationshipVerified'] is False
    assert evidence['links'][0]['requiresVerification'] is True


@pytest.mark.parametrize('link', [
    {'documentId':'absent','relation':'parent'},
    {'documentId':'guardian','relation':'parent','relationshipEvidenceDocumentIds':['absent']},
])
def test_m8_invalid_family_references_rejected(link):
    assert post('/reasoning', [document('guardian',holder='parent-guardian')], familyLinks=[link]).status_code == 422


def test_m8_unlinked_family_document_reported():
    r = post('/reasoning', [document('a'), document('f',holder='spouse')])
    assert r.status_code == 200
    assert 'f' in r.json()['familyEvidence']['unlinkedFamilyDocumentIds']


def test_m9_local_chat_reports_total_and_reviewed_counts():
    docs = [document('a'), document('b', reviewed=False), document('f',holder='spouse')]
    r = post('/chat', docs, question='How many documents in vault?')
    assert r.status_code == 200
    data = r.json()
    assert data['mode'] == 'local-explainable'
    assert '3 documents' in data['answer']
    assert '1 reviewed applicant' in data['answer']
    assert data['grounding']['reviewedApplicantDocumentIds'] == ['a']


def test_m9_local_chat_family_holder_named_without_verification():
    r = post('/chat', [document('f',holder='spouse')], question='Can I use family documents?')
    assert r.status_code == 200
    assert 'spouse' in r.json()['answer']
    assert 'cannot be officially verified' in r.json()['answer']


@pytest.mark.parametrize('question', ['Is my passport approved?', 'Am I eligible?', 'Can I apply?'])
def test_m9_local_chat_never_confirms_official_eligibility(question):
    r = post('/chat', [document()], question=question)
    assert r.status_code == 200
    assert r.json()['grounding']['officiallyVerified'] is False
    assert 'not a decision on passport eligibility' in r.json()['answer']


def test_m9_gemini_without_fictional_consent_denied():
    r = post('/chat', [document()], question='Help me', useGemini=True, fictionalDataConfirmed=False)
    assert r.status_code == 403


def test_m9_gemini_empty_key_returns_controlled_error(monkeypatch):
    from maadhyam_api import config
    settings = config.get_settings()
    monkeypatch.setattr(settings, 'gemini_api_key', '', raising=False)
    r = post('/chat', [document()], question='Help me', useGemini=True, fictionalDataConfirmed=True)
    assert r.status_code == 503


def test_m9_gemini_mocked_provider_receives_only_reviewed_self_metadata(monkeypatch):
    """MOCKED Gemini transport, not a live Gemini test."""
    from maadhyam_api import config
    monkeypatch.setattr(config.get_settings(), 'gemini_api_key', 'fake-test-key', raising=False)
    calls = []
    fake_client = MagicMock()
    def generate_content(**kwargs):
        calls.append(kwargs)
        return types.SimpleNamespace(text='Please verify current requirements on Passport Seva.')
    fake_client.models.generate_content.side_effect = generate_content
    fake_genai = types.ModuleType('google.genai')
    fake_genai.Client = lambda **kwargs: fake_client
    # The installed google namespace package can be imported without network.
    import google
    monkeypatch.setattr(google, 'genai', fake_genai, raising=False)
    r = post('/chat', [document('a'), document('b',name='SECRET_UNREVIEWED',reviewed=False),
                       document('f',name='SECRET_FAMILY',holder='spouse')],
             question='Help with passport', useGemini=True, fictionalDataConfirmed=True)
    assert r.status_code == 200, r.text
    assert r.json()['mode'] == 'gemini-demo'
    assert len(calls) == 1
    prompt = calls[0]['contents']
    assert 'SECRET_UNREVIEWED' not in prompt
    assert 'SECRET_FAMILY' not in prompt
    assert 'Rahul Kumar Sharma' in prompt
    assert r.json()['grounding']['reviewedApplicantDocumentIds'] == ['a']
    fake_client.close.assert_called_once()


@pytest.mark.parametrize('unsafe', ['You are definitely eligible.', 'Guaranteed approval!', 'Government approved.'])
def test_m9_mocked_gemini_unsafe_claim_triggers_fallback(monkeypatch, unsafe):
    """MOCKED Gemini safety filter regression; NOT exhaustive hallucination protection."""
    from maadhyam_api import config
    monkeypatch.setattr(config.get_settings(), 'gemini_api_key', 'fake-test-key', raising=False)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = types.SimpleNamespace(text=unsafe)
    import google
    monkeypatch.setattr(google, 'genai', types.SimpleNamespace(Client=lambda **kwargs: fake_client), raising=False)
    r = post('/chat', [document()], question='Help with passport', useGemini=True, fictionalDataConfirmed=True)
    assert r.status_code == 200, r.text
    assert r.json()['mode'] == 'local-safety-fallback'
    assert unsafe not in r.json()['answer']


def test_m9_mocked_gemini_failure_is_controlled(monkeypatch):
    from maadhyam_api import config
    monkeypatch.setattr(config.get_settings(), 'gemini_api_key', 'fake-test-key', raising=False)
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = RuntimeError('SENSITIVE_PROVIDER_INTERNAL_ERROR')
    import google
    monkeypatch.setattr(google, 'genai', types.SimpleNamespace(Client=lambda **kwargs: fake_client), raising=False)
    r = post('/chat', [document()], question='Help', useGemini=True, fictionalDataConfirmed=True)
    assert r.status_code == 503
    assert 'SENSITIVE_PROVIDER_INTERNAL_ERROR' not in r.text


@pytest.mark.parametrize('invalid', [
    {'question':'', 'documents':[]},
    {'question':'x'*1501, 'documents':[]},
    {'question':'Help','documents':[document()]*61},
    {'question':'Help','documents':[dict(document(), holder='not-a-holder')]},
])
def test_m9_invalid_requests_rejected(invalid):
    assert client.post(API+'/chat',json=invalid).status_code == 422
