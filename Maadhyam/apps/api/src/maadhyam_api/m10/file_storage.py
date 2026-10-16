"""Active storage with explicit legacy source selection during migration."""
from fastapi import HTTPException
from maadhyam_api.config import get_settings


class FileStorage:
    def __init__(self):
        self.provider = get_settings().file_storage
        self.adapters = {}
        self.active = self.for_provider(self.provider)

    def for_provider(self, provider):
        if provider not in self.adapters:
            if provider == 'gcs':
                from .gcs_files import GCSFiles
                self.adapters[provider] = GCSFiles()
            elif provider == 'supabase':
                from .supabase_files import SupabaseFiles
                self.adapters[provider] = SupabaseFiles()
            else:
                raise HTTPException(503, 'Unsupported private storage provider')
        return self.adapters[provider]

    def upload(self, key, data, mime):
        self.active.upload(key, data, mime)


def record_storage(files, value):
    # Existing records explicitly remain Supabase-backed until verified migration.
    return files.for_provider(value.get('storage_provider', 'supabase')) if isinstance(files, FileStorage) else files
