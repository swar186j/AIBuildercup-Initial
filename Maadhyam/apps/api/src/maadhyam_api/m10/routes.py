from maadhyam_api.m10.firestore_rest import transactional
"""M10 authenticated application lifecycle. No demo auth bypass."""
from uuid import uuid5, NAMESPACE_URL
from google.api_core.exceptions import AlreadyExists
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from maadhyam_api.m10.auth import authenticated_user
from maadhyam_api.m10.models import ApplicationCreate, ApplicationPatch, PlannerPatch, SectionPatch, MigrationRequest, TASK_DEPENDENCIES, utc_now
from maadhyam_api.m10.repository import FirestoreRepository, request_database
from maadhyam_api.m10.models import WorkspacePlannerPatch

router = APIRouter(prefix="/applications", tags=["applications"])

def repo(request: Request):
    return FirestoreRepository(request_database(request))

@router.post("", status_code=201)
def create_application(payload: ApplicationCreate, user: str = Depends(authenticated_user), store=Depends(repo)):
    now = utc_now()
    fields = payload.model_dump(exclude={"client_id"})
    record = {**fields, "planner_progress": {}, "household": {}, "documents": {}, "assessment_history": [], "progress_history": [], "revision": 1, "created_at": now, "updated_at": now}
    try:
        return store.create(user, record, record_id=payload.client_id)
    except AlreadyExists:
        # Retrying the same draft must not create a duplicate or overwrite it.
        if not payload.client_id:
            raise
        existing = store.get(user, payload.client_id)
        if existing.get("service_type") != payload.service_type:
            raise HTTPException(409, "Existing preparation has a different service type")
        return existing

@router.get("")
def list_applications(user: str = Depends(authenticated_user), store=Depends(repo)):
    return sorted(store.list(user), key=lambda x: x.get("updated_at", ""), reverse=True)

@router.get("/{application_id}")
def get_application(application_id: str, user: str = Depends(authenticated_user), store=Depends(repo)):
    return store.get(user, application_id)

@router.patch("/{application_id}")
def update_application(application_id: str, payload: ApplicationPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    fields = payload.model_dump(exclude_unset=True, exclude={"revision"})
    def transform(prev):
        now = utc_now()
        history = list(prev.get('progress_history', []))
        if any(key in fields and fields[key] != prev.get(key) for key in ('status', 'current_step')):
            history.append({'status': fields.get('status', prev.get('status')), 'current_step': fields.get('current_step', prev.get('current_step')), 'recorded_at': now})
        return {**fields, 'progress_history': history[-100:], 'revision': prev['revision'] + 1, 'updated_at': now}
    return store.update(user, application_id, payload.revision, transform)

@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: str, revision: int = Query(ge=1), user: str = Depends(authenticated_user), store=Depends(repo)):
    store.delete(user, application_id, revision)

@router.patch("/{application_id}/planner")
def update_planner(application_id: str, payload: PlannerPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    def transform(prev):
        progress = dict(prev.get("planner_progress", {}))
        if payload.completed:
            if not all(progress.get(dep) for dep in TASK_DEPENDENCIES[payload.task_id]):
                raise HTTPException(409, "Complete prerequisite tasks first")
            progress[payload.task_id] = utc_now()
        else:
            progress.pop(payload.task_id, None)
            for task, dependencies in TASK_DEPENDENCIES.items():
                if any(not progress.get(dep) for dep in dependencies):
                    progress.pop(task, None)
        return {"planner_progress": progress, "revision": prev["revision"]+1, "updated_at": utc_now()}
    return store.update(user, application_id, payload.revision, transform)

@router.patch("/{application_id}/{section}")
def update_section(application_id: str, section: str, payload: SectionPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    if section not in {"household", "documents"}:
        raise HTTPException(404, "Unknown section")
    return store.update(user, application_id, payload.revision, lambda prev: {section: payload.value, "revision": prev["revision"]+1, "updated_at": utc_now()})

@router.post("/{application_id}/assessments")
def append_assessment(application_id: str, payload: SectionPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    def transform(prev):
        history = list(prev.get("assessment_history", []))
        if len(history) >= 100:
            raise HTTPException(409, "Assessment history limit reached")
        history.append({**payload.value, "recorded_at": utc_now(), "rule_pack_version": prev.get("rule_pack_version", "unverified")})
        return {"assessment_history": history, "revision": prev["revision"]+1, "updated_at": utc_now()}
    return store.update(user, application_id, payload.revision, transform)

@router.post("/migrate", status_code=200)
def migrate(payload: MigrationRequest, user: str = Depends(authenticated_user), store=Depends(repo)):
    if not payload.confirmed:
        raise HTTPException(400, "Explicit confirmation required")
    now = utc_now()
    result = []
    for index, item in enumerate(payload.records):
        key = str(uuid5(NAMESPACE_URL, f"{user}:{payload.migration_id}:{item.client_id or index}"))
        data = {**item.model_dump(exclude={"client_id"}), "planner_progress": {}, "household": {}, "documents": {}, "assessment_history": [], "progress_history": [], "revision": 1, "created_at": now, "updated_at": now}
        try:
            result.append(store.create(user, data, record_id=key)["id"])
        except Exception as exc:
            # Firestore AlreadyExists is the only expected idempotent replay.
            if isinstance(exc, AlreadyExists):
                result.append(key)
            else:
                raise
    return {"application_ids": result, "local_data_deleted": False}


@router.get("/workspace/planner")
def get_workspace_planner(user: str = Depends(authenticated_user), store=Depends(repo)):
    ref = store.db.collection("users").document(user).collection("settings").document("planner")
    snapshot = ref.get()
    data = snapshot.to_dict() if snapshot.exists else {}
    return {"completed": sorted(data.get("completed", [])), "revision": int(data.get("revision", 0))}

@router.put("/workspace/planner")
def update_workspace_planner(payload: WorkspacePlannerPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    ref = store.db.collection("users").document(user).collection("settings").document("planner")
    transaction = store.db.transaction()
    from google.cloud import firestore
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        before = snapshot.to_dict() if snapshot.exists else {}
        revision = int(before.get("revision", 0))
        if payload.revision != revision:
            raise HTTPException(409, "Planner changed in another session; refresh to retry")
        done = set(before.get("completed", []))
        if payload.completed:
            if not all(dep in done for dep in TASK_DEPENDENCIES[payload.task_id]):
                raise HTTPException(409, "Complete prerequisite steps first")
            done.add(payload.task_id)
        else:
            done.discard(payload.task_id)
            for task in TASK_DEPENDENCIES:
                if not all(dep in done for dep in TASK_DEPENDENCIES[task]):
                    done.discard(task)
        result = {"completed": sorted(done), "revision": revision + 1, "updated_at": utc_now()}
        tx.set(ref, result)
        return result
    return commit(transaction)

@router.delete("/workspace/planner")
def reset_workspace_planner(revision: int = Query(ge=0), user: str = Depends(authenticated_user), store=Depends(repo)):
    ref = store.db.collection('users').document(user).collection('settings').document('planner')
    transaction = store.db.transaction()
    from google.cloud import firestore
    @transactional
    def commit(tx):
        snapshot = ref.get(transaction=tx)
        existing = snapshot.to_dict() if snapshot.exists else {}
        current = int(existing.get('revision', 0))
        if current != revision:
            raise HTTPException(409, 'Planner changed in another session; reload to retry')
        result = {'completed': [], 'revision': current + 1, 'updated_at': utc_now()}
        tx.set(ref, result)
        return result
    return commit(transaction)
