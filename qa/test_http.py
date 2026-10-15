"""HTTP integration against dedicated uvicorn on localhost:8001; no provider calls."""
import os
import pytest
import httpx

@pytest.fixture
def client():
    with httpx.Client(base_url=os.environ.get('MAADHYAM_TEST_API','http://127.0.0.1:8002'),timeout=10) as c:yield c

@pytest.mark.parametrize('payload,code',[
 ({'proposedPack':{'version':'qa-test','rules':[]}},200),
 ({'proposedPack':{'version':'qa-test','rules':[{'id':'bad','types':'bad'}]}},422),
])
def test_rule_change_impact(client,payload,code):
    r=client.post('/api/passport/rules/compare',json=payload);assert r.status_code==code
    if code==200:assert r.json()['changesDetected'] and not r.json()['officialChangeVerified'] and not r.json()['currentRulePackModified']

@pytest.mark.parametrize('cycle',[False,True])
def test_optimizer(client,cycle):
    def option(i,prereq): return {'id':i,'label':'Fictional correction','authority':'Fictional authority','costINR':0,'durationDays':3,'visits':1,'prerequisites':prereq}
    r=client.post('/api/intelligence/advanced-plan',json={'issues':[{'id':'a','options':[option('first',['b'] if cycle else [])]},{'id':'b','options':[option('second',['a'])]}]})
    assert r.status_code==200
    d=r.json();assert d['status']==('deadlock' if cycle else 'planned') and not d['officialAcceptanceVerified']

@pytest.mark.parametrize('key',['authority-bottlenecks','deadline-rescue','visit-eliminator'])
def test_circular_workflow(client,key):
    r=client.post('/api/citizen-workflows/'+key,json={'steps':[{'id':'a','label':'Fictional A','authority':'A','dependsOn':['b']},{'id':'b','label':'Fictional B','authority':'B','dependsOn':['a']}]})
    assert r.status_code==200 and r.json()['cycleOrCycleBlockedStepIds']

@pytest.mark.parametrize('payload,code',[({'question':''},422),({'question':'Help','useGemini':True},403),({'question':'Help','useGemini':True,'fictionalDataConfirmed':True},503)])
def test_chat_validation(client,payload,code):
    r=client.post('/api/intelligence/chat',json=payload);assert r.status_code==code
    assert 'gemini_api_key' not in r.text

@pytest.mark.parametrize('expiry,expected',[('2000-01-01','already-expired'),('wrong','invalid-expiry-date')])
def test_expiry(client,expiry,expected):
    r=client.post('/api/intelligence/reasoning',json={'documents':[{'id':'fictional','reviewed':True,'expiryDate':expiry}]})
    assert r.status_code==200
    d=r.json()['deadlineRescue'];assert d['documentExpiryConflicts'][0]['type']==expected and not d['officialDocumentValidityVerified']


def test_completion_available_versions_and_baseline_validation(client):
    r=client.get('/api/passport/rules/versions');assert r.status_code==200
    data=r.json();assert data['versions'][0]['pack']['rules'] and not data['officialChangeVerified']
    r=client.post('/api/passport/rules/compare',json={'baselineVersion':'missing','proposedPack':data['versions'][0]['pack']})
    assert r.status_code==422

@pytest.mark.parametrize('invalid',['consent','owner','member-reference','evidence-reference'])
def test_completion_household_http_validation(client,invalid):
    payload={'members':[{'id':'applicant','label':'Fictional applicant','relationship':'self'}],'documents':[{'id':'fictional','memberId':'applicant','associationConfirmed':True,'reviewed':True}]}
    if invalid=='consent':payload['documents'][0]['associationConfirmed']=False
    if invalid=='owner':payload['documents'][0]['memberId']='missing'
    if invalid=='member-reference':payload['members'][0]['dependsOnMemberIds']=['missing']
    if invalid=='evidence-reference':payload['members'][0]['relationshipEvidenceDocumentIds']=['missing']
    r=client.post('/api/household/assess',json=payload);assert r.status_code==422


def test_completion_household_http_owner_isolation(client):
    r=client.post('/api/household/assess',json={'members':[{'id':'a','label':'Fictional applicant','relationship':'self'},{'id':'p','label':'Fictional parent','relationship':'parent'}],'documents':[{'id':'parent-proof','memberId':'p','associationConfirmed':True,'reviewed':True}]})
    assert r.status_code==200
    d=r.json();assert d['reviewedEvidenceByMember']=={'a':[],'p':['parent-proof']} and not d['crossAccountAuthorizationVerified']
