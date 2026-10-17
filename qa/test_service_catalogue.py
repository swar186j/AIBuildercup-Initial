"""Catalogue acceptance against the user's independent seed inventory and real Chromium UI."""
import json
from pathlib import Path
import re
import subprocess
import pytest
from playwright.sync_api import expect
from qa.conftest import EVIDENCE

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'Maadhyam/apps/web/src/data/governmentServices.ts'


@pytest.fixture(scope='module')
def catalogue():
    result = subprocess.run(['node', '--input-type=module', '-e',
        f"import * as c from '{MODULE.as_uri()}'; console.log(JSON.stringify({{services:c.governmentServices,categories:c.serviceCategories}}))"],
        capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_all_requested_seed_concepts_and_unique_identities(catalogue):
    seeds = json.loads((ROOT/'qa/fixtures/service_catalogue_seed.json').read_text())
    services = catalogue['services']
    for group, terms in seeds.items():
        for term in terms:
            matches = [s for s in services if term in s['seedTerms']]
            assert len(matches) == 1, (group, term, matches)
    assert len({s['id'] for s in services}) == len(services)
    normalize = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
    assert len({normalize(s['title']) for s in services}) == len(services)
    assert len(services) == 256
    guided = [s for s in services if s['status'] == 'guided-preview']
    assert [(s['id'], s['supportedRoute']) for s in guided] == [('passport','/services/passport')]
    assert all(s['status']=='coming-soon' and not s.get('supportedRoute') for s in services if s not in guided)
    assert len(catalogue['categories']) == 18
    assert {s['category'] for s in services} == {c['id'] for c in catalogue['categories']}
    assert all(s['description'] and s['keywords'] and s['scope'] in ['central','state-specific','varies'] for s in services)
    assert all(s['scope']=='state-specific' for s in services if 'Maharashtra' in s['title'])
    local_ids = ['event-public-gathering-permission', 'farmer-registration-farmer-id-services', 'lost-document-report', 'police-complaint-services', 'police-verification-services', 'state-government-citizen-service-portals', 'state-scholarship-applications']
    assert all(s['scope']=='state-specific' for s in services if s['id'] in local_ids)
    assert all('officialCategoryUrl' not in s for s in services), 'No unverified individual links'


def test_search_fields_and_all_category_mappings(catalogue):
    # Every record must be discoverable by its full title, plus actual description/keyword/category terms.
    code = f"""import assert from 'node:assert/strict'; import * as c from '{MODULE.as_uri()}';
    for(const s of c.governmentServices) {{
      assert(c.filterGovernmentServices(s.title).some(x=>x.id===s.id),s.title);
      assert(c.filterGovernmentServices(s.description).some(x=>x.id===s.id),s.description);
      for(const category of s.categories??[s.category]) {{
        assert(c.filterGovernmentServices('',category).some(x=>x.id===s.id));
        assert(c.filterGovernmentServices(c.serviceCategories.find(x=>x.id===category).label).some(x=>x.id===s.id));
      }}
      for(const term of s.keywords) assert(c.filterGovernmentServices(term).some(x=>x.id===s.id),term);
    }}
    assert.deepEqual(c.filterGovernmentServices(' PM Kisan ').map(x=>x.id),c.filterGovernmentServices('pm-kisan').map(x=>x.id));
    assert.equal(c.filterGovernmentServices('ITR','health').length,0);
    assert(c.filterGovernmentServices('ITR','tax').length>0);
    """
    subprocess.run(['node','--input-type=module','-e',code],check=True)


def test_existing_routes_unchanged():
    source = (ROOT/'Maadhyam/apps/web/src/App.tsx').read_text()
    baseline = json.loads((ROOT/'qa/fixtures/service_catalogue_routes.json').read_text())
    assert re.findall(r'<Route\s+path="([^"]+)"', source) == baseline


def test_hierarchy_coverage_identity_and_search():
    code = f"""import assert from 'node:assert/strict'; import * as c from '{MODULE.as_uri()}';
    const families=c.serviceFamilies, sources=families.flatMap(f=>f.sourceIds), children=families.flatMap(f=>f.children);
    assert.equal(families.length,30); assert.equal(children.length,250);
    assert.equal(new Set(families.map(f=>f.id)).size,families.length);
    assert.equal(new Set(families.map(f=>f.title)).size,families.length);
    assert.equal(new Set(children.map(s=>s.id)).size,children.length);
    assert.equal(new Set(sources).size,256);
    assert.deepEqual([...sources].sort(),c.governmentServices.map(s=>s.id).sort());
    assert(children.every(s=>!families.some(f=>f.id===s.id)));
    assert.deepEqual(families.filter(f=>f.status==='guided-preview').map(f=>f.id),['passport']);
    for(const s of c.governmentServices) assert(c.filterServiceFamilies(s.title).some(f=>f.sourceIds.includes(s.id)),s.title);
    for(const [q,parent,child] of [['Aadhaar','aadhaar'],['PVC','aadhaar','aadhaar-pvc-card'],['birth certificate','birth-registration','birth-certificate'],['driving licence','transport-rto','permanent-driving-licence'],['PAN','income-tax','pan-card-application'],['passport','passport']]) {{
      const family=c.filterServiceFamilies(q).find(f=>f.id===parent);assert(family,q);
      if(child)assert(family.displayedChildren.some(s=>s.id===child),q);
    }}
    assert.equal(c.filterServiceFamilies('no-such-fictional-service').length,0);
    """
    subprocess.run(['node','--input-type=module','-e',code],check=True)


def cards(page):
    return page.locator('article[data-service-id]')


def test_catalogue_prominence_status_semantics_and_passport(page):
    page.goto('/services')
    expect(cards(page)).to_have_count(12)
    assert cards(page).evaluate_all('(els)=>els.slice(0,3).map(e=>e.dataset.serviceId)') == ['passport','aadhaar','epfo']
    for ident in ['aadhaar','epfo']:
        card=page.locator(f'[data-service-id="{ident}"]')
        expect(card).to_contain_text('Coming Soon')
        expect(card.locator('a,button')).to_have_count(0)
        card.locator('summary').focus();page.keyboard.press('Enter')
        expect(card.locator('[data-child-id]').first).to_be_visible()
        expect(card.locator('[data-child-id] a,[data-child-id] button')).to_have_count(0)
    page.get_by_role('link',name='Explore Passport Seva').click()
    expect(page).to_have_url(re.compile('/services/passport$'))
    expect(page.get_by_role('link', name=re.compile('Applying for a new passport'))).to_be_visible()


@pytest.mark.parametrize('query,parent,title',[
    ('Aadhaar','Aadhaar Services','Aadhaar Enrolment'),('PVC','Aadhaar Services','Aadhaar PVC Card'),
    ('birth certificate','Birth Registration','Birth Certificate'),
    ('driving licence','Transport / RTO Services','Permanent Driving Licence'),
    ('PAN','Income Tax Services','PAN Card Application'),
    ('passport','Passport Seva',None),('PM Kisan','PM-KISAN Services','PM-KISAN Farmer Registration'),
])
def test_browser_search_full_catalogue_and_synonyms(page,query,parent,title):
    page.goto('/services')
    page.get_by_role('searchbox',name='Search government services').fill(query)
    expect(page.get_by_role('heading',name=parent,exact=True)).to_be_visible()
    if title:expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
    assert 0 < cards(page).count() <= 12


@pytest.mark.parametrize('category',['identity','family','transport','tax','housing','utilities','health','jobs','welfare','education','agriculture','business','justice','tourism','culture','digital','defence','governance'])
def test_browser_category_filter(page,category):
    page.goto('/services')
    page.get_by_label('Category',exact=True).select_option(category)
    assert 0 < cards(page).count() <= 12
    ids=cards(page).evaluate_all('(els)=>els.map(e=>e.dataset.serviceId)')
    assert len(ids)==len(set(ids))
    for details in page.locator('details').all():details.locator('summary').click()
    for child in page.locator('[data-child-id]').all():
        expect(child).to_contain_text('Guided preparation Coming Soon')


def test_combination_empty_reset_and_pagination(page):
    page.goto('/services')
    page.get_by_role('button',name='Load More',exact=True).click()
    expect(cards(page)).to_have_count(24)
    page.get_by_label('Category',exact=True).select_option('tax')
    search=page.get_by_role('searchbox',name='Search government services');search.fill('ITR')
    expect(page.get_by_role('heading',name='Income Tax Return Filing',exact=True)).to_be_visible()
    page.get_by_label('Category',exact=True).select_option('health')
    expect(page.get_by_role('heading',name='No matching services found')).to_be_visible()
    page.get_by_role('button',name='Reset Filters',exact=True).click()
    expect(search).to_have_value('')
    while page.get_by_role('button',name='Load More',exact=True).count():page.get_by_role('button',name='Load More',exact=True).click()
    expect(cards(page)).to_have_count(30)
    expect(page.get_by_role('status')).to_have_text('Showing 30 of 30 service families · 256 catalogue records')
    for summary in page.locator('summary').all():summary.click()
    expect(page.locator('[data-child-id]')).to_have_count(250)
    ids=page.locator('[data-child-id]').evaluate_all('(els)=>els.map(e=>e.dataset.childId)')
    assert len(ids)==len(set(ids))


@pytest.mark.parametrize('width,columns',[(375,1),(768,2),(1440,3)])
def test_catalogue_responsive_keyboard_and_existing_style(page,width,columns):
    page.set_viewport_size({'width':width,'height':1000});page.goto('/services?q=Marriage')
    search=page.get_by_role('searchbox',name='Search government services');expect(search).to_have_value('Marriage')
    search.focus();search.press('Tab');expect(page.get_by_label('Category',exact=True)).to_be_focused()
    page.keyboard.press('Tab');expect(page.get_by_role('button',name='Reset Filters',exact=True)).to_be_focused()
    page.keyboard.press('Enter');expect(cards(page)).to_have_count(12)
    grid=page.get_by_label('Government service catalogue')
    assert grid.evaluate('(e)=>getComputedStyle(e).gridTemplateColumns.split(" ").length')==columns
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    style=cards(page).first.evaluate('(e)=>{const s=getComputedStyle(e);return [s.backgroundColor,s.borderRadius,s.padding]}')
    assert style==['rgb(255, 255, 255)','16px','28px']
    page.screenshot(path=str(EVIDENCE/f'services-{width}.png'),full_page=True,animations='disabled')


def test_static_catalogue_no_service_api_or_interaction_requests(page):
    calls=[];page.on('request',lambda r:calls.append(r.url) if '/api/' in r.url else None)
    with page.expect_response(lambda response: response.url.endswith('/api/documents')):page.goto('/services')
    expect(cards(page)).to_have_count(12)
    assert not any('/api/services' in url for url in calls)
    before=list(calls)
    page.get_by_role('searchbox',name='Search government services').fill('RTO')
    page.get_by_label('Category',exact=True).select_option('transport')
    page.locator('summary').click()
    assert calls==before
    link=page.get_by_role('link',name=re.compile('external government website'))
    expect(link).to_have_attribute('href','https://services.india.gov.in/feed/index?ln=en')
    expect(link).to_have_attribute('rel','noopener noreferrer')
