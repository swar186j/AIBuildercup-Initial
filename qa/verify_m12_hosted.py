"""Real hosted M12 acceptance. Small fictional files; no Gemini calls or token output."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/evidence/m12-hosted'
OUT.mkdir(parents=True,exist_ok=True)
BASE='https://maadhyam-1610.web.app'
CASES=[]
def record(name,details):
    CASES.append({'testId':name,'status':'PASS','observed':details})
    (OUT/'results.json').write_text(json.dumps(CASES,indent=2))
    print('PASS '+name,flush=True)


def main():
    with sync_playwright() as p:
        browser=p.chromium.launch()
        ctx=browser.new_context(base_url=BASE,viewport={'width':1440,'height':1000})
        page=ctx.new_page();page.set_default_timeout(20000)
        errors=[];localhost=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('request',lambda request:localhost.append(request.url) if '127.0.0.1' in request.url or '://localhost' in request.url else None)
        with page.expect_response(lambda r:r.request.method=='GET' and r.url.endswith('/api/documents')) as listed:
            page.goto('/documents')
        assert listed.value.status==200
        token=listed.value.request.headers['authorization']
        headers={'Authorization':token}
        record('firebase-authenticated-vault-list','Real Firebase ID token and own-user list; no mocked transport')
        page.once('dialog',lambda d:d.accept())
        page.get_by_role('button',name='Enable cloud storage for new files',exact=True).click()
        expect(page.get_by_role('button',name='Cloud storage enabled',exact=True)).to_be_visible()
        fixture=ROOT/'qa/fixtures/fictional_address.png'
        with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/documents')) as uploaded:
            page.get_by_label('Choose documents to add').set_input_files(str(fixture))
        assert uploaded.value.status==201,uploaded.value.text()
        document=uploaded.value.json();document_id=document['id']
        assert document['storageStatus']=='ready' and document['uploadedAt']
        expect(page.get_by_text('Saved to cloud.',exact=False)).to_be_visible()
        record('real-private-upload-and-server-timestamps',{'id':document_id,'createdAt':document['createdAt'],'uploadedAt':document['uploadedAt'],'sizeBytes':document['sizeBytes']})
        page.reload()
        expect(page.get_by_text(fixture.name,exact=True)).to_be_visible()
        assert page.locator('time').first.get_attribute('datetime')==document['uploadedAt']
        with page.expect_response(lambda r:r.url.endswith('/file')) as downloaded:
            page.get_by_role('button',name='Preview',exact=True).click()
        assert downloaded.value.status==200
        assert hashlib.sha256(downloaded.value.body()).hexdigest()==hashlib.sha256(fixture.read_bytes()).hexdigest()
        expect(page.get_by_role('dialog',name='Preview '+fixture.name,exact=True)).to_be_visible()
        page.keyboard.press('Escape')
        record('refresh-preview-byte-integrity','Cloud metadata/immutable upload time restored; authenticated bytes match fixture')
        page.get_by_role('button',name='Edit details',exact=True).click()
        page.get_by_role('checkbox',name='Address proof',exact=True).check()
        page.locator('#metadata-type').select_option('Utility bill')
        page.locator('#metadata-address').fill('Fictional M12 Sample Address')
        with page.expect_response(lambda r:r.request.method=='PATCH' and '/api/documents/' in r.url) as patched:
            page.get_by_role('button',name='Save details',exact=True).click()
        assert patched.value.status==200,patched.value.text()
        changed=patched.value.json()
        assert changed['createdAt']==document['createdAt'] and changed['uploadedAt']==document['uploadedAt']
        assert changed['updatedAt']!=document['updatedAt']
        with page.expect_response(lambda r:r.request.method=='PATCH' and '/api/documents/' in r.url) as reviewed:
            page.get_by_role('button',name='Mark self-reviewed',exact=True).click()
        assert reviewed.value.status==200
        record('metadata-review-authoritative-update','Created/uploaded dates preserved; metadata/review revisions and server update date advance')
        page.locator('a[href="/household"]').first.click()
        name='Fictional M12 Household '+uuid4().hex[:6]
        page.get_by_label('New member name').fill(name)
        page.get_by_label('New member relationship').select_option('spouse')
        page.get_by_role('button',name='Add member',exact=True).click()
        member=page.get_by_label('Household member '+name,exact=True)
        created=member.locator('time').first.get_attribute('datetime');assert created
        page.locator('a[href="/applications"]').first.click()
        page.get_by_role('button',name='Start new preparation',exact=True).click()
        page.get_by_role('link',name='Continue passport journey',exact=True).click()
        page.get_by_label('Select household applicant').select_option('__other__')
        page.get_by_label('Applicant name',exact=True).fill('Fictional M12 Passport Applicant')
        page.get_by_role('button',name='Continue',exact=True).click()
        page.get_by_role('radio',name='An adult',exact=True).check()
        page.get_by_role('radio',name='Yes',exact=True).check()
        page.get_by_role('button',name='Continue',exact=True).click()
        expect(page.get_by_text('Step 3 of 4',exact=True)).to_be_visible()
        page.once('dialog',lambda d:d.accept())
        with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/applications')) as saved:
            page.get_by_role('button',name='Save preparation',exact=True).click()
        assert saved.value.status==201,saved.value.text()
        application=saved.value.json();application_id=application['id']
        assert application['current_step']==2 and application['selected_document_ids']==[document_id]
        assert application['lastSavedAt']
        expect(page.get_by_text('Saved to Maadhyam cloud',exact=False)).to_be_visible()
        page.reload()
        expect(page.get_by_text('Step 3 of 4',exact=True)).to_be_visible()
        expect(page.get_by_label('Applicant name',exact=True)).to_have_value('Fictional M12 Passport Applicant')
        assert application_id in page.url
        assert page.locator('time').nth(1).get_attribute('datetime')==application['lastSavedAt']
        record('passport-real-step3-save-immediate-refresh',{'id':application_id,'currentStep':2,'lastSavedAt':application['lastSavedAt'],'exactSelectedIdsRetained':True})
        page.locator('a[href="/applications"]').first.click()
        card=page.locator('article').filter(has_text=application_id)
        expect(card.get_by_text('Current step: Step 3 of 4',exact=True)).to_be_visible()
        assert card.locator('time').nth(1).get_attribute('datetime')==application['lastSavedAt']
        card.get_by_role('button',name='Continue preparation',exact=True).click()
        page.get_by_role('link',name='Continue passport journey',exact=True).click()
        expect(page.get_by_text('Step 3 of 4',exact=True)).to_be_visible()
        record('my-applications-live-resume-timestamps','Same ID, step and last saved time without manual refresh')
        page.locator('a[href="/household"]').first.click()
        expect(page.get_by_label('Household member '+name,exact=True)).to_be_visible()
        assert page.get_by_label('Household member '+name,exact=True).locator('time').first.get_attribute('datetime')==created
        record('household-snapshot-timestamp-restore','Client-recorded member creation survives server-confirmed preparation save/refresh')
        # Separate real anonymous identity. Never expose tokens in evidence.
        other=browser.new_context(base_url=BASE)
        other_page=other.new_page()
        with other_page.expect_response(lambda r:r.request.method=='GET' and r.url.endswith('/api/documents')) as other_list:
            other_page.goto('/documents')
        assert other_list.value.status==200 and other_list.value.json()==[]
        other_headers={'Authorization':other_list.value.request.headers['authorization']}
        for method,suffix,payload in [('GET','',None),('GET','/file',None),('PATCH','',{'revision':2,'metadata':{'category':'other'}}),('DELETE','?revision=2',None)]:
            response=other.request.fetch(BASE+'/api/documents/'+document_id+suffix,method=method,headers=other_headers,**({'data':payload} if payload else {}))
            assert response.status==(204 if method=='DELETE' else 404),(method,response.status,response.text())
        assert ctx.request.get(BASE+'/api/documents/'+document_id,headers=headers).status==200
        assert ctx.request.get(BASE+'/api/documents').status==401
        assert other.request.get(BASE+'/api/applications/'+application_id,headers=other_headers).status==404
        record('real-two-user-document-and-preparation-isolation','Other user list empty; GET/file/PATCH denied; foreign DELETE no-op preserves original; missing token 401')
        other.close()
        # Backend guidance uses only explicit minimized reviewed context; no AI request.
        page.locator('a[href="/workflows"]').first.click()
        page.locator('#blocker').fill('My address proof was not accepted')
        page.get_by_role('checkbox',name='I consent to share one selected reviewed proof',exact=False).check()
        page.get_by_label('Reviewed address proof',exact=True).select_option(document_id)
        with page.expect_response(lambda r:r.url.endswith('/api/citizen-workflows/human-support')) as guidance:
            page.get_by_role('button',name='Get my guidance',exact=True).click()
        assert guidance.value.status==200
        assert any('utility bill' in x for x in guidance.value.json()['supportChecklist'])
        record('consented-contextual-blocker','Selected reviewed Utility bill produces possible checks; no Gemini call or invented expiry')
        page.locator('a[href="/documents"]').first.click()
        page.once('dialog',lambda d:d.dismiss())
        page.get_by_role('button',name='Delete this account’s cloud Vault and local copies',exact=True).click()
        assert ctx.request.get(BASE+'/api/documents/'+document_id,headers=headers).status==200
        page.once('dialog',lambda d:d.accept())
        with page.expect_response(lambda r:r.request.method=='DELETE' and r.url.endswith('/api/documents')) as deleted:
            page.get_by_role('button',name='Delete this account’s cloud Vault and local copies',exact=True).click()
        assert deleted.value.status==200 and document_id in deleted.value.json()['deleted']
        assert deleted.value.json()['failed']==[]
        page.reload()
        expect(page.get_by_text('No documents yet',exact=True)).to_be_visible()
        assert ctx.request.get(BASE+'/api/documents/'+document_id,headers=headers).status==404
        page.goto('/services/passport/journey?preparation='+application_id)
        expect(page.get_by_text('saved document reference(s) are unavailable',exact=False)).to_be_visible()
        record('real-confirmed-cloud-deletion-and-missing-reference','Cancel preserves; confirmation deletes; refresh stays empty; preparation warns without deleting application')
        # Clean up only the preparation created by this run, using current revision.
        current=ctx.request.get(BASE+'/api/applications/'+application_id,headers=headers).json()
        assert ctx.request.delete(BASE+'/api/applications/'+application_id+'?revision='+str(current['revision']),headers=headers).status==204
        assert not errors,errors
        assert not localhost,localhost
        record('runtime-and-production-routing','No uncaught browser errors or localhost calls; fictional test preparation cleaned up')
        ctx.close();browser.close()

if __name__=='__main__':main()
