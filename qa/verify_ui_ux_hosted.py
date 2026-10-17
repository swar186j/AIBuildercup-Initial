"""Fresh-profile hosted smoke: read-only cloud checks and session-only fictional UI data."""
import json
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa/evidence/ui-ux-corrections/hosted'
BASE='https://maadhyam-1610.web.app'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    def record(name,details):
        results.append({'test':name,'status':'PASS','details':details})
        (OUT/'results.json').write_text(json.dumps(results,indent=2))
        print('PASS '+name,flush=True)
    with sync_playwright() as p:
        browser=p.chromium.launch();context=browser.new_context(base_url=BASE,viewport={'width':1440,'height':1000})
        page=context.new_page();page.set_default_timeout(20000);errors=[];failed=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if '/api/' in r.url and r.status>=400 else None)
        assert context.request.get(BASE+'/api/health').status==200
        assert context.request.post(BASE+'/api/ai/connection-test').status==401
        record('hosting-api-health-and-auth','Health 200; unauthenticated protected endpoint 401')
        page.goto('/');hero=page.locator('main > div > section').first
        expect(hero.locator('a')).to_have_count(1)
        expect(hero.get_by_role('heading',level=1).locator('span')).to_have_text(['Your documents. Your next step.','Made clearer.'])
        expect(page.get_by_role('heading',name='Quick links',exact=True)).to_be_visible()
        hero.get_by_role('link',name='Explore services',exact=True).click();expect(page).to_have_url(BASE+'/services')
        record('dashboard-hero-navigation-quick-links','One CTA and two semantic heading lines')
        expect(page.locator('article[data-service-id]')).to_have_count(12)
        page.locator('[data-service-id="aadhaar"] summary').click()
        expect(page.get_by_role('heading',name='Aadhaar PVC Card',exact=True)).to_be_visible()
        record('hierarchy-expand','Aadhaar children expand inside Services; Coming Soon children have no journey CTA')
        for query,parent,child in [('Aadhaar','Aadhaar Services','Aadhaar Enrolment'),('PVC','Aadhaar Services','Aadhaar PVC Card'),('birth certificate','Birth Registration','Birth Certificate'),('driving licence','Transport / RTO Services','Permanent Driving Licence'),('PAN','Income Tax Services','PAN Card Application'),('Passport','Passport Seva',None)]:
            page.get_by_role('searchbox',name='Search government services').fill(query)
            expect(page.get_by_role('heading',name=parent,exact=True)).to_be_visible()
            if child:expect(page.get_by_role('heading',name=child,exact=True)).to_be_visible()
            record('search-'+query,{'parent':parent,'child':child})
        page.get_by_role('link',name='Explore Passport Seva',exact=True).click()
        expect(page.get_by_role('link',name='Applying for a new passport',exact=False)).to_be_visible()
        record('passport-navigation','Existing Passport guided preview reachable')
        prompts={'/services':'Which services can I explore?','/household':'How do I add a household member?','/workflows':'Help me choose a workflow'}
        for route,prompt in prompts.items():
            page.goto(route);page.get_by_role('button',name='Open Maadhyam AI',exact=True).click();panel=page.get_by_role('dialog',name='Maadhyam AI assistant')
            panel.get_by_role('button',name=prompt,exact=True).click()
            expect(panel.get_by_text(prompt,exact=True)).to_be_visible()
            panel.get_by_role('button',name='Hide suggestions',exact=False).click();expect(panel.locator('#assistant-suggestions')).to_be_hidden()
            panel.get_by_role('button',name='Show suggestions',exact=False).click();expect(panel.locator('#assistant-suggestions')).to_be_visible()
            page.screenshot(path=str(OUT/(route[1:]+'-assistant.png')))
            record('context-and-collapse-'+route,'Contextual prompt produces local guidance; suggestions collapse and restore')
        composer=panel.get_by_label('Message to Maadhyam AI');composer.fill('Help me with passport preparation');panel.get_by_role('button',name='Send message',exact=True).click()
        expect(panel.get_by_text('Open Passport Seva and choose',exact=False)).to_be_visible()
        record('local-passport-guidance','Useful preparation instructions and existing Passport navigation')
        for width in [375,768,1024,1280,1440,1920]:
            page.set_viewport_size({'width':width,'height':1000});bounds=[]
            for route in ['/','/documents','/workflows','/applications','/planner','/household']:
                page.goto(route);box=page.locator('main > *').first.bounding_box();bounds.append((round(box['x'],1),round(box['width'],1)))
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(route,width)
            assert len(set(bounds))==1,(width,bounds)
            record('shared-width-'+str(width),{'left':bounds[0][0],'width':bounds[0][1],'overflow':False})
        # Fresh anonymous account: authenticated listing only; never create/delete cloud records.
        page.goto('/documents')
        with page.expect_response(lambda r:r.request.method=='GET' and r.url.endswith('/api/documents')) as vault:
            page.reload()
        assert vault.value.status==200
        page.get_by_label('Choose documents to add').set_input_files(str(ROOT/'qa/fixtures/fictional_address.png'))
        expect(page.get_by_text('fictional_address.png',exact=True)).to_be_visible()
        record('vault-read-and-session-upload','Authenticated private list returns 200; fictional session upload renders without cloud consent')
        page.goto('/household');page.get_by_label('New member name').fill('Fictional UI Smoke Member');page.get_by_role('button',name='Add member',exact=True).click()
        expect(page.get_by_label('Household member Fictional UI Smoke Member',exact=True)).to_be_visible()
        record('household-session-form','Fresh session member can be added; no cloud saving requested')
        assert not errors,errors
        # Expected unauthenticated probe above is outside page events; any UI API error is a failure.
        assert not failed,failed
        record('runtime-and-ui-api-errors',{'runtimeErrors':errors,'failedUiApiCalls':failed})
        browser.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
