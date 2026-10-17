"""Environment-driven application settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

google_cloud_project: str = ""
firestore_database_id: str = "maadhyam"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAADHYAM_", env_file=".env", extra="ignore")
    app_name: str = "Maadhyam API"
    app_version: str = "0.1.0"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_vertexai: bool = False
    google_cloud_location: str = "global"
    ai_timeout_ms: int = Field(default=30000, ge=1000, le=40000)
    production: bool = False
    google_cloud_project: str = ""
    firestore_database_id: str = "maadhyam"
    document_bucket: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
