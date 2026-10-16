"""Real Chromium acceptance. Run with apps/api/.venv/bin/python -m pytest qa/test_browser.py.
All API traffic goes to the dedicated no-credentials localhost API (8001).
Only provider failure/success cases explicitly stub the relevant endpoint.
"""
import importlib.util
import os
import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = Path(os.environ.get('MAADHYAM_QA_EVIDENCE',str(ROOT / 'qa/evidence/final/screenshots')))
EVIDENCE.mkdir(parents=True,exist_ok=True)
API = os.environ.get('MAADHYAM_TEST_API', 'http://127.0.0.1:8002')
WEB = os.environ.get('MAADHYAM_TEST_WEB', 'http://127.0.0.1:5173')
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')


def upload(page, name='fictional_aadhaar.png', printed='Rahul Kumar Sharma', holder='self', address='12 MG Road, Pune, Maharashtra', categories=('identity','address','birth')):
    page.get_by_label('Choose documents to add').set_input_files({'name':name,'mimeType':'image/png','buffer':PNG})
    row = page.locator('article').filter(has_text=name)
    row.get_by_role('button',name='Edit details').click()
    d = page.get_by_role('dialog',name='Edit document details')
    d.locator('#metadata-type').select_option(label='PAN card' if 'pan' in name else 'Aadhaar card')
    d.locator('#metadata-printed-name').fill(printed)
    d.locator('#metadata-dob').fill('1998-06-15')
    d.locator('#metadata-holder').select_option('category:' + holder)
    d.locator('#metadata-address').fill(address)
    labels={'identity':'Identity proof','address':'Address proof','birth':'Date of birth','other':'Other / Unclassified'}
    for key,label in labels.items():
        d.get_by_role('checkbox',name=label,exact=True).set_checked(key in categories)
    d.get_by_role('button',name='Save details').click()
    row.get_by_role('button',name='Mark self-reviewed').click()
    return row

def spa(page, path):
    if page.viewport_size['width'] < 1024:
        menu=page.get_by_role('button',name='Open navigation',exact=True)
        if menu.is_visible() and menu.get_attribute('aria-expanded')!='true':menu.click()
    page.locator(f'a[href="{path}"]').first.click()

def response_for(page, endpoint, action, want=lambda payload: True):
    with page.expect_response(lambda r: endpoint in r.url and r.request.method=='POST' and want(r.request.post_data_json)) as info:
        action()
    r=info.value
    assert r.status==200, r.text()
    data=r.json()
    page.evaluate('(x) => { window.__qaResponses = [...(window.__qaResponses || []), x] }', {'endpoint':endpoint,'request':r.request.post_data_json,'response':data})
    return r.request.post_data_json,data

@pytest.mark.parametrize('path,title', [('/',''),('/services','Find a government service'),('/documents','Document Vault'),('/applications','My Preparations'),('/planner','Resolution Planner'),('/workflows','Citizen workflow assistant'),('/services/passport',''),('/services/passport/journey?type=fresh','')])
@pytest.mark.parametrize('width',[1440,390])
def test_navigation(page,path,title,width):
    page.set_viewport_size({'width':width,'height':900})
    page.goto(path)
    expect(page.locator('h1')).to_be_visible()
    if title: expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
    page.evaluate("() => document.fonts.ready")
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal layout overflow'
    assert 'needs a refresh' not in page.locator('body').inner_text()

@pytest.mark.parametrize('path,eyebrow,title', [('/services','Service Navigator','Find a government service'),('/documents','Document workspace','Document Vault'),('/applications','Your preparation workspace','My Preparations'),('/workflows','Maadhyam · Guided preparation','Citizen workflow assistant')])
def test_hero(page,path,eyebrow,title):
    page.goto(path)
    header=page.locator('header').filter(has=page.get_by_role('heading',name=title,exact=True))
    expect(header.get_by_text(eyebrow,exact=True)).to_be_visible()
    assert header.evaluate('e => getComputedStyle(e).backgroundColor')=='rgb(27, 65, 104)'

def test_vault_review_session(page):
    page.goto('/documents')
    upload(page)
    spa(page,'/planner')
    expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()
    spa(page,'/documents')
    page.get_by_role('button',name='Edit details').first.click()
    expect(page.locator('#metadata-printed-name')).to_have_value('Rahul Kumar Sharma')
    page.get_by_role('button',name='Save details').click()
    page.reload()
    expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()
    assert page.evaluate("localStorage.getItem('maadhyam-vault-persist-opt-in')") is None

def test_vault_optin_clear(page):
    page.goto('/documents')
    page.get_by_role('button',name='Enable local saving').click()
    upload(page)
    page.reload()
    expect(page.get_by_text('fictional_aadhaar.png',exact=True).first).to_be_visible()
    page.once('dialog',lambda d:d.accept())
    page.get_by_role('button',name='Clear all Vault data').click()
    expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()

@pytest.mark.parametrize('name,mime,content,message', [('empty.png','image/png',b'','empty files'),('bad.exe','application/octet-stream',b'bad','only PDF'),('huge.png','image/png',b'0'*(10*1024*1024+1),'exceeds the 10 MB limit'),('malformed.png','image/png',b'not an image','contents do not match')], ids=['empty','unsupported','oversized','malformed'])
def test_vault_invalid(page,name,mime,content,message):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files({'name':name,'mimeType':mime,'buffer':content})
    expect(page.get_by_text(message,exact=False)).to_be_visible()
    expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()

@pytest.mark.parametrize('mode',['missing','success','malformed'])
def test_ocr(page,mode):
    page.goto('/documents')
    page.get_by_label('Choose documents to add').set_input_files(str(ROOT/'qa/fixtures/fictional_aadhaar.pdf'))
    if mode=='success':
        page.route('**/api/ai/extract-document', lambda r:r.fulfill(json={'documentType':'Aadhaar card','printedName':'Rahul Kumar Sharma','dateOfBirth':'1998-06-15','residentialAddress':'12 MG Road, Pune, Maharashtra','categories':['identity','address'],'warnings':['Fictional provider stub; verify manually.']}))
    if mode=='malformed': page.route('**/api/ai/extract-document',lambda r:r.fulfill(json={'unexpected':True}))
    page.get_by_role('button',name='AI extraction',exact=True).click()
    d=page.get_by_role('dialog',name='Document extraction preview')
    expect(d.get_by_role('button',name='Extract with Gemini')).to_be_disabled()
    d.get_by_role('checkbox').check()
    d.get_by_role('button',name='Extract with Gemini').click()
    if mode=='success':
        expect(d.get_by_role('button',name='Review & apply extracted details')).to_be_visible()
        d.get_by_role('button',name='Review & apply extracted details').click()
        page.get_by_role('button',name='Edit details').click()
        expect(page.locator('#metadata-printed-name')).to_have_value('Rahul Kumar Sharma')
        page.get_by_role('button',name='Save details').click()
    else:
        expect(d.get_by_role('alert')).to_contain_text('not configured' if mode=='missing' else 'Unexpected extraction response')
        d.get_by_role('button',name='Close AI extraction').click()
        expect(page.get_by_role('button',name='Edit details')).to_be_enabled()

@pytest.mark.parametrize('complete',[True,False])
def test_passport_guided(page,complete):
    page.goto('/documents')
    if complete:
        upload(page)
        upload(page,'fictional_pan.png',categories=('identity','birth'))
    spa(page,'/services')
    page.get_by_role('link',name='Explore Passport Seva').click()
    payload,data=response_for(page,'/api/passport/assess',lambda:page.locator('a[href="/services/passport/journey?type=fresh"]').click())
    expect(page.get_by_text('Guided Preparation',exact=True)).to_be_visible()
    assert page.locator('h1').bounding_box()['y'] < page.get_by_label('Passport document requirements').bounding_box()['y']
    payload,data=response_for(page,'/api/passport/assess',lambda:page.get_by_label('Applicant date of birth (for document guidance)').fill('1998-06-15'),lambda p:p.get('applicantDateOfBirth')=='1998-06-15')
    for step in range(3):
        for f in page.locator('fieldset').all():
            radios=f.locator('input[type=radio]')
            yes=f.locator('input[value=yes]')
            (yes if complete and yes.count() else radios.first).check()
        page.get_by_role('button',name='Continue',exact=True).click()
    expect(page.get_by_text('Preparation questionnaire completed',exact=True)).to_be_visible()
    area=page.get_by_label('Passport document requirements')
    expect(area.locator('article').first).to_be_visible()
    assert data['checks'] and isinstance(data['official_requirements_verified'],bool)
    assert any(c['id']=='dob-old' for c in data['checks']), 'Entered DOB did not reach the applicable checklist rule'
    for check in data['checks']:
        expect(area.get_by_role('heading',name=check['title'],exact=True)).to_be_visible()
        assert check['source_url'].startswith('https://') and check['source_id']
    assert len(payload['documents'])==(2 if complete else 0)
    if complete: assert payload['documents'][0]['reviewed']
    page.evaluate('window.scrollTo(0, 0)')
    page.screenshot(path=str(EVIDENCE/f'passport-completed-{complete}.png'),full_page=True,animations='disabled')
    page.get_by_role('button',name='Back',exact=True).click()
    assert page.locator('input[type=radio]:checked').count()>0
    page.reload()
    # An unsaved record's URL must not silently create a replacement after reload.
    expect(page.get_by_role('alert')).to_contain_text('could not be restored')

@pytest.mark.parametrize('count',[0,1,3])
def test_planner_documents(page,count):
    page.goto('/documents')
    if count: upload(page)
    if count>1:
        upload(page,'fictional_pan.png','Rahul K Sharma',categories=('identity',))
        upload(page,'fictional_address.png',address='45 FC Road, Pune, Maharashtra',categories=('address',))
    payload,data=response_for(page,'/api/intelligence/passport-plan',lambda:spa(page,'/planner'))
    expect(page.get_by_text('Your next steps',exact=True)).to_be_visible()
    assert len(payload['documents'])==count
    assert data['passportPlan']['officialAcceptanceDetermined'] is False
    if count>1:
        assert {f['field'] for f in data['assessment']['findings']} >= {'printedName','residentialAddress'}
    for task in data['assessment']['tasks']:
        expect(page.get_by_role('heading',name=task['title'],exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text('Your next steps',exact=True)).to_be_visible()

@pytest.mark.parametrize('endpoint,body', [('/api/intelligence/passport-plan',{}),('/api/intelligence/reasoning',{}),('/api/intelligence/reasoning',{'simulations':None}),('/api/intelligence/passport-plan',{'assessment':{'tasks':[{}]},'passportPlan':{}})])
def test_planner_unexpected(page,endpoint,body):
    page.route('**'+endpoint,lambda r:r.fulfill(json=body))
    page.goto('/planner')
    expect(page.get_by_role('heading',name='Resolution Planner',exact=True)).to_be_visible()
    assert 'needs a refresh' not in page.locator('body').inner_text(), 'Error boundary caught a render crash'
    expect(page.get_by_role('alert').first).to_be_visible()

@pytest.mark.parametrize('endpoint',['/api/intelligence/passport-plan','/api/intelligence/reasoning'])
def test_planner_api_failure(page,endpoint):
    page.route('**'+endpoint,lambda r:r.fulfill(status=503,json={'error':{'message':'Synthetic outage'}}))
    page.goto('/planner')
    expect(page.get_by_role('alert').first).to_be_visible()
    expect(page.get_by_role('heading',name='Resolution Planner',exact=True)).to_be_visible()

def test_reasoning_whatif_family(page):
    page.goto('/documents')
    upload(page)
    upload(page,'fictional_pan.png','Rahul K Sharma')
    upload(page,'fictional_parent.png','Fictional Parent',holder='parent-guardian')
    spa(page,'/planner')
    expect(page.get_by_label('Minimum prerequisite review path')).to_be_visible()
    for label in ['Dependency diagnostics','Alternative evidence candidates','Identity name variations','Address consistency','Visit preparation','Deadline planning']:
        expect(page.get_by_label(label,exact=True)).to_be_visible()
    expect(page.get_by_label('Identity name variations').get_by_text('Rahul Kumar Sharma',exact=True)).to_be_visible()
    expect(page.get_by_label('Identity name variations').get_by_text('Rahul K Sharma',exact=True)).to_be_visible()
    expect(page.get_by_label('Address consistency').get_by_text('12 MG Road, Pune, Maharashtra',exact=True)).to_be_visible()
    page.get_by_label('What-if document').select_option(label='fictional_pan.png')
    page.get_by_label('Hypothetical value').fill('Rahul Kumar Sharma')
    payload,data=response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_role('button',name='See the impact').click(),lambda p:bool(p.get('simulations')))
    assert 'printedName-conflict' in data['simulations'][0]['resolvedFindingIds']
    expect(page.get_by_text('Potentially resolved: printedName-conflict',exact=True)).to_be_visible()
    assert data['simulations'][0]['officialAcceptanceVerified'] is False
    page.get_by_role('button',name="I have a family member's document").click()
    page.get_by_label('Family document',exact=True).select_option(label='fictional_parent.png')
    payload,data=response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_role('button',name='Check relationship evidence').click(),lambda p:bool(p.get('familyLinks')))
    assert data['familyEvidence']['officialRelationshipVerified'] is False
    expect(page.get_by_text('Relationship and proof acceptance still require official verification.',exact=True)).to_be_visible()
    order=data['dependencyGraph']['executionOrder']
    for edge in data['dependencyGraph']['edges']:
        assert order.index(edge['before'])<order.index(edge['after'])

WORKFLOWS=[('human-support','Human assistance'),('life-event-discovery','Life-event discovery'),('multi-department-rules','Multi-department guidance'),('rejection-diagnosis','Rejection diagnosis'),('legacy-reconstruction','Legacy record recovery'),('authority-bottlenecks','Authority bottlenecks'),('deadline-rescue','Deadline rescue'),('visit-eliminator','Visit reduction planner')]
@pytest.mark.parametrize('key,title',WORKFLOWS)
@pytest.mark.parametrize('error',[False,True])
def test_citizen_workflow(page,key,title,error):
    page.goto('/workflows')
    page.get_by_role('button',name=title,exact=False).click()
    if key=='human-support': page.get_by_label('What problem are you facing?').fill('Fictional address proof was not accepted')
    if key=='rejection-diagnosis': page.get_by_label('What reason was given for rejection?').fill('Name mismatch in identity proof')
    if key=='legacy-reconstruction':
        page.get_by_label('What supporting records do you have?').fill('School record, hospital record')
        page.get_by_label('Original issuing office').fill('Fictional municipal office')
    if key=='deadline-rescue': page.get_by_label('What is your target date?').fill('2000-01-01')
    if error:
        page.route('**/api/citizen-workflows/'+key,lambda r:r.fulfill(status=503,json={'error':{'message':'Synthetic service unavailable'}}))
        page.get_by_role('button',name='Get my guidance').click()
        expect(page.get_by_role('alert')).to_contain_text('Service error (503)')
        expect(page.get_by_role('button',name='Get my guidance')).to_be_enabled()
    else:
        payload,data=response_for(page,'/api/citizen-workflows/'+key,lambda:page.get_by_role('button',name='Get my guidance').click())
        expect(page.get_by_role('heading',name='Your guidance',exact=True)).to_be_visible()
        assert data.get('disclaimer') and payload
        if key=='rejection-diagnosis': assert data['possibleCauses'][0]['category']=='identity_mismatch'
        if key=='deadline-rescue': assert data['deadlineAtRiskUnderAssumptions'] is True
        if key=='legacy-reconstruction': assert data['evidenceInventory']==['School record','hospital record'] and not data['documentReconstructed']
        if key=='authority-bottlenecks': assert data['executionOrder']==['s1','s2'] and data['estimatedCriticalPathDays']==7
        page.get_by_role('button',name='Show technical API response').click()
        assert json.loads(page.locator('pre').inner_text())==data
    assert page.locator('textarea[placeholder*="JSON"]').count()==0

@pytest.mark.parametrize('mode',['local','missing','429','timeout','malformed'])
def test_assistant(page,mode):
    page.goto('/documents')
    page.get_by_role('button',name='Open Maadhyam AI').click()
    d=page.get_by_role('dialog',name='Maadhyam AI assistant')
    expect(d.get_by_role('button',name='Send message')).to_be_disabled()
    if mode=='missing':
        d.get_by_label('Use Gemini (fictional demo metadata only)').check()
        d.get_by_label('Message to Maadhyam AI').fill('Help with missing evidence')
        expect(d.get_by_role('button',name='Send message')).to_be_disabled()
        d.get_by_label('Confirm all metadata is fictional').check()
    if mode=='429': page.route('**/api/intelligence/chat',lambda r:r.fulfill(status=429,json={'error':{'message':'Rate limited'}}))
    if mode=='timeout': page.route('**/api/intelligence/chat',lambda r:r.abort('timedout'))
    if mode=='malformed': page.route('**/api/intelligence/chat',lambda r:r.fulfill(json={}))
    d.get_by_label('Message to Maadhyam AI').fill('What evidence is missing?')
    d.get_by_role('button',name='Send message').click()
    if mode=='local': expect(d.get_by_text('cannot determine',exact=False).or_(d.get_by_text('review',exact=False)).last).to_be_visible()
    else: expect(d.get_by_text('Assistant unavailable.',exact=False)).to_be_visible()
    expect(d.get_by_label('Message to Maadhyam AI')).to_be_enabled()

def test_preparations_session_and_layout(page):
    page.goto('/applications')
    note=page.get_by_text('Preparation only:',exact=True)
    button=page.get_by_role('button',name='Start new preparation',exact=True)
    assert note.bounding_box()['x'] < button.bounding_box()['x']
    button.click()
    expect(page.get_by_text('New preparation draft created in this browser session.',exact=False)).to_be_visible()
    page.get_by_role('button',name='Close preparation details').click()
    spa(page,'/documents');spa(page,'/applications')
    expect(page.get_by_text('New passport preparation',exact=True).first).to_be_visible()
    page.reload()
    expect(page.get_by_text('New passport preparation',exact=True)).to_have_count(0)

@pytest.mark.parametrize('key,title,field,message',[
 ('human-support','Human assistance','What problem are you facing?','Please describe the problem'),
 ('rejection-diagnosis','Rejection diagnosis','What reason was given for rejection?','Please describe the rejection'),
 ('legacy-reconstruction','Legacy record recovery','Which old document do you need?','Please enter the document type'),
 ('deadline-rescue','Deadline rescue','What is your target date?','Choose a target date')])
def test_workflow_required_inputs(page,key,title,field,message):
    page.goto('/workflows')
    page.get_by_role('button',name=title,exact=False).click()
    page.get_by_label(field,exact=False).fill('')
    page.get_by_role('button',name='Get my guidance').click()
    expect(page.get_by_role('alert')).to_contain_text(message)

@pytest.mark.parametrize('kind',['aadhaar','pan','address'])
@pytest.mark.parametrize('extension',['pdf','png','jpg'])
def test_supported_fictional_documents(page,kind,extension):
    page.goto('/documents')
    filename=f'fictional_{kind}.{extension}'
    page.get_by_label('Choose documents to add').set_input_files(str(ROOT/'qa/fixtures'/filename))
    card=page.locator('article').filter(has_text=filename)
    expect(card).to_be_visible()
    card.get_by_role('button',name='Preview',exact=True).click()
    expect(page.get_by_role('dialog',name='Preview '+filename)).to_be_visible()
    page.get_by_role('button',name='Close preview',exact=True).click()


def test_assistant_reviewed_context(page):
    page.goto('/documents')
    upload(page)
    upload(page,'fictional_unreviewed.png','SECRET_UNREVIEWED')
    page.locator('article').filter(has_text='fictional_unreviewed.png').get_by_role('button',name='Mark for review').click()
    page.get_by_role('button',name='Open Maadhyam AI').click()
    d=page.get_by_role('dialog',name='Maadhyam AI assistant')
    d.get_by_label('Message to Maadhyam AI').fill('How many reviewed documents are present?')
    payload,data=response_for(page,'/api/intelligence/chat',lambda:d.get_by_role('button',name='Send message').click())
    assert len(data['grounding']['reviewedApplicantDocumentIds'])==1 and not data['grounding']['officiallyVerified']
    assert not payload['useGemini'] and not payload['fictionalDataConfirmed']
    expect(d.get_by_text(data['answer'],exact=True)).to_be_visible()

@pytest.mark.parametrize('field',['minimumCorrectionPath','identityEvolution','proofSubstitution','deadlockAnalysis','deadlineRescue'])
def test_planner_malformed_advanced_fields(page,field):
    data=page.request.post(API+'/api/intelligence/reasoning',data={'documents':[]}).json()
    data[field]={}
    page.route('**/api/intelligence/reasoning',lambda r:r.fulfill(json=data))
    page.goto('/planner')
    expect(page.get_by_role('alert').first).to_be_visible()
    expect(page.get_by_role('heading',name='Resolution Planner',exact=True)).to_be_visible()
    assert 'needs a refresh' not in page.locator('body').inner_text()
