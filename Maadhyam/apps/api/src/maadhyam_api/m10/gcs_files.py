"""Private GCS objects using managed identity and generation preconditions."""
import hashlib
from fastapi import HTTPException
from google.api_core.exceptions import NotFound, PreconditionFailed
from maadhyam_api.config import get_settings


class GCSFiles:
    provider = 'gcs'

    def __init__(self, client=None):
        settings = get_settings()
        if not settings.gcs_bucket:
            raise HTTPException(503, 'Private Google Cloud Storage bucket is not configured')
        try:
            if client is None:
                from google.cloud import storage
                client = storage.Client(project=settings.google_cloud_project)
            self.bucket = client.bucket(settings.gcs_bucket)
            self.bucket.reload(timeout=10, retry=None)
            config = self.bucket.iam_configuration
            if not config.uniform_bucket_level_access_enabled or config.public_access_prevention != 'enforced':
                raise HTTPException(503, 'Bucket requires uniform access and enforced public access prevention')
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, 'Private Google Cloud Storage is unavailable') from None

    def upload(self, key, data, mime):
        try:
            blob = self.bucket.blob(key)
            blob.upload_from_string(data, content_type=mime, if_generation_match=0, timeout=20, retry=None)
        except PreconditionFailed:
            if hashlib.sha256(self.download(key)).digest() != hashlib.sha256(data).digest():
                raise HTTPException(409, 'Document ID already contains different bytes') from None
        except Exception:
            raise HTTPException(503, 'Private file upload unavailable; retry later') from None

    def download(self, key):
        try:
            return self.bucket.blob(key).download_as_bytes(timeout=20, retry=None)
        except NotFound:
            raise HTTPException(404, 'Private file not found') from None
        except Exception:
            raise HTTPException(503, 'Private file download unavailable; retry later') from None

    def delete(self, key):
        try:
            blob = self.bucket.blob(key)
            blob.reload(timeout=10, retry=None)
            blob.delete(if_generation_match=blob.generation, timeout=20, retry=None)
        except NotFound:
            return
        except PreconditionFailed:
            raise HTTPException(409, 'Private file changed; retry deletion') from None
        except Exception:
            raise HTTPException(503, 'Private file deletion unavailable; retry later') from None
