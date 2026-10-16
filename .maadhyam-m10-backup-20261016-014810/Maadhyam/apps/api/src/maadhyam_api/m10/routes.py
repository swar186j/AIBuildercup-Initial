"""M10 authenticated application lifecycle. No demo auth bypass."""
from uuid import uuid5, NAMESPACE_URL
from fastapi import APIRouter, Depends, HTTPException, Query
from maadhyam_api.m10.auth import authenticated_user
from maadhyam_api.m10.models import ApplicationCreate, ApplicationPatch, PlannerPatch, SectionPatch, MigrationRequest, TASK_DEPENDENCIES, utc_now
from maadhyam_api.m10.repository import FirestoreRepository

router = APIRouter(prefix="/applications", tags=["applications"])

def repo():
    return FirestoreRepository()

@router.post("", status_code=201)
def create_application(payload: ApplicationCreate, user: str = Depends(authenticated_user), store=Depends(repo)):
    now = utc_now()
    return store.create(user, {**payload.model_dump(), "planner_progress": {}, "household": {}, "documents": {}, "assessment_history": [], "progress_history": [], "revision": 1, "created_at": now, "updated_at": now})

@router.get("")
def list_applications(user: str = Depends(authenticated_user), store=Depends(repo)):
    return sorted(store.list(user), key=lambda x: x.get("updated_at", ""), reverse=True)

@router.get("/{application_id}")
def get_application(application_id: str, user: str = Depends(authenticated_user), store=Depends(repo)):
    return store.get(user, application_id)

@router.patch("/{application_id}")
def update_application(application_id: str, payload: ApplicationPatch, user: str = Depends(authenticated_user), store=Depends(repo)):
    fields = payload.model_dump(exclude_unset=True, exclude={"revision"})
    return store.update(user, application_id, payload.revision, lambda prev: {**fields, "revision": prev["revision"]+1, "updated_at": utc_now()})

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
        key = str(uuid5(NAMESPACE_URL, f"{user}:{payload.migration_id}:{index}"))
        data = {**item.model_dump(), "planner_progress": {}, "household": {}, "documents": {}, "assessment_history": [], "progress_history": [], "revision": 1, "created_at": now, "updated_at": now}
        try:
            result.append(store.create(user, data, record_id=key)["id"])
        except Exception as exc:
            # Firestore AlreadyExists is the only expected idempotent replay.
            from google.api_core.exceptions import AlreadyExists
            if isinstance(exc, AlreadyExists):
                result.append(key)
            else:
                raise
    return {"application_ids": result, "local_data_deleted": False}
