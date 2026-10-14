from starlette.testclient import TestClient
from maadhyam_api.main import app

client=TestClient(app)

def test_empty():
    r=client.post('/api/intelligence/analyze',json={'documents':[]})
    assert r.status_code==200
    assert r.json()['readyForOfficialSubmission'] is False

def test_conflicts_self_only():
    data={'documents':[{'id':'1','reviewed':True,'printedName':'A B','holder':'self'},
                       {'id':'2','reviewed':True,'printedName':'A C','holder':'self'},
                       {'id':'3','reviewed':True,'printedName':'Different','holder':'spouse'}]}
    r=client.post('/api/intelligence/analyze',json=data)
    assert r.status_code==200
    assert len([f for f in r.json()['findings'] if f['type']=='conflict'])==1

def test_unreviewed_excluded():
    r=client.post('/api/intelligence/analyze',json={'documents':[{'id':'1','reviewed':True,'printedName':'A'},{'id':'2','reviewed':False,'printedName':'B'}]})
    assert not [f for f in r.json()['findings'] if f['type']=='conflict']

def test_ai_requires_consent():
    r=client.post('/api/intelligence/chat',json={'question':'Help','useGemini':True})
    assert r.status_code==403

def test_local_chat():
    r=client.post('/api/intelligence/chat',json={'question':'What next?'})
    assert r.status_code==200 and r.json()['mode']=='local-explainable'
