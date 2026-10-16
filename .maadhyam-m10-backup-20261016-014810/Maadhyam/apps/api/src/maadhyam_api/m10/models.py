"""Firestore application documents. No document bytes are stored here."""
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_type: str = Field(default="passport", min_length=1, max_length=80)
    application_type: str = Field(default="fresh", min_length=1, max_length=80)
    status: Literal["draft", "in-progress", "completed"] = "draft"
    applicant_details: dict[str, Any] = Field(default_factory=dict)
    questionnaire_answers: dict[str, Any] = Field(default_factory=dict)
    current_step: int = Field(default=0, ge=0, le=100)
    selected_document_ids: list[str] = Field(default_factory=list, max_length=100)
    rule_pack_version: str = Field(default="unverified", max_length=100)

class ApplicationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    status: Literal["draft", "in-progress", "completed"] | None = None
    application_type: str | None = Field(default=None, min_length=1, max_length=80)
    applicant_details: dict[str, Any] | None = None
    questionnaire_answers: dict[str, Any] | None = None
    current_step: int | None = Field(default=None, ge=0, le=100)
    selected_document_ids: list[str] | None = Field(default=None, max_length=100)
    rule_pack_version: str | None = Field(default=None, max_length=100)

class PlannerPatch(BaseModel):
    revision: int = Field(ge=1)
    task_id: Literal["journey", "vault", "details", "differences", "next"]
    completed: bool

class SectionPatch(BaseModel):
    revision: int = Field(ge=1)
    value: dict[str, Any]

class MigrationRequest(BaseModel):
    records: list[ApplicationCreate] = Field(min_length=1, max_length=100)
    confirmed: bool
    migration_id: str = Field(min_length=8, max_length=120)

TASK_DEPENDENCIES = {"journey": [], "vault": ["journey"], "details": ["vault"], "differences": ["details"], "next": ["differences"]}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
