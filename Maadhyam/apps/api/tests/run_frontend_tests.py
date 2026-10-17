#!/usr/bin/env python3
"""Maadhyam browser E2E smoke tests. Run from apps/api with `uv run python ...`."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from playwright.sync_api import sync_playwright

CASES = []
def case(name):
    def wrap(fn): CASES.append((name, fn)); return fn
    return wrap

def check(condition, message):
    if not condition: raise AssertionError(message)

def http_ready(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as response: return response.status < 500
    except (urllib.error.URLError, TimeoutError): return False

def wait_ready(url, timeout=45):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if http_ready(url): return True
        time.sleep(.5)
    return False

@case('FE01 Dashboard renders')
def dashboard(page, base):
    page.goto(base + '/', wait_until='domcontentloaded')
    check(page.locator('body').inner_text().strip() != '', 'Dashboard empty')
    check(not page.get_by_text('Page not found', exact=True).is_visible(), 'Dashboard route missing')

@case('FE02 Document Vault route and upload control')
def vault(page, base):
    page.goto(base + '/documents', wait_until='domcontentloaded')
    check(page.get_by_role('heading', name='Document Vault').count() > 0, 'Vault heading missing')
    check(page.get_by_label('Choose documents to add').count() > 0, 'Accessible upload control missing')

@case('FE03 Fictional document upload stays local and needs review')
def upload(page, base):
    page.goto(base + '/documents', wait_until='domcontentloaded')
    # A minimal valid PNG with no personal data; no Gemini call is made.
    png = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
    page.get_by_label('Choose documents to add').set_input_files({'name':'fictional_qa.png','mimeType':'image/png','buffer':png})
    check(page.get_by_text('fictional_qa.png').count() > 0, 'Uploaded filename not visible')
    check('needs review' in page.locator('body').inner_text().lower(), 'Unreviewed status not shown')

@case('FE04 Passport Guided Journey renders')
def journey(page, base):
    page.goto(base + '/services/passport/journey', wait_until='domcontentloaded')
    check(page.locator('body').inner_text().strip() != '', 'Journey empty')
    check(not page.get_by_text('Page not found', exact=True).is_visible(), 'Journey route missing')
    page.locator('h1').wait_for(timeout=15000)
    check('passport' in page.locator('body').inner_text().lower(), 'Passport content absent')

@case('FE05 Planner displays API-generated steps')
def planner(page, base):
    page.goto(base + '/planner', wait_until='domcontentloaded')
    check(page.get_by_role('heading', name='Resolution Planner').count() > 0, 'Planner missing')
    page.get_by_text('Your next steps', exact=True).wait_for(timeout=15000)
    check(page.get_by_text('Frontend demo:').count() == 0, 'Old duplicate demo planner remains')
    check(page.get_by_text('Your document situation').count() > 0, 'Intelligence summary missing')

@case('FE06 Assistant opens and accepts local prompt')
def assistant(page, base):
    page.goto(base + '/planner', wait_until='domcontentloaded')
    dialog = page.get_by_role('dialog', name='Maadhyam AI assistant')
    if not dialog.is_visible():
        buttons = page.get_by_role('button', name='Open Maadhyam AI', exact=True)
        check(buttons.count() > 0, 'Assistant opener missing')
        buttons.first.click()
    dialog.wait_for(timeout=10000)
    field = page.get_by_label('Message to Maadhyam AI')
    field.fill('Show my documents')
    field.press('Enter')
    page.get_by_text('Show my documents', exact=True).last.wait_for(timeout=10000)

@case('FE07 No uncaught browser page errors across core routes')
def no_errors(page, base):
    errors = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    for path in ('/', '/documents', '/services/passport/journey', '/planner'):
        page.goto(base + path, wait_until='domcontentloaded')
        page.locator("h1").wait_for()
    check(not errors, 'Uncaught browser errors: ' + '; '.join(errors))

def main():
    parser = argparse.ArgumentParser(description='Maadhyam frontend E2E smoke runner')
    parser.add_argument('--base-url', default='http://127.0.0.1:5173')
    parser.add_argument('--api-url', default='http://127.0.0.1:8000')
    parser.add_argument('--start', action='store_true', help='Start Vite and FastAPI automatically')
    parser.add_argument('--headed', action='store_true', help='Show browser window')
    parser.add_argument('--report', default='frontend-test-results.json')
    args = parser.parse_args()
    script = Path(__file__).resolve()
    root = script.parent.parent.parent if script.parent.name == 'tests' else Path.cwd()
    # With recommended placement apps/api/tests/run_frontend_tests.py
    if script.parent.name == 'tests':
        api_dir = script.parent.parent
        web_dir = api_dir.parent / 'web'
    else:
        api_dir = Path.cwd()
        web_dir = api_dir.parent / 'web'
    processes = []
    try:
        if args.start:
            if not http_ready(args.api_url.rstrip('/') + '/openapi.json'):
                processes.append(subprocess.Popen(['uv','run','uvicorn','maadhyam_api.main:app','--host','127.0.0.1','--port','8000'], cwd=api_dir, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=(os.name=='nt')))
            if not http_ready(args.base_url):
                processes.append(subprocess.Popen(['npm','run','dev','--','--host','127.0.0.1'], cwd=web_dir, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=(os.name=='nt')))
        if not wait_ready(args.base_url):
            print('ERROR: Frontend unavailable. Start npm run dev in apps/web, or pass --start.'); return 2
        if not wait_ready(args.api_url.rstrip('/') + '/openapi.json'):
            print('ERROR: Backend unavailable. Start uv run uvicorn maadhyam_api.main:app --reload in apps/api, or pass --start.'); return 2
        results = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=not args.headed)
                for name, fn in CASES:
                    context = browser.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=False)
                    page = context.new_page()
                    started = time.monotonic()
                    try:
                        fn(page, args.base_url)
                        result = {'case': name, 'status':'PASS', 'seconds':round(time.monotonic()-started,2)}
                    except Exception as exc:
                        result = {'case': name, 'status':'FAIL', 'seconds':round(time.monotonic()-started,2), 'error':str(exc)[:1500]}
                        print('  Failure:', result['error'].splitlines()[0])
                    print(f"{result['status']:4} {name}")
                    results.append(result)
                    context.close()
                browser.close()
        except Exception as exc:
            print('Browser failed to launch:', exc)
            print('Try: uv run playwright install chromium')
            return 2
        report = {'suite':'Maadhyam Frontend E2E', 'base_url':args.base_url, 'results':results, 'passed':sum(r['status']=='PASS' for r in results), 'failed':sum(r['status']=='FAIL' for r in results)}
        Path(args.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f"\n{report['passed']} passed, {report['failed']} failed. Report: {Path(args.report).resolve()}")
        return 1 if report['failed'] else 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=4)
                except subprocess.TimeoutExpired: process.kill()

if __name__ == '__main__': sys.exit(main())
