import json
from pathlib import Path
import pytest
from maadhyam_api.routes import passport_source_monitor as m


def html(text):
    return ('<html><main>' + (text + ' ') * 80 + '</main></html>').encode()


def test_fallback_success():
    primary = 'https://www.passportindia.gov.in/psp/ListDocuments'
    backup = 'https://services1.passportindia.gov.in/psp/ListDocuments'
    def fetch(url):
        if url == primary:
            raise OSError('unavailable')
        return html('proof of address Aadhaar'), 'text/html', url
    result = m.evaluate([{'id':'official-documents','url':primary,'fallback_urls':[backup]}],{},fetch)
    assert result['sources']['official-documents']['status'] == 'unreviewed-baseline'
    assert result['sources']['official-documents']['fetched_url'] == backup


def test_wrong_page_rejected():
    url = 'https://www.passportindia.gov.in/psp/ListDocuments'
    result = m.evaluate([{'id':'official-documents','url':url}],{},lambda u:(html('welcome home'), 'text/html', u))
    assert result['sources']['official-documents']['status'] == 'fetch-failed'
    # Content-scoped extraction rejects pages without actual document guidance.
    assert 'source-guidance-not-found' in result['sources']['official-documents']['error']


def test_versions_recorded_only_on_change(tmp_path, monkeypatch):
    monkeypatch.setenv('MAADHYAM_PASSPORT_SOURCE_VERSIONS',str(tmp_path/'versions.json'))
    a={'last_checked':'2026-10-13T00:00:00+00:00','sources':{'s':{'status':'unreviewed-baseline','url':'https://www.passportindia.gov.in/x','observed_sha256':'a'}}}
    m.record_versions(a);m.record_versions(a)
    a['sources']['s']['observed_sha256']='b';m.record_versions(a)
    data=json.loads((tmp_path/'versions.json').read_text())
    assert [i['sha256'] for i in data['sources']['s']]==['a','b']


def test_review_proposal_requires_explicit_approval(tmp_path,monkeypatch):
    monkeypatch.setenv('MAADHYAM_PASSPORT_RULE_PROPOSALS',str(tmp_path/'proposals.json'))
    m._save_json(m.proposals_path(),{'proposals':[{'proposal_id':'p','status':'needs-human-review'}]})
    with pytest.raises(ValueError):m.review_proposal('p','reviewer','acknowledge',False)
    assert m.review_proposal('p','reviewer','acknowledge',True)['status']=='reviewed-acknowledge'


def test_rollback_requires_known_history(tmp_path, monkeypatch):
    monkeypatch.setenv('MAADHYAM_PASSPORT_SOURCE_VERSIONS', str(tmp_path / 'versions.json'))
    monkeypatch.setenv('MAADHYAM_PASSPORT_APPROVED_BASELINES', str(tmp_path / 'approved.json'))
    monkeypatch.setenv('MAADHYAM_PASSPORT_SOURCE_SNAPSHOTS', str(tmp_path / 'snapshots.json'))
    m._save_json(m.baseline_path(), {'sources': {'s': {'sha256': 'a'}}})

    with pytest.raises(ValueError, match='previously-approved-full-text-snapshot'):
        m.rollback_baseline('s', 'unknown', 'r', True)

    # Legacy SHA-only version history is NOT sufficient for a safe rollback.
    m._save_json(m.versions_path(), {'sources': {'s': [{'sha256': 'old'}]}})
    with pytest.raises(ValueError, match='previously-approved-full-text-snapshot'):
        m.rollback_baseline('s', 'old', 'r', True)

    # A previously approved snapshot containing actual source text is required.
    m._save_json(m.snapshots_path(), {'sources': {'s': {'old': {
        'sha256': 'old',
        'text': 'Previously reviewed official source content.',
        'official_url': 'https://www.passportindia.gov.in/psp/ListDocuments',
        'status': 'approved-source-content',
    }}}})
    result = m.rollback_baseline('s', 'old', 'r', True)
    assert result['sha256'] == 'old'
    assert result['reviewed_by'] == 'r'
    assert result['rollback'] is True


def test_no_ai_key(monkeypatch):
    from maadhyam_api.routes.passport_rule_change_ai import analyze_public_source
    monkeypatch.delenv('MAADHYAM_GEMINI_API_KEY',raising=False)
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    with pytest.raises(ValueError,match='key'):
        analyze_public_source('test','id','https://www.passportindia.gov.in','none')
