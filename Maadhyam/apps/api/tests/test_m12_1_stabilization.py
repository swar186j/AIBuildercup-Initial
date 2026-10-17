"""M12.1 deterministic evidence semantics; no external providers."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import app
from maadhyam_api.routes.passport_rules import pack
client=TestClient(app)

@pytest.mark.parametrize('documents',[[],[{'id':'a','reviewed':False,'dateOfBirth':'2000-01-01'}],[{'id':'a','reviewed':True,'printedName':'Fictional A'}]])
def test_no_unrelated_family_blocker_and_actual_age(documents):
    response=client.post('/api/intelligence/passport-plan',json={'documents':documents,'applicantAgeGroup':'adult'})
    assert response.status_code==200
    blockers=response.json()['passportPlan']['preparationBlockers']
    assert 'Applicant age group not specified' not in blockers
    assert 'Family relationship and evidence acceptance not verified' not in blockers

@pytest.mark.parametrize('field',['printedName','dateOfBirth','residentialAddress'])
def test_missing_field_simulation_not_confirmed_discrepancy(field):
    docs=[{'id':'a','reviewed':True},{'id':'b','reviewed':True}];original=deepcopy(docs)
    response=client.post('/api/intelligence/reasoning',json={'documents':docs,'applicantAgeGroup':'adult','simulations':[{'id':'fill','label':'Fill missing field','replaceFields':{'a':{field:'2000-01-01' if field=='dateOfBirth' else 'Fictional value'}}}]})
    assert response.status_code==200
    result=response.json()['simulations'][0]
    assert result['newFindingIds']==[] and result['before']['reviewFindings']==result['after']['reviewFindings']==[]
    assert docs==original

def test_unreviewed_value_reported_as_awaiting_review():
    response=client.post('/api/intelligence/passport-plan',json={'documents':[{'id':'reviewed','reviewed':True},{'id':'pending','reviewed':False,'dateOfBirth':'2000-01-01'}]})
    finding=next(f for f in response.json()['assessment']['findings'] if f['field']=='dateOfBirth')
    assert 'awaiting review' in finding['message'] and 'pending' in finding['evidence'][0]['documentIds']

@pytest.mark.parametrize('holder,owner',[('parent-guardian','parent-one'),('other','sibling-one')])
def test_other_person_never_applicant_conflict(holder,owner):
    response=client.post('/api/intelligence/passport-plan',json={'documents':[{'id':'a','reviewed':True,'printedName':'Fictional Applicant'},{'id':'b','reviewed':True,'holder':holder,'householdMemberId':owner,'associationConsent':True,'printedName':'Different Fictional Person'}]})
    assert response.status_code==200
    assert not any(f['id']=='printedName-conflict' for f in response.json()['assessment']['findings'])

def test_simulated_rule_change_preserves_active_pack_and_citations():
    original=deepcopy(pack());proposed=deepcopy(original);proposed['version']='local-proposal-fictional';proposed['rules'][0]['types']=[]
    response=client.post('/api/passport/rules/compare',json={'baselineVersion':original['version'],'proposedPack':proposed})
    assert response.status_code==200 and response.json()['changesDetected']
    assert response.json()['currentRulePackModified'] is False
    assert any(c['sourceUrl'] for c in response.json()['changes'])
    assert pack()==original

def test_adversarial_self_dependency_still_backend_deadlock():
    response=client.post('/api/intelligence/advanced-plan',json={'issues':[{'id':'one','options':[{'id':'option','label':'Fictional route','authority':'Unverified','costINR':0,'durationDays':0,'visits':0,'prerequisites':['one']}]}]})
    assert response.status_code==200 and response.json()['status']=='deadlock'


def ready_payload(**patch):
    value={'assistanceType':'fresh','applicantName':'Fictional Applicant','applicantAgeGroup':'adult','applicantDateOfBirth':'2000-01-01','hasAddressDocument':'yes','hasDateOfBirthDocument':'yes','nonEcrEligible':'no','documents':[
        {'id':'address','documentType':'Aadhaar card','holder':'self','reviewed':True,'printedName':'Fictional Applicant','dateOfBirth':'2000-01-01','residentialAddress':'Fictional address'},
        {'id':'birth','documentType':'PAN card','holder':'self','reviewed':True,'printedName':'Fictional Applicant','dateOfBirth':'2000-01-01'},
    ]}
    value.update(patch);return value


def readiness(payload):
    result=client.post('/api/passport/assess',json=payload)
    assert result.status_code==200
    data=result.json();r=data['readiness']
    assert r['percentage']==int(100*r['completed_checks']/r['total_checks']+0.5)
    assert r['total_checks']==len(r['items']) and r['official_acceptance_verified'] is False
    assert data['official_requirements_verified'] is False
    return r


def test_readiness_dynamic_applicable_pack_formula():
    empty=readiness(ready_payload(documents=[]))
    complete=readiness(ready_payload())
    assert empty['percentage']<complete['percentage']==100
    assert {i['id'] for i in complete['items']}=={'applicant-name','applicant-age','address','dob-old'}
    new_rule=readiness(ready_payload(applicantDateOfBirth='2024-01-01',applicantAgeGroup='minor'))
    assert {'dob-new','minor'}<={i['id'] for i in new_rule['items']}
    assert new_rule['percentage']<100

@pytest.mark.parametrize('patch',[
    {'reviewed':False}, {'printedName':''}, {'residentialAddress':''},
    {'holder':'other','householdMemberId':'another','associationConsent':True},
    {'documentType':'MBA marksheet','categories':['education']},
])
def test_readiness_irrelevant_missing_unreviewed_not_complete(patch):
    payload=ready_payload();payload['documents'][0].update(patch)
    r=readiness(payload)
    assert next(i for i in r['items'] if i['id']=='address')['state']!='complete'
    assert r['percentage']<100


def test_readiness_same_selected_member_only_and_conflict():
    payload=ready_payload(applicantHouseholdMemberId='parent-one')
    for doc in payload['documents']:doc.update(holder='parent-guardian',householdMemberId='parent-one',associationConsent=True)
    payload['documents'].append({**payload['documents'][0],'id':'other','householdMemberId':'parent-two','printedName':'Other Fictional Person'})
    assert readiness(payload)['percentage']==100
    payload['documents'][-1]['householdMemberId']='parent-one'
    r=readiness(payload)
    assert next(i for i in r['items'] if i['id']=='address')['state']=='difference'
    assert r['percentage']<100


def test_family_address_candidate_never_complete_without_official_acceptance():
    payload=ready_payload();payload['documents'][0].update(holder='parent-guardian')
    r=readiness(payload)
    assert next(i for i in r['items'] if i['id']=='address')['state']=='official-check'


def test_legacy_document_metadata_provenance_defaults_and_new_value():
    from maadhyam_api.routes.documents import Metadata
    assert Metadata.model_validate({'category':'identity'}).extractionSource=='manual'
    assert Metadata.model_validate({'category':'identity','extractionSource':'gemini'}).extractionSource=='gemini'
