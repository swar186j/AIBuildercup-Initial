
"""Cloud application lifecycle; existing citizen journeys stay unchanged."""

import json
from datetime import date, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field, model_validator

from maadhyam_api.services.firebase_auth import require_uid
from maadhyam_api.services.firestore_store import get_store


router = APIRouter(prefix="/applications", tags=["applications"])

Status = Literal["draft", "in-progress", "completed"]


def validate_record_fields(data: dict):
    # Bound unstructured questionnaire data stored in Firestore.
    encoded = json.dumps(data, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > 100_000:
        raise ValueError("Application payload exceeds 100 KB")


class PlannerState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manual_task_ids: list[str] = Field(default_factory=list, max_length=100)
    target_date: date | None = None
    generated_plan: dict[str, Any] = Field(default_factory=dict)


class HouseholdMemberState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=128)
    label: str = Field(min_length=1, max_length=200)
    relationship: Literal["self", "parent", "guardian", "spouse", "child", "sibling", "other"]
    dependsOnMemberIds: list[str] = Field(default_factory=list, max_length=30)
    dependsOnDocumentIds: list[str] = Field(default_factory=list, max_length=60)
    relationshipEvidenceDocumentIds: list[str] = Field(default_factory=list, max_length=60)
    # Nested member times are client recorded, not authoritative server clocks.
    createdAt: datetime | None = None
    updatedAt: datetime | None = None



class HouseholdState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    members: list[HouseholdMemberState] = Field(default_factory=list, max_length=30)


class AssessmentHistoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    captured_at: str = Field(max_length=50)
    task_count: int = Field(ge=0, le=1000)
    finding_count: int = Field(ge=0, le=1000)
    task_ids: list[str] = Field(default_factory=list, max_length=100)
    assessment_id: str = Field(default="", max_length=100)
    input_document_ids: list[str] = Field(default_factory=list, max_length=60)
    source_url: str = Field(default="", max_length=1000)
    rule_pack_version: str = Field(default="unverified", max_length=100)
    status: Literal["prepared", "needs-review", "failed"] = "prepared"


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_id: str | None = Field(
        default=None,
        pattern=r"^LOCAL-[A-Za-z0-9-]{8,100}$",
    )
    service_type: str = Field(default="passport", max_length=80)
    application_type: str = Field(default="fresh", max_length=80)
    status: Status = "draft"
    applicant_details: dict[str, Any] = Field(default_factory=dict)
    questionnaire_answers: dict[str, Any] = Field(default_factory=dict)
    current_step: int = Field(default=0, ge=0, le=100)
    selected_document_ids: list[str] = Field(
        default_factory=list,
        max_length=100,
    )
    rule_pack_version: str = Field(default="unverified", max_length=100)
    planner_state: PlannerState = Field(default_factory=PlannerState)
    household_state: HouseholdState = Field(default_factory=HouseholdState)
    assessment_history: list[AssessmentHistoryEntry] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def check_size(self):
        validate_record_fields(self.model_dump(mode="json"))
        return self


class ApplicationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(ge=1)
    application_type: str | None = Field(default=None, max_length=80)
    status: Status | None = None
    applicant_details: dict[str, Any] | None = None
    questionnaire_answers: dict[str, Any] | None = None
    current_step: int | None = Field(default=None, ge=0, le=100)
    selected_document_ids: list[str] | None = Field(
        default=None,
        max_length=100,
    )
    rule_pack_version: str | None = Field(default=None, max_length=100)
    planner_state: PlannerState | None = None
    household_state: HouseholdState | None = None
    assessment_history: list[AssessmentHistoryEntry] | None = Field(default=None, max_length=10)

    @model_validator(mode="after")
    def check_update(self):
        fields = self.model_dump(
            exclude_unset=True,
            exclude={"revision"},
        )

        if not fields:
            raise ValueError("At least one update field is required")

        if any(value is None for value in fields.values()):
            raise ValueError("Update fields cannot be null")

        validate_record_fields(self.model_dump(exclude_unset=True, exclude={"revision"}, mode="json"))
        return self


@router.post("", status_code=201)
def create_application(
    payload: ApplicationCreate,
    uid: str = Depends(require_uid),
    store=Depends(get_store),
):
    fields = payload.model_dump(exclude={"client_id"}, mode="json")
    return store.create(uid, fields, payload.client_id)


@router.get("")
def list_applications(
    uid: str = Depends(require_uid),
    store=Depends(get_store),
):
    return store.list(uid)


@router.get("/{application_id}")
def get_application(
    application_id: str = Path(min_length=8, max_length=110, pattern=r"^(?:LOCAL-[A-Za-z0-9-]{8,100}|[a-f0-9]{32})$"),
    uid: str = Depends(require_uid),
    store=Depends(get_store),
):
    return store.get(uid, application_id)


@router.patch("/{application_id}")
def update_application(
    payload: ApplicationPatch,
    application_id: str = Path(min_length=8, max_length=110, pattern=r"^(?:LOCAL-[A-Za-z0-9-]{8,100}|[a-f0-9]{32})$"),
    uid: str = Depends(require_uid),
    store=Depends(get_store),
):
    fields = payload.model_dump(
        exclude_unset=True,
        exclude={"revision"},
        mode="json",
    )
    return store.update(uid, application_id, payload.revision, fields)


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: str = Path(min_length=8, max_length=110, pattern=r"^(?:LOCAL-[A-Za-z0-9-]{8,100}|[a-f0-9]{32})$"),
    revision: int = Query(ge=1),
    uid: str = Depends(require_uid),
    store=Depends(get_store),
):
    store.delete(uid, application_id, revision)
