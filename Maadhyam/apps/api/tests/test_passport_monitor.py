"""Offline monitor tests; no calls to government websites."""
from maadhyam_api.routes.passport_source_monitor import evaluate, _fingerprint


def page(text):
    return ('<html><body><main>' + (' '.join([text] * 80)) + '</main></body></html>').encode()


def source(sid):
    return {'id': sid, 'url': f'https://www.passportindia.gov.in/{sid}'}


def fetch_factory(pages):
    def fetch(url):
        return pages[url.split('/')[-1]], 'text/html', url
    return fetch


def test_missing_approval_never_current():
    result = evaluate([source('fresh')], {}, fetch_factory({'fresh': page('Passport supporting evidence')}))
    assert result['sources']['fresh']['status'] == 'unreviewed-baseline'
    assert result['overall'] == 'review-required'


def test_approved_same_content_is_current():
    body = page('Passport supporting evidence')
    digest, method = _fingerprint(body, 'text/html')
    approved = {'fresh': {'sha256': digest, 'url': source('fresh')['url'], 'fingerprint_method': method}}
    result = evaluate([source('fresh')], approved, fetch_factory({'fresh': body}))
    assert result['overall'] == 'current'


def test_approved_changed_content_is_flagged():
    old, new = page('Passport old evidence'), page('Passport new evidence')
    digest, method = _fingerprint(old, 'text/html')
    approved = {'fresh': {'sha256': digest, 'url': source('fresh')['url'], 'fingerprint_method': method}}
    result = evaluate([source('fresh')], approved, fetch_factory({'fresh': new}))
    assert result['sources']['fresh']['status'] == 'changed-review-required'


def test_duplicate_portal_shell_is_not_verified():
    shared = page('Generic portal application shell')
    result = evaluate([source('fresh'), source('reissue')], {}, fetch_factory({'fresh': shared, 'reissue': shared}))
    assert all(x['status'] == 'ambiguous-shared-content' for x in result['sources'].values())


def test_empty_or_tiny_html_is_rejected():
    result = evaluate([source('fresh')], {}, fetch_factory({'fresh': b'<html>Loading...</html>'}))
    assert result['sources']['fresh']['status'] == 'fetch-failed'
