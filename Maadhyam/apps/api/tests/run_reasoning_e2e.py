#!/usr/bin/env python3
"""M7/M8 browser + real API tests. Requires running frontend/backend; no API mocks."""
import argparse
import json
from playwright.sync_api import sync_playwright

PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')

def require(value, message):
    if not value: raise AssertionError(message)

def upload(page, name, printed_name, holder='self'):
    page.get_by_label('Choose documents to add').set_input_files({'name':name,'mimeType':'image/png','buffer':PNG})
    page.get_by_text(name).first.wait_for()
    row = page.locator('article').filter(has_text=name)
    button = row.get_by_role('button', name='Edit details')
    if button.count()!=1: button = page.get_by_role('button', name='Edit details')
    button.click()
    dialog=page.get_by_role('dialog',name='Edit document details')
    dialog.locator('#metadata-printed-name').fill(printed_name)
    dialog.locator('#metadata-holder').select_option(holder)
    dialog.get_by_role('button',name='Save details').click()
    dialog.wait_for(state='hidden')
    row=page.locator('article').filter(has_text=name)
    review=row.get_by_role('button',name='Mark self-reviewed')
    if review.count()!=1: review=page.get_by_role('button',name='Mark self-reviewed')
    review.click()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report', default='reasoning-e2e-results.json')
    parser.add_argument('--web',default='http://127.0.0.1:5173')
    parser.add_argument('--headed',action='store_true')
    args=parser.parse_args()
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=not args.headed)
        context=browser.new_context(base_url=args.web)
        page=context.new_page()
        captured=[]
        def on_response(response):
            if '/api/intelligence/reasoning' in response.url and response.request.method=='POST':
                try: captured.append({'request':response.request.post_data_json,'response':response.json(),'status':response.status})
                except Exception: pass
        page.on('response',on_response)
        def check(name, fn):
            try: fn(); results.append((name,'PASS','')); print('PASS',name,flush=True)
            except Exception as e: results.append((name,'FAIL',str(e))); print('FAIL',name,'\n ',str(e),flush=True)
        page.goto('/documents')
        upload(page,'fictional-aadhaar.png','Rahul Kumar Sharma')
        upload(page,'fictional-pan.png','Rahul K Sharma')
        upload(page,'fictional-parent.png','Parent Sharma','parent-guardian')
        # Navigate via client-side router: don't reset in-memory Vault.
        page.get_by_role('link',name='Resolution Planner').first.click()
        page.get_by_label('Minimum prerequisite review path').wait_for(timeout=20000)
        def baseline():
            require(captured and captured[-1]['status']==200,'No successful real reasoning API response')
            require(len(captured[-1]['request']['documents'])==3,'Vault metadata missing in reasoning request')
            require('printedName-conflict' in captured[-1]['response']['baseline']['reviewFindings'],'Name mismatch not detected')
        check('RE01 Real API receives reviewed Vault metadata and detects conflict',baseline)
        def graph():
            graph=captured[-1]['response']['dependencyGraph']; order=graph['executionOrder']
            require(all(order.index(edge['before']) < order.index(edge['after']) for edge in graph['edges']),'Invalid task ordering')
            page.get_by_text('See your preparation steps and analysis details',exact=True).click()
            require(page.locator('details[open] ol').count()>0,'Dependency order not rendered')
        check('RE02 Dependency-safe graph rendered and valid',graph)
        def simulate():
            page.get_by_label('What-if document').select_option(label='fictional-pan.png')
            page.get_by_label('Hypothetical value').fill('Rahul Kumar Sharma')
            before=len(captured)
            page.get_by_role('button',name='See the impact').click()
            page.get_by_text("Here's what your correction could change",exact=True).wait_for(timeout=20000)
            require(len(captured)>before,'Simulation did not call real API')
            data=captured[-1]
            require(data['status']==200,'Simulation failed')
            require(data['request']['simulations'][0]['replaceFields'],'Replacement missing from API request')
            require('printedName-conflict' in data['response']['simulations'][0]['resolvedFindingIds'],'Conflict not resolved in simulation')
            require(page.get_by_text('Potentially resolved: printedName-conflict',exact=True).is_visible(),'Resolved finding not rendered')
            require(data['response']['simulations'][0]['officialAcceptanceVerified'] is False,'Incorrect official acceptance claim')
        check('RE03 What-if recomputes and displays resolved name conflict',simulate)
        def family():
            page.get_by_role('button',name="I have a family member's document").click()
            page.get_by_label('Family document',exact=True).select_option(label='fictional-parent.png')
            page.get_by_label('Claimed relationship').select_option('parent')
            # The "Official relationship verified: No" text is already visible
            # from the baseline response. Wait for the NEW network response,
            # not for that stale text, to avoid a timing-dependent false fail.
            def is_family_response(response):
                if '/api/intelligence/reasoning' not in response.url or response.request.method != 'POST':
                    return False
                try:
                    links = response.request.post_data_json.get('familyLinks', [])
                    return any(link.get('relation') == 'parent' for link in links)
                except (AttributeError, TypeError, ValueError):
                    return False
            with page.expect_response(is_family_response, timeout=20000) as response_info:
                page.get_by_role('button',name='Check relationship evidence').click()
            response = response_info.value
            require(response.status == 200, f'Family reasoning API returned {response.status}')
            request = response.request.post_data_json
            data = response.json()
            require(request['familyLinks'][0]['relation']=='parent','Family relation not forwarded')
            require(data['familyEvidence']['officialRelationshipVerified'] is False,'Unverified relationship falsely verified')
            page.get_by_text('Relationship and proof acceptance still require official verification.',exact=True).wait_for(timeout=20000)
        check('RE04 Family claim reaches real API, remains unverified',family)
        def reset():
            page.get_by_role('button',name='I need to correct a detail').click()
            page.get_by_role('button',name='Start over',exact=True).click()
            page.get_by_text("Here's what your correction could change",exact=True).wait_for(state='hidden',timeout=20000)
            require(not captured[-1]['request']['simulations'],'Simulation not cleared in request')
        check('RE05 Clearing what-if removes hypothetical changes',reset)
        browser.close()
    passed=sum(s=='PASS' for _,s,_ in results)
    print(f'\n{passed} passed, {len(results)-passed} failed',flush=True)
    with open(args.report,'w',encoding='utf-8') as f: json.dump([{'case':n,'status':s,'detail':d} for n,s,d in results],f,indent=2)
    return 0 if passed==len(results) else 1

if __name__=='__main__': raise SystemExit(main())
