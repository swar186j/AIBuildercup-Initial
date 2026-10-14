"""M4 functional hardening: run from apps/api using uv run pytest tests/test_intelligence_hardening.py -q."""
import pytest
from fastapi.testclient import TestClient
from maadhyam_api.main import app

client = TestClient(app)
URL = '/api/intelligence/analyze'


def document(id, **kw):
    return {'id': id, 'reviewed': True, 'holder': 'self', **kw}


def analyze(documents):
    return client.post(URL, json={'documents': documents})


def finding_ids(result):
    return {x['id'] for x in result['findings']}


@pytest.mark.parametrize('ids', [
    ['same', 'same'], ['Doc-1', 'doc-1'], [' doc ', 'doc'],
])
def test_duplicate_ids_rejected(ids):
    result = analyze([document(ids[0]), document(ids[1])])
    assert result.status_code == 422, result.text


def test_distinct_ids_allowed():
    assert analyze([document('a'), document('b')]).status_code == 200


@pytest.mark.parametrize('invalid', [' ', '\t', '\n'])
def test_whitespace_id_rejected(invalid):
    assert analyze([document(invalid)]).status_code == 422


@pytest.mark.parametrize('date_a,date_b', [
    ('2000-05-12', '12/05/2000'),
    ('2000-12-05', '05/12/2000'),
])
def test_equivalent_dob_formats_do_not_conflict(date_a, date_b):
    response = analyze([document('a', dateOfBirth=date_a), document('b', dateOfBirth=date_b)])
    assert response.status_code == 200
    assert 'dateOfBirth-conflict' not in finding_ids(response.json())


@pytest.mark.parametrize('bad_dob', ['2000-02-30', '31/02/2000', '05-12-2000', '12/13/2000'])
def test_invalid_or_ambiguous_dob_flagged(bad_dob):
    response = analyze([document('a', dateOfBirth=bad_dob)])
    assert response.status_code == 200
    data = response.json()
    assert 'dateOfBirth-invalid' in finding_ids(data)
    assert 'verify-dateOfBirth' in {x['id'] for x in data['tasks']}


def test_valid_dob_conflict_still_detected():
    response = analyze([document('a', dateOfBirth='2000-05-12'), document('b', dateOfBirth='2000-12-05')])
    assert 'dateOfBirth-conflict' in finding_ids(response.json())


@pytest.mark.parametrize('confidence', [None, 0.2, 0.84])
def test_low_confidence_ocr_review_requires_recheck(confidence):
    response = analyze([document('a', extractionSource='ocr', extractionConfidence=confidence)])
    assert response.status_code == 200
    assert 'extraction-low-confidence' in finding_ids(response.json())


def test_high_confidence_ocr_not_flagged_for_quality():
    response = analyze([document('a', extractionSource='ocr', extractionConfidence=0.95)])
    assert 'extraction-low-confidence' not in finding_ids(response.json())


def test_unreviewed_ocr_excluded_from_conflicts():
    response = analyze([document('a', printedName='A'), {'id':'b', 'reviewed':False, 'holder':'self', 'printedName':'B', 'extractionSource':'ocr', 'extractionConfidence':0.2}])
    # Build an unreviewed document without duplicate keyword arguments.
    assert response.status_code == 200
    assert 'printedName-conflict' not in finding_ids(response.json())


def test_execution_order_respects_dependencies():
    response = analyze([document('a', printedName='A'), document('b', printedName='B')])
    data = response.json()
    position = {task_id: i for i, task_id in enumerate(data['executionOrder'])}
    assert set(position) == {t['id'] for t in data['tasks']}
    for task in data['tasks']:
        assert all(position[dep] < position[task['id']] for dep in task['dependsOn'])


def test_invalid_extraction_confidence_rejected():
    assert analyze([document('a', extractionConfidence=1.5)]).status_code == 422
