"""Fictional, mocked-cloud persistence regressions; no paid inference."""
from copy import deepcopy
import pytest
from playwright.sync_api import expect
from qa.test_remediation import mocked_auth, cloud_record


@pytest.mark.parametrize('step', [0, 1, 2, 3])
def test_confirmed_save_hard_refresh_exact_step(page, step):
    mocked_auth(page)
    saved = cloud_record()
    saved['current_step'] = 0
    saved['applicant_details']['date_of_birth'] = ''
    writes = []
    def api(route):
        if route.request.method == 'GET':
            route.fulfill(json=[saved] if route.request.url.endswith('/applications') else saved)
        else:
            payload = route.request.post_data_json
            writes.append(deepcopy(payload))
            saved.update(payload)
            saved['revision'] += 1
            saved['lastSavedAt'] = '2026-10-17T09:25:00Z'
            route.fulfill(json=saved)
    page.route('**/api/applications**', api)
    page.goto('/services/passport/journey?preparation=' + saved['id'])
    expect(page.get_by_text('Step 1 of 4', exact=True)).to_be_visible()
    if step>=1:page.get_by_role('button',name='Continue',exact=True).click()
    if step>=2:
        page.get_by_role('radio',name='An adult',exact=True).check()
        page.get_by_role('radio',name='Yes',exact=True).check()
        page.get_by_role('button',name='Continue',exact=True).click()
    if step>=3:
        for radio in page.get_by_role('radio',name='Yes',exact=True).all():radio.check()
        page.get_by_role('button',name='Continue',exact=True).click()
    expect(page.get_by_text(f'Step {step+1} of 4', exact=True)).to_be_visible()
    page.get_by_label('Applicant name', exact=True).fill('Fictional Saved Applicant')
    page.once('dialog', lambda dialog: dialog.accept())
    page.get_by_role('button', name='Save preparation', exact=True).click()
    expect(page.get_by_text('Saved to Maadhyam cloud (Firestore).', exact=False)).to_be_visible()
    assert writes[-1]['current_step'] == step
    timestamp=page.locator('time').nth(1).get_attribute('datetime')
    assert timestamp=='2026-10-17T09:25:00Z'
    page.reload()
    expect(page.get_by_text(f'Step {step+1} of 4', exact=True)).to_be_visible()
    expect(page.get_by_label('Applicant name', exact=True)).to_have_value('Fictional Saved Applicant')
    assert saved['id'] in page.url
    assert page.locator('time').nth(1).get_attribute('datetime')==timestamp


def mock_vault(page, initial=None, fail_delete=False, fail_upload=False):
    import hashlib
    import json
    from email.parser import BytesParser
    from email.policy import default
    mocked_auth(page)
    page.route('**/api/applications**', lambda route: route.fulfill(json=[]))
    records = deepcopy(initial or {})
    files = {}
    requests = []
    def api(route):
        request = route.request
        requests.append((request.method, request.url))
        path = request.url.split('/api/documents',1)[1]
        if request.method == 'GET':
            if path.endswith('/file'):
                route.fulfill(body=files.get(path.split('/')[1],b'%PDF-1.7\nfictional'),content_type='application/pdf')
            else:
                route.fulfill(json=list(records.values()) if not path else records[path.split('/')[1]])
        elif request.method == 'POST':
            if fail_upload:
                return route.fulfill(status=503,json={'error':{'message':'Fictional upload failure'}})
            message=BytesParser(policy=default).parsebytes(('Content-Type: '+request.headers['content-type']+'\r\n\r\n').encode()+request.post_data_buffer)
            parts={part.get_param('name',header='content-disposition'):part for part in message.iter_parts()}
            document_id=parts['document_id'].get_content().strip()
            data=parts['file'].get_payload(decode=True)
            fields=json.loads(parts['fields'].get_content())
            records[document_id]={'id':document_id,**fields,'filename':parts['file'].get_filename(),
                'contentType':parts['file'].get_content_type(),'sizeBytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                'revision':2,'storageStatus':'ready','createdAt':'2026-10-17T10:00:00Z','uploadedAt':'2026-10-17T10:00:01Z','updatedAt':'2026-10-17T10:00:01Z'}
            files[document_id]=data
            route.fulfill(status=201,json=records[document_id])
        elif request.method == 'PATCH':
            document_id=path.split('/')[1];payload=request.post_data_json
            if payload['revision']!=records[document_id]['revision']:
                return route.fulfill(status=409,json={'error':{'message':'Revision conflict'}})
            records[document_id].update(payload);records[document_id]['revision']+=1;records[document_id]['updatedAt']='2026-10-17T10:01:01Z'
            route.fulfill(json=records[document_id])
        else:
            deleted=[] if fail_delete else list(records)
            failed=list(records) if fail_delete else []
            for document_id in deleted: records.pop(document_id);files.pop(document_id,None)
            route.fulfill(json={'deleted':deleted,'failed':failed})
    page.route('**/api/documents**',api)
    return records,files,requests


def add_fictional_pdf(page):
    page.get_by_label('Choose documents to add').set_input_files({'name':'fictional-proof.pdf','mimeType':'application/pdf','buffer':b'%PDF-1.7\nfictional fixture'})
    expect(page.get_by_text('fictional-proof.pdf',exact=True)).to_be_visible()


def test_cloud_vault_upload_refresh_on_demand_preview_and_delete(page):
    records,files,requests=mock_vault(page)
    page.goto('/documents')
    expect(page.get_by_text('Cloud Vault restored (0).',exact=False)).to_be_visible()
    page.once('dialog',lambda dialog:dialog.accept())
    page.get_by_role('button',name='Enable cloud storage for new files',exact=True).click()
    expect(page.get_by_role('button',name='Cloud storage enabled',exact=True)).to_be_visible()
    add_fictional_pdf(page)
    expect(page.get_by_text('Saved to cloud.',exact=False)).to_be_visible()
    document_id=next(iter(records))
    assert page.locator('time').first.get_attribute('datetime')=='2026-10-17T10:00:01Z'
    page.reload()
    expect(page.get_by_text('fictional-proof.pdf',exact=True)).to_be_visible()
    assert page.locator('time').first.get_attribute('datetime')=='2026-10-17T10:00:01Z'
    assert not any(url.endswith('/file') for _,url in requests)
    page.get_by_role('button',name='Preview',exact=True).click()
    expect(page.get_by_role('dialog',name='Preview fictional-proof.pdf',exact=True)).to_be_visible()
    assert any(url.endswith('/file') for _,url in requests)
    page.keyboard.press('Escape')
    page.once('dialog',lambda dialog:dialog.dismiss())
    page.get_by_role('button',name='Delete this account’s cloud Vault and local copies',exact=True).click()
    assert document_id in records
    page.once('dialog',lambda dialog:dialog.accept())
    page.get_by_role('button',name='Delete this account’s cloud Vault and local copies',exact=True).click()
    expect(page.get_by_text('Cloud deletion: 1 deleted; 0 failed.',exact=False)).to_be_visible()
    page.reload()
    expect(page.get_by_text('Cloud Vault restored (0).',exact=False)).to_be_visible()
    expect(page.get_by_text('fictional-proof.pdf',exact=True)).to_have_count(0)


@pytest.mark.parametrize('fail_upload',[False,True])
def test_explicit_local_migration_preserves_originals(page,fail_upload):
    records,_,requests=mock_vault(page,fail_upload=fail_upload)
    page.goto('/documents')
    expect(page.get_by_text('Cloud Vault restored (0).',exact=False)).to_be_visible()
    add_fictional_pdf(page)
    assert not any(method=='POST' for method,_ in requests)
    page.get_by_role('button',name='Enable local saving',exact=True).click()
    expect(page.get_by_role('button',name='Disable local saving',exact=True)).to_be_visible()
    document_id=page.evaluate("() => new Promise((resolve,reject)=>{const r=indexedDB.open('maadhyam-local-vault-v1',1);r.onsuccess=()=>{const q=r.result.transaction('documents').objectStore('documents').getAll();q.onsuccess=()=>resolve(q.result[0]?.id);q.onerror=reject;};})")
    assert document_id
    page.once('dialog',lambda dialog:dialog.accept())
    page.get_by_role('button',name='Migrate existing local files to cloud',exact=True).click()
    expect(page.get_by_text('Migration verified:',exact=False)).to_be_visible()
    if fail_upload:
        assert records=={}
        expect(page.get_by_text('0 succeeded; 1 failed.',exact=False)).to_be_visible()
    else:
        assert document_id in records
        expect(page.get_by_text('1 succeeded; 0 failed.',exact=False)).to_be_visible()
    retained=page.evaluate("() => new Promise(resolve=>{const r=indexedDB.open('maadhyam-local-vault-v1',1);r.onsuccess=()=>{const q=r.result.transaction('documents').objectStore('documents').getAll();q.onsuccess=()=>resolve(q.result.length);};})")
    assert retained==1


def test_passport_slow_ack_duplicate_save_disabled(page):
    mocked_auth(page)
    record=cloud_record();held=[]
    def api(route):
        if route.request.method=='GET':route.fulfill(json=[record])
        else:held.append(route)
    page.route('**/api/applications**',api)
    page.goto('/services/passport/journey?preparation='+record['id'])
    expect(page.get_by_label('Applicant name',exact=True)).to_be_visible()
    page.once('dialog',lambda dialog:dialog.accept())
    button=page.get_by_role('button',name='Save preparation',exact=True)
    button.click()
    expect(button).to_be_disabled()
    expect(page.get_by_text('Saving preparation…',exact=True)).to_be_visible()
    expect(page.get_by_text('Saved to Maadhyam cloud',exact=False)).to_have_count(0)
    page.wait_for_timeout(150)
    assert len(held)==1
    held[0].fulfill(status=503,json={'error':{'message':'Fictional failed save'}})
    expect(page.get_by_text('Cloud save failed.',exact=False)).to_be_visible()
    expect(button).to_be_enabled()


def test_household_creation_edit_timestamps_and_legacy(page):
    from qa.test_completion import add_member
    mock_vault(page)
    page.goto('/household')
    default=page.get_by_label('Household member Applicant (this workspace)',exact=True)
    expect(default.get_by_text('Not recorded',exact=True)).to_be_visible()
    add_member(page,'Fictional Timestamp Member')
    row=page.get_by_label('Household member Fictional Timestamp Member',exact=True)
    created=row.locator('time').first.get_attribute('datetime')
    assert created
    page.wait_for_timeout(20)
    row.get_by_role('textbox').fill('Fictional Renamed Timestamp Member')
    renamed=page.get_by_label('Household member Fictional Renamed Timestamp Member',exact=True)
    assert renamed.locator('time').first.get_attribute('datetime')==created
    assert renamed.locator('time').nth(1).get_attribute('datetime')!=created


def test_shared_date_formatter_utc_local_legacy():
    import os
    import subprocess
    from pathlib import Path
    uri=(Path(__file__).resolve().parents[1]/'Maadhyam/apps/web/src/utils/dateTime.ts').as_uri()
    source=f"""import assert from 'node:assert/strict';
import {{formatDateTime}} from '{uri}';
assert.equal(formatDateTime('2026-10-17T09:05:00Z'),'17 Oct 2026, 02:35 PM');
assert.equal(formatDateTime('2026-10-17T03:05:00Z'),'17 Oct 2026, 08:35 AM');
for (const value of [undefined,null,'bad',{{seconds:1}},'']) assert.equal(formatDateTime(value),'Not recorded');
"""
    subprocess.run(['node','--input-type=module','-e',source],check=True,env={**os.environ,'TZ':'Asia/Kolkata'})


def test_stable_household_applicant_duplicate_names_and_refresh(page):
    mocked_auth(page)
    record=cloud_record()
    original=record['household_state']['members'][0]
    record['household_state']['members']=[original,*[
        {'id':key,'label':'Fictional Same Name','relationship':'parent','dependsOnMemberIds':[],
         'dependsOnDocumentIds':[],'relationshipEvidenceDocumentIds':[],'createdAt':'2026-10-17T07:00:00Z','updatedAt':'2026-10-17T07:00:00Z'}
        for key in ('fictional-parent-one','fictional-parent-two')]]
    record['applicant_details']['name']='Fictional Same Name'
    record['applicant_details']['household_member_id']='fictional-parent-two'
    page.route('**/api/applications**',lambda r:r.fulfill(json=[record] if r.request.url.endswith('/applications') else record))
    page.route('**/api/documents**',lambda r:r.fulfill(json=[]))
    page.goto('/services/passport/journey?preparation='+record['id'])
    expect(page.get_by_label('Select household applicant')).to_have_value('fictional-parent-two')
    page.reload()
    expect(page.get_by_label('Select household applicant')).to_have_value('fictional-parent-two')
    page.locator('a[href="/household"]').first.click()
    cards=page.get_by_label('Household member Fictional Same Name',exact=True)
    expect(cards).to_have_count(2)
    assert cards.nth(1).locator('time').first.get_attribute('datetime')=='2026-10-17T07:00:00Z'


def test_conflicting_passport_save_keeps_confirmed_timestamp(page):
    mocked_auth(page)
    record=cloud_record();record['lastSavedAt']='2026-10-17T07:00:00Z'
    def api(route):
        if route.request.method=='GET':route.fulfill(json=[record])
        else:route.fulfill(status=409,json={'error':{'message':'Other tab saved'}})
    page.route('**/api/applications**',api)
    page.goto('/services/passport/journey?preparation='+record['id'])
    expect(page.get_by_label('Applicant name',exact=True)).to_be_visible()
    before=page.locator('time').nth(1).get_attribute('datetime')
    page.get_by_label('Applicant name',exact=True).fill('Fictional Unsaved Conflict')
    page.once('dialog',lambda dialog:dialog.accept())
    page.get_by_role('button',name='Save preparation',exact=True).click()
    expect(page.get_by_text('Cloud revision conflict;',exact=False)).to_be_visible()
    assert page.locator('time').nth(1).get_attribute('datetime')==before
    expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional Unsaved Conflict')


def test_restoration_map_key_order_does_not_write_or_advance_saved_time(page):
    mocked_auth(page)
    record=cloud_record()
    # Firestore maps may return fields in any order.
    record['planner_state']={key:record['planner_state'][key] for key in reversed(record['planner_state'])}
    record['household_state']['members'][0]['createdAt']=None
    record['household_state']['members'][0]['updatedAt']=None
    record['lastSavedAt']='2026-10-17T07:00:00Z'
    writes=[]
    page.add_init_script("localStorage.setItem('maadhyam-cloud-workspace-consent-v2','yes')")
    def api(route):
        if route.request.method=='GET':route.fulfill(json=[record])
        else:
            writes.append(route.request.post_data_json)
            route.fulfill(status=409,json={'error':{'message':'Unexpected hydration write'}})
    page.route('**/api/applications**',api)
    page.goto('/services/passport/journey?preparation='+record['id'])
    expect(page.get_by_text('Step 2 of 4',exact=True)).to_be_visible()
    page.wait_for_timeout(1600)
    assert not writes,'Restoring equivalent unordered maps must not write or change saved dates'
    assert page.locator('time').nth(1).get_attribute('datetime')==record['lastSavedAt']


def test_cloud_unassign_uses_explicit_null_and_one_write(page):
    from uuid import uuid4
    document_id=str(uuid4())
    record={'id':document_id,'filename':'fictional-owner.pdf','contentType':'application/pdf','sizeBytes':20,
        'metadata':{'category':'address','categories':['address'],'documentType':'Utility bill','holder':'parent-guardian',
                    'householdMemberId':'fictional-removed-parent','associationConsent':True,'printedName':'Fictional Original Name'},
        'status':'reviewed','revision':2,'storageStatus':'ready','createdAt':'2026-10-17T10:00:00Z','uploadedAt':'2026-10-17T10:00:01Z','updatedAt':'2026-10-17T10:00:01Z','sha256':'fictional'}
    records,_,requests=mock_vault(page,initial={document_id:record})
    page.goto('/documents')
    expect(page.get_by_text('fictional-owner.pdf',exact=True)).to_be_visible()
    page.get_by_role('button',name='Edit details',exact=True).click()
    page.locator('#metadata-holder').select_option('category:other')
    page.get_by_role('button',name='Save details',exact=True).click()
    expect(page.get_by_text('Reviewed metadata saved to cloud.',exact=False)).to_be_visible()
    assert records[document_id]['metadata']['householdMemberId'] is None
    assert records[document_id]['metadata']['associationConsent'] is False
    assert records[document_id]['metadata']['printedName']=='Fictional Original Name'
    assert sum(method=='PATCH' for method,_ in requests)==1
