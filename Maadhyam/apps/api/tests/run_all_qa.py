#!/usr/bin/env python3
"""Single-command QA orchestrator for Maadhyam. Run from apps/api.
Default: backend pytest + real-browser suites, no Gemini network charges.
Does not pretend missing scripts or skipped provider tests passed.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
TESTS=HERE
SUITES=[
 ('backend-full','pytest',['-q']),
 ('frontend-smoke','python',['-u','tests/run_frontend_tests.py']),
 ('frontend-functional','python',['-u','tests/run_frontend_functional.py']),
 ('vault-e2e','python',['-u','tests/run_vault_e2e.py']),
 ('reasoning-e2e','python',['-u','tests/run_reasoning_e2e.py']),
 ('m9-browser','python',['-u','tests/run_m9_browser_e2e.py']),
]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--backend-only',action='store_true')
    ap.add_argument('--browser-only',action='store_true')
    ap.add_argument('--live-gemini',action='store_true',help='Explicitly run external paid Gemini OCR using fictional PDFs')
    args=ap.parse_args()
    root=Path.cwd()
    if not (root/'pyproject.toml').exists() or not (root/'tests').is_dir():
        print('ERROR: Run from Maadhyam/apps/api (where pyproject.toml and tests/ exist).')
        return 2
    selected=[x for x in SUITES if not (args.backend_only and x[0]!='backend-full') and not (args.browser_only and x[0]=='backend-full')]
    if args.live_gemini: selected.append(('live-gemini-ocr','python',['-u','tests/run_live_gemini_ocr.py','--allow-live-gemini']))
    results=[]
    for label,kind,arguments in selected:
        if kind=='python' and not (root/arguments[1]).is_file():
            results.append({'suite':label,'status':'MISSING','detail':f'{arguments[1]} not installed'})
            print(f'\nMISSING {label}: {arguments[1]}',flush=True)
            continue
        command=['uv','run'] + (['pytest']+arguments if kind=='pytest' else [sys.executable]+arguments[1:])
        # uv run pytest respects the project venv; uv run python should also use project python.
        if kind=='python': command=['uv','run','python']+arguments[1:]
        print(f'\n===== {label}: {" ".join(command)} =====',flush=True)
        try:
            p=subprocess.run(command,cwd=root,timeout=420,check=False)
            status='PASS' if p.returncode==0 else 'FAIL'
            results.append({'suite':label,'status':status,'exitCode':p.returncode})
        except subprocess.TimeoutExpired:
            results.append({'suite':label,'status':'TIMEOUT'})
        except OSError as exc:
            results.append({'suite':label,'status':'ERROR','detail':str(exc)})
        print(f"===== {label}: {results[-1]['status']} =====",flush=True)
    if not args.live_gemini:
        results.append({'suite':'live-gemini-ocr','status':'NOT_RUN','detail':'Opt-in only; use --live-gemini with fictional docs and configured key'})
    report={'generatedAt':datetime.now(timezone.utc).isoformat(),'results':results,
            'passedSuites':sum(x['status']=='PASS' for x in results),
            'failedSuites':sum(x['status'] in {'FAIL','ERROR','TIMEOUT','MISSING'} for x in results)}
    path=root/'maadhyam-comprehensive-qa-report.json'
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'\nSUMMARY: {report["passedSuites"]} suites passed, {report["failedSuites"]} failed/missing. {path}',flush=True)
    return 1 if report['failedSuites'] else 0

if __name__=='__main__':raise SystemExit(main())
