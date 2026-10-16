"""Live synthetic free-host acceptance. No personal users/documents are accessed.
Run with API Python from apps/api. Uses existing local ADC only to publish
reviewed rules and create/remove two disposable QA identities; runtime requests
use Firebase ID tokens and require no Google credentials on the hosting server.
"""
import base64
import json
import os
import secrets
import sys
import time
from pathlib import Path
from uuid import uuid4
import requests
import google.auth
from google.auth.transport.requests import AuthorizedSession
from dotenv import dotenv_values
from fastapi.testclient import TestClient
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'Maadhyam/apps/api/src'))
from maadhyam_api.config import get_settings
from maadhyam_api.m10.auth import _firebase_app
from firebase_admin import auth
from maadhyam_api.m10.supabase_files import SupabaseFiles
from maadhyam_api.m10.repository import client as admin_database
from maadhyam_api.m10.firestore_rest import RestDatabase
from maadhyam_api.main import create_app

out = root / 'qa/evidence/m10-m12'
out.mkdir(parents=True, exist_ok=True)
results = []
users = []
records = []
files = []
checks = json.loads((out / 'firestore-rules-tests.json').read_text())
assert len(checks.get('testResults', [])) == 21 and all(x['state'] == 'SUCCESS' for x in checks['testResults'])
session = AuthorizedSession(google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])[0])
source = {'files': [{'name': 'firestore.rules', 'content': (root / 'firestore.free.rules').read_text()}]}
r = session.post('https://firebaserules.googleapis.com/v1/projects/maadhyam-1610/rulesets', json={'source': source}, timeout=20)
r.raise_for_status()
ruleset = r.json()['name']
r = session.patch('https://firebaserules.googleapis.com/v1/projects/maadhyam-1610/releases/cloud.firestore', params={'updateMask':'rulesetName'}, json={'release': {'name':'projects/maadhyam-1610/releases/cloud.firestore','rulesetName':ruleset}}, timeout=20)
r.raise_for_status()
results.append('21 inline owner/cross-user/anonymous rules cases passed; owner-scoped rules published')
web = dotenv_values(root / 'Maadhyam/apps/web/.env.local')
public_key = web['VITE_FIREBASE_API_KEY']
settings = get_settings()
app_identity = _firebase_app()
try:
    tokens = []
    for _ in range(2):
        email = 'maadhyam-qa-' + uuid4().hex + '@example.invalid'
        password = secrets.token_urlsafe(32)
        user = auth.create_user(email=email, password=password, email_verified=True, app=app_identity)
        users.append(user.uid)
        r = requests.post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword', params={'key':public_key}, json={'email':email,'password':password,'returnSecureToken':True}, timeout=15)
        r.raise_for_status()
        tokens.append(r.json()['idToken'])
    results.append('two disposable Firebase QA users signed in with real ID tokens')
    os.environ['MAADHYAM_FIRESTORE_TRANSPORT'] = 'user-rest'
    os.environ['MAADHYAM_ENVIRONMENT'] = 'production'
    get_settings.cache_clear()
    app = create_app()
    a = {'Authorization': 'Bearer ' + tokens[0]}
    b = {'Authorization': 'Bearer ' + tokens[1]}
    with TestClient(app) as api:
        record_id = 'LOCAL-qa-free-' + uuid4().hex
        response = api.post('/api/applications', headers=a, json={'client_id':record_id,'service_type':'passport','application_type':'fresh','applicant_details':{'name':'Fictional Free Hosting Applicant'}})
        assert response.status_code == 201, ('create', response.status_code)
        records.append((users[0], record_id))
        assert api.get('/api/applications', headers=b).json() == []
        assert api.get('/api/applications/'+record_id, headers=b).status_code == 404
        response = api.patch('/api/applications/'+record_id, headers=a, json={'revision':1,'applicant_details':{'name':'Fictional Updated Applicant'}})
        assert response.status_code == 200, ('patch', response.status_code)
        assert api.patch('/api/applications/'+record_id, headers=a, json={'revision':1,'current_step':1}).status_code == 409
        assert api.get('/api/applications/'+record_id, headers=a).json()['applicant_details']['name'] == 'Fictional Updated Applicant'
        results.append('real owner application create/update/restore; other-user isolation; stale revision rejected')
        response = api.put('/api/applications/workspace/planner', headers=a, json={'revision':0,'task_id':'questionnaire','completed':True})
        # Use the canonical task IDs rather than an assumed planner label.
        if response.status_code == 422:
            from maadhyam_api.m10.models import TASK_DEPENDENCIES
            first = next(k for k,v in TASK_DEPENDENCIES.items() if not v)
            response = api.put('/api/applications/workspace/planner', headers=a, json={'revision':0,'task_id':first,'completed':True})
        assert response.status_code == 200, ('planner', response.status_code)
        response = api.put('/api/workspace/household', headers=a, json={'revision':0,'members':[{'id':'applicant','label':'Fictional Applicant','relationship':'self','dependsOnMemberIds':[],'dependsOnDocumentIds':[],'relationshipEvidenceDocumentIds':[]}]})
        assert response.status_code == 200, ('household', response.status_code)
        assert api.get('/api/workspace/household', headers=b).json()['revision'] == 0
        results.append('real planner and household first-save, restore and isolation')
        document_id = 'qa-document-' + uuid4().hex
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aMxkAAAAASUVORK5CYII=')
        response = api.put('/api/workspace/documents/'+document_id, headers=a, files={'file':('fictional-qa.png',png,'image/png')}, data={'metadata':json.dumps({'category':'identity','holder':'self'})})
        assert response.status_code == 201, ('upload', response.status_code)
        files.append((users[0], document_id))
        assert api.get('/api/workspace/documents/'+document_id+'/content', headers=a).content == png
        assert api.get('/api/workspace/documents/'+document_id+'/content', headers=b).status_code == 404
        assert api.delete('/api/workspace/documents/'+document_id+'?revision=1', headers=a).status_code == 204
        files.clear()
        assert api.delete('/api/applications/'+record_id+'?revision=2', headers=a).status_code == 204
        records.clear()
        results.append('real Supabase private bytes round-trip and owner-only deletion via keyless API')
        try:
            RestDatabase(settings.google_cloud_project,tokens[1]).collection('users').document(users[0]).collection('settings').document('household').get()
            raise AssertionError('Cross-owner direct REST read succeeded')
        except Exception as error:
            from fastapi import HTTPException
            assert isinstance(error, HTTPException) and error.status_code == 403
        results.append('deployed Firestore rules reject direct cross-owner user-token access')
    status = 'COMPLETE'
except Exception as error:
    status = 'BLOCKED'
    results.append({'errorType':type(error).__name__,'stage':len(results)})
finally:
    cleanup = []
    for uid, document_id in files:
        try:
            SupabaseFiles().delete(f'users/{uid}/vault/{document_id}')
            admin_database().collection('users').document(uid).collection('vault').document(document_id).delete()
        except Exception:
            cleanup.append('test-file-cleanup-pending')
    for uid, record_id in records:
        try:
            admin_database().collection('users').document(uid).collection('applications').document(record_id).delete()
        except Exception:
            cleanup.append('test-application-cleanup-pending')
    for uid in users:
        try:
            for key in ['planner','household']:
                admin_database().collection('users').document(uid).collection('settings').document(key).delete()
            auth.delete_user(uid, app=app_identity)
        except Exception:
            cleanup.append('test-account-cleanup-pending')
    report={'status':status,'project':'maadhyam-1610','runtimeAuth':'real Firebase tokens, public signing keys, no service-account key','ruleset':ruleset,'checks':results,'cleanup':cleanup or ['all disposable QA records and users removed'],'hostedRender':'NOT TESTED'}
    (out/'free-firestore-live.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    get_settings.cache_clear()
raise SystemExit(0 if status=='COMPLETE' and not cleanup else 1)
