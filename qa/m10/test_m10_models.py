"""Offline M10 schema smoke tests; integration requires Firebase/Firestore emulator."""
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Maadhyam/apps/api/src'))
from maadhyam_api.m10.models import ApplicationCreate, ApplicationPatch, PlannerPatch, MigrationRequest

def test_create_defaults():
    item = ApplicationCreate()
    assert item.service_type == 'passport'
    assert item.current_step == 0
    assert item.selected_document_ids == []

def test_reject_owner_spoofing():
    with pytest.raises(ValidationError):
        ApplicationCreate(owner_user_id='someone-else')

def test_reject_invalid_steps():
    with pytest.raises(ValidationError):
        ApplicationCreate(current_step=-1)

def test_revision_required():
    with pytest.raises(ValidationError):
        ApplicationPatch(status='completed')

def test_planner_task_whitelist():
    with pytest.raises(ValidationError):
        PlannerPatch(revision=1, task_id='arbitrary', completed=True)

def test_migration_requires_explicit_confirmation_field():
    with pytest.raises(ValidationError):
        MigrationRequest(records=[ApplicationCreate()], migration_id='test-id-123')
