import pytest
from pydantic import ValidationError
from maadhyam_api.routes.reasoning_engine import ReasoningRequest, reason


def doc(id, name, holder='self', reviewed=True):
    return {'id':id,'documentType':'Fictional demo','holder':holder,'reviewed':reviewed,
            'categories':['identity'],'printedName':name}


def run(payload):
    return reason(ReasoningRequest.model_validate(payload))


def test_conflict_what_if_resolves_without_legal_claim():
    data = run({'documents':[doc('a','Rahul Sharma'),doc('b','Rahul K Sharma')],
        'simulations':[{'id':'fix','label':'Align demo names','replaceFields':{'b':{'printedName':'Rahul Sharma'}}}]})
    assert 'printedName-conflict' in data['baseline']['reviewFindings']
    assert 'printedName-conflict' in data['simulations'][0]['resolvedFindingIds']
    assert not data['simulations'][0]['officialAcceptanceVerified']


def test_what_if_never_mutates_baseline():
    result = run({'documents':[doc('a','One'),doc('b','Two')],
                  'simulations':[{'id':'s','label':'change','removeDocumentIds':['b']}]})
    assert 'printedName-conflict' in result['baseline']['reviewFindings']
    assert 'printedName-conflict' not in result['simulations'][0]['after']['reviewFindings']


def test_dependency_graph_is_valid():
    result = run({'documents':[doc('a','One',reviewed=False)]})
    order = result['dependencyGraph']['executionOrder']
    for edge in result['dependencyGraph']['edges']:
        assert order.index(edge['before']) < order.index(edge['after'])


def test_family_document_not_applicant_evidence():
    result = run({'documents':[doc('p','Parent','parent-guardian')],
        'familyLinks':[{'documentId':'p','relation':'parent','claimedByApplicant':True}]})
    assert result['baseline']['assessment']['reviewedSelfDocuments'] == 0
    assert result['familyEvidence']['links'][0]['requiresVerification']
    assert not result['familyEvidence']['officialRelationshipVerified']


def test_unlinked_family_documents_flagged():
    result = run({'documents':[doc('p','Parent','parent-guardian')]})
    assert result['familyEvidence']['unlinkedFamilyDocumentIds'] == ['p']

@pytest.mark.parametrize('payload',[
    {'documents':[doc('a','A')],'familyLinks':[{'documentId':'missing','relation':'parent'}]},
    {'documents':[doc('a','A')],'simulations':[{'id':'s','label':'bad','removeDocumentIds':['missing']}]},
    {'documents':[doc('a','A')],'simulations':[{'id':'s','label':'bad','removeDocumentIds':['a'],'markReviewedIds':['a']}]},
    {'documents':[doc('a','A')],'simulations':[{'id':'s','label':'one'},{'id':'s','label':'two'}]},
    {'documents':[doc('a','A')],'familyLinks':[{'documentId':'a','relation':'parent'},{'documentId':'a','relation':'parent'}]},
])
def test_invalid_references_rejected(payload):
    with pytest.raises(ValidationError):
        ReasoningRequest.model_validate(payload)


def test_simulation_reveals_new_conflict():
    result = run({'documents':[doc('a','One'),doc('b','One')],
        'simulations':[{'id':'s','label':'introduce','replaceFields':{'b':{'printedName':'Two'}}}]})
    assert 'printedName-conflict' in result['simulations'][0]['newFindingIds']


def test_review_simulation_changes_review_gate():
    result = run({'documents':[doc('a','One',reviewed=False)],
        'simulations':[{'id':'s','label':'review','markReviewedIds':['a']}]})
    assert 'Unreviewed applicant documents' in result['simulations'][0]['before']['blockers']
    assert 'Unreviewed applicant documents' not in result['simulations'][0]['after']['blockers']
