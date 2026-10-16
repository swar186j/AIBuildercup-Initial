"""Build the traceability matrix and result counts from actual final evidence."""
import csv,json,re
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=[];counts={'passed':0,'failed':0,'skipped':0,'errors':0};suites={}

def milestone(name):
    s=name.lower()
    if any(x in s for x in ['extraction','vault','ocr','supported_fictional']):return 'M4'
    if any(x in s for x in ['assistant','gemini','chat','m9b']):return 'M9'
    if any(x in s for x in ['family','household','ownership']):return 'M8'
    if any(x in s for x in ['planner','ff05','ff06','ff08','ff10']):return 'M6'
    if any(x in s for x in ['reasoning','optimizer','proof_substitution','deadline','rule_change','name_matching','intelligence','rejection','visit','bottleneck','citizen','workflow','simulation']):return 'M7'
    if any(x in s for x in ['passport','journey','preparation','ff0','ff1']):return 'M5'
    return 'Cross-page'

for filename,label in [('backend-final.xml','Backend regression'),('acceptance-final.xml','Browser and HTTP acceptance')]:
    ts=list(ET.parse(ROOT/'evidence'/filename).iter('testcase')); local={'passed':0,'failed':0,'skipped':0,'errors':0}
    for t in ts:
        status='FAIL' if t.find('failure') is not None or t.find('error') is not None else 'SKIPPED' if t.find('skipped') is not None else 'PASS'
        key={'FAIL':'failed','SKIPPED':'skipped','PASS':'passed'}[status];local[key]+=1;counts[key]+=1
        if t.find('error') is not None:local['errors']+=1;counts['errors']+=1
        name=t.attrib['name'];group=t.attrib.get('classname','')
        is_browser='test_browser' in group
        evidence='qa/evidence/'+filename
        if is_browser:
            screenshot=re.sub(r'[^a-zA-Z0-9_-]','_',name)+'.png'
            if (ROOT/'evidence'/screenshot).exists():evidence='qa/evidence/'+screenshot
        rows.append([milestone(group+' '+name),group,name,'Real browser' if is_browser else 'HTTP integration' if 'test_http' in group else 'Backend regression / stubbed provider','Assertions pass; no false official acceptance','Assertions passed' if status=='PASS' else status,status,evidence,label])
    suites[label]=local
for filename,label in [('legacy-functional-final.json','Existing functional browser'),('legacy-smoke-final.json','Existing smoke browser'),('legacy-m9-final.json','Existing M9 browser')]:
    data=json.loads((ROOT/'evidence'/filename).read_text());local={'passed':0,'failed':0,'skipped':0,'errors':0}
    for t in data['results']:
        status=t['status'];key='passed' if status=='PASS' else 'failed';counts[key]+=1;local[key]+=1
        rows.append([milestone(t['case']),label,t['case'],'Real browser','Current UI and real API assertions pass',t.get('error','Assertions passed'),status,'qa/evidence/'+filename,'No live Gemini'])
    suites[label]=local
for filename,label,prefix in [('legacy-reasoning-final.log','Existing reasoning browser','RE'),('legacy-vault-final.log','Existing Vault browser','VE')]:
    text=(ROOT/'evidence'/filename).read_text();local={'passed':0,'failed':0,'skipped':0,'errors':0}
    for status,name in re.findall(r'^(PASS|FAIL) ('+prefix+r'\d+[^\n]+)',text,re.M):
        key='passed' if status=='PASS' else 'failed';counts[key]+=1;local[key]+=1
        rows.append([milestone(name),label,name,'Real browser','Real API or IndexedDB assertions pass',status,status,'qa/evidence/'+filename,'No live Gemini'])
    suites[label]=local
GAPS=[
 ('M5','Saved preparation resume','Navigate away from an answered questionnaire and reopen','Acceptance gap','Resume saved answers and step','Questionnaire state is component-local; preparation cards do not reopen saved answers','PARTIAL','Maadhyam/apps/web/src/pages/GuidedJourney.tsx','Records are session-memory prototypes; no durable linked journey summary'),
 ('M7','Deadline and expiry solver UI','Enter document expiry through Vault','Frontend acceptance','Expiry can be entered and conflict guidance displayed','expiryDate supported by API; absent from DocumentMetadata and Vault editor','PARTIAL','Maadhyam/apps/web/src/context/DocumentContext.tsx','Actual expiry API edge cases passed'),
 ('M7','Government rule-change impact UI','Compare a proposed pack through citizen controls','Frontend acceptance','Readable impact analysis without JSON input','/api/passport/rules/compare has no frontend consumer','PARTIAL','Maadhyam/apps/api/src/maadhyam_api/routes/rule_change_impact.py','Valid and invalid HTTP checks passed; no official change verified'),
 ('M7','Full weighted correction optimizer UI','Enter candidate correction paths','Frontend acceptance','Citizen-friendly cost/days/visit optimizer','Advanced-plan endpoint exists; planner UI renders prerequisite subset only','PARTIAL','Maadhyam/apps/api/src/maadhyam_api/routes/advanced_planning.py','Actual valid/deadlock HTTP scenarios passed'),
 ('M8','Household member dependency graph','Order tasks across named household members','Frontend acceptance','Member-specific graph with incomplete/cyclic household coverage','Current family evidence associations and task graph are prototypes; no member-specific graph model','PARTIAL','Maadhyam/apps/web/src/components/ReasoningWorkspace.tsx','Family ownership labels are not authenticated users'),
 ('M8','Multi-user authorization and consent','Attempt cross-member document access','Authorization acceptance','Authenticated member permissions and explicit sharing consent','No multi-user authentication or household sharing model exists; cannot execute cross-account denial test','NOT IMPLEMENTED','Maadhyam/apps/web/src/context/DocumentContext.tsx','Local browser isolation tested; no claim of household authorization'),
 ('M9','Live Gemini','Execute live provider acceptance','Provider acceptance','Live provider result recorded separately','NOT RUN: no existing explicit live-call permission was found or exercised','NOT RUN','qa/evidence/backend-final.xml','Provider success, failure, actual SDK 429, timeout, empty output, and safety fallback were stubbed'),
]
rows.extend(GAPS)
with (ROOT/'M4-M9_TEST_MATRIX.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Milestone','Feature','TestCase','TestType','ExpectedResult','ActualResult','Status','EvidencePath','Notes']);w.writerows(rows)
summary={'finalTestCases':sum(counts[k] for k in ['passed','failed','skipped']),'counts':counts,'suites':suites,'acceptanceGaps':len(GAPS),'liveGemini':'NOT RUN'}
(ROOT/'evidence/final-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
# Fill the human-readable report from the same evidence used by the matrix.
backend=suites['Backend regression'];acceptance=suites['Browser and HTTP acceptance']
http_cases=sum('test_http' in t.attrib.get('classname','') for t in ET.parse(ROOT/'evidence/acceptance-final.xml').iter('testcase'))
browser_cases=sum('test_browser' in t.attrib.get('classname','') for t in ET.parse(ROOT/'evidence/acceptance-final.xml').iter('testcase'))+sum(v['passed']+v['failed']+v['skipped'] for k,v in suites.items() if k not in ['Backend regression','Browser and HTTP acceptance'])
block=f'''<!-- COUNTS -->
| Final regression set | Executed | Result |
|---|---:|---|
| Backend pytest | {backend['passed']+backend['failed']+backend['skipped']} | {backend['passed']} passed, {backend['failed']} failed, {backend['skipped']} skipped; 1 existing Starlette deprecation warning |
| Playwright Chromium (new + existing suites) | {browser_cases} | Browser cases recorded in final XML and legacy suite evidence |
| Separate real HTTP integration | {http_cases} | Included in final acceptance XML |
| **Total final test cases** | **{summary['finalTestCases']}** | **{counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped** |
| Frontend TypeScript and Vite build | 1 build | PASS; `qa/evidence/frontend-build-final.log` |

The combined new browser/HTTP suite reports {acceptance['passed']} passed and {acceptance['failed']} failed. Existing browser suites contribute {browser_cases-(acceptance['passed']+acceptance['failed']-http_cases)} additional cases. No live-provider test is counted as passed or as a pytest skip; it is explicitly NOT RUN.
<!-- END COUNTS -->'''
p=ROOT/'M4-M9_ACCEPTANCE_REPORT.md';content=p.read_text()
content=re.sub(r'<!-- COUNTS -->.*?<!-- END COUNTS -->',lambda _:block,content,flags=re.S) if '<!-- END COUNTS -->' in content else content.replace('<!-- COUNTS -->',block)
p.write_text(content)
