"""Read-only hosted smoke checks. No customer data, tokens or writes."""
import argparse
import json
import time
import urllib.request
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--url', required=True)
p.add_argument('--api-only', action='store_true')
a = p.parse_args()
base = a.url.rstrip('/')
if not base.startswith('https://') and not base.startswith(('http://localhost:', 'http://127.0.0.1:')):
    p.error('HTTPS required for a hosted target')
checks = []
for path in ['/api/health', '/api/services'] + ([] if a.api_only else ['/services/passport/journey?type=fresh', '/applications']):
    start = time.monotonic()
    with urllib.request.urlopen(base + path, timeout=55) as r:
        content = r.read()
        assert r.status == 200
        if path == '/api/health':
            assert json.loads(content)['status'] == 'healthy'
        elif path.startswith('/api/'):
            json.loads(content)
        else:
            assert b'<html' in content.lower() and b'<div id="root"' in content
        checks.append({'path': path, 'http': r.status, 'elapsedSeconds': round(time.monotonic()-start, 3)})
# Protected records must not be anonymously readable.
import urllib.error
try:
    urllib.request.urlopen(base + '/api/applications', timeout=15)
    raise AssertionError('Anonymous application access succeeded')
except urllib.error.HTTPError as e:
    assert e.code == 401
checks.append({'path': '/api/applications', 'anonymousHttp': 401})
out = Path(__file__).resolve().parents[1] / 'qa/evidence/m10-m12/hosted-smoke.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'target': base, 'checks': checks, 'authenticatedE2E': 'NOT TESTED'}, indent=2))
print(json.dumps(checks))
