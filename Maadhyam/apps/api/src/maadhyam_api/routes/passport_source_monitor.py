"""Offline-testable official-source drift monitor.

Never auto-publishes legal requirements. CLI commands: check, inspect, approve.
Approval requires an explicit human-reviewed source and is stored separately.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid
from urllib.parse import quote
from datetime import datetime, timezone
from difflib import unified_diff
from html import unescape
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
PACK = HERE / 'passport_rules_pack.json'
MAX_BYTES = 5_000_000
ALLOWED_HOSTS = {'passportindia.gov.in', 'www.passportindia.gov.in', 'services1.passportindia.gov.in', 'services2.passportindia.gov.in', 'portal1.passportindia.gov.in', 'portal4.passportindia.gov.in'}
MAX_RETRIES = 1  # no aggressive scraping

# A monitored URL is never silently replaced with a different government document.
# Missing sources remain visibly unavailable until an official replacement is reviewed.
GAZETTE_MARKERS = (('ministry of external affairs', 'passport rules', 'date of birth'),
                   ('विदेश मंत्रालय', 'पासपोर्ट', 'जन्म'))


def state_path():
    return Path(os.getenv('MAADHYAM_PASSPORT_SOURCE_STATE', str(HERE / 'passport_source_state.json')))


def baseline_path():
    return Path(os.getenv('MAADHYAM_PASSPORT_APPROVED_BASELINES', str(HERE / 'passport_approved_baselines.json')))


def _gcs_location(path):
    value = str(path)
    if value.startswith('gs://'):
        rest = value[5:]
        bucket, _, key = rest.partition('/')
        if not bucket or not key or '..' in key.split('/'):
            raise ValueError('invalid-gcs-location')
        return bucket, key
    return None


def _gcs_client():
    try:
        from google.cloud import storage
    except ImportError as exc:
        raise RuntimeError('GCS state requires: uv add google-cloud-storage') from exc
    return storage.Client()


def _read_state_bytes(path):
    loc = _gcs_location(path)
    if loc:
        bucket, key = loc
        blob = _gcs_client().bucket(bucket).blob(key)
        try:
            return blob.download_as_bytes()
        except Exception as exc:
            if type(exc).__name__ == 'NotFound':
                return b'{}'
            raise
    return Path(path).read_bytes()


def _write_state_bytes(path, payload):
    loc = _gcs_location(path)
    if loc:
        bucket, key = loc
        # Generation-match precondition prevents overwriting concurrent writes.
        client = _gcs_client()
        blob = client.bucket(bucket).blob(key)
        try:
            blob.reload()
            generation = blob.generation
        except Exception as exc:
            if type(exc).__name__ != 'NotFound':
                raise
            generation = 0
        blob.upload_from_string(payload, content_type='application/json', if_generation_match=generation)
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_bytes(payload)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _load_json(path):
    try:
        value = json.loads(_read_state_bytes(path).decode('utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_json(path, data):
    _write_state_bytes(path, (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))


def _allowed(url):
    parsed = urlparse(url)
    return parsed.scheme == 'https' and parsed.hostname in ALLOWED_HOSTS and not parsed.username and not parsed.password


def _fetch(url):
    if not _allowed(url):
        raise ValueError('untrusted-source-host')
    req = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; MaadhyamOfficialSourceMonitor/1.0)',
        'Accept': 'text/html,application/pdf;q=0.9,*/*;q=0.1',
    })
    with urlopen(req, timeout=12) as response:
        final_url = response.geturl()
        if not _allowed(final_url):
            raise ValueError('unexpected-redirect')
        ctype = response.headers.get('Content-Type', '').lower()
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError('source-too-large')
    if not body:
        raise ValueError('empty-response')
    return body, ctype, final_url


def _is_spa_shell(body, ctype):
    """Recognize an empty JS app shell; do not treat it as official guidance."""
    if 'html' not in ctype.lower():
        return False
    sample = body[:20000].decode('utf-8', 'replace').lower()
    return ('<div id="root"></div>' in sample or "<div id='root'></div>" in sample) and (
        'static/js/' in sample or 'enable javascript' in sample
    )


def _render_spa(url, timeout_ms=18000):
    """Render only allowlisted official HTTPS pages with a locally installed browser."""
    if not _allowed(url):
        raise ValueError('untrusted-source-host')
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError as exc:
        raise ValueError('playwright-not-installed') from exc
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(service_workers='block', accept_downloads=False)
                page = context.new_page()
                # Restrict browser navigation and resource requests to official hosts.
                def restrict(route):
                    target = route.request.url
                    if target.startswith(('data:', 'blob:')):
                        route.continue_()
                    elif _allowed(target):
                        route.continue_()
                    else:
                        route.abort()
                page.route('**/*', restrict)
                page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
                try:
                    page.locator('body').wait_for(state='visible', timeout=4000)
                    page.wait_for_function('document.body && document.body.innerText.trim().length > 160', timeout=7000)
                except PlaywrightTimeout:
                    pass
                final_url = page.url
                if not _allowed(final_url):
                    raise ValueError('unexpected-redirect')
                # Capture DOM after JS; never execute content in our Python process.
                html = page.content().encode('utf-8')
                if len(html) > MAX_BYTES:
                    raise ValueError('source-too-large')
                return html, 'text/html; charset=utf-8', final_url
            finally:
                browser.close()
    except PlaywrightTimeout as exc:
        raise ValueError('browser-render-timeout') from exc


def _fetch_with_browser_fallback(url, fetcher=_fetch, renderer=None):
    body, ctype, final_url = fetcher(url)
    if _is_spa_shell(body, ctype):
        renderer = renderer or _render_spa
        body, ctype, final_url = renderer(final_url)
        if not _allowed(final_url):
            raise ValueError('unexpected-redirect')
        if _is_spa_shell(body, ctype):
            raise ValueError('spa-render-returned-empty-shell')
    return body, ctype, final_url


def _normalized_text(value):
    return re.sub(r'\s+', ' ', unescape(value)).strip().lower()


# Do not fingerprint the portal clock, navigation, rotating news, or page chrome.
# Fail closed if no substantive source-specific content can be isolated.
NOISE_SELECTORS = (
    'script, style, noscript, svg, nav, header, footer, aside, '
    '[role="navigation"], [role="banner"], [role="contentinfo"], '
    '.navbar, .navigation, .breadcrumb, .breadcrumbs, .ticker, '
    '.marquee, .announcement, .announcements, .news-ticker, '
    '.header, .footer, .sidebar, .sitemap'
)

SOURCE_TERMS = {
    'official-documents': ('proof of address', 'aadhaar', 'electricity', 'rent agreement'),
    'official-fresh': ('fresh passport', 'fresh application', 'proof of address', 'proof of date of birth', 'documents required'),
    'official-reissue': ('re-issue', 'reissue', 're issue', 'old passport', 'documents required'),
}


def _guidance_text(body, ctype, source_id=None):
    if body.startswith(b'%PDF-'):
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError('pypdf-required: uv add pypdf') from exc
        from io import BytesIO
        try:
            reader = PdfReader(BytesIO(body), strict=False)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 250:
                raise ValueError('pdf-unreadable-or-invalid-page-count')
            text = _normalized_text(' '.join(page.extract_text() or '' for page in reader.pages))
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('pdf-text-extraction-failed') from exc
        if len(text) < 200:
            raise ValueError('pdf-insufficient-extracted-text')
        return text, 'pdf-text-v2'
    if 'pdf' in ctype.lower():
        raise ValueError('unexpected-non-pdf-response')
    if 'html' not in ctype.lower() and not body.lstrip().lower().startswith((b'<!doctype html', b'<html')):
        raise ValueError('unsupported-content-type')
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise ValueError('beautifulsoup4-required: uv add beautifulsoup4') from exc
    soup = BeautifulSoup(body, 'html.parser')
    for element in soup.select(NOISE_SELECTORS):
        element.decompose()
    for element in list(soup.find_all(True)):
        attrs = ' '.join(str(x) for x in (element.get('id', ''), ' '.join(element.get('class', [])))).lower()
        if re.search(r'(?:^|[-_\s])(ticker|marquee|announcement|breaking-news|newsfeed|clock)(?:$|[-_\s])', attrs):
            element.decompose()
    # Prefer actual content containers over the body; reject chrome-only pages.
    containers = soup.select('main, article, [role="main"], #mainContent, #main-content, .main-content, .page-content, .content-area')
    candidates = containers if containers else [soup.body or soup]
    terms = SOURCE_TERMS.get(source_id, ())
    ranked = []
    for node in candidates:
        value = _normalized_text(node.get_text(' ', strip=True))
        if not value:
            continue
        hits = sum(term in value for term in terms)
        ranked.append((hits, len(value), value))
    if not ranked:
        raise ValueError('no-official-guidance-container')
    # For sources with known keywords, pick the smallest substantial relevant region.
    matches = [x for x in ranked if x[0] and x[1] >= 160]
    if terms and not matches:
        raise ValueError('source-guidance-not-found')
    chosen = min(matches, key=lambda x: x[1]) if matches else max(ranked, key=lambda x: x[1])
    text = chosen[2]
    # Eliminate volatile portal clock lines, even if they remain inside <main>.
    text = re.sub(r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday),?\s+'
                  r'(?:january|february|march|april|may|june|july|august|september|october|november|december)'
                  r'\s+\d{1,2},?\s+\d{4}\s*\|?\s*\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?', ' ', text)
    text = _normalized_text(text)
    if len(text) < 160:
        raise ValueError('insufficient-official-content')
    if any(term in text[:900] for term in ('access denied', 'captcha', '403 forbidden', 'page not found', 'just a moment')):
        raise ValueError('blocked-or-error-page')
    if terms and not any(term in text for term in terms):
        raise ValueError('source-guidance-not-found')
    return text, 'html-guidance-v2'


def _visible_text(body, ctype):
    # Legacy helper retained for existing callers and tests.
    return _guidance_text(body, ctype)


def _fingerprint(body, ctype, source_id=None):
    text, method = _guidance_text(body, ctype, source_id)
    return hashlib.sha256(text.encode('utf-8')).hexdigest(), method


def _validate_source(source_id, body, ctype):
    text, method = _guidance_text(body, ctype, source_id)
    if len(text) < 160:
        raise ValueError('insufficient-official-content')
    if method == 'pdf-text-v2' and source_id == 'official-gazette':
        # Require multiple contextual indicators, not generic 'notification'/'birth'.
        # PDF extraction can distort Hindi; a human must still inspect the official PDF.
        english = ('ministry of external affairs' in text and
                   ('passport rules' in text or 'passport (amendment)' in text) and
                   ('date of birth' in text or 'proof of birth' in text))
        hindi = ('पासपोर्ट' in text and 'जन्म' in text and
                 ('नियम' in text or 'अधिनियम' in text))
        if not (english or hindi):
            raise ValueError('pdf-source-content-mismatch')


def _source_candidates(source):
    urls = [source['url']] + source.get('fallback_urls', [])
    return list(dict.fromkeys(urls))


def _fetch_source(source, fetcher, renderer=None):
    errors = []
    for url in _source_candidates(source):
        if not _allowed(url):
            errors.append(f'{url}: untrusted-source-host')
            continue
        try:
            body, ctype, final_url = _fetch_with_browser_fallback(url, fetcher, renderer)
            if not _allowed(final_url):
                raise ValueError('unexpected-redirect')
            _validate_source(source['id'], body, ctype)
            return body, ctype, final_url, url
        except (HTTPError, URLError, OSError, ValueError, TimeoutError) as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
    raise ValueError('all-source-candidates-failed: ' + '; '.join(errors)[:360])


def evaluate(sources, approved, fetcher=_fetch, now=None, renderer=None):
    now = now or datetime.now(timezone.utc).isoformat()
    entries = {}
    for source in sources:
        sid, url = source['id'], source['url']
        baseline = approved.get(sid, {})
        baseline = baseline if isinstance(baseline, dict) else {}
        entry = {'url': url, 'last_checked': now, 'baseline_sha256': baseline.get('sha256'),
                 'approved_at': baseline.get('approved_at')}
        try:
            if not _allowed(url):
                raise ValueError('untrusted-source-host')
            body, ctype, final_url, fetched_url = _fetch_source(source, fetcher, renderer)
            digest, method = _fingerprint(body, ctype, sid)
            entry.update(observed_sha256=digest, fingerprint_method=method,
                         content_type=ctype, final_url=final_url, fetched_url=fetched_url)
            if not baseline.get('sha256'):
                entry['status'] = 'unreviewed-baseline'
            elif baseline.get('url') != url or baseline.get('fingerprint_method') != method:
                entry['status'] = 'baseline-metadata-mismatch'
            else:
                entry['status'] = 'current' if digest == baseline['sha256'] else 'changed-review-required'
        except (HTTPError, URLError, OSError, ValueError, TimeoutError) as exc:
            entry.update(status='fetch-failed', error=f'{type(exc).__name__}: {exc}'[:200])
        entries[sid] = entry
    # Detect duplicate portal shells even if they match separately approved fingerprints.
    groups = {}
    for sid, entry in entries.items():
        if entry.get('fingerprint_method') == 'html-guidance-v2' and entry.get('observed_sha256'):
            groups.setdefault(entry['observed_sha256'], []).append(sid)
    for ids in groups.values():
        if len(ids) > 1:
            for sid in ids:
                entries[sid]['status'] = 'ambiguous-shared-content'
                entries[sid]['warning'] = 'Distinct URLs returned identical visible text; manually inspect actual guidance.'
    overall = 'current' if entries and all(e['status'] == 'current' for e in entries.values()) else 'review-required'
    return {'overall': overall, 'last_checked': now, 'sources': entries,
            'note': 'Content drift detection only. Human approval is required before interpreting or changing rules.'}


def check():
    pack = _load_json(PACK)
    approved = _load_json(baseline_path()).get('sources', {})
    result = evaluate(pack.get('sources', []), approved)
    _save_json(state_path(), result)
    record_versions(result)
    print(json.dumps({'overall': result['overall'], 'statuses': {
        sid: {'status': item['status'], **({'error': item['error']} if 'error' in item else {})}
        for sid, item in result['sources'].items()}}, indent=2))
    return result


def diagnose(source_id):
    """Read-only, one attempt per URL. Never approves or changes rules."""
    pack = _load_json(PACK)
    source = next((s for s in pack.get('sources', []) if s['id'] == source_id), None)
    if source is None:
        raise ValueError('unknown-source-id')
    results = []
    for url in _source_candidates(source):
        item = {'url': url}
        try:
            body, ctype, final_url = _fetch_with_browser_fallback(url)
            item.update(final_url=final_url, content_type=ctype, bytes=len(body),
                        pdf_magic=body.startswith(b'%PDF-'))
            try:
                text, method = _guidance_text(body, ctype, source_id)
                item['extraction_method'] = method
                if text is not None:
                    item['visible_characters'] = len(text)
                    item['matching_terms'] = [term for term in SOURCE_TERMS.get(source_id, ()) if term in text]
                    item['page_title'] = unescape(re.search(r'<title[^>]*>(.*?)</title>', body.decode('utf-8', errors='replace'), re.I | re.S).group(1)).strip()[:120] if re.search(r'<title[^>]*>(.*?)</title>', body.decode('utf-8', errors='replace'), re.I | re.S) else None
                _validate_source(source_id, body, ctype)
                item['validation'] = 'passed'
            except ValueError as exc:
                item['validation'] = 'failed'
                item['validation_error'] = str(exc)
                # No raw content is printed: avoids echoing unexpected data from websites.
        except (HTTPError, URLError, OSError, ValueError, TimeoutError) as exc:
            item['fetch_error'] = f'{type(exc).__name__}: {exc}'[:240]
        results.append(item)
    output = {'source_id': source_id, 'candidates': results,
              'note': 'Diagnostics only. No source is approved and no rule is changed.'}
    print(json.dumps(output, indent=2))
    return output


def inspect(source_id):
    pack = _load_json(PACK)
    source = next((s for s in pack.get('sources', []) if s['id'] == source_id), None)
    if source is None:
        raise ValueError('unknown-source-id')
    body, ctype, final_url, fetched_url = _fetch_source(source, _fetch)
    digest, method = _fingerprint(body, ctype, source_id)
    text, _ = _guidance_text(body, ctype, source_id)
    result = {'id': source_id, 'url': source['url'], 'final_url': final_url, 'fetched_url': fetched_url,
              'sha256': digest, 'fingerprint_method': method,
              'content_preview': text[:1200]}
    print(json.dumps(result, indent=2))
    return result


def approve(source_id, reviewed_by, confirmed):
    if not confirmed or not reviewed_by.strip():
        raise ValueError('approval-requires-reviewer-and-explicit-confirmation')
    pack = _load_json(PACK)
    source = next((x for x in pack.get('sources', []) if x['id'] == source_id), None)
    if source is None:
        raise ValueError('unknown-source-id')
    body, ctype, final_url, fetched_url = _fetch_source(source, _fetch)
    digest, method = _fingerprint(body, ctype, source_id)
    text = _snapshot_text(body, ctype, source_id)
    state = _load_json(state_path()).get('sources', {})
    if state.get(source_id, {}).get('status') == 'ambiguous-shared-content':
        raise ValueError('shared-portal-shell-cannot-be-approved')
    # Snapshot must be saved before the baseline pointer is changed.
    _save_snapshot(source_id, digest, text, final_url, 'approved-source-content')
    baselines = _load_json(baseline_path())
    sources = baselines.setdefault('sources', {})
    previous = sources.get(source_id, {}).copy()
    approved_at = datetime.now(timezone.utc).isoformat()
    if previous and (previous.get('sha256') != digest or previous.get('fingerprint_method') != method):
        audit = baselines.setdefault('approval_history', [])
        audit.append({'event': 'fingerprint-method-migration' if previous.get('fingerprint_method') != method else 'baseline-reapproval',
                      'source_id': source_id, 'previous_sha256': previous.get('sha256'),
                      'previous_fingerprint_method': previous.get('fingerprint_method'),
                      'new_sha256': digest, 'new_fingerprint_method': method,
                      'reviewed_by': reviewed_by.strip(), 'reviewed_at': approved_at})
    sources[source_id] = {'url': source['url'], 'sha256': digest,
                          'fingerprint_method': method, 'fetched_url': fetched_url,
                          'approved_at': approved_at,
                          'reviewed_by': reviewed_by.strip(), 'reviewed_ruleset_version': pack.get('version')}
    _save_json(baseline_path(), baselines)
    print(f'Approved full-text snapshot for {source_id}; no legal rules were changed.')


def snapshots_path():
    return os.getenv('MAADHYAM_PASSPORT_SOURCE_SNAPSHOTS', str(HERE / 'passport_source_snapshots.json'))


def _snapshot_text(body, ctype, source_id=None):
    text, _ = _guidance_text(body, ctype, source_id)
    return text


def _save_snapshot(source_id, digest, text, official_url, status):
    data = _load_json(snapshots_path())
    items = data.setdefault('sources', {}).setdefault(source_id, {})
    if digest not in items:
        items[digest] = {'sha256': digest, 'text': text, 'official_url': official_url,
                         'captured_at': datetime.now(timezone.utc).isoformat(), 'status': status}
        _save_json(snapshots_path(), data)
    elif status == 'approved-source-content' and items[digest].get('status') != status:
        # Human approval promotes an observed snapshot to rollback-eligible history.
        items[digest].update(status=status, approved_at=datetime.now(timezone.utc).isoformat())
        _save_json(snapshots_path(), data)
    return items[digest]


def _snapshot(source_id, digest):
    return _load_json(snapshots_path()).get('sources', {}).get(source_id, {}).get(digest)


def versions_path():
    return os.getenv('MAADHYAM_PASSPORT_SOURCE_VERSIONS', str(HERE / 'passport_source_versions.json'))


def proposals_path():
    return os.getenv('MAADHYAM_PASSPORT_RULE_PROPOSALS', str(HERE / 'passport_rule_proposals.json'))


def record_versions(result):
    data = _load_json(versions_path())
    history = data.setdefault('sources', {})
    for sid, entry in result['sources'].items():
        digest = entry.get('observed_sha256')
        if not digest:
            continue
        items = history.setdefault(sid, [])
        if not items or items[-1]['sha256'] != digest:
            items.append({'sha256': digest, 'seen_at': result['last_checked'],
                          'status': entry['status'], 'url': entry.get('fetched_url', entry['url'])})
            history[sid] = items[-20:]
    _save_json(versions_path(), data)


def compare(source_id, use_gemini=False):
    pack = _load_json(PACK)
    source = next((s for s in pack.get('sources', []) if s['id'] == source_id), None)
    if not source:
        raise ValueError('unknown-source-id')
    baseline = _load_json(baseline_path()).get('sources', {}).get(source_id)
    if not baseline:
        raise ValueError('approve-a-reviewed-baseline-first')
    old = _snapshot(source_id, baseline['sha256'])
    if not old or not old.get('text'):
        raise ValueError('approved-full-text-snapshot-missing; reapprove-after-review')
    body, ctype, final_url, fetched_url = _fetch_source(source, _fetch)
    digest, method = _fingerprint(body, ctype, source_id)
    if baseline.get('fingerprint_method') != method or baseline.get('url') != source['url']:
        raise ValueError('baseline-metadata-mismatch-requires-manual-review')
    if digest == baseline.get('sha256'):
        return {'status': 'unchanged', 'source_id': source_id}
    new_text = _snapshot_text(body, ctype, source_id)
    old_text = old['text']
    # Text is normalized for fingerprinting; differences are still real, but not word-level formatting.
    diff = list(unified_diff(old_text.split(), new_text.split(), fromfile='approved', tofile='observed', lineterm=''))
    proposal = {'proposal_id': uuid.uuid4().hex, 'source_id': source_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'needs-human-review', 'baseline_sha256': baseline['sha256'],
                'observed_sha256': digest, 'official_url': final_url,
                'summary': 'Official source text changed; human verification required.',
                'text_diff_preview': '\n'.join(diff[:160]),
                'diff_truncated': len(diff) > 160,
                'suggested_rule_changes': [], 'rule_activation': 'not-authorized'}
    _save_snapshot(source_id, digest, new_text, final_url, 'observed-unapproved')
    if use_gemini:
        from .passport_rule_change_ai import analyze_public_source
        try:
            proposal['ai_analysis'] = analyze_public_source(new_text, source_id, final_url, old_text)
        except Exception as exc:
            # Save the human-review proposal even when the optional AI API fails.
            proposal['ai_analysis_error'] = type(exc).__name__
            proposal['ai_analysis'] = {'requires_human_review': True, 'status': 'unavailable'}
    store = _load_json(proposals_path())
    store.setdefault('proposals', []).append(proposal)
    _save_json(proposals_path(), store)
    return proposal


def review_proposal(proposal_id, reviewer, decision, confirmed):
    if not confirmed or not reviewer.strip() or decision not in ('acknowledge', 'reject'):
        raise ValueError('review-requires-confirmation')
    store = _load_json(proposals_path())
    for proposal in store.get('proposals', []):
        if proposal['proposal_id'] == proposal_id:
            if proposal['status'] != 'needs-human-review':
                raise ValueError('proposal-already-reviewed')
            proposal.update(status='reviewed-' + decision, reviewed_by=reviewer,
                            reviewed_at=datetime.now(timezone.utc).isoformat())
            _save_json(proposals_path(), store)
            return proposal
    raise ValueError('unknown-proposal')


def rollback_baseline(source_id, sha256, reviewer, confirmed):
    if not confirmed or not reviewer.strip():
        raise ValueError('rollback-requires-human-confirmation')
    snapshot = _snapshot(source_id, sha256)
    if not snapshot or not snapshot.get('text') or snapshot.get('status') != 'approved-source-content':
        raise ValueError('rollback-requires-previously-approved-full-text-snapshot')
    approved = _load_json(baseline_path())
    baseline = approved.get('sources', {}).get(source_id)
    if not baseline:
        raise ValueError('missing-approved-baseline')
    old_sha = baseline.get('sha256')
    if snapshot.get('fingerprint_method') and snapshot['fingerprint_method'] != baseline.get('fingerprint_method'):
        raise ValueError('rollback-fingerprint-method-mismatch')
    baseline.update(sha256=sha256, approved_at=datetime.now(timezone.utc).isoformat(),
                    reviewed_by=reviewer, rollback=True)
    approved.setdefault('approval_history', []).append(
        {'event': 'rollback', 'source_id': source_id, 'previous_sha256': old_sha,
         'new_sha256': sha256, 'reviewed_by': reviewer, 'reviewed_at': baseline['approved_at']})
    _save_json(baseline_path(), approved)
    return baseline


def run():
    return check()['overall']


def main(argv=None):
    parser = argparse.ArgumentParser(description='Official Passport source monitoring (no automatic rule changes)')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('check')
    compare_cmd = sub.add_parser('compare')
    compare_cmd.add_argument('source_id')
    compare_cmd.add_argument('--gemini', action='store_true')
    review_cmd = sub.add_parser('review-proposal')
    review_cmd.add_argument('proposal_id')
    review_cmd.add_argument('--reviewed-by', required=True)
    review_cmd.add_argument('--decision', choices=['acknowledge','reject'], required=True)
    review_cmd.add_argument('--confirm-reviewed', action='store_true')
    rollback_cmd = sub.add_parser('rollback-baseline')
    rollback_cmd.add_argument('source_id')
    rollback_cmd.add_argument('sha256')
    rollback_cmd.add_argument('--reviewed-by', required=True)
    rollback_cmd.add_argument('--confirm-reviewed', action='store_true')
    diagnose_cmd = sub.add_parser('diagnose')
    diagnose_cmd.add_argument('source_id')
    inspect_cmd = sub.add_parser('inspect')
    inspect_cmd.add_argument('source_id')
    approve_cmd = sub.add_parser('approve')
    approve_cmd.add_argument('source_id')
    approve_cmd.add_argument('--reviewed-by', required=True)
    approve_cmd.add_argument('--confirm-reviewed', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command in (None, 'check'):
            check()
        elif args.command == 'compare':
            print(json.dumps(compare(args.source_id, args.gemini), indent=2))
        elif args.command == 'review-proposal':
            print(json.dumps(review_proposal(args.proposal_id, args.reviewed_by, args.decision, args.confirm_reviewed), indent=2))
        elif args.command == 'rollback-baseline':
            print(json.dumps(rollback_baseline(args.source_id, args.sha256, args.reviewed_by, args.confirm_reviewed), indent=2))
        elif args.command == 'diagnose':
            diagnose(args.source_id)
        elif args.command == 'inspect':
            inspect(args.source_id)
        elif args.command == 'approve':
            approve(args.source_id, args.reviewed_by, args.confirm_reviewed)
    except (ValueError, HTTPError, URLError, OSError, TimeoutError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
