"""Isolated M10 browser acceptance: synthetic Firebase identity, real HTTP API,
real production repository logic against an in-memory Firestore adapter.
No live Firebase users or Firestore documents are modified.
"""
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / 'Maadhyam/apps/api'
sys.path.insert(0, str(API / 'tests'))

if '--api-server' in sys.argv:
    from google.cloud import firestore
    import uvicorn
    from m10_support import test_app
    firestore.transactional = lambda fn: fn
    app, _ = test_app()
    uvicorn.run(app, host='127.0.0.1', port=int(sys.argv[-1]), log_level='warning')
    raise SystemExit()

from playwright.sync_api import sync_playwright, expect


def main():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    out = ROOT / ('qa/evidence/m10-m12' if '--m12' in sys.argv else 'qa/m10/evidence')
    out.mkdir(parents=True, exist_ok=True)
    log = (out / 'api.log').open('w')
    env = {**os.environ, 'MAADHYAM_GEMINI_API_KEY': '', 'GOOGLE_API_KEY': '', 'GEMINI_API_KEY': ''}
    server = subprocess.Popen([sys.executable, __file__, '--api-server', str(port)], cwd=API, env=env, stdout=log, stderr=subprocess.STDOUT)
    api = f'http://127.0.0.1:{port}'
    checks = []
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(api + '/api/health', timeout=1)
                break
            except OSError:
                if server.poll() is not None:
                    raise RuntimeError('Isolated API exited')
                time.sleep(.1)
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(base_url='http://127.0.0.1:5173')
            # Reproduce Cloud Vault hydration changing createDraft's identity while
            # the first creation request is pending (the user's stuck screen).
            def delayed_hydration(route):
                response = route.fetch()
                body = response.text()
                marker = 'const records = await listDocuments();'
                assert marker in body
                route.fulfill(response=response, body=body.replace(marker, marker + '\n await new Promise(resolve => setTimeout(resolve, 500));', 1))
            context.route('**/src/context/DocumentContext.tsx*', delayed_hydration)
            # Replace only the Firebase auth SDK in this test browser context.
            # Application code, saving API and repository logic remain real.
            sdk = '''
let listener;
const user = id => ({uid:id, email:id+'@example.invalid', getIdToken:async()=> 'test-'+id});
const auth = {currentUser:user(localStorage.getItem('m10-test-user') || 'a')};
export const getAuth = () => auth;
export const connectAuthEmulator = () => {};
export function onAuthStateChanged(a, cb) {listener=cb; queueMicrotask(()=>cb(a.currentUser)); return ()=>{listener=null;};}
export async function signOut(a) {a.currentUser=null; if(listener)listener(null);}
export async function signInWithEmailAndPassword(a, email) {const id=email.startsWith('b')?'b':'a'; localStorage.setItem('m10-test-user',id); a.currentUser=user(id); if(listener)listener(a.currentUser);}
'''
            context.route('**/node_modules/.vite/deps/firebase_auth.js*', lambda route: route.fulfill(status=200, content_type='application/javascript', body=sdk))
            first_creation = [True]
            def proxy(route):
                path = route.request.url.split('/api', 1)[1]
                response = route.fetch(url=api + '/api' + path)
                if path == '/applications' and route.request.method == 'POST' and first_creation[0]:
                    first_creation[0] = False
                    time.sleep(1)  # Deliberate synthetic delayed response, not an assertion wait.
                route.fulfill(response=response)
            context.route('**/api/**', proxy)
            page = context.new_page()
            page.set_default_timeout(10000)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('/services/passport/journey?type=fresh')
            name = page.get_by_role('textbox', name='Applicant name', exact=True)
            expect(name).to_be_visible()
            checks.append('Cloud Vault hydration during pending creation still opens the journey')
            context.unroute('**/src/context/DocumentContext.tsx*', delayed_hydration)
            name.fill('M10 Fictional Applicant')
            expect(page.get_by_text('Latest preparation changes saved to Firestore.', exact=True)).to_be_visible()
            preparation_url = page.url
            page.reload()
            expect(name).to_have_value('M10 Fictional Applicant')
            checks.append('create, save and refresh persistence')
            page.goto('/planner')
            first = page.get_by_role('checkbox', name='Complete your passport preparation questionnaire', exact=True)
            second = page.get_by_role('checkbox', name='Organize sample supporting documents', exact=True)
            expect(first).to_be_enabled()
            expect(second).to_be_disabled()
            first.click()
            expect(first).to_be_checked()
            expect(second).to_be_enabled()
            second.click()
            expect(second).to_be_checked()
            page.reload()
            expect(second).to_be_checked()
            first.click()
            expect(first).not_to_be_checked()
            expect(second).not_to_be_checked()
            checks.append('planner first save, prerequisites, refresh and cascade')
            page.goto('/documents')
            expect(page.get_by_role('button', name='Choose files', exact=True)).to_be_enabled()
            png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aMxkAAAAASUVORK5CYII=')
            fail_upload = [True]
            def upload_failure(route):
                if route.request.method == 'PUT' and fail_upload[0]:
                    fail_upload[0] = False
                    route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"Synthetic private storage outage"}}')
                else:
                    proxy(route)
            context.route('**/api/workspace/documents/*', upload_failure)
            page.get_by_label('Choose documents to add').set_input_files({'name': 'm10-fictional.png', 'mimeType': 'image/png', 'buffer': png})
            expect(page.get_by_role('region', name='Cloud Vault storage controls').get_by_role('alert')).to_have_text('Synthetic private storage outage')
            page.get_by_role('button', name='Retry cloud sync', exact=True).click()
            expect(page.get_by_text('m10-fictional.png', exact=True)).to_be_visible()
            context.unroute('**/api/workspace/documents/*', upload_failure)
            checks.append('failed cloud upload retains the file for explicit retry')
            expect(page.get_by_role('region', name='Cloud Vault storage controls').get_by_text('Cloud changes saved.', exact=True)).to_be_visible()
            expect(page.get_by_role('button', name='Enable local saving', exact=True)).to_have_count(0)
            page.reload()
            expect(page.get_by_text('m10-fictional.png', exact=True)).to_be_visible()
            checks.append('private cloud file and metadata survive refresh without local saving')
            def switch(email):
                page.get_by_role('button', name='Account menu', exact=True).click()
                page.get_by_role('button', name='Sign out', exact=True).click()
                page.get_by_role('textbox', name='Email', exact=True).fill(email)
                page.get_by_label('Password', exact=True).fill('synthetic-test-password')
                page.get_by_role('button', name='Sign in', exact=True).click()
                expect(page.get_by_role('button', name='Account menu', exact=True)).to_be_visible()
            switch('b@example.invalid')
            expect(page.get_by_text('m10-fictional.png', exact=True)).not_to_be_visible()
            page.goto('/applications')
            expect(page.get_by_role('button', name='Start new preparation', exact=True)).to_be_enabled()
            expect(page.locator('article')).to_have_count(0)
            expect(page.get_by_text('No matching preparation records.', exact=True)).to_be_visible()
            assert preparation_url.split('preparation=')[1] not in page.locator('body').inner_text()
            page.goto('/documents')
            switch('a@example.invalid')
            expect(page.get_by_text('m10-fictional.png', exact=True)).to_be_visible()
            checks.append('sign-out, account isolation and original-account restore')
            response = context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'})
            original = response.json()[0]
            second_payload = {key: original[key] for key in ('service_type', 'application_type', 'questionnaire_answers')}
            second_payload.update(client_id='LOCAL-second-filled-123', applicant_details={'name': 'Second fictional applicant'})
            assert context.request.post(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}, data=second_payload).status == 201
            page.goto('/household')
            page.get_by_role('textbox', name='New member name', exact=True).fill('Cloud Fictional Spouse')
            page.get_by_role('button', name='Add member', exact=True).click()
            expect(page.get_by_role('region', name='Household cloud storage').get_by_text('Household changes saved.', exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role('article', name='Household member Cloud Fictional Spouse', exact=True)).to_be_visible()
            checks.append('household members save and restore from cloud')
            switch('b@example.invalid')
            expect(page.get_by_role('button', name='Add member', exact=True)).to_be_enabled()
            expect(page.get_by_role('article', name='Household member Cloud Fictional Spouse', exact=True)).to_have_count(0)
            switch('a@example.invalid')
            expect(page.get_by_role('article', name='Household member Cloud Fictional Spouse', exact=True)).to_be_visible()
            checks.append('household data is isolated between accounts')
            fail_next = [True]
            def create_failure(route):
                if route.request.method == 'POST' and fail_next[0]:
                    fail_next[0] = False
                    route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"Synthetic create failure"}}')
                else:
                    proxy(route)
            context.route('**/api/applications', create_failure)
            page.goto('/services/passport/journey?type=fresh')
            expect(page.get_by_role('alert')).to_have_text('Synthetic create failure')
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 2
            page.get_by_role('button', name='Retry connection', exact=True).click()
            expect(name).to_be_visible()
            disposable_id = page.url.split('preparation=')[1]
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 3
            checks.append('failed create has no phantom draft; retry creates one record')
            page.goto(preparation_url)
            expect(name).to_have_value('M10 Fictional Applicant')
            def failed_save(route):
                if route.request.method == 'PATCH':
                    route.fulfill(status=409, content_type='application/json', body='{"error":{"message":"Synthetic revision conflict"}}')
                else:
                    proxy(route)
            context.route('**/api/applications/LOCAL-*', failed_save)
            name.fill('Unsaved fictional change')
            expect(page.get_by_role('region', name='Preparation save controls').get_by_text('Synthetic revision conflict', exact=False)).to_be_visible()
            page.get_by_role('button', name='Account menu', exact=True).click()
            page.get_by_role('button', name='Sign out', exact=True).click()
            expect(page.get_by_role('alert')).to_have_text('Some changes are not saved. Wait for confirmation or retry saving before signing out.')
            page.get_by_role('button', name='Account menu', exact=True).click()
            context.unroute('**/api/applications/LOCAL-*', failed_save)
            page.get_by_role('button', name='Save preparation', exact=True).click()
            expect(page.get_by_text('Latest preparation changes saved to Firestore.', exact=True)).to_be_visible()
            page.reload()
            expect(name).to_have_value('Unsaved fictional change')
            checks.append('failed save preserves edits, blocks sign-out and can be retried')
            page.goto('/applications')
            card = page.locator('article').filter(has_text=disposable_id)
            page.get_by_role('button', name='Show empty drafts', exact=True).click()
            card.get_by_role('button', name='Continue preparation', exact=True).click()
            def failed_delete(route):
                if route.request.method == 'DELETE':
                    route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"Synthetic delete failure"}}')
                else:
                    proxy(route)
            context.route('**/api/applications/LOCAL-*', failed_delete)
            page.get_by_role('button', name='Delete this preparation', exact=True).click()
            expect(page.get_by_role('region', name='Preparation storage controls').get_by_text('Synthetic delete failure', exact=False)).to_be_visible()
            expect(card).to_be_visible()
            context.unroute('**/api/applications/LOCAL-*', failed_delete)
            card.get_by_role('button', name='Continue preparation', exact=True).click()
            page.get_by_role('button', name='Delete this preparation', exact=True).click()
            expect(card).not_to_be_visible()
            checks.append('failed delete retains the record; confirmed retry removes it')
            page.goto('/services/passport/journey?type=fresh&preparation=' + disposable_id)
            expect(page.get_by_role('heading', name='Preparation unavailable', exact=True)).to_be_visible()
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 2
            checks.append('deleted preparation URL does not create a replacement draft')
            lost_response = [True]
            def committed_create_failure(route):
                if route.request.method == 'POST' and lost_response[0]:
                    lost_response[0] = False
                    route.fetch(url=api + '/api/applications')  # Commit succeeds; caller loses the response.
                    route.fulfill(status=503, content_type='application/json', body='{"error":{"message":"Synthetic lost create response"}}')
                else:
                    proxy(route)
            context.route('**/api/applications', committed_create_failure)
            page.goto('/services/passport/journey?type=fresh')
            expect(page.get_by_role('alert')).to_have_text('Synthetic lost create response')
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 3
            page.get_by_role('button', name='Retry connection', exact=True).click()
            expect(name).to_be_visible()
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 3
            checks.append('lost creation response retries with the same idempotency key')
            for number in (1, 2):
                payload = {key: original[key] for key in ('service_type', 'application_type', 'questionnaire_answers')}
                payload['client_id'] = f'LOCAL-empty-group-{number}'
                response = context.request.post(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}, data=payload)
                assert response.status == 201
            page.goto('/applications')
            expect(page.get_by_role('button', name='Show empty drafts', exact=True)).to_be_visible()
            expect(page.locator('article')).to_have_count(2)
            page.get_by_role('button', name='Show empty drafts', exact=True).click()
            expect(page.locator('article')).to_have_count(5)
            page.get_by_role('button', name='Hide empty drafts', exact=True).click()
            page.get_by_role('textbox', name='Search preparations').fill('LOCAL-empty-group-1')
            expect(page.locator('article')).to_have_count(1)
            page.goto('/services/passport/journey?type=fresh')
            expect(name).to_be_visible()
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == 5
            checks.append('empty drafts group safely; search finds them; revisiting journey reuses a blank')
            page.goto(preparation_url)
            expect(name).to_have_value('Unsaved fictional change')
            page.screenshot(path=str(out / 'saved-journey.png'), full_page=True)
            saved_records = context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()
            for record in saved_records:
                if record['applicant_details'].get('name'):
                    response = context.request.delete(api + '/api/applications/' + record['id'] + '?revision=' + str(record['revision']), headers={'Authorization': 'Bearer test-a'})
                    assert response.status == 204
            remaining = len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json())
            page.goto('/applications')
            expect(page.locator('article')).to_have_count(0)
            expect(page.get_by_role('button', name='Show empty drafts', exact=True)).to_be_visible()
            page.goto(preparation_url)
            expect(page.get_by_role('heading', name='Preparation unavailable', exact=True)).to_be_visible()
            assert len(context.request.get(api + '/api/applications', headers={'Authorization': 'Bearer test-a'}).json()) == remaining
            checks.append('deleting last filled record leaves list empty and creates no new records')
            if '--m12' in sys.argv:
                sys.path.insert(0, str(ROOT))
                from qa.test_browser import WORKFLOWS, test_citizen_workflow, test_navigation, test_assistant
                for width in (1440, 390):
                    page.set_viewport_size({'width': width, 'height': 900})
                    for key, title in WORKFLOWS:
                        test_citizen_workflow(page, key, title, False)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.screenshot(path=str(out / f'workflow-{key}-{width}.png'), full_page=True)
                        test_citizen_workflow(page, key, title, True)
                        page.unroute('**/api/citizen-workflows/' + key)
                    checks.append(f'all eight workflows success and provider failure at {width}px')
                    for path, title in [('/services', 'Find a government service'), ('/documents', 'Document Vault'), ('/applications', 'My Preparations'), ('/planner', 'Resolution Planner'), ('/workflows', 'Citizen workflow assistant')]:
                        test_navigation(page, path, title, width)
                    checks.append(f'five workspace routes and no horizontal overflow at {width}px')
                page.set_viewport_size({'width': 1440, 'height': 900})
                for mode in ['local', 'missing', '429', 'timeout', 'malformed']:
                    test_assistant(page, mode)
                    page.unroute('**/api/intelligence/chat')
                checks.append('assistant local guidance, consent and four failure states')
                page.goto('/documents')
                page.get_by_role('button', name='Open Maadhyam AI').click()
                expect(page.get_by_role('dialog', name='Maadhyam AI assistant')).to_be_visible()
                page.keyboard.press('Escape')
                expect(page.get_by_role('dialog', name='Maadhyam AI assistant')).not_to_be_visible()
                checks.append('assistant keyboard Escape dismissal')
                # Simulate an external free host failing its first wake-up. No
                # workspace writes may begin before the health gate succeeds.
                def external_origin(route):
                    response = route.fetch()
                    import re
                    body, count = re.subn(r'const apiOrigin = [^;]+;', 'const apiOrigin = "https://fictional-api.example.invalid";', response.text(), count=1)
                    assert count == 1
                    route.fulfill(response=response, body=body)
                context.route('**/src/services/apiFetch.ts*', external_origin)
                wake = [True]
                before_ready = []
                def warming_proxy(route):
                    path = route.request.url.split('/api', 1)[1]
                    if wake[0] and path != '/health':
                        before_ready.append(path)
                    proxy(route)
                context.route('https://fictional-api.example.invalid/api/**', warming_proxy)
                def first_wake_failure(route):
                    if wake[0]:
                        route.fulfill(status=503, json={'error': {'message': 'Synthetic cold start'}})
                    else:
                        proxy(route)
                context.route('https://fictional-api.example.invalid/api/health', first_wake_failure)
                page.reload()
                expect(page.get_by_role('alert')).to_contain_text('The workspace could not start')
                assert before_ready == []
                wake[0] = False
                page.get_by_role('button', name='Retry workspace connection').click()
                expect(page.get_by_role('heading', name='Document Vault', exact=True)).to_be_visible()
                checks.append('external API origin and cold-start retry gate avoid premature workspace requests')

            assert errors == [], errors
            checks.append('no uncaught browser runtime errors')
            browser.close()
        (out / 'browser.json').write_text(json.dumps({'passed': checks, 'liveFirebaseWrites': False, 'auth': 'synthetic SDK fixture', 'repository': 'production logic with in-memory Firestore adapter'}, indent=2))
        print(json.dumps({'passed': checks}), flush=True)
    finally:
        server.terminate()
        server.wait(timeout=10)
        log.close()


if __name__ == '__main__':
    main()
