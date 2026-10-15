"""Reproducible local acceptance with owned servers, deterministic providers and cleanup.
Run from any directory using the API virtualenv Python. No installs or live providers.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
API_DIR=ROOT/'Maadhyam/apps/api'
WEB_DIR=ROOT/'Maadhyam/apps/web'
OUT=ROOT/'qa/evidence/final'
OUT.mkdir(parents=True,exist_ok=True)
PYTHON=str(API_DIR/'.venv/bin/python')

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

def ready(url,proc):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if proc.poll() is not None:raise RuntimeError(f'Owned server exited: {url}')
        try:
            with urllib.request.urlopen(url,timeout=1) as r:
                if r.status==200:return
        except (OSError,ValueError):pass
        time.sleep(.1) # bounded readiness polling, never a browser assertion sleep
    raise RuntimeError(f'Owned server did not become ready: {url}')

def main():
    env={**os.environ,'MAADHYAM_GEMINI_API_KEY':'','GEMINI_API_KEY':'','GOOGLE_API_KEY':'','PYTHONUNBUFFERED':'1'}
    results={}
    def run(name,args,cwd=ROOT):
        print(f'Running {name}',flush=True)
        with (OUT/(name+'.log')).open('w') as log:
            p=subprocess.run(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        results[name]=p.returncode
        print(f'{name}: exit {p.returncode}',flush=True)
    run('backend',[PYTHON,'-m','pytest','-q','--tb=short',f'--junitxml={OUT}/backend.xml'],API_DIR)
    run('frontend-build',['npm','run','build'],WEB_DIR)
    api_port,web_port=free_port(),free_port()
    env['MAADHYAM_TEST_API']=f'http://127.0.0.1:{api_port}'
    env['MAADHYAM_TEST_WEB']=f'http://127.0.0.1:{web_port}'
    env['MAADHYAM_QA_EVIDENCE']=str(OUT/'screenshots')
    processes=[]
    try:
        for name,args,cwd in [
            ('api-server',[PYTHON,'-m','uvicorn','maadhyam_api.main:app','--host','127.0.0.1','--port',str(api_port),'--no-access-log'],API_DIR),
            ('web-server',['npm','run','preview','--','--host','127.0.0.1','--port',str(web_port),'--strictPort'],WEB_DIR),
        ]:
            log=(OUT/(name+'.log')).open('w')
            proc=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            processes.append((proc,log))
        ready(env['MAADHYAM_TEST_API']+'/openapi.json',processes[0][0])
        ready(env['MAADHYAM_TEST_WEB'],processes[1][0])
        run('collection',[PYTHON,'-m','pytest','qa','--collect-only','-q'])
        run('browser',[PYTHON,'-m','pytest','qa/test_browser.py','qa/test_completion.py','qa/test_final_journeys.py','-q','--tb=short',f'--junitxml={OUT}/browser.xml'])
        run('http',[PYTHON,'-m','pytest','qa/test_http.py','-q','--tb=short',f'--junitxml={OUT}/http.xml'])
        web=env['MAADHYAM_TEST_WEB']
        for name,script,args in [
            ('legacy-functional','run_frontend_functional.py',['--base-url',web,'--report',str(OUT/'legacy-functional.json')]),
            ('legacy-reasoning','run_reasoning_e2e.py',['--web',web,'--report',str(OUT/'legacy-reasoning.json')]),
            ('legacy-m9','run_m9_browser_e2e.py',['--web',web,'--report',str(OUT/'legacy-m9.json')]),
            ('legacy-vault','run_vault_e2e.py',[]),
            ('legacy-smoke','run_frontend_tests.py',['--base-url',web,'--api-url',env['MAADHYAM_TEST_API'],'--report',str(OUT/'legacy-smoke.json')]),
        ]:run(name,[PYTHON,str(ROOT/'qa/run_legacy.py'),script,*args])
    finally:
        for proc,log in reversed(processes):
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            log.close()
        (OUT/'execution.json').write_text(json.dumps({'exitCodes':results,'serversOwnedAndStopped':True,'liveProviders':False},indent=2))
    return int(any(results.values()))

if __name__=='__main__':raise SystemExit(main())
