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


def cards(page):
    return page.locator('article[data-service-id]')


def test_catalogue_prominence_status_semantics_and_passport(page):
    page.goto('/services')
    expect(cards(page)).to_have_count(12)
    assert cards(page).evaluate_all('(els)=>els.slice(0,3).map(e=>e.dataset.serviceId)') == ['passport','aadhaar','epfo']
    expect(page.locator('[data-service-id="passport"]')).to_contain_text('Guided preview available')
    for ident in ['aadhaar','epfo']:
        card=page.locator(f'[data-service-id="{ident}"]')
        expect(card).to_contain_text('Coming Soon')
        expect(card.locator('a,button,input,select,[tabindex]')).to_have_count(0)
    page.get_by_role('link',name='Explore Passport Seva').click()
    expect(page).to_have_url(re.compile('/services/passport$'))
    expect(page.get_by_role('link', name=re.compile('Applying for a new passport'))).to_be_visible()


@pytest.mark.parametrize('query,title',[
    (' RTO ','Driving Licence Renewal'),('dl','Permanent Driving Licence'),
    ('RC','Duplicate Vehicle RC'),('ITR','Income Tax Return Filing'),
    ('PAN','PAN Card Application'),('EPFO','EPFO Services'),
    ('PM Kisan','PM-KISAN Farmer Registration'),('Marriage','Marriage Registration'),
    ('Birth','Birth Registration'),('Disaster Damage','Disaster Damage Compensation Scheme'),
])
def test_browser_search_full_catalogue_and_synonyms(page,query,title):
    page.goto('/services')
    page.get_by_role('searchbox',name='Search government services').fill(query)
    expect(page.get_by_role('heading',name=title,exact=True)).to_be_visible()
    assert 0 < cards(page).count() <= 12


@pytest.mark.parametrize('category',['identity','family','transport','tax','housing','utilities','health','jobs','welfare','education','agriculture','business','justice','tourism','culture','digital','defence','governance'])
def test_browser_category_filter(page,catalogue,category):
    page.goto('/services')
    page.get_by_label('Category',exact=True).select_option(category)
    expected=[s for s in catalogue['services'] if category in s.get('categories',[s['category']])]
    expect(cards(page)).to_have_count(min(12,len(expected)))
    expect(page.get_by_role('status')).to_have_text(f'Showing {min(12,len(expected))} of {len(expected)} services (256 in the catalogue)')
    assert cards(page).evaluate_all('(els)=>els.map(e=>e.dataset.serviceId)') == [s['id'] for s in expected[:12]]


def test_combination_empty_reset_and_pagination(page,catalogue):
    page.goto('/services')
    page.get_by_role('button',name='Load More',exact=True).click()
    expect(cards(page)).to_have_count(24)
    page.get_by_label('Category',exact=True).select_option('tax')
    expect(cards(page)).to_have_count(12)
    search=page.get_by_role('searchbox',name='Search government services')
    search.fill('ITR')
    expect(page.get_by_role('heading',name='Income Tax Return Filing',exact=True)).to_be_visible()
    page.get_by_label('Category',exact=True).select_option('health')
    expect(page.get_by_role('heading',name='No matching services found')).to_be_visible()
    expect(cards(page)).to_have_count(0)
    page.get_by_role('button',name='Reset Filters',exact=True).click()
    expect(search).to_have_value('')
    expect(cards(page)).to_have_count(12)
    # Walk every page, verifying unique identities and truthful unsupported semantics.
    while page.get_by_role('button',name='Load More',exact=True).count():
        page.get_by_role('button',name='Load More',exact=True).click()
    expect(cards(page)).to_have_count(len(catalogue['services']))
    ids=cards(page).evaluate_all('(els)=>els.map(e=>e.dataset.serviceId)')
    assert len(set(ids))==len(ids)
    expect(cards(page).filter(has_not=page.get_by_role('link',name='Explore Passport Seva')).locator('a,button,input,select,[tabindex]')).to_have_count(0)
    expect(page.get_by_role('status')).to_have_text('Showing 256 of 256 services')
    search.fill('birth')
    expect(cards(page)).to_have_count(3)


@pytest.mark.parametrize('width,columns',[(390,1),(834,2),(1440,3)])
def test_catalogue_responsive_keyboard_and_existing_style(page,width,columns):
    page.set_viewport_size({'width':width,'height':1000})
    page.goto('/services?q=Marriage')
    search=page.get_by_role('searchbox',name='Search government services')
    expect(search).to_have_value('Marriage')
    search.focus();search.press('Tab')
    expect(page.get_by_label('Category',exact=True)).to_be_focused()
    page.keyboard.press('Tab');expect(page.get_by_role('button',name='Reset Filters',exact=True)).to_be_focused()
    page.keyboard.press('Enter')
    expect(cards(page)).to_have_count(12)
    grid=page.get_by_label('Government service catalogue')
    assert grid.evaluate('(e)=>getComputedStyle(e).gridTemplateColumns.split(" ").length')==columns
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    style=cards(page).first.evaluate('(e)=>{const s=getComputedStyle(e);return [s.backgroundColor,s.borderRadius,s.padding]}')
    assert style==['rgb(255, 255, 255)','16px','28px']
    expect(page.get_by_text('Service Navigator',exact=True)).to_be_visible()
    expect(page.get_by_role('link',name='Explore Passport Seva')).to_be_visible()
    assert page.locator('header').filter(has=page.get_by_text('Service Navigator',exact=True)).evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(27, 65, 104)'
    comparison=EVIDENCE.parent/'comparison'
    comparison.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(comparison/f'services-after-{width}.png'),full_page=False,animations='disabled')
    if width == 390:
        while page.get_by_role('button',name='Load More',exact=True).count():
            page.get_by_role('button',name='Load More',exact=True).click()
        expect(cards(page)).to_have_count(256)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')


def test_static_catalogue_no_service_api_or_interaction_requests(page):
    calls=[]
    page.on('request',lambda r:calls.append(r.url) if '/api/' in r.url else None)
    # Existing DocumentProvider restores its Vault independently of this page.
    # Finish that real initial request before measuring catalogue interactions.
    with page.expect_response(lambda response: response.url.endswith('/api/documents')):
        page.goto('/services')
    expect(cards(page)).to_have_count(12)
    assert not any('/api/services' in url for url in calls)
    before=list(calls)
    page.get_by_role('searchbox',name='Search government services').fill('RTO')
    page.get_by_label('Category',exact=True).select_option('transport')
    page.get_by_role('button',name='Load More',exact=True).click()
    expect(cards(page)).to_have_count(18)
    assert calls==before
    link=page.get_by_role('link',name=re.compile('external government website'))
    expect(link).to_have_attribute('href','https://services.india.gov.in/feed/index?ln=en')
    expect(link).to_have_attribute('rel','noopener noreferrer')
