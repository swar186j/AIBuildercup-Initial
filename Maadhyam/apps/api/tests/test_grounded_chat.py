"""M9 regression: grounded local answers, consent gate, unreviewed data exclusion."""
import importlib.util
import sys
from pathlib import Path
import pytest
from fastapi import HTTPException

SOURCE = Path(__file__).resolve().parents[1] / 'src' / 'maadhyam_api' / 'routes' / 'intelligence.py'
if not SOURCE.exists():
    SOURCE = Path(__file__).with_name('intelligence.py')  # standalone batch verification
spec = importlib.util.spec_from_file_location('maadhyam_grounded_chat_under_test', SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def req(docs=None, question='What is my passport status?', **kwargs):
    return module.ChatRequest(documents=docs or [], question=question, **kwargs)


def test_local_mode_no_external_ai():
    response = module.chat(req())
    assert response['mode'] == 'local-explainable'
    assert response['grounding']['officiallyVerified'] is False
    assert response['sourceUrl'].startswith('https://www.passportindia.gov.in/')


def test_gemini_requires_explicit_fictional_consent():
    with pytest.raises(HTTPException) as exc:
        module.chat(req(useGemini=True, fictionalDataConfirmed=False))
    assert exc.value.status_code == 403


def test_only_reviewed_self_documents_in_grounding():
    docs = [
        {'id':'self-reviewed','holder':'self','reviewed':True,'printedName':'Demo One'},
        {'id':'self-unreviewed','holder':'self','reviewed':False,'printedName':'Hidden Two'},
        {'id':'family-reviewed','holder':'parent-guardian','reviewed':True,'printedName':'Hidden Three'},
    ]
    response = module.chat(req(docs, question='How many documents in vault?'))
    assert response['grounding']['reviewedApplicantDocumentIds'] == ['self-reviewed']
    assert '1 reviewed applicant' in response['answer']


def test_conflicts_are_not_declared_officially_wrong():
    docs = [
        {'id':'aadhaar','reviewed':True,'printedName':'Demo Kumar'},
        {'id':'pan','reviewed':True,'printedName':'Demo K'},
    ]
    response = module.chat(req(docs, question='Is there a name mismatch?'))
    assert 'discrepanc' in response['answer'].lower()
    assert 'does not establish which record is correct' in response['answer']


def test_unreviewed_conflict_not_treated_as_confirmed():
    docs = [
        {'id':'aadhaar','reviewed':True,'printedName':'Demo Kumar'},
        {'id':'pan','reviewed':False,'printedName':'Demo K'},
    ]
    response = module.chat(req(docs, question='name mismatch?'))
    assert not any(f['field'] == 'printedName' and 'conflict' in f['message'].lower() for f in response['assessment']['findings'])


def test_family_claim_never_verified():
    response = module.chat(req(question='Is my parent relationship verified?'))
    assert 'cannot be officially verified' in response['answer']


def test_empty_question_is_invalid():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        req(question='')


def test_no_eligibility_approval():
    response = module.chat(req(question='Am I eligible to apply for passport?'))
    assert 'not a decision on passport eligibility' in response['answer']


def test_context_has_no_unreviewed_metadata():
    docs = [{'id':'private','reviewed':False,'printedName':'DO NOT SEND'}]
    context = module.grounded_chat_context(req(docs))
    assert 'DO NOT SEND' not in str(context)
