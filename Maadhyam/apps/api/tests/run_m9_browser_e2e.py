#!/usr/bin/env python3
"""M9 real-browser, real-backend checks. Does NOT make paid Gemini calls.
Run from apps/api: uv run python -u tests/run_m9_browser_e2e.py
"""
import argparse
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

PNG=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')

def check(ok, reason):
    if not ok: raise AssertionError(reason)

def assistant(page):
    page.get_by_role('button',name='Open Maadhyam AI').click()
    return page.get_by_role('dialog',name='Maadhyam AI assistant')

def send(page, dialog, question):
    dialog.get_by_label('Message to Maadhyam AI').fill(question)
    with page.expect_response(lambda r: '/api/intelligence/chat' in r.url and r.request.method=='POST', timeout=20000) as response:
        dialog.get_by_role('button',name='Send message').click()
    result=response.value
    return result.request.post_data_json, result.json(), result.status

def upload_review(page, filename, name, reviewed=True):
    page.get_by_label('Choose documents to add').set_input_files({'name':filename,'mimeType':'image/png','buffer':PNG})
    page.get_by_text(filename).first.wait_for()
    row=page.locator('article').filter(has_text=filename)
    row.get_by_role('button',name='Edit details').click()
    dialog=page.get_by_role('dialog',name='Edit document details')
    dialog.locator('#metadata-printed-name').fill(name)
    dialog.get_by_role('button',name='Save details').click()
    dialog.wait_for(state='hidden')
    if reviewed:
        row.get_by_role('button',name='Mark self-reviewed').click()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--web',default='http://127.0.0.1:5173')
    parser.add_argument('--headed',action='store_true')
    parser.add_argument('--report',default='m9-browser-results.json')
    args=parser.parse_args()
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=not args.headed)
        def run(name,fn):
            ctx=browser.new_context(base_url=args.web,viewport={'width':1440,'height':900})
            page=ctx.new_page()
            try:
                page.goto('/documents')
                fn(page)
                print('PASS',name,flush=True)
                results.append({'case':name,'status':'PASS'})
            except Exception as exc:
                print('FAIL',name,'\n ',str(exc)[:450],flush=True)
                results.append({'case':name,'status':'FAIL','error':str(exc)[:1500]})
            finally: ctx.close()
        def consent(page):
            dialog=assistant(page)
            dialog.get_by_label('Use Gemini (fictional demo metadata only)').check()
            check(dialog.get_by_label('Confirm all metadata is fictional').is_visible(),'Consent control missing')
            dialog.get_by_label('Message to Maadhyam AI').fill('Help with passport')
            check(dialog.get_by_role('button',name='Send message').is_disabled(),'Gemini request not blocked before consent')
        run('M9B01 Gemini consent required before sending',consent)
        def reset_consent(page):
            dialog=assistant(page)
            dialog.get_by_label('Use Gemini (fictional demo metadata only)').check()
            dialog.get_by_label('Confirm all metadata is fictional').check()
            check(dialog.get_by_role('button',name='Send message').is_disabled(),'Empty prompt unexpectedly sendable')
            dialog.get_by_label('Message to Maadhyam AI').fill('Help with passport')
            check(dialog.get_by_role('button',name='Send message').is_enabled(),'Confirmed fictional consent did not enable send')
            dialog.get_by_label('Use Gemini (fictional demo metadata only)').uncheck()
            dialog.get_by_label('Use Gemini (fictional demo metadata only)').check()
            check(not dialog.get_by_label('Confirm all metadata is fictional').is_checked(),'Consent retained after toggle')
            check(dialog.get_by_role('button',name='Send message').is_disabled(),'Send allowed after consent reset')
        run('M9B02 Consent reset when Gemini mode toggled',reset_consent)
        def reviewed_context(page):
            upload_review(page,'fictional_self_reviewed.png','Rahul Kumar Sharma',True)
            upload_review(page,'fictional_unreviewed.png','SECRET_UNREVIEWED',False)
            dialog=assistant(page)
            req,res,status=send(page,dialog,'How many documents are in my vault?')
            check(status==200,'Local chat request failed')
            check(req['useGemini'] is False,'Gemini enabled without opt-in')
            check(len(req['documents'])==2,'Document metadata missing from chat request')
            check(res['grounding']['officiallyVerified'] is False,'Assistant claimed official verification')
            check(len(res['grounding']['reviewedApplicantDocumentIds'])==1,'Unreviewed document used as trusted evidence')
            check('2 documents' in res['answer'] and '1 reviewed applicant' in res['answer'],'Counts incorrect')
            dialog.get_by_text(res['answer'],exact=True).wait_for()
        run('M9B03 Reviewed Vault context reaches real local assistant',reviewed_context)
        def conflict(page):
            upload_review(page,'fictional_aadhaar.png','Rahul Kumar Sharma',True)
            upload_review(page,'fictional_pan.png','Rahul K Sharma',True)
            dialog=assistant(page)
            req,res,status=send(page,dialog,'Is there a name mismatch?')
            check(status==200,'Local chat request failed')
            check(any(x['id']=='printedName-conflict' for x in res['assessment']['findings']),'Name conflict missing')
            check('discrepanc' in res['answer'].lower(),'Conflict not explained')
            check(res['grounding']['officiallyVerified'] is False,'Official verification claimed')
            dialog.get_by_text(res['answer'],exact=True).wait_for()
        run('M9B04 Real UI name mismatch flows into grounded assistant',conflict)
        def clear(page):
            dialog=assistant(page)
            send(page,dialog,'My unique fictional question 7793')
            dialog.get_by_role('button',name='Clear chat').click()
            check('My unique fictional question 7793' not in dialog.inner_text(),'Chat history retained after clear')
            check(not dialog.get_by_label('Use Gemini (fictional demo metadata only)').is_checked(),'Gemini not reset')
        run('M9B05 Clear chat resets history and Gemini mode',clear)
        browser.close()
    report={'suite':'M9 browser real-API no-live-Gemini','passed':sum(x['status']=='PASS' for x in results),
            'failed':sum(x['status']=='FAIL' for x in results),'results':results}
    Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"\n{report['passed']} passed, {report['failed']} failed. Report: {Path(args.report).resolve()}",flush=True)
    return 1 if report['failed'] else 0

if __name__=='__main__': raise SystemExit(main())
