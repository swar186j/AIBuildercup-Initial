"""M12.1 fictional browser regressions. All persistence requests intercepted locally."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import pytest
from playwright.sync_api import expect
from qa.test_remediation import mocked_auth, cloud_record
from qa.test_completion import add_member, fill_optimizer
from qa.test_browser import spa, response_for
from qa.test_m12_persistence import mock_vault


def household_api(page, fail=None, hold=False, records=None):
    mocked_auth(page)
    records=records if records is not None else {}
    writes=[]; held=[]
    def ack(route):
        body=route.request.post_data_json
        key=body.get('client_id') or route.request.url.rsplit('/',1)[-1]
        record=records.get(key,cloud_record(key))
        record.update({k:v for k,v in body.items() if k not in ('client_id','revision')})
        record['revision']+=1;record['lastSavedAt']='2026-10-17T10:30:00Z';record['updated_at']=record['lastSavedAt']
        records[key]=record
        route.fulfill(json=record)
    def api(route):
        if route.request.method=='GET':
            if route.request.url.endswith('/applications'):return route.fulfill(json=list(records.values()))
            key=route.request.url.rsplit('/',1)[-1]
            return route.fulfill(json=records[key]) if key in records else route.fulfill(status=404,json={'detail':'Fictional record not found'})
        writes.append(deepcopy(route.request.post_data_json))
        if fail and len(writes)==1:return route.fulfill(status=fail,json={'error':{'message':'Fictional failure'}})
        if hold:held.append(route)
        else:ack(route)
    page.route('**/api/applications**',api)
    page.route('**/api/documents**',lambda r:r.fulfill(json=[]))
    return records,writes,held,ack


def test_household_first_save_reload_exact_identity_and_timestamps(page):
    records,writes,_,_=household_api(page)
    page.goto('/household');add_member(page,'Fictional Member','spouse')
    row=page.get_by_label('Household member Fictional Member',exact=True)
    created=row.locator('time').first.get_attribute('datetime')
    row.get_by_role('textbox').fill('Fictional Edited')
    row=page.get_by_label('Household member Fictional Edited',exact=True)
    row.get_by_role('combobox').select_option('sibling')
    updated=row.locator('time').nth(1).get_attribute('datetime')
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
    expect(page.get_by_text('Household saved to cloud under',exact=False)).to_be_visible()
    key=next(iter(records));member=deepcopy(records[key]['household_state']['members'][1])
    assert member['createdAt']==created and member['updatedAt']==updated
    assert member['relationship']=='sibling' and member['label']=='Fictional Edited'
    page.reload();row=page.get_by_label('Household member Fictional Edited',exact=True)
    expect(row).to_be_visible();assert row.get_by_role('textbox').get_attribute('aria-label')=='Label for '+member['id']
    assert row.locator('time').first.get_attribute('datetime')==created
    assert row.locator('time').nth(1).get_attribute('datetime')==updated
    assert key in page.get_by_text('Cloud destination:',exact=False).inner_text()
    assert len(writes)==1


@pytest.mark.parametrize('status',[401,404,409,503])
def test_household_failed_save_preserves_edits_and_retry(page,status):
    records,_,_,_=household_api(page,fail=status)
    page.goto('/household');add_member(page,'Fictional Retry')
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
    expect(page.get_by_role('button',name='Retry household save',exact=True)).to_be_visible()
    expect(page.get_by_label('Household member Fictional Retry',exact=True)).to_be_visible()
    expect(page.get_by_label('Cloud save notifications').get_by_role('alert')).to_contain_text('failed')
    assert not records
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Retry household save',exact=True).click()
    expect(page.get_by_text('Household saved to cloud under',exact=False)).to_be_visible()
    assert len(records)==1


def test_household_missing_ack_slow_response_and_newer_edits(page):
    records,writes,held,ack=household_api(page,hold=True)
    page.goto('/household');add_member(page,'Fictional Slow')
    page.once('dialog',lambda d:d.accept());button=page.get_by_role('button',name='Save household to cloud',exact=True);button.click()
    expect(page.get_by_role('button',name='Saving household…',exact=True)).to_be_disabled()
    expect(page.get_by_text('Household saved to cloud under',exact=False)).to_have_count(0)
    page.get_by_label('Household member Fictional Slow',exact=True).get_by_role('textbox').fill('Fictional Newer Edit')
    page.wait_for_timeout(100);assert len(held)==1
    ack(held.pop(0))
    expect(page.get_by_label('Household member Fictional Newer Edit',exact=True)).to_be_visible()
    page.wait_for_timeout(1500);assert len(held)==1,'Newer edit must be queued after first acknowledgment'
    ack(held.pop(0));page.reload()
    expect(page.get_by_label('Household member Fictional Newer Edit',exact=True)).to_be_visible()
    assert len(writes)==2


def test_household_malformed_ack_is_failure(page):
    household_api(page)
    page.route('**/api/applications',lambda r:r.fulfill(json={} if r.request.method=='POST' else []))
    page.goto('/household');add_member(page,'Fictional Invalid Ack')
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
    expect(page.get_by_role('button',name='Retry household save',exact=True)).to_be_visible()
    expect(page.get_by_text('Household saved to cloud under',exact=False)).to_have_count(0)


@pytest.mark.parametrize('priority',['balanced','cost','days','visits'])
def test_simple_optimizer_priority_and_unknown_estimates(page,priority):
    page.goto('/planner');area=page.get_by_label('Weighted correction optimizer')
    expect(area.get_by_label('Priority for cost',exact=True)).to_have_count(0)
    assert all(i.input_value()=='' for i in area.get_by_label('Estimated cost (INR)',exact=True).all())
    area.get_by_label('What matters most to you?',exact=True).select_option(priority)
    fill_optimizer(area)
    payload,data=response_for(page,'/api/intelligence/advanced-plan',lambda:area.get_by_role('button',name='Find recommended path',exact=True).click())
    assert payload['weights']==({k:10 if k==priority else 1 for k in ['cost','days','visits']} if priority!='balanced' else dict(cost=1,days=1,visits=1))
    assert data['status']=='planned' and not data['officialAcceptanceVerified']
    expect(area.get_by_label('Correction optimization results')).to_contain_text('using only your estimates')


def test_same_rule_version_disabled_hypothetical_is_explicit(page):
    page.goto('/planner');area=page.get_by_label('Government rule change impact analyzer')
    expect(area.get_by_text('Only one stored rule version is available.',exact=False)).to_be_visible()
    expect(area.get_by_role('button',name='Compare preparation impact',exact=True)).to_be_disabled()
    area.get_by_role('button',name='Create hypothetical comparison version').click()
    expect(area.get_by_text('Hypothetical simulation — not an official government rule change.',exact=True)).to_be_visible()
    _,data=response_for(page,'/api/passport/rules/compare',lambda:area.get_by_role('button',name='Compare preparation impact',exact=True).click())
    assert data['changesDetected'] is False and data['currentRulePackModified'] is False


def document(key, name='',owner=None,reviewed=True,holder='self',dob=''):
    return dict(id=key,filename=key+'.pdf',contentType='application/pdf',sizeBytes=20,
        metadata=dict(category='identity',categories=['identity'],documentType='Aadhaar',holder=holder,printedName=name,dateOfBirth=dob,residentialAddress='',**(dict(householdMemberId=owner,associationConsent=True) if owner else {})),
        status='reviewed' if reviewed else 'needs-review',revision=2,storageStatus='ready',createdAt='2026-10-17T10:00:00Z',uploadedAt='2026-10-17T10:00:01Z',updatedAt='2026-10-17T10:00:01Z',sha256='fictional')


@pytest.mark.parametrize('field,value',[('printedName','Fictional Filled Name'),('dateOfBirth','2020-11-10')])
def test_missing_field_what_if_no_false_conflict_and_reset(page,field,value):
    docs={k:document(k,name='Other Fictional Person' if k=='second' else '',holder='other' if k=='second' else 'self') for k in ['first','second']}
    records,_,requests=mock_vault(page,initial=docs)
    page.goto('/documents');expect(page.get_by_text('first.pdf',exact=True)).to_be_visible()
    spa(page,'/planner');area=page.get_by_label('Citizen document decision assistant')
    area.get_by_label('What-if document',exact=True).select_option('first')
    area.get_by_label('What-if field',exact=True).select_option(field)
    area.get_by_label('Hypothetical value',exact=True).fill(value)
    area.get_by_role('button',name='See the impact →',exact=True).click()
    expect(area.get_by_text('This field was missing;',exact=False)).to_be_visible()
    expect(area.get_by_text('No other document for this holder',exact=False)).to_be_visible()
    assert records==docs and not any(method=='PATCH' for method,_ in requests)
    area.get_by_role('button',name='Start over',exact=True).click()
    expect(area.get_by_text("Here's what your hypothetical detail could change",exact=True)).to_have_count(0)


@pytest.mark.parametrize('reviewed',[True,False])
def test_findings_friendly_missing_fields_and_no_unrelated_family_blocker(page,reviewed):
    mock_vault(page,initial={'first':document('first',name='Fictional Applicant',reviewed=reviewed)})
    page.goto('/documents');expect(page.get_by_text('first.pdf',exact=True)).to_be_visible()
    spa(page,'/planner')
    expect(page.get_by_text('Family relationship and evidence acceptance not verified',exact=True)).to_have_count(0)
    if reviewed:
        expect(page.get_by_text('Date of Birth — Missing information',exact=True)).to_be_visible()
        expect(page.get_by_text('Residential Address — Missing information',exact=True)).to_be_visible()
    expect(page.get_by_text('No correction alternatives identified',exact=False)).to_be_visible()


def test_comparison_engine_identity_review_missing_and_pure_simulation():
    uri=(Path(__file__).resolve().parents[1]/'Maadhyam/apps/web/src/utils/documentComparison.ts').as_uri()
    # Type-only imports disappear in Node's built-in TypeScript loader.
    code=f'''import assert from 'node:assert/strict';import {{compareDocuments}} from '{uri}';
const d=(id,owner,holder='parent-guardian',name='Fictional Name',status='reviewed')=>({{id,file:{{name:id}},status,metadata:{{holder,householdMemberId:owner,associationConsent:!!owner,printedName:name}}}});
assert.equal(compareDocuments([d('a',null),d('b',null)]).comparedPairs,0);
assert.equal(compareDocuments([d('a','one'),d('b','two')]).comparedPairs,0);
assert.equal(compareDocuments([d('a','one'),d('b','one')]).comparedPairs,1);
assert.equal(compareDocuments([d('a',null,'self'),d('b',null,'self')]).comparedPairs,1);
for(const names of [['',''],['','Fictional B']]){{let r=compareDocuments([d('a','one','other',names[0]),d('b','one','other',names[1])]);assert.equal(r.findings.length,0);assert.equal(r.skippedFieldPairs,3);}}
const baseline=[d('a','one','other','Fictional A'),d('b','one','other','Fictional B','needs-review')];
const original=JSON.stringify(baseline);let r=compareDocuments(baseline);assert.equal(r.findings.length,1);assert.equal(r.comparisons.filter(c=>c.status==='difference'&&c.needsReview).length,1);
compareDocuments(baseline.map(d=>({{...d,metadata:{{...d.metadata,printedName:'Hypothetical'}}}})));assert.equal(JSON.stringify(baseline),original);
baseline[1].metadata.householdMemberId='two';assert.equal(compareDocuments(baseline).comparedPairs,0);
'''
    subprocess.run(['node','--input-type=module','-e',code],check=True)


@pytest.mark.parametrize('missing,provisional',[(True,False),(False,False),(False,True)])
def test_what_if_same_owner_separates_confirmed_provisional_and_missing(page,missing,provisional):
    initial={'first':document('first',name='' if missing else 'Fictional Before'),
             'second':document('second',name='Fictional Other',reviewed=not provisional)}
    records,_,requests=mock_vault(page,initial=initial)
    page.goto('/documents');expect(page.get_by_text('first.pdf',exact=True)).to_be_visible()
    spa(page,'/planner');area=page.get_by_label('Citizen document decision assistant')
    area.get_by_label('What-if document',exact=True).select_option('first')
    area.get_by_label('Hypothetical value',exact=True).fill('Fictional Other')
    area.get_by_role('button',name='See the impact →',exact=True).click()
    expect(area.get_by_text("Here's what your hypothetical detail could change",exact=True)).to_be_visible()
    if missing:expect(area.get_by_text('This field was missing;',exact=False)).to_be_visible()
    else:expect(area.get_by_text('Existing value replaced for this preview.',exact=False)).to_be_visible()
    expect(area.get_by_text('Before:',exact=False).filter(has_text='differing field pairs')).to_contain_text('After: 0 differing field pairs')
    if provisional:expect(area.get_by_text('1 provisional differences before;',exact=False)).to_be_visible()
    assert records==initial and not any(method in ('POST','PATCH') for method,_ in requests)
    # Draft typing invalidates the submitted result, rather than moving its counters.
    area.get_by_label('Hypothetical value',exact=True).fill('Unsubmitted draft')
    expect(area.get_by_text("Here's what your hypothetical detail could change",exact=True)).to_have_count(0)


def test_distinct_stored_versions_and_same_selection(page):
    import urllib.request
    from qa.conftest import API
    with urllib.request.urlopen(API+'/api/passport/rules/versions') as response:
        versions=json.load(response)
    first=versions['versions'][0]['pack'];second=deepcopy(first);second['version']='fictional-stored-reference-two'
    versions['versions'].append({'version':second['version'],'kind':'stored-reference','pack':second})
    page.route('**/api/passport/rules/versions',lambda r:r.fulfill(json=versions))
    page.goto('/planner');area=page.get_by_label('Government rule change impact analyzer')
    expect(area.get_by_label('Compare with version',exact=True)).to_have_value(second['version'])
    expect(area.get_by_role('button',name='Compare preparation impact',exact=True)).to_be_enabled()
    area.get_by_label('Compare with version',exact=True).select_option(first['version'])
    expect(area.get_by_role('button',name='Compare preparation impact',exact=True)).to_be_disabled()


def test_existing_household_revision_conflict_retry_does_not_hydrate_away_edits(page):
    record=cloud_record();records={record['id']:record}
    _,writes,_,_=household_api(page,fail=409,records=records)
    page.goto('/household');expect(page.get_by_text('Cloud destination: '+record['id'],exact=True)).to_be_visible()
    add_member(page,'Fictional Conflict Member')
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
    expect(page.get_by_text('Cloud revision conflict. Local edits are intact.',exact=False)).to_be_visible()
    expect(page.get_by_label('Household member Fictional Conflict Member',exact=True)).to_be_visible()
    page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Retry household save',exact=True).click()
    expect(page.get_by_text('Household saved to cloud. Snapshot',exact=False)).to_be_visible()
    assert writes[0]['revision']==writes[1]['revision']==record['revision']-1
    page.reload();expect(page.get_by_label('Household member Fictional Conflict Member',exact=True)).to_be_visible()


def test_delayed_authentication_household_save_waits_for_real_request(page):
    _,writes,_,_=household_api(page)
    held=[]
    page.route('**/identitytoolkit.googleapis.com/**',lambda r:held.append(r))
    page.goto('/household');add_member(page,'Fictional Auth Delay')
    # Restoration waits for Firebase; save cannot claim a success during this delay.
    page.get_by_role('button',name='Save household to cloud',exact=True).click()
    expect(page.get_by_text('Cloud restoration is still running.',exact=False)).to_be_visible()
    assert not writes
    page.unroute('**/identitytoolkit.googleapis.com/**')
    mocked_auth(page)
    # Release the delayed SDK call by using the same deterministic auth responder.
    for route in held:route.fulfill(status=503,json={'error':{'message':'Fictional delayed authentication'}})
    expect(page.get_by_label('Household member Fictional Auth Delay',exact=True)).to_be_visible()


def test_selected_saved_applicant_age_is_used_in_planner(page):
    record=cloud_record();household_api(page,records={record['id']:record})
    page.goto('/planner')
    expect(page.get_by_text('No correction alternatives identified',exact=False)).to_be_visible()
    expect(page.get_by_text('Applicant age group not specified',exact=True)).to_have_count(0)
    expect(page.locator('#planning-date')).to_have_value('2027-12-31')


@pytest.mark.parametrize('body',[{},[None],[{'id':'fictional-invalid','metadata':None}]])
def test_malformed_cloud_document_response_preserves_usable_vault(page,body):
    mocked_auth(page)
    page.route('**/api/applications**',lambda r:r.fulfill(json=[]))
    page.route('**/api/documents**',lambda r:r.fulfill(json=body))
    page.goto('/documents')
    expect(page.get_by_text('Cloud Vault unavailable',exact=False)).to_be_visible()
    expect(page.get_by_label('Choose documents to add')).to_be_attached()


def test_orphaned_owner_id_requires_assignment_before_comparison():
    uri=(Path(__file__).resolve().parents[1]/'Maadhyam/apps/web/src/utils/documentComparison.ts').as_uri()
    subprocess.run(['node','--input-type=module','-e',f"""import assert from 'node:assert/strict';import {{compareDocuments}} from '{uri}';const docs=['a','b'].map(id=>({{id,file:{{name:id}},status:'reviewed',metadata:{{householdMemberId:'orphan',associationConsent:true,holder:'other',printedName:id}}}}));const result=compareDocuments(docs,new Set(['applicant']));assert.equal(result.comparedPairs,0);assert.deepEqual(result.excludedDocumentIds,['a','b']);"""],check=True)


def test_wireframe_discovery_search_service_selection_and_assistant(page):
    page.goto('/')
    expect(page.get_by_label('Connected preparation journey')).to_be_visible()
    page.get_by_label('Search services from landing',exact=True).fill('Passport')
    page.get_by_role('button',name='Find services',exact=True).click()
    expect(page.get_by_label('Search government services')).to_have_value('Passport')
    page.get_by_role('link',name='Explore Passport Seva',exact=True).click()
    expect(page.locator('h1')).to_be_visible()
    page.get_by_role('button',name='Open Maadhyam AI',exact=True).click()
    expect(page.get_by_role('dialog',name='Maadhyam AI assistant',exact=True)).to_be_visible()


def test_wireframe_dynamic_readiness_requires_review_and_correct_owner(page):
    doc=document('fictional-proof',name='Fictional Applicant',dob='2000-01-01',reviewed=False)
    doc['metadata'].update(documentType='Aadhaar card',residentialAddress='Fictional Address')
    mock_vault(page,initial={doc['id']:doc})
    page.goto('/documents');expect(page.get_by_text('fictional-proof.pdf',exact=True)).to_be_visible()
    spa(page,'/services/passport/journey')
    page.get_by_label('Applicant name',exact=True).fill('Fictional Applicant')
    page.get_by_label('Applicant date of birth (for document guidance)',exact=True).fill('2000-01-01')
    page.get_by_label('Preparation document references').get_by_role('checkbox').check()
    page.get_by_role('button',name='Continue',exact=True).click()
    page.get_by_role('radio',name='An adult',exact=True).check()
    area=page.get_by_label('Passport preparation readiness',exact=True)
    expect(area).to_contain_text('Evidence needs review')
    before=int(area.get_by_role('progressbar').get_attribute('aria-valuenow'))
    spa(page,'/documents');page.get_by_role('button',name='Mark self-reviewed',exact=True).click()
    spa(page,'/services/passport/journey')
    # Reopen the existing local preparation through Applications to avoid a new draft.
    spa(page,'/applications')
    row=page.locator('article').filter(has_text='Fictional Applicant').first
    row.get_by_role('button',name='Continue preparation',exact=True).click()
    page.get_by_role('link',name='Continue passport journey',exact=True).click()
    area=page.get_by_label('Passport preparation readiness',exact=True)
    expect(area).to_contain_text('Reviewed preparation check complete')
    expect(area.get_by_role('progressbar')).not_to_have_attribute('aria-valuenow',str(before))
    after=int(area.get_by_role('progressbar').get_attribute('aria-valuenow'))
    assert after>before
    expect(area).to_contain_text('Government acceptance remains unverified')
    expect(page.get_by_label('Connected preparation journey')).to_contain_text('completed workspace action')


def test_wireframe_pages_add_no_new_route_or_fake_progress(page):
    page.goto('/')
    nav=page.get_by_label('Connected preparation journey')
    expect(nav.get_by_text('completed workspace action',exact=False)).to_have_count(0)
    targets=nav.get_by_role('link').evaluate_all('(links)=>links.map(a=>new URL(a.href).pathname)')
    assert set(targets)<={'/services','/services/passport','/documents','/planner','/services/passport/journey','/applications'}
    page.goto('/planner')
    expect(page.get_by_text('temporary previews',exact=False)).to_be_visible()
    expect(page.get_by_role('button',name='Open Maadhyam AI',exact=True)).to_be_visible()


def test_notifications_repeated_save_has_one_current_operation_notice(page):
    record=cloud_record();household_api(page,records={record['id']:record})
    page.goto('/household');expect(page.get_by_text('Cloud destination: '+record['id'],exact=True)).to_be_visible()
    for _ in range(2):
        page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
        expect(page.get_by_text('Household saved to cloud. Snapshot',exact=False)).to_be_visible()
    expect(page.get_by_label('Cloud save notifications').get_by_role('status')).to_have_count(1)


def test_household_real_fastapi_contract_save_reload_and_server_defaults(page):
    """Browser -> actual FastAPI schemas/routes -> local memory store -> reload.
    Unlike echo mocks, create serializes nullable timestamps and nested defaults.
    """
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from maadhyam_api.main import create_app
    from maadhyam_api.routes.applications import get_store, require_uid
    class Store:
        def __init__(self):self.records={}
        def create(self,uid,fields,client_id):
            key=(uid,client_id)
            self.records.setdefault(key,{**deepcopy(fields),'id':client_id,'revision':1,'owner_uid':uid,
                'created_at':'2026-10-17T11:00:00+00:00','updated_at':'2026-10-17T11:00:00+00:00','lastSavedAt':'2026-10-17T11:00:00+00:00'})
            return deepcopy(self.records[key])
        def list(self,uid):return [deepcopy(v) for (owner,_),v in self.records.items() if owner==uid]
        def get(self,uid,key):
            if (uid,key) not in self.records:raise HTTPException(404,'Not found')
            return deepcopy(self.records[(uid,key)])
        def update(self,uid,key,revision,fields):
            old=self.get(uid,key)
            if old['revision']!=revision:raise HTTPException(409,'Conflict')
            old.update(deepcopy(fields));old['revision']+=1;old['lastSavedAt']=old['updated_at']='2026-10-17T11:01:00+00:00'
            self.records[(uid,key)]=old;return deepcopy(old)
    store=Store();api=create_app();api.dependency_overrides[get_store]=lambda:store;api.dependency_overrides[require_uid]=lambda:'fictional-api-user'
    mocked_auth(page)
    with TestClient(api) as client:
        def forward(route):
            request=route.request;path='/api/applications'+request.url.split('/api/applications',1)[1]
            assert request.headers.get('authorization','').startswith('Bearer ')
            response=client.request(request.method,path,json=request.post_data_json if request.method in ('POST','PATCH') else None)
            route.fulfill(status=response.status_code,body=response.content,content_type='application/json')
        page.route('**/api/applications**',forward);page.route('**/api/documents**',lambda r:r.fulfill(json=[]))
        page.goto('/household');add_member(page,'Fictional Actual API Member','sibling')
        row=page.get_by_label('Household member Fictional Actual API Member',exact=True);created=row.locator('time').first.get_attribute('datetime')
        page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
        expect(page.get_by_text('Household saved to cloud under',exact=False)).to_be_visible()
        stored=next(iter(store.records.values()));key=stored['id'];member=deepcopy(stored['household_state']['members'][1])
        assert stored['household_state']['members'][0]['createdAt'] is None
        page.reload();row=page.get_by_label('Household member Fictional Actual API Member',exact=True);expect(row).to_be_visible()
        from datetime import datetime
        assert datetime.fromisoformat(row.locator('time').first.get_attribute('datetime'))==datetime.fromisoformat(created)
        assert row.get_by_role('textbox').get_attribute('aria-label')=='Label for '+member['id']
        assert key in page.get_by_text('Cloud destination:',exact=False).inner_text()
        row.get_by_role('textbox').fill('Fictional Actual API Edited')
        page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Save household to cloud',exact=True).click()
        expect(page.get_by_text('Household saved to cloud. Snapshot',exact=False)).to_be_visible()
        page.reload();expect(page.get_by_label('Household member Fictional Actual API Edited',exact=True)).to_be_visible()
        assert store.get('fictional-api-user',key)['household_state']['members'][1]['id']==member['id']
    api.dependency_overrides.clear()


def test_planner_saved_checklist_target_and_dependency_cascade(page):
    record=cloud_record();record['selected_document_ids']=['fictional-proof'];record['planner_state']['manual_task_ids']=['journey']
    records,_,_,_=household_api(page,records={record['id']:record})
    page.add_init_script("localStorage.setItem('maadhyam-cloud-workspace-consent-v2','yes')")
    page.route('**/api/documents**',lambda r:r.fulfill(json=[document('fictional-proof',name='Fictional Applicant',dob='2000-01-01')]))
    page.goto('/planner');area=page.get_by_label('Saved preparation checklist',exact=True)
    review=area.get_by_role('checkbox',name='Complete: Review potential discrepancies',exact=True)
    expect(review).to_be_enabled();review.check()
    page.locator('#planning-date').fill('2028-02-01')
    page.wait_for_function("() => document.querySelector('[aria-label=\"Cloud save notifications\"]')?.textContent.includes('saved to cloud')")
    assert records[record['id']]['planner_state']['target_date']=='2028-02-01'
    assert 'differences' in records[record['id']]['planner_state']['manual_task_ids']
    page.reload();expect(page.locator('#planning-date')).to_have_value('2028-02-01')
    area=page.get_by_label('Saved preparation checklist',exact=True)
    expect(area.get_by_role('checkbox',name='Complete: Review potential discrepancies',exact=True)).to_be_checked()
    area.get_by_role('checkbox',name='Complete: Complete your passport preparation questionnaire',exact=True).uncheck()
    expect(area.get_by_role('checkbox',name='Complete: Review potential discrepancies',exact=True)).not_to_be_checked()
    expect(area.get_by_role('checkbox',name='Complete: Review potential discrepancies',exact=True)).to_be_disabled()


def test_document_slow_metadata_ack_keeps_newer_edits(page):
    record=document('fictional-slow-metadata',name='Fictional Original')
    records,_,_=mock_vault(page,initial={record['id']:record})
    held=[]
    def patch(route):
        if route.request.method=='PATCH':held.append(route)
        else:route.fallback()
    page.route('**/api/documents/*',patch)
    page.goto('/documents');expect(page.get_by_text(record['filename'],exact=True)).to_be_visible()
    def edit_name(name):
        page.get_by_role('button',name='Edit details',exact=True).click();page.locator('#metadata-printed-name').fill(name);page.get_by_role('button',name='Save details',exact=True).click()
    edit_name('Fictional First Edit');page.wait_for_timeout(100);assert len(held)==1
    # Vault locks its editor during a write. A separately authorized household
    # association can still change metadata while the old response is pending.
    expect(page.get_by_role('button',name='Edit details',exact=True)).to_be_disabled()
    spa(page,'/household');add_member(page,'Fictional New Owner')
    from qa.test_completion import associate
    associate(page,record['filename'],'Fictional New Owner')
    first=held.pop(0);payload=first.request.post_data_json;records[record['id']].update(payload);records[record['id']]['revision']+=1
    first.fulfill(json=records[record['id']])
    page.wait_for_timeout(150);assert len(held)==1
    expect(page.get_by_label('Associate household evidence').locator('li').filter(has_text=record['filename'])).to_contain_text('Fictional New Owner')
    second=held.pop(0);payload=second.request.post_data_json
    assert payload['revision']==records[record['id']]['revision']
    assert payload['metadata']['householdMemberId'] and payload['metadata']['associationConsent'] is True
    assert payload['metadata']['printedName']=='Fictional First Edit'
    records[record['id']].update(payload);records[record['id']]['revision']+=1;second.fulfill(json=records[record['id']])
    spa(page,'/documents');expect(page.get_by_text('Reviewed metadata saved to cloud.',exact=False)).to_be_visible()
    page.reload();page.get_by_role('button',name='Edit details',exact=True).click();expect(page.locator('#metadata-printed-name')).to_have_value('Fictional First Edit')
