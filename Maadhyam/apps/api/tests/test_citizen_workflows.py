from fastapi.testclient import TestClient
from maadhyam_api.main import app

client = TestClient(app)
BASE = '/api/citizen-workflows'

def post(name, data, code=200):
    response = client.post(BASE + '/' + name, json=data)
    assert response.status_code == code, response.text
    return response.json()

def steps():
    return {'steps': [
        {'id':'a','authority':'Aadhaar','label':'Correct record','estimatedDays':4,'visits':1,'onlinePossible':True,'onlineOfficiallyVerified':False},
        {'id':'b','authority':'Passport','label':'Submit evidence','dependsOn':['a'],'estimatedDays':3,'visits':1,'onlinePossible':True,'onlineOfficiallyVerified':True}
    ]}

def test_rejection_reason():
    result=post('rejection-diagnosis', {'reason':'Name mismatch in proof','authority':'Passport'})
    assert result['possibleCauses'][0]['category']=='identity_mismatch'
    assert result['officialRootCauseConfirmed'] is False

def test_unknown_rejection():
    assert post('rejection-diagnosis',{'reason':'Other reason','authority':'A'})['possibleCauses'][0]['category']=='unclassified'

def test_legacy():
    result=post('legacy-reconstruction',{'documentType':'Old birth record','availableEvidence':['school record']})
    assert result['documentReconstructed'] is False
    assert result['evidenceInventory']==['school record']

def test_discovery():
    result=post('life-event-discovery',{'lifeEvents':['Marriage'],'catalog':[{'id':'one','label':'Service','lifeEvents':['marriage'],'department':'A'},{'id':'two','label':'Other','lifeEvents':['retirement'],'department':'B'}]})
    assert result['matchCount']==1

def test_multi_rules():
    result=post('multi-department-rules',{'departments':['A'],'rulePacks':[{'id':'a','department':'A','service':'X','version':'v1'},{'id':'b','department':'B','service':'Y','version':'v1'}]})
    assert result['count']==1 and result['officialRuleValidityVerified'] is False

def test_human_support_no_real_assignment():
    assert post('human-support',{'service':'Passport','blocker':'Missing document'})['caseAssignedToHuman'] is False

def test_bottleneck_critical_path():
    result=post('authority-bottlenecks',steps())
    assert result['estimatedCriticalPathDays']==7
    assert result['executionOrder']==['a','b']

def test_cycle():
    data=steps();data['steps'][0]['dependsOn']=['b']
    assert set(post('authority-bottlenecks',data)['cycleOrCycleBlockedStepIds'])=={'a','b'}
    assert post('deadline-rescue',data)['deadlineAtRiskUnderAssumptions'] is True

def test_deadline():
    data=steps();data['targetDate']='2000-01-01'
    result=post('deadline-rescue',data)
    assert result['deadlineAtRiskUnderAssumptions'] is True
    assert result['officialDeadlineOrExpediteVerified'] is False

def test_visits():
    result=post('visit-eliminator',steps())
    assert result['baselineEstimatedVisits']==2
    assert result['potentialAvoidableVisitsUnderAssumptions']==1
    assert result['onlineAvailabilityNeedsVerificationStepIds']==['a']
    assert result['governmentVisitsActuallyEliminated'] is False

def test_invalid_dependency():
    data=steps();data['steps'][1]['dependsOn']=['missing']
    post('visit-eliminator',data,422)

def test_unknown_fields_rejected():
    post('legacy-reconstruction',{'documentType':'Old','fakeField':1},422)
