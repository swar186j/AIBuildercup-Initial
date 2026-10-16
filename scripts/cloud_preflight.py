"""Read-only Cloud Run prerequisites. Never links/upgrades billing or enables APIs."""
import json
import os
import subprocess
import sys

PROJECT = 'maadhyam-1610'
REQUIRED = {'run.googleapis.com', 'cloudbuild.googleapis.com',
    'artifactregistry.googleapis.com', 'secretmanager.googleapis.com', 'storage.googleapis.com'}


def read_gcloud(*args):
    result = subprocess.run(['gcloud', *args, '--format=json'], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Google CLI authorization or project access is unavailable')
    return json.loads(result.stdout)


def main():
    if os.environ.get('TRIAL_CREDIT_CONFIRMED') != 'true':
        raise RuntimeError('Verify active free-trial credit and expiry first; paid upgrade is not authorized')
    billing = read_gcloud('billing', 'projects', 'describe', PROJECT)
    if not billing.get('billingEnabled'):
        raise RuntimeError('Project has no active linked billing account')
    services = read_gcloud('services', 'list', '--enabled', '--project', PROJECT)
    enabled = {item.get('config', {}).get('name', '') for item in services}
    missing = sorted(REQUIRED - enabled)
    if missing:
        raise RuntimeError('Required services are not enabled: ' + ', '.join(missing))
    if not os.environ.get('RUNTIME_SERVICE_ACCOUNT'):
        raise RuntimeError('Dedicated runtime service account is required')
    if not os.environ.get('GCS_BUCKET'):
        raise RuntimeError('Private Google Cloud Storage bucket is required')
    result = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True)
    if result.returncode or result.stdout.strip():
        raise RuntimeError('Commit and review tracked source changes before building a revision-tagged image')
    print('Cloud preflight passed; billing was not modified and no resources were provisioned')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError) as error:
        print('BLOCKED:', str(error), file=sys.stderr)
        raise SystemExit(1)
