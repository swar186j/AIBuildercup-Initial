#!/usr/bin/env python3
"""Real FastAPI + Chromium functional tests for Maadhyam M4-M6. No API mocks."""
import argparse, json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

PNG=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')
CASES=[]
def case(name):
    def decorate(fn): CASES.append((name,fn)); return fn
    return decorate

def require(ok, why):
    if not ok: raise AssertionError(why)

def plan_responses(page):
    out=[]
    def capture(response):
        if '/api/intelligence/passport-plan' in response.url and response.request.method=='POST':
            try: out.append({'request':response.request.post_data_json,'status':response.status,'response':response.json()})
            except Exception: pass
    page.on('response',capture)
    return out

def wait_plan(page,out):
    page.wait_for_function('() => !!document.querySelector("[aria-label=\'Personalized Passport checklist\'], [aria-label=\'Passport correction alternatives\']")',timeout=15000)
    page.wait_for_timeout(400)
    require(bool(out),'No real passport-plan API response captured')
    require(out[-1]['status']==200,f"passport-plan returned {out[-1]['status']}")
    return out[-1]

def upload(page,name):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files({'name':name,'mimeType':'image/png','buffer':PNG})
    page.get_by_text(name).first.wait_for(timeout=10000)

def edit(page,name,printed_name,holder=None):
    # Scope edit action to the uploaded document card when possible.
    row=page.locator('article').filter(has_text=name)
    buttons=row.get_by_role('button',name='Edit details')
    if buttons.count()!=1:
        buttons=page.get_by_role('button',name='Edit details')
    require(buttons.count()==1,f'Expected one Edit details button for {name}; got {buttons.count()}')
    buttons.click()
    dialog=page.get_by_role('dialog',name='Edit document details')
    dialog.wait_for()
    dialog.locator('#metadata-printed-name').fill(printed_name)
    if holder: dialog.locator('#metadata-holder').select_option(holder)
    dialog.get_by_role('button',name='Save details').click()
    dialog.wait_for(state='hidden')

def mark_reviewed(page,name):
    row=page.locator('article').filter(has_text=name)
    button=row.get_by_role('button',name='Mark self-reviewed')
    if button.count()!=1: button=page.get_by_role('button',name='Mark self-reviewed')
    require(button.count()==1,'Could not uniquely identify document review button')
    button.click()

@case('FF01 Fresh journey uses real API and displays every returned checklist label')
def fresh(page):
    out=plan_responses(page); page.goto('/services/passport/journey?type=fresh')
    result=wait_plan(page,out); data=result['response']['passportPlan']
    require(result['request']['assistanceType']=='fresh','Wrong scenario sent to backend')
    area=page.get_by_label('Personalized Passport checklist')
    for item in data['checklist']:
        require(area.get_by_text(item['label'],exact=True).count()>0,f"Missing checklist item: {item['id']}")
    require(data['officialEligibilityDetermined'] is False,'Backend incorrectly claims official eligibility')

@case('FF02 Reissue journey changes backend scenario and checklist')
def reissue(page):
    out=plan_responses(page); page.goto('/services/passport/journey?type=reissue')
    result=wait_plan(page,out); plan=result['response']['passportPlan']
    require(result['request']['assistanceType']=='reissue','Reissue request not sent')
    require(any(i['id']=='existing-passport' for i in plan['checklist']),'Reissue proof missing from API')
    require(page.get_by_label('Personalized Passport checklist').get_by_text(plan['scenarioTitle'],exact=False).count()>0,'Scenario title not rendered')

@case('FF03 Correction journey sends correction scenario')
def correction(page):
    out=plan_responses(page); page.goto('/services/passport/journey?type=correction')
    result=wait_plan(page,out)
    require(result['request']['assistanceType']=='correction','Correction request not sent')
    require(any(i['id']=='change-evidence' for i in result['response']['passportPlan']['checklist']),'Correction checklist missing')

@case('FF04 Empty Vault produces backend blockers rendered in journey')
def empty_vault(page):
    out=plan_responses(page); page.goto('/services/passport/journey?type=fresh')
    result=wait_plan(page,out)
    blockers=result['response']['passportPlan']['preparationBlockers']
    require('No reviewed applicant-held evidence' in blockers,'Backend missing empty-Vault blocker')
    section=page.get_by_label('Preparation blockers')
    for b in blockers: require(section.get_by_text(b,exact=True).count()>0,f'Blocker missing in UI: {b}')

@case('FF05 Planner reflects real API task count and blockers')
def planner(page):
    out=plan_responses(page); page.goto('/planner')
    page.get_by_text('Your next steps',exact=True).wait_for(timeout=15000)
    require(bool(out),'No real API response in planner')
    result=out[-1]; require(result['status']==200,'Planner API failed')
    data=result['response']; tasks=data['assessment']['tasks']
    require(len(tasks)>0,'No tasks in backend response')
    for task in tasks:
        require(page.get_by_role('heading',name=task['title'],exact=True).count()>0,f"Missing backend task: {task['id']}")
    for b in data['passportPlan']['preparationBlockers']:
        require(page.get_by_label('Preparation blockers').get_by_text(b,exact=True).count()>0,f'Planner blocker missing: {b}')

@case('FF06 Planner must not claim official acceptance or verified completion')
def no_false_claims(page):
    out=plan_responses(page); page.goto('/planner')
    page.get_by_text('Your next steps',exact=True).wait_for(timeout=15000)
    require(bool(out),'Planner did not call API')
    plan=out[-1]['response']['passportPlan']
    require(plan['officialEligibilityDetermined'] is False and plan['officialAcceptanceDetermined'] is False,'Unsafe official determination')
    require(all(not x['officialAcceptanceVerified'] for x in plan['checklist']),'Unsafe acceptance flag')
    require('not an official checklist' in page.locator('body').inner_text().lower(),'Missing user-facing official disclaimer')

@case('FF07 Unreviewed fictional upload cannot become accepted applicant evidence')
def unreviewed(page):
    upload(page,'fictional_pending_qa.png')
    # React Router navigation preserves the in-memory DocumentProvider.
    # page.goto() triggers a full reload and wipes the temporary Vault.
    out=plan_responses(page)
    page.get_by_role('link', name='Find Services').click()
    page.get_by_role('link', name='Explore Passport Seva').click()
    page.locator('a[href="/services/passport/journey?type=fresh"]').click()
    result=wait_plan(page,out)
    req=result['request']; require(len(req['documents'])==1,'Vault upload not sent to API after SPA navigation')
    require(req['documents'][0]['reviewed'] is False,'Unreviewed upload incorrectly marked reviewed')
    plan=result['response']['passportPlan']
    require(all(not x['candidateDocumentIds'] for x in plan['checklist']),'Unreviewed document matched as applicant evidence')
    require('Unreviewed applicant documents' in plan['preparationBlockers'],'Unreviewed blocker missing')
    require(page.get_by_label('Preparation blockers').get_by_text('Unreviewed applicant documents').count()>0,'Unreviewed blocker not visible')

@case('FF08 API failure displays actionable planner error, not stale success')
def failure_planner(page):
    page.route('**/api/intelligence/passport-plan',lambda route: route.abort('failed'))
    page.goto('/planner')
    alert=page.get_by_role('alert')
    alert.wait_for(timeout=12000)
    require('cannot reach' in alert.inner_text().lower(),'Planner did not show backend failure')
    require(page.get_by_text('Your next steps',exact=True).count()==0,'Planner showed stale plan despite failed API')

@case('FF09 API failure displays visible journey error')
def failure_journey(page):
    page.route('**/api/intelligence/passport-plan',lambda route: route.abort('failed'))
    page.goto('/services/passport/journey?type=fresh')
    page.get_by_role('alert').filter(has_text='Citizen intelligence is unavailable').wait_for(timeout=12000)
    require(page.get_by_label('Personalized Passport checklist').count()==0,'Journey displayed fake checklist on API failure')

@case('FF10 Planner correction alternatives match backend response')
def alternatives(page):
    out=plan_responses(page); page.goto('/planner')
    page.get_by_text('Your next steps',exact=True).wait_for(timeout=15000)
    data=out[-1]['response']['passportPlan']
    section=page.get_by_label('Passport correction alternatives')
    for option in data['resolutionOptions']:
        for alt in option['alternatives']:
            require(section.get_by_text(alt['label'],exact=True).count()>0,f"Missing correction alternative {alt['id']}")
    if not data['resolutionOptions']:
        require(section.get_by_text('No conflicting fields detected',exact=False).count()>0,'Missing empty-conflict explanation')


# Batch 2: additional real-browser tests. Each test gets a fresh browser context.
def spa_to_journey(page):
    page.get_by_role('link', name='Find Services').click()
    page.get_by_role('link', name='Explore Passport Seva').click()
    page.locator('a[href="/services/passport/journey?type=fresh"]').click()

def set_metadata(page, name, category='identity', document_type='Aadhaar card', holder='self'):
    row=page.locator('article').filter(has_text=name)
    row.get_by_role('button',name='Edit details').click()
    dialog=page.get_by_role('dialog',name='Edit document details')
    # Two supported Vault UIs: legacy category <select> and newer
    # multi-purpose category checkboxes. Do not assume either layout.
    category_select = dialog.locator('#metadata-category')
    if category_select.count():
        category_select.select_option(category, timeout=5000)
    else:
        labels = {
            'identity': 'Identity proof', 'address': 'Address proof',
            'birth': 'Date of birth', 'education': 'Education',
            'employment': 'Employment', 'other': 'Other / Unclassified',
        }
        category_label = labels[category]
        category_checkbox = dialog.get_by_role('checkbox', name=category_label)
        require(category_checkbox.count() == 1,
                f'Cannot find category selector or checkbox for {category_label}; '
                f'edit dialog controls: {dialog.locator("input, select").evaluate_all("els => els.map(e => ({tag:e.tagName,id:e.id,type:e.type}))")}')
        category_checkbox.check(timeout=5000)
    type_select = dialog.locator('#metadata-type')
    require(type_select.count() == 1, 'Document type selector missing from editor')
    type_select.select_option(label=document_type, timeout=5000)
    holder_select = dialog.locator('#metadata-holder')
    require(holder_select.count() == 1, 'Document holder selector missing from editor')
    holder_select.select_option(holder, timeout=5000)
    dialog.get_by_role('button',name='Save details').click()
    dialog.wait_for(state='hidden')

@case('FF11 Reviewed applicant document reaches Passport API with correct type and category')
def reviewed_metadata(page):
    upload(page,'fictional_aadhaar.png')
    set_metadata(page,'fictional_aadhaar.png')
    mark_reviewed(page,'fictional_aadhaar.png')
    out=plan_responses(page); spa_to_journey(page)
    result=wait_plan(page,out)
    doc=result['request']['documents'][0]
    require(doc['reviewed'] is True,'Review status lost across SPA navigation')
    require(doc['holder']=='self' and doc['documentType']=='Aadhaar card','Wrong applicant document metadata')
    require('identity' in doc['categories'],'Identity category lost')
    require(result['response']['assessment']['reviewedSelfDocuments']==1,'Backend did not count reviewed applicant evidence')

@case('FF12 Reviewed family-held document is excluded from applicant evidence')
def family_exclusion(page):
    upload(page,'fictional_guardian.png')
    set_metadata(page,'fictional_guardian.png',holder='parent-guardian')
    mark_reviewed(page,'fictional_guardian.png')
    out=plan_responses(page); spa_to_journey(page)
    result=wait_plan(page,out)
    require(result['request']['documents'][0]['holder']=='parent-guardian','Family holder lost')
    require(result['response']['assessment']['reviewedSelfDocuments']==0,'Family proof counted as self evidence')
    require(all(not item['candidateDocumentIds'] for item in result['response']['passportPlan']['checklist']),'Family document accepted as applicant evidence')

@case('FF13 Removing a reviewed document removes it from subsequent API payload')
def removal_propagates(page):
    upload(page,'fictional_remove.png')
    mark_reviewed(page,'fictional_remove.png')
    page.get_by_role('button',name='Remove fictional_remove.png').click()
    require(page.get_by_text('fictional_remove.png',exact=True).count()==0,'Removed document still listed')
    out=plan_responses(page); spa_to_journey(page)
    result=wait_plan(page,out)
    require(len(result['request']['documents'])==0,'Removed document leaked into Passport API')

@case('FF14 Unsupported executable upload is rejected and not sent to API')
def reject_executable(page):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files({'name':'not_a_document.exe','mimeType':'application/octet-stream','buffer':b'not an image'})
    require('only PDF, JPG and PNG' in page.locator('body').inner_text(),'Unsupported upload missing validation')
    require(page.get_by_text('No documents yet').count()>0,'Unsupported file added to Vault')

@case('FF15 Empty file upload is rejected')
def reject_empty(page):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files({'name':'empty.png','mimeType':'image/png','buffer':b''})
    require('empty files cannot be added' in page.locator('body').inner_text(),'Empty file validation missing')
    require(page.get_by_text('No documents yet').count()>0,'Empty file accepted')

@case('FF16 File above 10 MB is rejected')
def reject_large(page):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files({'name':'oversized.png','mimeType':'image/png','buffer':b'0'*(10*1024*1024+1)})
    require('exceeds the 10 MB limit' in page.locator('body').inner_text(),'File-size validation missing')
    require(page.get_by_text('No documents yet').count()>0,'Oversized file accepted')

@case('FF17 Review toggle is reversible and reaches API as unreviewed')
def review_toggle(page):
    upload(page,'fictional_toggle.png')
    mark_reviewed(page,'fictional_toggle.png')
    page.get_by_role('button',name='Mark for review').click()
    out=plan_responses(page); spa_to_journey(page)
    result=wait_plan(page,out)
    require(result['request']['documents'][0]['reviewed'] is False,'Review toggle did not revoke trust')
    require(result['response']['assessment']['reviewedSelfDocuments']==0,'Revoked review still counted')

@case('FF18 Vault search and review filter actually filter documents')
def vault_filter(page):
    upload(page,'fictional_alpha.png')
    page.get_by_label('Choose documents to add').set_input_files({'name':'fictional_beta.png','mimeType':'image/png','buffer':PNG})
    mark_reviewed(page,'fictional_alpha.png')
    page.get_by_label('Search documents').fill('alpha')
    require(page.locator('article').filter(has_text='fictional_alpha.png').count()==1,'Search omitted matching document')
    require(page.locator('article').filter(has_text='fictional_beta.png').count()==0,'Search failed to exclude other document')
    page.get_by_label('Search documents').fill('')
    page.get_by_role('button',name='Self-reviewed',exact=True).click()
    require(page.locator('article').filter(has_text='fictional_alpha.png').count()==1,'Reviewed filter omitted reviewed doc')
    require(page.locator('article').filter(has_text='fictional_beta.png').count()==0,'Reviewed filter included pending doc')

@case('FF19 Assistant uses real API with Gemini disabled by default and user prompt')
def assistant_local(page):
    page.goto('/documents')
    calls=[]
    def capture(response):
        if '/api/intelligence/chat' in response.url and response.request.method=='POST':
            try: calls.append((response.status,response.request.post_data_json,response.json()))
            except Exception: pass
    page.on('response',capture)
    page.get_by_role('button',name='Open Maadhyam AI').click()
    dialog=page.get_by_role('dialog',name='Maadhyam AI assistant')
    dialog.get_by_label('Message to Maadhyam AI').fill('How many documents do I have?')
    with page.expect_response(lambda response: '/api/intelligence/chat' in response.url and response.request.method == 'POST', timeout=15000):
        dialog.get_by_role('button',name='Send message').click()
    page.wait_for_timeout(250)
    require(bool(calls),'Assistant never sent request to real backend')
    status,req,response=calls[-1]
    require(status==200,'Local assistant backend failed')
    require(req['useGemini'] is False and req['fictionalDataConfirmed'] is False,'Gemini/consent enabled without user selection')
    require(req['question']=='How many documents do I have?','Prompt mutated in transit')
    require(bool(response.get('answer')),'Assistant returned empty answer')
    require(response['answer'] in dialog.inner_text(),'Assistant response not rendered')

@case('FF20 Assistant shows failure when backend unavailable')
def assistant_error(page):
    page.route('**/api/intelligence/chat',lambda route: route.abort('failed'))
    page.goto('/documents')
    page.get_by_role('button',name='Open Maadhyam AI').click()
    dialog=page.get_by_role('dialog',name='Maadhyam AI assistant')
    dialog.get_by_label('Message to Maadhyam AI').fill('Help with passport preparation')
    dialog.get_by_role('button',name='Send message').click()
    dialog.get_by_text('Assistant unavailable.',exact=False).wait_for(timeout=12000)
    require('Check backend connection' in dialog.inner_text(),'Assistant failure explanation missing')

@case('FF21 Assistant Clear chat removes earlier user messages')
def assistant_clear(page):
    page.goto('/documents')
    page.get_by_role('button',name='Open Maadhyam AI').click()
    dialog=page.get_by_role('dialog',name='Maadhyam AI assistant')
    dialog.get_by_label('Message to Maadhyam AI').fill('My unique test prompt 9017')
    dialog.get_by_role('button',name='Send message').click()
    dialog.get_by_text('My unique test prompt 9017').wait_for()
    dialog.get_by_role('button',name='Clear chat').click()
    require('My unique test prompt 9017' not in dialog.inner_text(),'Chat reset retained earlier user prompt')

@case('FF22 Preview opens and closes for fictional image')
def preview(page):
    upload(page,'fictional_preview.png')
    page.get_by_role('button',name='Preview',exact=True).click()
    dialog=page.get_by_role('dialog',name='Preview fictional_preview.png')
    dialog.wait_for()
    require(dialog.locator('img').count()==1,'Image preview missing')
    dialog.get_by_role('button',name='Close preview').click()
    dialog.wait_for(state='hidden')

# Known gaps are expected to fail until implemented; tracked separately from passing tests.
KNOWN_GAPS=[]
def gap(name):
    def decorate(fn): KNOWN_GAPS.append((name,fn)); return fn
    return decorate

@gap('GAP01 Vault has editable printed name and DOB for real mismatch detection')
def missing_identity_fields(page):
    upload(page,'fictional_identity.png')
    page.get_by_role('button',name='Edit details').click()
    dialog=page.get_by_role('dialog',name='Edit document details')
    require(dialog.locator('#metadata-printed-name').count()==1,'Missing printed name field: cannot create UI-level Aadhaar/PAN mismatch')
    require(dialog.locator('#metadata-date-of-birth').count()==1,'Missing DOB field: cannot test DOB conflict from UI')

@gap('GAP02 Vault metadata survives browser reload')
def missing_persistence(page):
    upload(page,'fictional_persistence.png')
    page.reload()
    require(page.get_by_text('fictional_persistence.png',exact=True).count()>0,'In-memory Vault lost on refresh')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-url',default='http://127.0.0.1:5173')
    ap.add_argument('--headed',action='store_true')
    ap.add_argument('--report',default='frontend-functional-results.json')
    args=ap.parse_args()
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=not args.headed)
        for name,fn in CASES:
            ctx=browser.new_context(base_url=args.base_url,viewport={'width':1440,'height':900})
            page=ctx.new_page(); started=time.monotonic()
            try:
                fn(page); r={'case':name,'status':'PASS','seconds':round(time.monotonic()-started,2)}
            except Exception as exc:
                r={'case':name,'status':'FAIL','seconds':round(time.monotonic()-started,2),'error':str(exc)[:2500]}
            print(f"{r['status']} {name}",flush=True)
            if r['status']=='FAIL': print('  '+r['error'].splitlines()[0],flush=True)
            results.append(r);ctx.close()
        # Known missing features are reported as XFAIL, not counted as passing.
        for name,fn in KNOWN_GAPS:
            ctx=browser.new_context(base_url=args.base_url,viewport={'width':1440,'height':900})
            page=ctx.new_page(); started=time.monotonic()
            try:
                fn(page)
                r={'case':name,'status':'XPASS','seconds':round(time.monotonic()-started,2),'error':'Known gap appears fixed; promote to regression test'}
            except Exception as exc:
                r={'case':name,'status':'XFAIL','seconds':round(time.monotonic()-started,2),'error':str(exc)[:2500]}
            print(f"{r['status']} {name}",flush=True)
            if r['status']=='XFAIL': print('  Known gap: '+r['error'].splitlines()[0],flush=True)
            results.append(r);ctx.close()
        browser.close()
    report={'suite':'Maadhyam Real-API Frontend Functional Extended','passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'known_gaps':sum(x['status']=='XFAIL' for x in results),'resolved_gaps':sum(x['status']=='XPASS' for x in results),'results':results}
    Path(args.report).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f"\n{report['passed']} passed, {report['failed']} failed, {report['known_gaps']} known gaps. Report: {Path(args.report).resolve()}",flush=True)
    return 1 if report['failed'] else 0
if __name__=='__main__':sys.exit(main())
