from maadhyam_api.config import Settings
from maadhyam_api.m10.models import WorkspacePlannerPatch, PlannerPatch
from pydantic import ValidationError
import pytest


def test_backend_reads_firebase_settings_from_dotenv(tmp_path, monkeypatch):
    monkeypatch.delenv('GOOGLE_CLOUD_PROJECT', raising=False)
    monkeypatch.delenv('GOOGLE_APPLICATION_CREDENTIALS', raising=False)
    config = tmp_path / '.env'
    config.write_text('GOOGLE_CLOUD_PROJECT=test-project\nGOOGLE_APPLICATION_CREDENTIALS=C:/test/key.json\n')
    settings = Settings(_env_file=config)
    assert settings.google_cloud_project == 'test-project'
    assert settings.google_application_credentials == 'C:/test/key.json'


def test_new_workspace_planner_accepts_zero_revision():
    assert WorkspacePlannerPatch(revision=0, task_id='journey', completed=True).revision == 0
    with pytest.raises(ValidationError):
        PlannerPatch(revision=0, task_id='journey', completed=True)
