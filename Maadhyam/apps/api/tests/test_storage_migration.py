import json
import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore
from maadhyam_api.m10 import cloud_workspace
from maadhyam_api.m10.file_storage import FileStorage
from m10_support import test_app as make_app, Files


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setattr(firestore,'transactional',lambda fn:fn)
    app,store=make_app()
    files=object.__new__(FileStorage)
    files.provider='supabase';files.adapters={'supabase':Files(),'gcs':Files()};files.active=files.adapters['supabase']
    app.dependency_overrides[cloud_workspace.bucket]=lambda:files
    with TestClient(app,headers={'Authorization':'Bearer test-a'}) as client:
        path='/api/workspace/documents/fictional-file-123'
        data=b'\x89PNG\r\n\x1a\nfictional'
        response=client.put(path,files={'file':('fictional.png',data,'image/png')},data={'metadata':json.dumps({'category':'identity'})})
        assert response.status_code==201
        files.provider='gcs';files.active=files.adapters['gcs']
        yield client,store,files,path,data


def test_verified_migration_preserves_original_and_private_routing(setup):
    client,store,files,path,data=setup
    assert client.post(path+'/migrate-storage',json={'revision':1}).status_code==400
    assert client.post(path+'/migrate-storage',headers={'Authorization':'Bearer test-b'},json={'revision':1,'confirmed':True}).status_code==404
    result=client.post(path+'/migrate-storage',json={'revision':1,'confirmed':True})
    assert result.status_code==200 and result.json()['storage_provider']=='gcs' and result.json()['revision']==2
    key='users/a/vault/fictional-file-123'
    assert files.adapters['supabase'].objects[key]==data
    assert files.adapters['gcs'].objects[key]==data
    assert client.get(path+'/content').content==data
    assert client.post(path+'/migrate-storage',json={'revision':2,'confirmed':True}).json()['revision']==2
    assert client.delete(path+'?revision=2').status_code==204
    assert key not in files.adapters['gcs'].objects and key not in files.adapters['supabase'].objects


def test_source_integrity_failure_does_not_switch_storage(setup):
    client,store,files,path,data=setup
    key='users/a/vault/fictional-file-123'
    files.adapters['supabase'].objects[key]=b'corrupt'
    result=client.post(path+'/migrate-storage',json={'revision':1,'confirmed':True})
    assert result.status_code==409 and files.adapters['gcs'].objects=={}
    assert store.db.collection('users').document('a').collection('vault').document('fictional-file-123').get().to_dict()['storage_provider']=='supabase'


def test_original_cleanup_requires_confirmation_and_verified_target(setup):
    client,store,files,path,data=setup
    assert client.post(path+'/migrate-storage',json={'revision':1,'confirmed':True}).status_code==200
    key='users/a/vault/fictional-file-123'
    assert client.post(path+'/finalize-storage-migration',json={'revision':2}).status_code==400
    files.adapters['gcs'].objects[key]=b'corrupt'
    assert client.post(path+'/finalize-storage-migration',json={'revision':2,'confirmed':True}).status_code==409
    assert files.adapters['supabase'].objects[key]==data
    files.adapters['gcs'].objects[key]=data
    result=client.post(path+'/finalize-storage-migration',json={'revision':2,'confirmed':True})
    assert result.status_code==200 and result.json()['migration_source_retained'] is None
    assert key not in files.adapters['supabase'].objects and files.adapters['gcs'].objects[key]==data
