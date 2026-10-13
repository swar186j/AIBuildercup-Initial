from fastapi.testclient import TestClient
from maadhyam_api.main import create_app

def test_empty_requires_confirmation():
    with TestClient(create_app()) as client:
        response=client.post('/api/passport/assess',json={})
    assert response.status_code==200
    data=response.json()
    assert data['official_requirements_verified'] is False
    assert any(c['id']=='dob-cutoff' for c in data['checks'])

def test_document_type_not_category_only():
    with TestClient(create_app()) as client:
        response=client.post('/api/passport/assess',json={'hasAddressDocument':'yes','documents':[{'id':'x','categories':['address'],'reviewed':True,'documentType':'Unclassified'}]})
    assert response.status_code==200
    assert next(c for c in response.json()['checks'] if c['id']=='address')['status']=='needs-confirmation'

def test_minor_and_adverse():
    with TestClient(create_app()) as client:
        response=client.post('/api/passport/assess',json={'applicantAgeGroup':'minor','nameConsistent':'no','policeVerificationStatus':'adverse'})
    ids={c['id'] for c in response.json()['checks']}
    assert {'minor','name-change','police'} <= ids

def test_invalid_category_rejected():
    with TestClient(create_app()) as client:
        response=client.post('/api/passport/assess',json={'documents':[{'id':'x','categories':['fake-category']}]})
    assert response.status_code==422
