from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from maadhyam_api.config import get_settings
from maadhyam_api.m10.gcs_files import GCSFiles


class Blob:
    def __init__(self):
        self.data = None
        self.generation = 7
    def upload_from_string(self, data, **kwargs):
        assert kwargs['if_generation_match'] == 0 and kwargs['retry'] is None
        if self.data is not None: raise PreconditionFailed('private-provider-detail')
        self.data = data
    def download_as_bytes(self, **kwargs):
        if self.data is None: raise NotFound('private-provider-detail')
        return self.data
    def reload(self, **kwargs):
        if self.data is None: raise NotFound('private-provider-detail')
    def delete(self, **kwargs):
        assert kwargs['if_generation_match'] == 7
        self.data = None


class Bucket:
    iam_configuration = SimpleNamespace(uniform_bucket_level_access_enabled=True, public_access_prevention='enforced')
    def __init__(self): self.object = Blob()
    def reload(self, **kwargs): pass
    def blob(self, key): return self.object


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.setenv('MAADHYAM_GCS_BUCKET','fictional-private-bucket')
    get_settings.cache_clear()
    bucket = Bucket()
    try: yield GCSFiles(SimpleNamespace(bucket=lambda name: bucket))
    finally: get_settings.cache_clear()


def test_generation_create_idempotency_and_private_delete(backend):
    backend.upload('users/a/vault/file',b'fictional','image/png')
    backend.upload('users/a/vault/file',b'fictional','image/png')
    with pytest.raises(HTTPException) as exc: backend.upload('users/a/vault/file',b'changed','image/png')
    assert exc.value.status_code == 409
    assert backend.download('users/a/vault/file') == b'fictional'
    backend.delete('users/a/vault/file')
    backend.delete('users/a/vault/file')
    with pytest.raises(HTTPException) as exc: backend.download('users/a/vault/file')
    assert exc.value.status_code == 404 and 'private-provider-detail' not in exc.value.detail


@pytest.mark.parametrize('uniform,pap',[(False,'enforced'),(True,'inherited')])
def test_bucket_fails_closed_without_private_policy(monkeypatch,uniform,pap):
    monkeypatch.setenv('MAADHYAM_GCS_BUCKET','fictional-private-bucket');get_settings.cache_clear()
    bucket=Bucket();bucket.iam_configuration=SimpleNamespace(uniform_bucket_level_access_enabled=uniform,public_access_prevention=pap)
    try:
        with pytest.raises(HTTPException) as exc:GCSFiles(SimpleNamespace(bucket=lambda name:bucket))
        assert exc.value.status_code==503
    finally:get_settings.cache_clear()
