"""Consolidated UI regressions; isolated fictional fixtures, no production writes."""
import json
import subprocess
from pathlib import Path
import pytest
from playwright.sync_api import expect
from qa.conftest import EVIDENCE
ROOT=Path(__file__).resolve().parents[1]
GUIDANCE=ROOT/'Maadhyam/apps/web/src/data/assistantGuidance.ts'

@pytest.fixture(scope='module')
def guidance():
    result=subprocess.run(['node','--input-type=module','-e',f"import * as g from '{GUIDANCE.as_uri()}'; console.log(JSON.stringify(g.assistantGuidance)); for(const [key,value] of Object.entries(g.assistantGuidance)) {{ if(g.getAssistantPage(value.path)!==key) throw Error(key); for(const question of value.prompts) {{if(!g.getProductGuidance(question)?.answer.includes(value.answer)) throw Error(question);}}}}"],capture_output=True,text=True,check=True)
    return json.loads(result.stdout)

@pytest.mark.parametrize('width',[375,768,1024,1440])
def test_dashboard_hero_quick_links(page,width):
    page.set_viewport_size({'width':width,'height':900});page.goto('/')
    hero=page.locator('main > div > section').first
    expect(hero.locator('a')).to_have_count(1)
    title=hero.get_by_role('heading',level=1)
    expect(title.locator('span')).to_have_text(['Your documents. Your next step.','Made clearer.'])
    if width>=768:
        first,second=title.locator('span').all()
        assert first.bounding_box()['height'] < second.bounding_box()['height']*1.1
        assert first.bounding_box()['y'] < second.bounding_box()['y']
    expect(page.get_by_role('heading',name='Quick links',exact=True)).to_be_visible()
    assert page.get_by_text('Passport: guided preparation · Aadhaar and EPFO: advisory service information.',exact=True).count()==0
    for label,path in [('Passport assistance','/services/passport'),('Aadhaar guidance','/services?q=Aadhaar'),('EPFO guidance','/services?q=EPFO')]:
        expect(page.get_by_role('link',name=label,exact=True)).to_have_attribute('href',path)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(EVIDENCE/f'dashboard-{width}.png'),full_page=True)
    hero.get_by_role('link',name='Explore services',exact=True).click();expect(page).to_have_url('http://127.0.0.1:'+page.url.split(':')[2].split('/')[0]+'/services')

@pytest.mark.parametrize('key',['dashboard','services','household','workflows','documents','applications','planner','passport'])
def test_contextual_prompts_and_local_answers(page,guidance,key):
    entry=guidance[key];page.goto(entry['path']);page.get_by_role('button',name='Open Maadhyam AI',exact=True).click()
    panel=page.get_by_role('dialog',name='Maadhyam AI assistant');calls=[]
    page.on('request',lambda r:calls.append(r.url) if '/api/intelligence/chat' in r.url else None)
    for prompt in entry['prompts']:
        panel.get_by_role('button',name=prompt,exact=True).click()
        expect(panel.get_by_text(entry['answer'],exact=True).last).to_be_visible()
    assert calls==[]
    expect(panel.get_by_role('button',name=entry['label'],exact=True).last).to_be_visible()
    page.screenshot(path=str(EVIDENCE/f'assistant-{key}.png'))

@pytest.mark.parametrize('width,height',[(375,667),(768,600),(1024,900),(1440,1000),(375,400)])
def test_assistant_collapse_composer_focus_and_history(page,width,height):
    page.set_viewport_size({'width':width,'height':height});page.goto('/');page.get_by_role('button',name='Open Maadhyam AI',exact=True).click()
    panel=page.get_by_role('dialog',name='Maadhyam AI assistant');composer=panel.get_by_label('Message to Maadhyam AI')

    if height<600:panel.get_by_role('button',name='Show suggestions',exact=False).click()
    composer.fill('Draft fictional question');before=panel.locator('.assistant-scroll').bounding_box()['height']
    toggle=panel.locator('[aria-controls="assistant-suggestions"]');toggle.click()
    expect(panel.locator('#assistant-suggestions')).to_be_hidden();expect(toggle).to_have_attribute('aria-expanded','false')
    assert panel.locator('.assistant-scroll').bounding_box()['height']>before
    expect(composer).to_have_value('Draft fictional question');expect(composer).to_be_visible()
    panel.get_by_role('button',name='Show suggestions',exact=False).click()
    expect(panel.locator('#assistant-suggestions')).to_be_visible()
    panel_box=panel.bounding_box();input_box=composer.bounding_box()
    assert input_box['y']+input_box['height']<=panel_box['y']+panel_box['height'], 'Expanded suggestions clip composer'
    header=panel.get_by_role('heading',name='Maadhyam AI',exact=True).bounding_box()
    assert header['y']>=panel_box['y'], 'Panel header is clipped'
    composer.fill('Help me with passport preparation');panel.get_by_role('button',name='Send message',exact=True).click()
    expect(panel.get_by_text('Open Passport Seva and choose',exact=False)).to_be_visible()
    panel.get_by_role('button',name='Hide suggestions',exact=False).click()
    page.keyboard.press('Escape');expect(panel).to_have_count(0)
    expect(page.get_by_role('button',name='Open Maadhyam AI',exact=True)).to_be_focused()
    page.get_by_role('button',name='Open Maadhyam AI',exact=True).click()
    expect(panel.locator('#assistant-suggestions')).to_be_hidden()
    expect(panel.get_by_text('Open Passport Seva and choose',exact=False)).to_be_visible()
    box=composer.bounding_box();assert box['y']>=0 and box['y']+box['height']<=height
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    expect(page.get_by_role('button',name='Close AI assistant',exact=True)).to_have_count(1)
    expect(page.get_by_role('button',name='Close Maadhyam AI',exact=True)).to_have_count(0)
    page.screenshot(path=str(EVIDENCE/f'assistant-{width}-{height}.png'))

@pytest.mark.parametrize('width',[375,768,1024,1280,1440,1920])
def test_shared_content_boundaries(page,width):
    page.set_viewport_size({'width':width,'height':1000});boundaries=[]
    for route in ['/','/documents','/workflows','/applications','/planner','/household']:
        page.goto(route);root=page.locator('main > *').first
        box=root.bounding_box();boundaries.append((route,round(box['x'],1),round(box['width'],1)))
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),route
        if route in ['/applications','/planner','/household']:
            page.screenshot(path=str(EVIDENCE/f'{route[1:]}-{width}.png'),full_page=True)
    assert len({(x,w) for _,x,w in boundaries})==1,boundaries
