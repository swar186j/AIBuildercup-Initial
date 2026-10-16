"""Explicit live synthetic acceptance: two provider calls; no personal records."""
import json
import sys
import time
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'Maadhyam/apps/api/src'))
from maadhyam_api.config import get_settings
from maadhyam_api.routes.intelligence import ChatRequest, chat
from maadhyam_api.routes.extraction import extract_with_gemini
s = get_settings()
results = []
for kind in ['assistant', 'extraction']:
    started = time.monotonic()
    try:
        if kind == 'assistant':
            result = chat(ChatRequest(question='What should a fictional applicant prepare next?', useGemini=True, fictionalDataConfirmed=True, documents=[]))
            assert result['mode'] == 'gemini-demo' and result['answer']
            result = {'mode': result['mode'], 'answer': result['answer']}
        else:
            result = extract_with_gemini((root / 'qa/fixtures/fictional_aadhaar.pdf').read_bytes(), 'application/pdf', s.gemini_api_key, s.gemini_model).model_dump()
            assert result['printedName'], 'No fictional holder extracted'
        results.append({'check': kind, 'status': 'COMPLETE', 'result': result, 'elapsedSeconds': round(time.monotonic()-started, 2)})
    except Exception as exc:
        # Record only exception class; exception strings may contain provider credentials.
        results.append({'check': kind, 'status': 'BLOCKED', 'errorType': type(exc).__name__, 'elapsedSeconds': round(time.monotonic()-started, 2)})
out = root / 'qa/evidence/m10-m12/live-ai.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'provider': 'real Gemini', 'model': s.gemini_model, 'syntheticOnly': True, 'checks': results}, indent=2))
print(json.dumps([{k:v for k,v in r.items() if k != 'result'} for r in results]))
sys.exit(0 if all(r['status'] == 'COMPLETE' for r in results) else 1)
