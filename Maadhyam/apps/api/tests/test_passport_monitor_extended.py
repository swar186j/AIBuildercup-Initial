"""Additional offline tests for M3 approval, trust boundaries, freshness and state."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from maadhyam_api.routes import passport_source_monitor as monitor
from maadhyam_api.routes import passport_rules


def page(word):
    return ('<html><body><main>' + (word + ' ') * 120 + '</main></body></html>').encode()


def test_untrusted_source_rejected_even_with_mock_fetcher():
    result = monitor.evaluate([{'id': 'evil', 'url': 'https://example.com/x'}], {},
                              lambda url: (page('legitimate'), 'text/html', url))
    assert result['sources']['evil']['status'] == 'fetch-failed'
    assert 'untrusted' in result['sources']['evil']['error']


def test_redirect_to_untrusted_domain_fails():
    result = monitor.evaluate([{'id': 'fresh', 'url': 'https://www.passportindia.gov.in/fresh'}], {},
                              lambda url: (page('passport'), 'text/html', 'https://example.com/fresh'))
    assert result['sources']['fresh']['status'] == 'fetch-failed'


def test_approval_requires_confirmation(monkeypatch, tmp_path):
    path = tmp_path / 'approved.json'
    monkeypatch.setenv('MAADHYAM_PASSPORT_APPROVED_BASELINES', str(path))
    with pytest.raises(ValueError):
        monitor.approve('official-fresh', 'reviewer', False)
    assert not path.exists()


def test_approved_baseline_written_separately(monkeypatch, tmp_path):
    approved = tmp_path / 'approved.json'
    state = tmp_path / 'state.json'
    monkeypatch.setenv('MAADHYAM_PASSPORT_APPROVED_BASELINES', str(approved))
    monkeypatch.setenv('MAADHYAM_PASSPORT_SOURCE_STATE', str(state))
    monkeypatch.setattr(monitor, 'inspect', lambda sid: {
        'url': 'https://www.passportindia.gov.in/psp/ListDocuments',
        'sha256': 'ab' * 32, 'fingerprint_method': 'html-text'})
    monitor.approve('official-documents', 'test-reviewer', True)
    result = json.loads(approved.read_text())
    assert result['sources']['official-documents']['reviewed_by'] == 'test-reviewer'
    assert not state.exists()


def test_old_monitoring_state_fails_closed(monkeypatch, tmp_path):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'overall': 'current', 'last_checked': (
        datetime.now(timezone.utc) - timedelta(days=3)).isoformat(), 'sources': {}}))
    monkeypatch.setattr(passport_rules, 'STATE', state)
    assert passport_rules.source_health() == 'stale-monitoring'


def test_recent_monitoring_state_keeps_health(monkeypatch, tmp_path):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'overall': 'review-required',
                                 'last_checked': datetime.now(timezone.utc).isoformat(), 'sources': {}}))
    monkeypatch.setattr(passport_rules, 'STATE', state)
    assert passport_rules.source_health() == 'review-required'


def test_no_monitoring_file_is_not_verified(monkeypatch, tmp_path):
    monkeypatch.setattr(passport_rules, 'STATE', tmp_path / 'missing.json')
    assert passport_rules.source_health() == 'not-monitored'
