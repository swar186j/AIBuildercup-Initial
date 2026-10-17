"""Execute an existing browser suite against the dedicated no-credentials API.
Route.fetch forwards real requests to uvicorn; it does not stub responses.
"""
import os
from pathlib import Path
import runpy
import sys
from playwright.sync_api import Browser, BrowserContext
root=Path(__file__).resolve().parents[1]
name=sys.argv[1]
allowed={'run_frontend_functional.py','run_reasoning_e2e.py','run_vault_e2e.py','run_m9_browser_e2e.py','run_frontend_tests.py'}
if name not in allowed:raise SystemExit('Unknown browser suite')
sys.path.insert(0,str(root))
from qa.test_remediation import mocked_auth
original=Browser.new_context
original_browser_close=Browser.close
def close_browser(self,*args,**kwargs):
    for context in list(self.contexts):context.close()
    return original_browser_close(self,*args,**kwargs)
Browser.close=close_browser
original_close=BrowserContext.close
def close_context(self,*args,**kwargs):
    self.unroute_all(behavior='wait')
    return original_close(self,*args,**kwargs)
BrowserContext.close=close_context
api=os.environ.get('MAADHYAM_TEST_API','http://127.0.0.1:8001')
def context(self,*args,**kwargs):
    ctx=original(self,*args,**kwargs)
    mocked_auth(ctx,cloud_consent=False)
    ctx.route('**/api/**',lambda route:route.fulfill(response=route.fetch(url=api+'/api'+route.request.url.split('/api',1)[1])))
    return ctx
Browser.new_context=context
script=root/'Maadhyam/apps/api/tests'/name
os.chdir(root/'Maadhyam/apps/api')
sys.argv=[str(script),*sys.argv[2:]]
runpy.run_path(str(script),run_name='__main__')
