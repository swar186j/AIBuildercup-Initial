"""M5/M7/M8 completion tests. Reuse isolated real-browser/HTTP fixtures."""
import json
import re
import pytest
from playwright.sync_api import expect
from qa.test_browser import upload, spa, response_for, API, WEB


def new_preparation(page):
    if page.url.startswith(WEB):spa(page,'/applications')
    else:page.goto('/applications')
    page.get_by_role('button',name='Start new preparation',exact=True).click()
    record=page.get_by_role('dialog').locator('p').first.inner_text()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_label('Preparation save controls')).to_contain_text(record)
    return record


def test_m5_resume_edit_multiple(page):
    a=new_preparation(page)
    page.get_by_label('Applicant name',exact=True).fill('Fictional Rahul')
    page.get_by_label('Applicant date of birth (for document guidance)').fill('1998-06-15')
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('radio',name='An adult',exact=True).check()
    page.get_by_role('button',name='Save preparation',exact=True).click()
    spa(page,'/applications')
    article=page.locator('article').filter(has_text=a)
    article.get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_text('Step 2 of 4',exact=True)).to_be_visible()
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional Rahul')
    expect(page.get_by_role('radio',name='An adult',exact=True)).to_be_checked()
    expect(page.get_by_label('Applicant date of birth (for document guidance)')).to_have_value('1998-06-15')
    page.get_by_label('Applicant name',exact=True).fill('Edited Fictional Rahul')
    spa(page,'/applications')
    page.get_by_role('button',name='Start new preparation',exact=True).click()
    b=page.get_by_role('dialog').locator('p').first.inner_text();assert a!=b
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('')
    page.get_by_label('Applicant name',exact=True).fill('Independent Fictional Applicant')
    spa(page,'/applications')
    page.locator('article').filter(has_text=a).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Edited Fictional Rahul')
    assert page.evaluate("localStorage.getItem('maadhyam-preparations-v1')") is None
    spa(page,'/applications')
    storage=page.get_by_label('Preparation storage controls')
    storage.get_by_role('checkbox').check();storage.get_by_role('button',name='Enable preparation saving',exact=True).click()
    page.reload()
    for record,expected in [(a,'Edited Fictional Rahul'),(b,'Independent Fictional Applicant')]:
        page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
        page.get_by_role('link',name='Continue passport journey',exact=True).click()
        expect(page.get_by_label('Applicant name',exact=True)).to_have_value(expected)
        spa(page,'/applications')


@pytest.mark.parametrize('persist',[False,True])
def test_m5_reload_consent(page,persist):
    a=new_preparation(page)
    page.get_by_label('Applicant name',exact=True).fill('Fictional saved applicant')
    page.get_by_role('button',name='Continue',exact=True).click()
    spa(page,'/applications')
    control=page.get_by_label('Preparation storage controls')
    expect(control.get_by_role('button',name='Enable preparation saving',exact=True)).to_be_disabled()
    if persist:
        control.get_by_role('checkbox').check()
        control.get_by_role('button',name='Enable preparation saving',exact=True).click()
    page.reload()
    row=page.locator('article').filter(has_text=a)
    if persist:
        expect(row).to_be_visible()
        row.get_by_role('button',name='Continue preparation',exact=True).click()
        page.get_by_role('link',name='Continue passport journey',exact=True).click()
        expect(page.get_by_text('Step 2 of 4',exact=True)).to_be_visible()
        expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional saved applicant')
        spa(page,'/applications')
        page.get_by_role('button',name='Disable preparation saving and delete local copies',exact=True).click()
        assert page.evaluate("localStorage.getItem('maadhyam-preparations-v1')") is None
        page.reload();expect(page.locator('article').filter(has_text=a)).to_have_count(0)
    else: expect(row).to_have_count(0)

@pytest.mark.parametrize('value',['not-json','{"schemaVersion":0,"records":[]}','{"schemaVersion":1,"records":[{"id":"LOCAL-broken","journey":{}}]}'])
def test_m5_malformed_saved(page,value):
    page.goto('/applications')
    page.evaluate('v=>{localStorage.setItem("maadhyam-preparations-save-consent","yes");localStorage.setItem("maadhyam-preparations-v1",v)}',value)
    page.reload()
    expect(page.get_by_text('Saved preparations could not be restored',exact=False)).to_be_visible()
    page.get_by_role('button',name='Start new preparation',exact=True).click()
    expect(page.get_by_role('dialog')).to_be_visible()

@pytest.mark.parametrize('expiry,target,kind',[('2000-01-01','2099-02-01','already expired'),('2099-01-01','2099-02-01','expires before target'),('','2099-02-01','No expiry conflicts detected')])
def test_m7_expiry_ui(page,expiry,target,kind):
    page.goto('/documents');row=upload(page)
    row.get_by_role('button',name='Edit details').click()
    page.get_by_label('Document expiry date (optional)').fill(expiry)
    page.get_by_role('button',name='Save details',exact=True).click()
    spa(page,'/planner')
    payload,data=response_for(page,'/api/intelligence/reasoning',lambda:page.get_by_label('When do you want your documents ready?',exact=False).fill(target),lambda p:p.get('targetDate')==target)
    assert payload['documents'][0]['expiryDate']==expiry
    expect(page.get_by_label('Document expiry conflicts')).to_contain_text(kind)
    assert data['deadlineRescue']['officialDocumentValidityVerified'] is False

@pytest.mark.parametrize('changed',[False,True])
def test_m7_rule_comparison(page,changed):
    page.goto('/planner')
    area=page.get_by_label('Government rule change impact analyzer')
    expect(area.get_by_label('Stored baseline version')).to_be_visible()
    if changed:
        area.get_by_role('button',name='Create hypothetical comparison version').click()
        requirement=area.get_by_label('Proposed requirement address',exact=True)
        requirement.get_by_role('button',name='Remove Aadhaar card from address',exact=True).click()
        requirement.get_by_label('Requirement description').fill('Hypothetical changed address requirement')
        area.get_by_role('button',name='Add hypothetical requirement').click()
    payload,data=response_for(page,'/api/passport/rules/compare',lambda:area.get_by_role('button',name='Compare preparation impact',exact=True).click())
    assert data['changesDetected'] is changed
    assert not data['officialChangeVerified'] and not data['currentRulePackModified']
    result=page.get_by_label('Rule change comparison results')
    expect(result).to_contain_text('Potential changes to review' if changed else 'No rule differences detected')
    if changed:
        assert any('Aadhaar card' in c['removedProofTypes'] for c in data['changes'])
        expect(result).to_contain_text('Removed proof options: Aadhaar card')
        assert {c['changeType'] for c in data['changes']} >= {'added','modified'}

@pytest.mark.parametrize('mode',['missing-baseline','malformed-result','invalid-version'])
def test_m7_rule_errors(page,mode):
    if mode=='missing-baseline':page.route('**/api/passport/rules/versions',lambda r:r.fulfill(json={'versions':[]}))
    if mode=='malformed-result':page.route('**/api/passport/rules/compare',lambda r:r.fulfill(json={}))
    if mode=='invalid-version':page.route('**/api/passport/rules/compare',lambda r:r.fulfill(status=422,json={'error':{'message':'Unavailable version'}}))
    page.goto('/planner');area=page.get_by_label('Government rule change impact analyzer')
    if mode!='missing-baseline':area.get_by_role('button',name='Compare preparation impact',exact=True).click()
    expect(area.get_by_role('alert')).to_contain_text({'missing-baseline':'No complete comparison baseline','malformed-result':'Unexpected rule comparison','invalid-version':'version or comparison baseline'}[mode])

@pytest.mark.parametrize('priority',['cost','days'])
def test_m7_weighted_paths(page,priority):
    page.goto('/planner');area=page.get_by_label('Weighted correction optimizer')
    for key in ['cost','days','visits']:area.get_by_label('Priority for '+key,exact=True).fill('100' if key==priority else '0')
    payload,data=response_for(page,'/api/intelligence/advanced-plan',lambda:area.get_by_role('button',name='Find recommended path',exact=True).click())
    assert data['status']=='planned' and len(data['alternatives'])==1
    assert data['selectedOptions'][0]['label']==('Lower-cost evidence review' if priority=='cost' else 'Quicker review estimate')
    assert not data['officialAcceptanceVerified'] and payload['weights'][priority]==100
    expect(page.get_by_label('Correction optimization results')).to_contain_text(data['selectedOptions'][0]['label'])
    expect(page.get_by_label('Correction optimization results')).to_contain_text('Alternative paths and trade-offs')


def test_m7_optimizer_cycle_invalid(page):
    page.goto('/planner');area=page.get_by_label('Weighted correction optimizer')
    expect(area).to_be_visible()
    expect(area.locator('[aria-label^="Issue 1 option"]')).to_have_count(2)
    for option in area.locator('[aria-label^="Issue 1 option"]').all(): option.get_by_role('checkbox',name='Review identity details (self-dependency creates a cycle)',exact=True).check()
    payload,data=response_for(page,'/api/intelligence/advanced-plan',lambda:area.get_by_role('button',name='Find recommended path',exact=True).click())
    assert data['status']=='deadlock'
    expect(page.get_by_label('Correction optimization results')).to_contain_text('No feasible correction path')
    area.get_by_label('Priority for cost',exact=True).fill('-1')
    area.get_by_role('button',name='Find recommended path',exact=True).click()
    assert area.get_by_label('Priority for cost',exact=True).evaluate('e=>!e.checkValidity()')


def add_member(page,name,relation='parent'):
    page.get_by_label('New member name',exact=True).fill(name)
    page.get_by_label('New member relationship',exact=True).select_option(relation)
    page.get_by_role('button',name='Add member',exact=True).click()
    expect(page.get_by_label('Household member '+name,exact=True)).to_be_visible()


def associate(page,filename,member):
    area=page.get_by_label('Associate household evidence')
    area.get_by_label('Evidence document',exact=True).select_option(label=filename)
    area.get_by_label('Evidence owner',exact=True).select_option(label=member)
    expect(area.get_by_role('button',name='Associate evidence',exact=True)).to_be_disabled()
    area.get_by_role('checkbox').check()
    area.get_by_role('button',name='Associate evidence',exact=True).click()


def household_result(page):
    payload,data=response_for(page,'/api/household/assess',lambda:page.get_by_role('button',name='Analyze household dependencies',exact=True).click())
    expect(page.get_by_label('Household dependency graph',exact=True)).to_be_visible()
    return payload,data


def test_m8_members_ownership_dependencies(page):
    page.goto('/documents');upload(page);upload(page,'fictional_pan.png','Fictional Parent')
    spa(page,'/household')
    add_member(page,'Fictional Parent');add_member(page,'Fictional Spouse','spouse')
    associate(page,'fictional_aadhaar.png','Applicant (this workspace)')
    associate(page,'fictional_pan.png','Fictional Parent')
    page.get_by_label('Fictional Spouse depends on Fictional Parent',exact=True).check()
    page.get_by_label('Fictional Spouse requires fictional_pan.png',exact=True).check()
    payload,data=household_result(page)
    assert data['memberCount']==3 and data['documentCount']==2
    assert not data['officialRelationshipVerified'] and not data['crossAccountAuthorizationVerified']
    assert len(data['missingRelationshipEvidenceMemberIds'])==2
    parent=next(m for m in payload['members'] if m['label']=='Fictional Parent')
    applicant_docs=data['reviewedEvidenceByMember']['applicant']
    assert len(applicant_docs)==1 and set(applicant_docs).isdisjoint(data['reviewedEvidenceByMember'][parent['id']])
    graph=data['dependencyGraph'];order=graph['executionOrder']
    assert all(order.index(e['before'])<order.index(e['after']) for e in graph['edges'])
    expect(page.get_by_label('Household dependency graph',exact=True)).to_contain_text('Missing reviewed relationship evidence')
    page.get_by_label('Fictional Parent relationship evidence fictional_aadhaar.png',exact=True).check()
    _,data=household_result(page);assert len(data['missingRelationshipEvidenceMemberIds'])==1
    spa(page,'/planner')
    expect(page.get_by_text('2 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()
    spa(page,'/documents')
    row=page.locator('article').filter(has_text='fictional_pan.png');row.get_by_role('button',name='Edit details').click()
    expect(page.locator('#metadata-holder')).to_be_disabled()
    expect(page.locator('#metadata-holder')).to_have_value('parent-guardian')


def test_m8_cycle_edit_delete(page):
    page.goto('/documents');upload(page)
    spa(page,'/household');add_member(page,'Fictional Parent');associate(page,'fictional_aadhaar.png','Fictional Parent')
    page.get_by_label('Fictional Parent depends on Applicant (this workspace)',exact=True).check()
    page.get_by_label('Applicant (this workspace) depends on Fictional Parent',exact=True).check()
    _,data=household_result(page);assert data['dependencyGraph']['cycleOrBlockedNodeIds']
    expect(page.get_by_label('Household dependency graph',exact=True).get_by_role('alert')).to_contain_text('Circular')
    member=page.get_by_label('Household member Fictional Parent',exact=True)
    member.get_by_role('textbox').fill('Edited Fictional Parent')
    page.get_by_role('button',name='Remove member Edited Fictional Parent',exact=True).click()
    _,data=household_result(page)
    assert data['memberCount']==1 and data['documentCount']==0 and not data['dependencyGraph']['cycleOrBlockedNodeIds']
    spa(page,'/documents');row=page.locator('article').filter(has_text='fictional_aadhaar.png')
    expect(row).to_be_visible();row.get_by_role('button',name='Edit details').click()
    expect(page.locator('#metadata-holder')).to_have_value('other')
    page.get_by_role('button',name='Save details',exact=True).click()
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 0 reviewed self-held',exact=False)).to_be_visible()


def test_m8_session_isolation(page,browser):
    page.goto('/household');add_member(page,'Private Fictional Member')
    other=browser.new_context(base_url=WEB)
    try:
        p=other.new_page();p.goto('/household')
        expect(p.get_by_label('Household member Private Fictional Member',exact=True)).to_have_count(0)
    finally:other.close()
    page.reload();expect(page.get_by_label('Household member Private Fictional Member',exact=True)).to_have_count(0)


def test_cross_milestone_household_assistant(page):
    a=new_preparation(page);page.get_by_label('Applicant name',exact=True).fill('Fictional Rahul')
    spa(page,'/documents');upload(page)
    spa(page,'/planner');expect(page.get_by_text('1 uploaded · 1 reviewed self-held',exact=False)).to_be_visible()
    spa(page,'/household');add_member(page,'Fictional Parent');associate(page,'fictional_aadhaar.png','Fictional Parent');household_result(page)
    page.get_by_role('button',name='Open Maadhyam AI').click();dialog=page.get_by_role('dialog',name='Maadhyam AI assistant')
    dialog.get_by_label('Message to Maadhyam AI').fill('How many reviewed applicant documents do I have?')
    payload,data=response_for(page,'/api/intelligence/chat',lambda:dialog.get_by_role('button',name='Send message').click())
    assert payload['documents'][0]['holder']=='parent-guardian' and data['grounding']['reviewedApplicantDocumentIds']==[]
    expect(dialog.get_by_text(data['answer'],exact=True)).to_be_visible()


def test_m5_selected_type_and_delete(page):
    record=new_preparation(page)
    page.locator('a').filter(has_text='Reissuing an existing passport').click()
    expect(page.get_by_role('heading',name='Reissuing an existing passport',exact=True)).to_be_visible()
    spa(page,'/applications')
    row=page.locator('article').filter(has_text=record)
    expect(row.get_by_role('heading',name='Passport reissue preparation',exact=True)).to_be_visible()
    row.get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    expect(page.get_by_role('heading',name='Reissuing an existing passport',exact=True)).to_be_visible()
    spa(page,'/applications')
    page.locator('article').filter(has_text=record).get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('button',name='Delete this preparation',exact=True).click()
    expect(page.locator('article').filter(has_text=record)).to_have_count(0)

@pytest.mark.parametrize('path',['/planner','/household','/applications'])
def test_completion_mobile(page,path):
    page.set_viewport_size({'width':390,'height':900});page.goto(path)
    expect(page.locator('h1')).to_be_visible()
    if path=='/planner':expect(page.get_by_label('Weighted correction optimizer')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')

@pytest.mark.parametrize('endpoint,action,region',[
 ('/api/intelligence/advanced-plan','Find recommended path','Weighted correction optimizer'),
 ('/api/passport/rules/compare','Compare preparation impact','Government rule change impact analyzer'),
 ('/api/household/assess','Analyze household dependencies','Household members')])
def test_completion_unexpected_results(page,endpoint,action,region):
    page.route('**'+endpoint,lambda r:r.fulfill(json={'unexpected':True}))
    page.goto('/household' if '/household/' in endpoint else '/planner')
    page.get_by_role('button',name=action,exact=True).click()
    expect(page.get_by_role('alert').filter(has_text='Unexpected').first).to_be_visible()
    expect(page.get_by_role('button',name=action,exact=True)).to_be_enabled()


def test_m8_distinct_parents_do_not_compare_as_one_person(page):
    page.goto('/documents');upload(page,'fictional_parent_one.png','First Fictional Parent');upload(page,'fictional_parent_two.png','Second Fictional Parent')
    spa(page,'/household');add_member(page,'First Parent');add_member(page,'Second Parent')
    associate(page,'fictional_parent_one.png','First Parent');associate(page,'fictional_parent_two.png','Second Parent')
    spa(page,'/documents');page.get_by_role('button',name='Analyze documents',exact=True).click()
    expect(page.get_by_label('Document-by-document field comparison')).to_contain_text('0 same-holder document pairs')


def test_m8_remove_owned_dependency_safely(page):
    page.goto('/documents');upload(page)
    spa(page,'/household');add_member(page,'Fictional Parent');associate(page,'fictional_aadhaar.png','Fictional Parent')
    page.get_by_label('Applicant (this workspace) requires fictional_aadhaar.png',exact=True).check()
    page.get_by_role('button',name='Remove member Fictional Parent',exact=True).click()
    payload,data=household_result(page)
    assert payload['members'][0]['dependsOnDocumentIds']==[] and data['documentCount']==0
