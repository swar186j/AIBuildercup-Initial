import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from maadhyam_api.routes import passport_source_monitor as m

SOURCE = {'id': 'official-documents', 'url': 'https://www.passportindia.gov.in/psp/ListDocuments'}
OLD = 'proof of address aadhaar electricity rent agreement ' * 12
NEW = OLD + ' additional official requirement '

def configure(monkeypatch, tmp_path):
    for env, name in [('MAADHYAM_PASSPORT_SOURCE_SNAPSHOTS','snap.json'), ('MAADHYAM_PASSPORT_APPROVED_BASELINES','base.json'), ('MAADHYAM_PASSPORT_RULE_PROPOSALS','prop.json'), ('MAADHYAM_PASSPORT_SOURCE_STATE','state.json')]:
        monkeypatch.setenv(env, str(tmp_path / name))
    monkeypatch.setattr(m, 'PACK', tmp_path / 'pack.json')
    (tmp_path / 'pack.json').write_text(json.dumps({'version':'test', 'sources':[SOURCE]}))
    monkeypatch.setattr(m, '_fetch_source', lambda source, fetcher: (f'<html><body>{OLD}</body></html>'.encode(), 'text/html', SOURCE['url'], SOURCE['url']))

def test_approve_saves_full_text(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    m.approve('official-documents', 'reviewer', True)
    approved = m._load_json(m.baseline_path())['sources']['official-documents']
    snap = m._snapshot('official-documents', approved['sha256'])
    assert 'proof of address' in snap['text']
    assert snap['status'] == 'approved-source-content'

def test_compare_uses_real_old_and_new(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    m.approve('official-documents', 'reviewer', True)
    monkeypatch.setattr(m, '_fetch_source', lambda source, fetcher: (f'<html><body>{NEW}</body></html>'.encode(), 'text/html', SOURCE['url'], SOURCE['url']))
    result = m.compare('official-documents')
    assert result['status'] == 'needs-human-review'
    assert '+additional' in result['text_diff_preview']
    assert result['rule_activation'] == 'not-authorized'
    with pytest.raises(ValueError, match='previously-approved'):
        m.rollback_baseline('official-documents', result['observed_sha256'], 'reviewer', True)

def test_unchanged_does_not_create_proposal(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    m.approve('official-documents', 'reviewer', True)
    assert m.compare('official-documents')['status'] == 'unchanged'
    assert not m._load_json(m.proposals_path()).get('proposals')

def test_invalid_pdf_is_not_approvable():
    with pytest.raises(ValueError, match='pdf-text-extraction-failed'):
        m._snapshot_text(b'%PDF-' + b'X'*1200, 'application/pdf', 'official-gazette')
