"""M4-M9 contract regression; providers are deterministic stubs, never live calls."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import create_app
from maadhyam_api.routes import extraction
from maadhyam_api.config import get_settings

@pytest.fixture
def client():
    with TestClient(create_app()) as c:
        yield c

DOCS=[{'id':'a','holder':'self','reviewed':True,'documentType':'Aadhaar card','categories':['identity','address','birth'],'printedName':'Rahul Kumar Sharma','dateOfBirth':'1998-06-15','residentialAddress':'12 MG Road, Pune, Maharashtra'},
      {'id':'p','holder':'self','reviewed':True,'documentType':'PAN card','categories':['identity'],'printedName':'Rahul K Sharma','dateOfBirth':'1998-06-15'},
      {'id':'r','holder':'self','reviewed':True,'documentType':'Electricity bill','categories':['address'],'printedName':'Rahul Kumar Sharma','residentialAddress':'45 FC Road, Pune, Maharashtra'}]

@pytest.mark.parametrize('field',['minimumCorrectionPath','identityEvolution','proofSubstitution','deadlineRescue','deadlockAnalysis','visitPreparation'])
@pytest.mark.parametrize('edge',[False,True])
def test_reasoning_capability_contract(client,field,edge):
    payload={'documents':[] if edge else DOCS,'targetDate':'invalid' if edge else '2000-01-01'}
    r=client.post('/api/intelligence/reasoning',json=payload)
    assert r.status_code==200,r.text
    result=r.json();assert isinstance(result[field],dict) and result[field]
    assert result['officialEligibilityDetermined'] is False and result['disclaimer']
    if field=='identityEvolution': assert result[field]['variationDetected'] is (not edge) and not result[field]['legalNameChangeVerified']
    if field=='proofSubstitution': assert not result[field]['officialSubstitutionApproved']
    if field=='deadlineRescue': assert not result[field]['officialDeadlineVerified']
    if field=='visitPreparation': assert not result[field]['governmentVisitEliminated']
    order=result['dependencyGraph']['executionOrder']
    for e in result['dependencyGraph']['edges']: assert order.index(e['before'])<order.index(e['after'])

@pytest.mark.parametrize('payload,code',[
 ({'documents':DOCS,'simulations':[{'id':'s','label':'align','replaceFields':{'p':{'printedName':'Rahul Kumar Sharma'}}}]},200),
 ({'documents':DOCS,'simulations':[{'id':'s','label':'bad','replaceFields':{'unknown':{'printedName':'Test'}}}]},422),
 ({'documents':DOCS,'familyLinks':[{'documentId':'unknown','relation':'parent'}]},422),
 ({'documents':DOCS,'familyLinks':[{'documentId':'a','relation':'parent','relationshipEvidenceDocumentIds':['unknown']}]},422),
])
def test_simulation_family_invalid_references(client,payload,code):
    r=client.post('/api/intelligence/reasoning',json=payload);assert r.status_code==code,r.text
    if code==200:
        d=r.json(); assert 'printedName-conflict' in d['simulations'][0]['resolvedFindingIds'];assert not d['simulations'][0]['officialAcceptanceVerified']

@pytest.mark.parametrize('with_evidence',[False,True])
def test_household_evidence(client,with_evidence):
    docs=DOCS+[dict(DOCS[0],id='parent',holder='parent-guardian'),dict(DOCS[0],id='spouse',holder='spouse')]
    links=[{'documentId':i,'relation':r,'claimedByApplicant':True,'relationshipEvidenceDocumentIds':['a'] if with_evidence else []} for i,r in [('parent','parent'),('spouse','spouse')]]
    result=client.post('/api/intelligence/reasoning',json={'documents':docs,'familyLinks':links}).json()
    assert result['baseline']['assessment']['reviewedSelfDocuments']==3
    assert len(result['familyEvidence']['links'])==2 and not result['familyEvidence']['officialRelationshipVerified']
    assert all(x['requiresVerification'] for x in result['familyEvidence']['links'])

@pytest.mark.parametrize('target,expiry,expected',[('2000-01-02','2000-01-01','already-expired'),('2099-02-02','2099-02-01','expires-before-target'),('2099-02-01','2099-02-01','expires-on-target'),('invalid','invalid','invalid-expiry-date')])
def test_deadline_expiry_http(client,target,expiry,expected):
    r=client.post('/api/intelligence/reasoning',json={'documents':[dict(DOCS[0],expiryDate=expiry)],'targetDate':target})
    assert r.status_code==200
    data=r.json()['deadlineRescue'];assert data['documentExpiryConflicts'][0]['type']==expected
    assert data['officialDocumentValidityVerified'] is False

@pytest.mark.parametrize('proposed,code',[({'version':'qa-v2','rules':[]},200),({'version':'','rules':[]},422),({'version':'qa-v2','rules':[{'id':'x','types':[]},{'id':'x','types':[]}]},422)])
def test_rule_impact_http(client,proposed,code):
    r=client.post('/api/passport/rules/compare',json={'proposedPack':proposed,'documents':DOCS});assert r.status_code==code,r.text
    if code==200: assert r.json()['officialChangeVerified'] is False and not r.json()['currentRulePackModified'] and r.json()['changes']

@pytest.mark.parametrize('edge',[False,True])
def test_advanced_optimizer_http(client,edge):
    option={'id':'o','label':'Fictional correction','costINR':0,'durationDays':2,'visits':1,'authority':'Fictional authority','prerequisites':['b'] if edge else []}
    other={**option,'id':'p','prerequisites':['a']}
    r=client.post('/api/intelligence/advanced-plan',json={'issues':[{'id':'a','options':[option]},{'id':'b','options':[other]}]})
    assert r.status_code==200,r.text
    d=r.json();assert d['status']==('deadlock' if edge else 'planned') and not d['officialAcceptanceVerified']

@pytest.mark.parametrize('name,mime,content,code',[('bad.exe','application/octet-stream',b'x',415),('empty.png','image/png',b'',400),('bad.png','image/png',b'wrong',415),('big.pdf','application/pdf',b'%PDF-'+b'0'*(10*1024*1024),413)],ids=['unsupported','empty','signature-mismatch','oversized'])
def test_extraction_invalid(client,monkeypatch,name,mime,content,code):
    monkeypatch.setattr(extraction,'get_settings',lambda:SimpleNamespace(gemini_api_key='fake',gemini_model='stub'))
    monkeypatch.setattr(extraction,'extract_with_gemini',lambda *a:pytest.fail('Invalid file reached provider'))
    r=client.post('/api/ai/extract-document',files={'file':(name,content,mime)},data={'fictional_document_confirmed':'true'})
    assert r.status_code==code,r.text

@pytest.mark.parametrize('failure',[TimeoutError('SECRET_PROVIDER_DETAILS'),RuntimeError('SECRET_PROVIDER_DETAILS')])
def test_extraction_provider_failure(client,monkeypatch,failure):
    monkeypatch.setattr(extraction,'get_settings',lambda:SimpleNamespace(gemini_api_key='fake',gemini_model='stub'))
    def fail(*a): raise failure
    monkeypatch.setattr(extraction,'extract_with_gemini',fail)
    r=client.post('/api/ai/extract-document',files={'file':('test.pdf',b'%PDF-1.4 fictional','application/pdf')},data={'fictional_document_confirmed':'true'})
    assert r.status_code==(504 if isinstance(failure, TimeoutError) else 502) and 'SECRET_PROVIDER_DETAILS' not in r.text

@pytest.mark.parametrize('mode',['success','timeout','rate-limit','empty','unsafe'])
def test_assistant_provider_stub(client,monkeypatch,mode):
    from google import genai
    from google.genai import errors
    monkeypatch.setenv('MAADHYAM_GEMINI_API_KEY','fake-qa-key');get_settings.cache_clear()
    provider=MagicMock()
    if mode=='timeout': provider.models.generate_content.side_effect=TimeoutError('SECRET_PROVIDER_DETAILS')
    elif mode=='rate-limit': provider.models.generate_content.side_effect=errors.ClientError(429, {'error':{'message':'SECRET_PROVIDER_DETAILS','status':'RESOURCE_EXHAUSTED'}})
    else: provider.models.generate_content.return_value=SimpleNamespace(text={'success':'Review the original records and confirm with Passport Seva.','empty':'','unsafe':'You have guaranteed approval.'}[mode])
    monkeypatch.setattr(genai,'Client',lambda **kw:provider)
    try:
        r=client.post('/api/intelligence/chat',json={'documents':DOCS,'question':'What evidence is missing?','useGemini':True,'fictionalDataConfirmed':True})
        assert r.status_code=={'timeout':504,'rate-limit':429,'empty':503}.get(mode,200),r.text
        if mode=='rate-limit': assert r.headers['retry-after']=='60'
        assert 'SECRET_PROVIDER_DETAILS' not in r.text and 'fake-qa-key' not in r.text
        if r.status_code==200:
            assert not r.json()['grounding']['officiallyVerified']
            if mode=='unsafe': assert r.json()['mode']=='local-safety-fallback'
        provider.close.assert_called_once()
    finally:get_settings.cache_clear()

@pytest.mark.parametrize('question',['','   ','\t\n','x'*1501],ids=['empty','whitespace','newline','too-long'])
def test_assistant_invalid_question(client,question):
    r=client.post('/api/intelligence/chat',json={'question':question})
    assert r.status_code==422 and r.json()['error']['code']=='validation_error'
