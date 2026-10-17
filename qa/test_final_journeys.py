"""Cross-feature journeys and failure regressions, using fictional local evidence only."""
import json
import re
import pytest
from playwright.sync_api import expect
from qa.test_browser import upload, spa, response_for, API, WORKFLOWS, EVIDENCE
from qa.test_completion import new_preparation, add_member, associate, household_result, fill_optimizer


def reopen(page, record):
    spa(page, '/applications')
    page.locator('article').filter(has_text=record).get_by_role('button', name=re.compile(r'^(Continue preparation|View preparation summary)$')).click()
    page.get_by_role('link', name=re.compile(r'^(Continue passport journey|View saved questionnaire)$')).click()
    expect(page.get_by_label('Preparation save controls')).to_contain_text(record)


def enable_preparations(page):
    area=page.get_by_label('Preparation storage controls')
    area.get_by_role('checkbox').check()
    area.get_by_role('button',name='Enable preparation saving',exact=True).click()


def test_journey_a_passport_full(page):
    page.goto('/')
    spa(page,'/services')
    page.get_by_role('link',name='Explore Passport Seva').click()
    page.locator('a[href="/services/passport/journey?type=fresh"]').click()
    expect(page.get_by_text('Guided Preparation',exact=True)).to_be_visible()
    page.wait_for_url('**/*preparation=*')
    url=page.url
    record=url.split('preparation=')[1]
    page.get_by_label('Applicant name',exact=True).fill('Fictional Journey Applicant')
    page.get_by_label('Applicant date of birth (for document guidance)').fill('1998-06-15')
    spa(page,'/documents');upload(page)
    page.locator(f'a[href="/services"]').first.click()
    # Reopen the existing record, retaining answers and explicitly choosing its evidence.
    spa(page,'/applications')
    page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    area=page.get_by_label('Preparation document references')
    payload,data=response_for(page,'/api/passport/assess',lambda:area.get_by_role('checkbox',name='fictional_aadhaar.png',exact=True).check(),lambda p:len(p['documents'])==1)
    assert payload['documents'][0]['reviewed'] and data['checks']
    for _ in range(3):
        for field in page.locator('fieldset').all():
            radios=field.locator('input[type=radio]')
            yes=field.locator('input[value=yes]')
            (yes if yes.count() else radios.first).check()
        page.get_by_role('button',name='Continue',exact=True).click()
    expect(page.get_by_text('Preparation questionnaire completed',exact=True)).to_be_visible()
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()
    reopen(page,record)
    page.get_by_role('button',name='Save preparation',exact=True).click()
    expect(page.get_by_text('Step 4 of 4',exact=True)).to_be_visible()
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional Journey Applicant')
    expect(page.get_by_label('Preparation document references').get_by_role('checkbox')).to_be_checked()


def test_m5_document_references_isolated_and_missing(page):
    page.goto('/documents');upload(page,'fictional_first.png')
    a=new_preparation(page)
    expect(page.get_by_label('Preparation document references').get_by_role('checkbox')).to_be_checked()
    spa(page,'/documents');upload(page,'fictional_second.png','Second Fictional Person')
    b=new_preparation(page)
    page.get_by_label('Preparation document references').get_by_role('checkbox',name='fictional_first.png',exact=True).uncheck()
    reopen(page,a)
    area=page.get_by_label('Preparation document references')
    expect(area.get_by_role('checkbox',name='fictional_first.png',exact=True)).to_be_checked()
    expect(area.get_by_role('checkbox',name='fictional_second.png',exact=True)).not_to_be_checked()
    spa(page,'/applications');enable_preparations(page)
    stored=page.evaluate('JSON.parse(localStorage.getItem("maadhyam-preparations-v1"))')
    records={r['id']:r['journey']['documentIds'] for r in stored['records']}
    assert len(records[a])==len(records[b])==1 and set(records[a]).isdisjoint(records[b])
    page.reload()
    page.locator('article').filter(has_text=a).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_text('saved document reference(s) are unavailable',exact=False)).to_be_visible()
    page.get_by_role('button',name='Remove unavailable references',exact=True).click()
    expect(page.get_by_text('saved document reference(s) are unavailable',exact=False)).to_have_count(0)


@pytest.mark.parametrize('invalid',['missing','deleted'])
def test_m5_invalid_deleted_id(page,invalid):
    record=new_preparation(page)
    if invalid=='deleted':
        spa(page,'/applications')
        page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
        page.get_by_role('button',name='Delete this preparation',exact=True).click()
    page.goto('/services/passport/journey?preparation='+('LOCAL-missing' if invalid=='missing' else record))
    expect(page.get_by_role('alert')).to_contain_text('could not be restored')
    expect(page.get_by_label('Preparation save controls')).to_have_count(0)
    expect(page.get_by_label('Applicant name',exact=True)).to_have_count(0)


def test_m5_repeated_create_click(page):
    page.goto('/applications')
    page.get_by_role('button',name='Start new preparation',exact=True).evaluate('b=>{b.click();b.click();b.click()}')
    page.get_by_role('button',name='Close preparation details',exact=True).click()
    assert page.locator('article').filter(has_text='LOCAL-').count()==1


@pytest.mark.parametrize('storage',['read-denied','write-denied','indexeddb'])
def test_storage_failure_usable_workspace(page,storage):
    if storage=='read-denied':page.add_init_script("Storage.prototype.getItem=()=>{throw new DOMException('Denied','SecurityError')}")
    if storage=='write-denied':page.add_init_script("Storage.prototype.setItem=()=>{throw new DOMException('Full','QuotaExceededError')}")
    if storage=='indexeddb':page.add_init_script("IDBFactory.prototype.open=()=>{throw new DOMException('Denied','SecurityError')}")
    page.goto('/documents');upload(page)
    if storage!='read-denied':page.get_by_role('button',name='Enable local saving',exact=True).click()
    expect(page.get_by_text('storage is unavailable' if storage!='indexeddb' else 'Local Vault save failed',exact=False)).to_be_visible()
    expect(page.get_by_role('button',name='Enable local saving',exact=True)).to_be_visible()
    spa(page,'/applications')
    if storage=='write-denied':
        enable_preparations(page)
        expect(page.get_by_text('Could not change local storage',exact=False)).to_be_visible()
    page.get_by_role('button',name='Start new preparation',exact=True).click()
    expect(page.get_by_role('dialog')).to_be_visible()


@pytest.mark.parametrize('body',[{}, {'checks':[{}]}, {'checks':None}])
def test_passport_malformed_response(page,body):
    page.route('**/api/passport/assess',lambda r:r.fulfill(json=body))
    new_preparation(page)
    expect(page.get_by_role('alert')).to_contain_text('Unexpected Passport assessment response')
    expect(page.get_by_label('Applicant name',exact=True)).to_be_enabled()


def test_journey_b_identity_whatif(page):
    page.goto('/documents');upload(page);upload(page,'fictional_pan.png','Rahul K Sharma')
    page.get_by_role('button',name='Analyze documents',exact=True).click()
    expect(page.get_by_label('Document-by-document field comparison')).to_contain_text('DIFFERENCE')
    spa(page,'/planner')
    expect(page.get_by_label('Identity name variations')).to_contain_text('Different name values')
    expect(page.get_by_label('Passport correction alternatives')).to_contain_text('Name on Document')
    page.get_by_label('What-if document').select_option(label='fictional_pan.png')
    page.get_by_label('Hypothetical value').fill('Rahul Kumar Sharma')
    _,data=response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_role('button',name='See the impact').click(),lambda p:bool(p.get('simulations')))
    assert data['simulations'][0]['resolvedFindingIds']==['printedName-conflict']
    assert not data['simulations'][0]['officialAcceptanceVerified']
    expect(page.get_by_text('Potentially resolved: Printed Name conflict',exact=True)).to_be_visible()


def test_journey_c_address_continuity(page):
    page.goto('/documents');upload(page,address='Fictional Pune');upload(page,'fictional_pan.png',address='Fictional Mumbai')
    spa(page,'/planner')
    expect(page.get_by_label('Address consistency')).to_contain_text('Different addresses')
    new_preparation(page)
    payload,data=response_for(page,'/api/passport/assess',lambda:page.get_by_label('Applicant date of birth (for document guidance)').fill('1998-06-15'),lambda p:p.get('applicantDateOfBirth')=='1998-06-15')
    assert len(payload['documents'])==2 and any('address' in c['id'] for c in data['checks'])
    spa(page,'/planner');expect(page.get_by_label('Passport correction alternatives')).to_contain_text('Residential Address')


def test_journey_d_deadline_dependencies_expiry(page):
    page.goto('/documents');row=upload(page)
    row.get_by_role('button',name='Edit details').click()
    page.get_by_label('Document expiry date (optional)').fill('2099-01-01')
    page.get_by_role('button',name='Save details',exact=True).click()
    spa(page,'/planner')
    _,data=response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_label('When do you want your documents ready?',exact=False).fill('2099-02-01'),lambda p:p.get('targetDate')=='2099-02-01')
    deadline=data['deadlineRescue']
    assert deadline['documentExpiryConflicts'] and deadline['resolutionOptions'][0]['prerequisiteTaskIds']
    expect(page.get_by_label('Document expiry conflicts')).to_contain_text('expires before target')
    area=page.get_by_label('Weighted correction optimizer')
    fill_optimizer(area)
    _,data=response_for(page,'/api/intelligence/advanced-plan',lambda:area.get_by_role('button',name='Find recommended path',exact=True).click())
    assert data['alternatives'] and not data['officialAcceptanceVerified']
    expect(page.get_by_label('Correction optimization results')).to_contain_text('Alternative paths')


def test_journey_e_household_consent_withdrawal(page):
    page.goto('/documents');upload(page)
    new_preparation(page)
    spa(page,'/household');add_member(page,'Fictional Parent');associate(page,'fictional_aadhaar.png','Fictional Parent')
    page.get_by_label('Applicant (this workspace) depends on Fictional Parent',exact=True).check()
    _,data=household_result(page)
    assert data['missingRelationshipEvidenceMemberIds'] and data['reviewedEvidenceByMember']['applicant']==[]
    page.get_by_role('button',name='Unassign fictional_aadhaar.png',exact=True).click()
    _,data=household_result(page);assert data['documentCount']==0
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 0 reviewed self-held',exact=False)).to_be_visible()
    spa(page,'/household');associate(page,'fictional_aadhaar.png','Applicant (this workspace)')
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()


def test_journey_f_rule_saved_preparation(page):
    record=new_preparation(page)
    page.get_by_label('Applicant name',exact=True).fill('Fictional rule applicant')
    spa(page,'/planner');area=page.get_by_label('Government rule change impact analyzer')
    area.get_by_label('Preparation to review').select_option(record)
    area.get_by_role('button',name='Create hypothetical comparison version').click()
    area.get_by_label('Proposed requirement address',exact=True).get_by_role('button',name='Remove requirement',exact=True).click()
    _,data=response_for(page,'/api/passport/rules/compare',lambda:area.get_by_role('button',name='Compare preparation impact',exact=True).click())
    assert any(c['changeType']=='removed' for c in data['changes'])
    assert not data['officialChangeVerified'] and not data['currentRulePackModified']
    expect(area).to_contain_text('hypothetical, unverified')
    reopen(page,record);expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional rule applicant')


def test_journey_g_assistant_grounding_provider_failure(page):
    page.goto('/documents');upload(page)
    spa(page,'/household');add_member(page,'Fictional Parent')
    spa(page,'/documents');upload(page,'fictional_parent.png','Private Fictional Parent',holder='parent-guardian')
    spa(page,'/household');associate(page,'fictional_parent.png','Fictional Parent')
    page.get_by_role('button',name='Open Maadhyam AI').click()
    d=page.get_by_role('dialog',name='Maadhyam AI assistant')
    d.get_by_label('Message to Maadhyam AI').fill('What should I prepare?')
    _,data=response_for(page,'/api/intelligence/chat',lambda:d.get_by_role('button',name='Send message').click())
    assert len(data['grounding']['reviewedApplicantDocumentIds'])==1 and not data['grounding']['officiallyVerified']
    expect(d.get_by_text(data['answer'],exact=True)).to_be_visible()
    page.route('**/api/intelligence/chat',lambda r:r.fulfill(status=503,json={'error':{'message':'Fictional provider unavailable'}}))
    d.get_by_label('Message to Maadhyam AI').fill('Help me again')
    d.get_by_role('button',name='Send message').click()
    expect(d.get_by_text('Assistant unavailable',exact=False)).to_be_visible()
    d.get_by_label('Message to Maadhyam AI').fill('Retry local guidance')
    expect(d.get_by_role('button',name='Send message')).to_be_enabled()


def fill_workflow(page,key):
    if key=='human-support':page.get_by_label('What problem are you facing?').fill('Fictional address evidence needs review')
    if key=='rejection-diagnosis':page.get_by_label('What reason was given for rejection?').fill('Name mismatch in identity proof')
    if key=='legacy-reconstruction':page.get_by_label('What supporting records do you have?').fill('Fictional school record')
    if key=='deadline-rescue':page.get_by_label('What is your target date?').fill('2099-02-01')


def test_journey_h_all_workflows_mobile(page):
    page.set_viewport_size({'width':390,'height':900})
    record=new_preparation(page);page.get_by_label('Applicant name',exact=True).fill('Fictional untouched preparation')
    spa(page,'/workflows')
    for key,title in WORKFLOWS:
        page.get_by_role('button',name=title,exact=False).click();fill_workflow(page,key)
        payload,data=response_for(page,'/api/citizen-workflows/'+key,lambda:page.get_by_role('button',name='Get my guidance').click())
        assert payload and data['disclaimer']
        expect(page.get_by_role('heading',name='Your guidance',exact=True)).to_be_visible()
        page.get_by_role('button',name='Show technical API response').click()
        assert json.loads(page.locator('pre').inner_text())==data
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(EVIDENCE/f'mobile-workflow-{key}.png'),full_page=True,animations='disabled')
    reopen(page,record)
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional untouched preparation')


@pytest.mark.parametrize('key,title',WORKFLOWS)
@pytest.mark.parametrize('mode',['malformed','invalid-input','loading-retry'])
def test_workflow_contract_error_retry(page,key,title,mode):
    page.goto('/workflows');page.get_by_role('button',name=title,exact=False).click();fill_workflow(page,key)
    held=[]
    def intercept(route):
        if mode=='loading-retry':
            held.append(route)
            page.evaluate('window.__qaHeld=true')
        else:route.fulfill(status=422 if mode=='invalid-input' else 200,json={'unexpected':True})
    page.route('**/api/citizen-workflows/'+key,intercept)
    page.get_by_role('button',name='Get my guidance').click()
    if mode=='loading-retry':
        expect(page.get_by_role('button',name='Preparing guidance…')).to_be_disabled()
        page.wait_for_function('window.__qaHeld===true')
        held[0].fulfill(response=held[0].fetch())
        expect(page.get_by_role('heading',name='Your guidance',exact=True)).to_be_visible()
    else:expect(page.get_by_role('alert')).to_contain_text('invalid' if mode=='invalid-input' else 'Unexpected response')
    page.unroute('**/api/citizen-workflows/'+key,intercept)
    response_for(page,'/api/citizen-workflows/'+key,lambda:page.get_by_role('button',name='Get my guidance').click())
    expect(page.get_by_role('heading',name='Your guidance',exact=True)).to_be_visible()


def test_household_stale_response_after_edit(page):
    page.goto('/household');add_member(page,'Fictional stale member')
    held=[]
    def hold(r):
        held.append(r);page.evaluate('window.__qaHeld=true')
    page.route('**/api/household/assess',hold)
    page.get_by_role('button',name='Analyze household dependencies',exact=True).click()
    expect(page.get_by_role('button',name='Analyzing household…')).to_be_disabled()
    page.get_by_label('Household member Fictional stale member',exact=True).get_by_role('textbox').fill('Edited Fictional Member')
    page.wait_for_function('window.__qaHeld===true')
    with page.expect_response(lambda r:'/api/household/assess' in r.url):held[0].fulfill(response=held[0].fetch())
    expect(page.get_by_role('button',name='Analyze household dependencies',exact=True)).to_be_enabled()
    expect(page.get_by_label('Household dependency graph',exact=True)).to_have_count(0)
    page.unroute('**/api/household/assess')
    _,data=household_result(page)
    assert any(n['label']=='Edited Fictional Member' for n in data['dependencyGraph']['nodes'])


def test_workflow_stale_response_after_switch(page):
    page.goto('/workflows');fill_workflow(page,'human-support')
    held=[]
    def hold(r):
        held.append(r);page.evaluate('window.__qaHeld=true')
    page.route('**/api/citizen-workflows/human-support',hold)
    page.get_by_role('button',name='Get my guidance').click()
    expect(page.get_by_role('button',name='Preparing guidance…')).to_be_disabled()
    page.wait_for_function('window.__qaHeld===true')
    page.get_by_role('button',name='Life-event discovery',exact=False).click()
    with page.expect_response(lambda r:'/api/citizen-workflows/human-support' in r.url):held[0].fulfill(response=held[0].fetch())
    response_for(page,'/api/citizen-workflows/life-event-discovery',lambda:page.get_by_role('button',name='Get my guidance').click())
    expect(page.get_by_text('possible service(s) found',exact=False)).to_be_visible()
    expect(page.get_by_text('helpdesk conversation. No human agent',exact=False)).to_have_count(0)


def test_m7_malformed_expiry_conflict(page):
    data=page.request.post(API+'/api/intelligence/reasoning',data={'documents':[]}).json()
    data['deadlineRescue']['documentExpiryConflicts']=[{'type':{},'documentId':'fictional'}]
    page.route('**/api/intelligence/reasoning',lambda r:r.fulfill(json=data))
    page.goto('/planner');expect(page.get_by_role('alert').first).to_be_visible()
    assert 'needs a refresh' not in page.locator('body').inner_text()


@pytest.mark.parametrize('which',['preparations','vault-edit','vault-preview','vault-ocr'])
def test_keyboard_modal_focus_escape(page,which):
    if which=='preparations':
        page.goto('/applications')
        opener=page.get_by_role('button',name='Start new preparation',exact=True);opener.click()
    else:
        page.goto('/documents');row=upload(page)
        opener=row.get_by_role('button',name={'vault-edit':'Edit details','vault-preview':'Preview','vault-ocr':'AI extraction'}[which],exact=True)
        opener.click()
    d=page.get_by_role('dialog')
    expect(d).to_be_visible()
    assert d.evaluate('d=>d.contains(document.activeElement)')
    page.keyboard.press('Shift+Tab')
    assert d.evaluate('d=>d.contains(document.activeElement)')
    page.keyboard.press('Tab')
    assert d.evaluate('d=>d.contains(document.activeElement)')
    page.keyboard.press('Escape')
    expect(d).to_have_count(0)
    expect(opener).to_be_focused()


def test_assistant_focus_escape_and_stale_reset(page):
    page.goto('/documents')
    opener=page.get_by_role('button',name='Open Maadhyam AI',exact=True);opener.click()
    d=page.get_by_role('dialog',name='Maadhyam AI assistant')
    expect(d.get_by_label('Message to Maadhyam AI')).to_be_focused()
    held=[]
    def hold(r):held.append(r);page.evaluate('window.__qaHeld=true')
    page.route('**/api/intelligence/chat',hold)
    d.get_by_label('Message to Maadhyam AI').fill('Fictional request before clearing')
    d.get_by_role('button',name='Send message').click()
    page.wait_for_function('window.__qaHeld===true')
    d.get_by_role('button',name='Clear chat',exact=True).click()
    with page.expect_response(lambda r:'/api/intelligence/chat' in r.url):held[0].fulfill(json={'answer':'STALE_FICTIONAL_REPLY'})
    # A second real request proves that the released reply and its callbacks settled.
    page.unroute('**/api/intelligence/chat',hold)
    d.get_by_label('Message to Maadhyam AI').fill('New fictional request')
    _,data=response_for(page,'/api/intelligence/chat',lambda:d.get_by_role('button',name='Send message').click())
    expect(d.get_by_text(data['answer'],exact=True)).to_be_visible()
    expect(d.get_by_text('STALE_FICTIONAL_REPLY',exact=True)).to_have_count(0)
    page.keyboard.press('Escape');expect(d).to_have_count(0)
    expect(page.get_by_role('button',name='Open Maadhyam AI',exact=True)).to_be_focused()


def test_m5_both_persistence_consents_and_delete_reload(page):
    page.goto('/documents');page.get_by_role('button',name='Enable local saving',exact=True).click();upload(page)
    record=new_preparation(page)
    page.get_by_label('Applicant name',exact=True).fill('Fictional Persistent Applicant')
    spa(page,'/applications');enable_preparations(page)
    page.reload()
    page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_label('Preparation document references').get_by_role('checkbox')).to_be_checked()
    expect(page.get_by_text('saved document reference(s) are unavailable',exact=False)).to_have_count(0)
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional Persistent Applicant')
    spa(page,'/applications')
    page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('button',name='Delete this preparation',exact=True).click()
    page.reload();expect(page.locator('article').filter(has_text=record)).to_have_count(0)
    spa(page,'/documents');expect(page.get_by_text('fictional_aadhaar.png',exact=True).first).to_be_visible()


def test_m8_owned_payloads_passport_planner_family(page):
    page.goto('/documents');upload(page,'fictional_applicant.png');upload(page,'fictional_parent.png','Private Fictional Parent')
    record=new_preparation(page)
    spa(page,'/household');add_member(page,'Fictional Parent');associate(page,'fictional_parent.png','Fictional Parent')
    _,graph=household_result(page)
    assert len(graph['missingRelationshipEvidenceMemberIds'])==1
    payload,data=response_for(page,'/api/intelligence/passport-plan',lambda:spa(page,'/planner'))
    assert all(d['printedName']!='Private Fictional Parent' for d in payload['documents'])
    assert data['assessment']['reviewedSelfDocuments']==1
    reopen(page,record)
    payload,data=response_for(page,'/api/passport/assess',lambda:page.get_by_label('Applicant date of birth (for document guidance)').fill('1998-06-15'),lambda p:p.get('applicantDateOfBirth')=='1998-06-15')
    parent=next(d for d in payload['documents'] if d['printedName']=='Private Fictional Parent')
    assert parent['holder']=='parent-guardian' and parent['associationConsent']
    assert all(parent['id'] not in c['matching_document_ids'] for c in data['checks'] if c['id'] in ['identity','dob-old'])
    address=next(c for c in data['checks'] if c['id']=='address')
    if parent['id'] in address['matching_document_ids']:assert 'not applicant identity evidence' in address['reason']


@pytest.mark.parametrize('target,expected',[('2099-01-01','expires on target'),('2098-01-01','No expiry conflicts detected')])
def test_m7_expiry_on_after_target(page,target,expected):
    page.goto('/documents');row=upload(page)
    row.get_by_role('button',name='Edit details').click();page.get_by_label('Document expiry date (optional)').fill('2099-01-01')
    page.get_by_role('button',name='Save details',exact=True).click();spa(page,'/planner')
    response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_label('When do you want your documents ready?',exact=False).fill(target),lambda p:p.get('targetDate')==target)
    expect(page.get_by_label('Document expiry conflicts')).to_contain_text(expected)


@pytest.mark.parametrize('endpoint,body,action',[
    ('/api/intelligence/advanced-plan',{'status':'deadlock','candidatePathsEvaluated':0,'message':{}},'Find recommended path'),
    ('/api/household/assess',{'memberCount':1,'dependencyGraph':{'nodes':[None]}},'Analyze household dependencies'),
])
def test_nested_invalid_results_recover(page,endpoint,body,action):
    page.route('**'+endpoint,lambda r:r.fulfill(json=body))
    page.goto('/household' if 'household' in endpoint else '/planner')
    if 'advanced-plan' in endpoint:fill_optimizer(page.get_by_label('Weighted correction optimizer'))
    page.get_by_role('button',name=action,exact=True).click()
    expect(page.get_by_role('alert').filter(has_text='Unexpected').first).to_be_visible()
    expect(page.get_by_role('button',name=action,exact=True)).to_be_enabled()


def test_session_clear_when_indexeddb_denied(page):
    page.add_init_script("IDBFactory.prototype.open=()=>{throw new DOMException('Denied','SecurityError')}")
    page.goto('/documents');upload(page)
    page.once('dialog',lambda d:d.accept())
    page.get_by_role('button',name='Clear local browser Vault copies',exact=True).click()
    expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()
    expect(page.get_by_role('alert')).to_contain_text('browser-local deletion failed')


def test_m5_saved_service_not_overwritten_by_missing_url_type(page):
    record=new_preparation(page)
    page.locator('a').filter(has_text='Reissuing an existing passport').click()
    spa(page,'/applications');enable_preparations(page)
    page.goto('/services/passport/journey?preparation='+record)
    expect(page.get_by_role('heading',name='Reissuing an existing passport',exact=True)).to_be_visible()
    spa(page,'/applications')
    expect(page.locator('article').filter(has_text=record)).to_contain_text('Passport reissue preparation')


def test_m6_old_plan_hidden_while_evidence_changes(page):
    page.goto('/documents');upload(page)
    spa(page,'/household');add_member(page,'Fictional Parent')
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()
    spa(page,'/household');associate(page,'fictional_aadhaar.png','Fictional Parent')
    held=[]
    def hold(r):held.append(r);page.evaluate('window.__qaHeld=true')
    page.route('**/api/intelligence/passport-plan',hold)
    spa(page,'/planner');page.wait_for_function('window.__qaHeld===true')
    expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_have_count(0)
    expect(page.get_by_text('Building your plan…',exact=True)).to_be_visible()
    held[0].fulfill(response=held[0].fetch())
    expect(page.get_by_text('1 uploaded · 0 reviewed self-held',exact=False)).to_be_visible()


def test_m5_future_birth_date_not_saved(page):
    record=new_preparation(page)
    page.get_by_label('Applicant date of birth (for document guidance)').fill('2099-01-01')
    expect(page.get_by_role('button',name='Save preparation',exact=True)).to_be_disabled()
    expect(page.get_by_text('Enter a valid birth date',exact=False)).to_be_visible()
    reopen(page,record)
    expect(page.get_by_label('Applicant date of birth (for document guidance)')).to_have_value('')
