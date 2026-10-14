#!/usr/bin/env python3
"""Real browser + real backend checks. No API mocking. Use fictional documents only."""
import json
from playwright.sync_api import sync_playwright
PNG=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
BASE='http://127.0.0.1:5173'

def upload(page,name,doc_type,printed_name,dob):
    page.get_by_label('Choose documents to add').set_input_files({'name':name,'mimeType':'image/png','buffer':PNG})
    card=page.locator('article').filter(has_text=name)
    card.wait_for(timeout=10000)
    card.get_by_role('button',name='Edit details').click()
    modal=page.get_by_role('dialog',name='Edit document details')
    modal.locator('#metadata-type').select_option(label=doc_type)
    modal.locator('#metadata-printed-name').fill(printed_name)
    modal.locator('#metadata-dob').fill(dob)
    modal.get_by_role('button',name='Save details').click()
    card.get_by_role('button',name='Mark self-reviewed').click()

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        context=browser.new_context(base_url=BASE)
        page=context.new_page()
        failures=[]
        def run(name,fn):
            try: fn(); print('PASS',name,flush=True)
            except Exception as e: failures.append(name); print('FAIL',name,str(e)[:300],flush=True)
        def setup():
            page.goto('/documents')
            page.get_by_role('button',name='Enable local saving').click()
            upload(page,'fictional_aadhaar.png','Aadhaar card','Rahul Kumar Sharma','2000-05-12')
            upload(page,'fictional_pan.png','PAN card','Rahul K Sharma','2000-05-12')
        run('VE01 Metadata editor creates reviewed fictional Aadhaar and PAN',setup)
        def api_check():
            captures=[]
            def capture(r):
                if '/api/intelligence/passport-plan' in r.url and r.request.method=='POST':
                    captures.append((r.request.post_data_json,r.json()))
            page.on('response',capture)
            # SPA route to retain in-memory context
            page.get_by_role('link',name='Services').first.click() if page.get_by_role('link',name='Services').count() else None
            page.goto('/services/passport/journey?type=fresh')
            page.get_by_label('Personalized Passport checklist').wait_for(timeout=15000)
            assert captures, 'No passport-plan API request'
            docs=captures[-1][0]['documents']
            assert len(docs)==2, f'Expected 2 reviewed docs; got {len(docs)}'
            assert {d['printedName'] for d in docs}=={'Rahul Kumar Sharma','Rahul K Sharma'}
            assert all(d['dateOfBirth']=='2000-05-12' and d['reviewed'] for d in docs)
            findings=captures[-1][1]['assessment']['findings']
            assert any(f['field']=='printedName' for f in findings), f'Name conflict not detected: {findings}'
        # Full reload is safe here only because local persistence was explicitly enabled.
        run('VE02 Real Passport API detects reviewed name conflict',api_check)
        def refresh_check():
            page.goto('/documents'); page.reload()
            page.get_by_text('fictional_aadhaar.png').first.wait_for(timeout=10000)
            page.get_by_text('fictional_pan.png').first.wait_for(timeout=10000)
            assert page.get_by_role('button',name='Disable local saving').count()==1
        run('VE03 Opt-in IndexedDB restores files and metadata after reload',refresh_check)
        def clear_check():
            page.once('dialog',lambda d:d.accept())
            page.get_by_role('button',name='Clear all Vault data').click()
            page.reload()
            assert page.get_by_text('fictional_aadhaar.png').count()==0
            assert page.get_by_text('fictional_pan.png').count()==0
        run('VE04 Clear all deletes persisted documents',clear_check)
        context.close();browser.close()
        print(f'{4-len(failures)} passed, {len(failures)} failed',flush=True)
        raise SystemExit(1 if failures else 0)
if __name__=='__main__':main()
