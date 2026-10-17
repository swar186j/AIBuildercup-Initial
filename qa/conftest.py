"""Shared Chromium lifecycle; every test gets an isolated browser context."""
import json
import re
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path(os.environ.get("MAADHYAM_QA_EVIDENCE", str(ROOT / "qa/evidence/final/screenshots")))
EVIDENCE.mkdir(parents=True, exist_ok=True)
API = os.environ.get("MAADHYAM_TEST_API", "http://127.0.0.1:8002")
WEB = os.environ.get("MAADHYAM_TEST_WEB", "http://127.0.0.1:5173")

@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()

@pytest.fixture
def page(browser, request):
    ctx = browser.new_context(base_url=WEB, viewport={'width':1440,'height':1000})
    # Preserve real HTTP backend behavior while isolating from developer credentials.
    ctx.route('**/api/**', lambda r: r.fulfill(response=r.fetch(url=API + '/api' + r.request.url.split('/api',1)[1])))
    p = ctx.new_page()
    from qa.test_remediation import mocked_auth
    mocked_auth(p, cloud_consent=False)
    p.set_default_timeout(6000)
    errors, console, network = [], [], []
    p.on('pageerror', lambda e: errors.append(str(e)))
    p.on('console', lambda m: console.append({'type':m.type,'text':m.text}))
    p.on('response', lambda r: network.append({'url':r.url,'status':r.status}))
    yield p
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', request.node.name)
    p.evaluate('window.scrollTo(0, 0)')
    p.screenshot(path=str(EVIDENCE / (name+'.png')), full_page=True, animations='disabled')
    (EVIDENCE/(name+'.json')).write_text(json.dumps({'runtimeErrors':errors,'console':console,'network':network,'apiAssertions':p.evaluate('window.__qaResponses || []')},indent=2))
    ctx.unroute_all(behavior='wait')
    ctx.close()
    assert not errors, f'Uncaught runtime errors: {errors}'
    assert not any('Rahul' in x['text'] or 'SECRET_' in x['text'] for x in console), 'Document metadata in browser logs'
