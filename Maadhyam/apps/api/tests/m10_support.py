"""In-memory Firestore adapter for isolated M10 tests; never used by production."""
from copy import deepcopy
from google.api_core.exceptions import AlreadyExists
from fastapi import Header, HTTPException
from maadhyam_api.main import create_app
from maadhyam_api.m10 import routes
from maadhyam_api.m10.auth import authenticated_user
from maadhyam_api.m10.repository import FirestoreRepository
from maadhyam_api.m10 import cloud_workspace


class Files:
    def __init__(self):
        self.objects = {}
        self.fail_delete = False

    def upload(self, key, data, mime):
        if key in self.objects and self.objects[key] != data:
            raise HTTPException(409, 'Upload conflict')
        self.objects[key] = data

    def download(self, key):
        if key not in self.objects:
            raise HTTPException(404, 'File not found')
        return self.objects[key]

    def delete(self, key):
        if self.fail_delete:
            raise HTTPException(503, 'Synthetic storage outage')
        self.objects.pop(key, None)


class Snapshot:
    def __init__(self, value):
        self.exists = value is not None
        self.value = value

    def to_dict(self):
        return deepcopy(self.value)


class Reference:
    def __init__(self, db, path=()):
        self.db, self.path = db, path
        self.id = path[-1] if path else ''

    def collection(self, name):
        return Reference(self.db, (*self.path, name))

    def document(self, name=None):
        from uuid import uuid4
        return Reference(self.db, (*self.path, name or str(uuid4())))

    def get(self, transaction=None):
        return Snapshot(self.db.records.get(self.path))

    def create(self, value):
        if self.path in self.db.records:
            raise AlreadyExists('Already exists')
        self.set(value)

    def set(self, value):
        self.db.records[self.path] = deepcopy(value)

    def update(self, value):
        self.db.records[self.path].update(deepcopy(value))

    def delete(self):
        del self.db.records[self.path]

    def stream(self):
        return [Snapshot(value) for path, value in self.db.records.items()
                if path[:-1] == self.path]


class Database(Reference):
    def __init__(self):
        super().__init__(self)
        self.records = {}

    def transaction(self):
        return self

    def update(self, ref, value):
        ref.update(value)

    def set(self, ref, value):
        ref.set(value)

    def delete(self, ref):
        ref.delete()


def test_app():
    app = create_app()
    store = object.__new__(FirestoreRepository)
    store.db = Database()

    def identity(authorization: str | None = Header(default=None)):
        if authorization not in ('Bearer test-a', 'Bearer test-b'):
            raise HTTPException(401, 'Authentication required')
        return authorization.removeprefix('Bearer test-')

    app.dependency_overrides[authenticated_user] = identity
    app.dependency_overrides[routes.repo] = lambda: store
    app.dependency_overrides[cloud_workspace.database] = lambda: store.db
    files = Files()
    app.dependency_overrides[cloud_workspace.bucket] = lambda: files
    app.state.test_files = files
    return app, store
