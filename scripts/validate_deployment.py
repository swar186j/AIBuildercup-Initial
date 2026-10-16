"""Offline checks: never provision resources or read secrets."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'firebase.json').read_text())
rewrites = config['hosting']['rewrites']
assert rewrites[0]['source'] == '/api/**'
assert rewrites[0]['run'] == {'serviceId': 'maadhyam-api', 'region': 'asia-south1', 'pinTag': True}
assert rewrites[-1]['destination'] == '/index.html'
docker = (root / 'Maadhyam/apps/api/Dockerfile').read_text()
assert 'USER 10001' in docker and '--frozen' in docker and '--no-access-log' in docker
assert '--reload' not in docker
assert 'allow read, write: if false' in (root / 'firestore.rules').read_text()
script = (root / 'scripts/deploy.sh').read_text()
for flag in ['--min-instances 0', '--max-instances 1', '--concurrency 8', '--timeout 55', '--set-secrets', 'COST_APPROVED', 'MAADHYAM_ENVIRONMENT=production']:
    assert flag in script, flag
assert '--set-env-vars' in script
assert (root / '.github/workflows/verify.yml').exists()
assert (root / '.github/workflows/deploy.yml').exists()
print('Offline deployment validation passed')

free = json.loads((root / 'firebase.free.json').read_text())
assert free['hosting']['rewrites'] == [{'source': '**', 'destination': '/index.html'}]
assert free['firestore']['rules'] == 'firestore.free.rules'
render = (root / 'render.yaml').read_text()
assert 'plan: free' in render and 'value: user-rest' in render
assert 'GOOGLE_APPLICATION_CREDENTIALS' not in render
print('Free Firebase Hosting + Render configuration passed')

assert "MAADHYAM_FILE_STORAGE=gcs" in script and "MAADHYAM_GCS_BUCKET=$GCS_BUCKET" in script
print("Cloud Run private GCS deployment configuration passed")
