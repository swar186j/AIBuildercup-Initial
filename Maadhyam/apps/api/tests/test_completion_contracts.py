"""Acceptance for local household model, stored versions and optimizer extensions."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from maadhyam_api.main import create_app
from maadhyam_api.routes.advanced_planning import PlanningRequest

@pytest.fixture
def client():
    with TestClient(create_app()) as c:yield c


def model():
    return {'members':[{'id':'a','label':'Fictional applicant','relationship':'self'},{'id':'p','label':'Fictional parent','relationship':'parent','dependsOnMemberIds':['a']}],
            'documents':[{'id':'applicant-proof','memberId':'a','reviewed':True,'associationConfirmed':True},{'id':'parent-proof','memberId':'p','reviewed':True,'associationConfirmed':True}]}

@pytest.mark.parametrize('evidence',[False,True])
def test_household_owner_graph_and_evidence(client,evidence):
    data=model()
    if evidence:data['members'][1]['relationshipEvidenceDocumentIds']=['applicant-proof']
    r=client.post('/api/household/assess',json=data);assert r.status_code==200,r.text
    d=r.json();assert d['memberCount']==2 and d['documentCount']==2
    assert d['reviewedEvidenceByMember']=={'a':['applicant-proof'],'p':['parent-proof']}
    assert d['missingRelationshipEvidenceMemberIds']==([] if evidence else ['p'])
    assert not d['officialRelationshipVerified'] and not d['crossAccountAuthorizationVerified']
    order=d['dependencyGraph']['executionOrder']
    for e in d['dependencyGraph']['edges']:assert order.index(e['before'])<order.index(e['after'])


def test_household_cycle(client):
    data=model();data['members'][0]['dependsOnMemberIds']=['p']
    d=client.post('/api/household/assess',json=data).json()
    assert set(d['dependencyGraph']['cycleOrBlockedNodeIds'])=={'member:a','member:p'}
    assert set(d['dependencyGraph']['executionOrder'])=={'document:applicant-proof','document:parent-proof'}

@pytest.mark.parametrize('mutation',['unknown-owner','no-consent','unknown-member-dependency','unknown-document-dependency','unknown-evidence','duplicate-owner','duplicate-member','two-applicants','blank-label'])
def test_household_rejects_invalid_references_and_ownership(client,mutation):
    d=model()
    if mutation=='unknown-owner':d['documents'][0]['memberId']='unknown'
    if mutation=='no-consent':d['documents'][0]['associationConfirmed']=False
    if mutation=='unknown-member-dependency':d['members'][1]['dependsOnMemberIds']=['unknown']
    if mutation=='unknown-document-dependency':d['members'][1]['dependsOnDocumentIds']=['unknown']
    if mutation=='unknown-evidence':d['members'][1]['relationshipEvidenceDocumentIds']=['unknown']
    if mutation=='duplicate-owner':d['documents'].append(deepcopy(d['documents'][0]))
    if mutation=='duplicate-member':d['members'].append(deepcopy(d['members'][0]))
    if mutation=='two-applicants':d['members'][1]['relationship']='self'
    if mutation=='blank-label':d['members'][1]['label']='  '
    r=client.post('/api/household/assess',json=d);assert r.status_code==422,r.text

@pytest.mark.parametrize('data',[{'members':[],'documents':[]},{'members':[{'id':'p','label':'Fictional','relationship':'parent'}],'documents':[]}])
def test_household_incomplete(client,data):
    r=client.post('/api/household/assess',json=data);assert r.status_code==200
    assert r.json()['applicantLabelMissing'] and not r.json()['officialRelationshipVerified']


def test_available_versions_are_real_stored_packs(client):
    r=client.get('/api/passport/rules/versions');assert r.status_code==200
    d=r.json();assert len(d['versions'])==1 and d['versions'][0]['kind']=='stored-reference' and not d['officialChangeVerified']
    p=d['versions'][0]['pack'];assert p['version']==d['versions'][0]['version'] and p['sources'] and p['rules']
    response=client.post('/api/passport/rules/compare',json={'baselineVersion':p['version'],'proposedPack':p})
    assert response.status_code==200 and not response.json()['changesDetected']
    assert not response.json()['currentRulePackModified']


def test_invalid_baseline_version(client):
    r=client.post('/api/passport/rules/compare',json={'baselineVersion':'nonexistent-version','proposedPack':{'version':'hypothetical','rules':[]}})
    assert r.status_code==422 and 'baseline' in r.text


def options():
    return {'issues':[{'id':'name','options':[{'id':'slow','label':'Lower cost','authority':'Fictional','costINR':100,'durationDays':10,'visits':1},
            {'id':'fast','label':'Less time','authority':'Fictional','costINR':1000,'durationDays':2,'visits':2}]}]}

@pytest.mark.parametrize('weight,chosen',[('cost','slow'),('days','fast'),('visits','slow')])
def test_optimizer_tradeoffs_and_alternatives(client,weight,chosen):
    payload={**options(),'weights':{k:100 if k==weight else 0 for k in ['cost','days','visits']}}
    r=client.post('/api/intelligence/advanced-plan',json=payload);assert r.status_code==200
    d=r.json();assert d['selectedOptions'][0]['id']==chosen and len(d['alternatives'])==1 and d['candidatePathsEvaluated']==2
    assert d['alternatives'][0]['selectedOptions'][0]['id']!=chosen
    assert not d['officialAcceptanceVerified'] and not d['officialProcessingTimesVerified']

@pytest.mark.parametrize('weight',[-1,101,float('inf'),float('nan')])
def test_optimizer_invalid_weights(weight):
    with pytest.raises(ValidationError):PlanningRequest.model_validate({**options(),'weights':{'cost':weight}})


def test_optimizer_limits_candidate_explosion(client):
    option=options()['issues'][0]['options'][0]
    payload={'issues':[{'id':str(i),'options':[{**option,'id':str(j)} for j in range(8)]} for i in range(12)]}
    r=client.post('/api/intelligence/advanced-plan',json=payload)
    assert r.status_code==422 and 'candidate paths' in r.text

@pytest.mark.parametrize('endpoint',['/api/passport/assess','/api/intelligence/passport-plan','/api/intelligence/chat'])
@pytest.mark.parametrize('scenario',['wrong-applicant','missing-consent'])
def test_household_cannot_be_relabelled_as_applicant(client,endpoint,scenario):
    document={'id':'fictional-parent','householdMemberId':'parent-label','associationConsent':scenario!='missing-consent','holder':'self' if scenario=='wrong-applicant' else 'parent-guardian','reviewed':True}
    r=client.post(endpoint,json={'documents':[document],**({'question':'Help'} if endpoint.endswith('/chat') else {})})
    assert r.status_code==422,r.text
