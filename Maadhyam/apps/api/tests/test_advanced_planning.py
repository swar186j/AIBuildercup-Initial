from maadhyam_api.routes.advanced_planning import PlanningRequest, plan

def test_chooses_lower_cost_option():
    req=PlanningRequest.model_validate({'issues':[{'id':'identity','options':[
        {'id':'expensive','label':'Office','costINR':3000,'durationDays':2,'visits':2,'authority':'A'},
        {'id':'cheap','label':'Online','costINR':100,'durationDays':1,'visits':0,'authority':'A','onlinePossible':True}]}]})
    result=plan(req)
    assert result['selectedOptions'][0]['id']=='cheap'
    assert result['estimatedVisits']==0
    assert result['officialAcceptanceVerified'] is False

def test_cycle_detected():
    req=PlanningRequest.model_validate({'issues':[
      {'id':'a','options':[{'id':'a1','label':'A','costINR':0,'durationDays':1,'visits':0,'authority':'X','prerequisites':['b']}]},
      {'id':'b','options':[{'id':'b1','label':'B','costINR':0,'durationDays':1,'visits':0,'authority':'Y','prerequisites':['a']}]}]})
    assert plan(req)['status']=='deadlock'
