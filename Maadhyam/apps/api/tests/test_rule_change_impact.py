from copy import deepcopy
from maadhyam_api.routes.rule_change_impact import compare_packs, ImpactDocument

def baseline():
    return {'version':'v1','rules':[{'id':'address','types':['Aadhaar card','Voter ID'],'source_url':'https://example.org'}]}

def test_no_change():
    old=baseline()
    assert compare_packs(old, deepcopy(old))['changes'] == []

def test_added_and_removed_proofs():
    old=baseline(); new=deepcopy(old); new['version']='v2'; new['rules'][0]['types']=['Aadhaar card','Electricity bill']
    result=compare_packs(old,new,[ImpactDocument(id='voter',documentType='Voter ID')])
    change=result['changes'][0]
    assert change['removedProofTypes']==['Voter ID']
    assert change['addedProofTypes']==['Electricity bill']
    assert change['affectedDocumentIds']==['voter']
    assert result['officialChangeVerified'] is False
    assert old['rules'][0]['types']==['Aadhaar card','Voter ID']

def test_added_rule():
    new=baseline(); new['rules'].append({'id':'birth','types':['Birth certificate']})
    assert compare_packs(baseline(),new)['changes'][0]['changeType']=='added'

def test_removed_rule():
    new={'version':'v2','rules':[]}
    assert compare_packs(baseline(),new)['changes'][0]['changeType']=='removed'

def test_metadata_change_detected():
    new=deepcopy(baseline()); new['rules'][0]['action']='Check latest requirements'
    assert compare_packs(baseline(),new)['changes'][0]['changeType']=='modified'

def test_invalid_duplicate_ids():
    import pytest
    new=baseline(); new['rules'].append(deepcopy(new['rules'][0]))
    with pytest.raises(ValueError, match='unique'):
        compare_packs(baseline(),new)
