"""Environment-driven application settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MAADHYAM_", env_file=".env", extra="ignore")
    app_name: str = "Maadhyam API"
    app_version: str = "0.1.0"
    environment: str = "development"
    web_dist: str = ""
    firestore_transport: str = "admin"
    file_storage: str = "supabase"
    gcs_bucket: str = ""
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    google_cloud_project: str = Field(default="", validation_alias="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: str = Field(default="", validation_alias="GOOGLE_APPLICATION_CREDENTIALS")
    supabase_url: str = Field(default="", validation_alias="MAADHYAM_SUPABASE_URL")
    supabase_secret_key: str = Field(default="", validation_alias="MAADHYAM_SUPABASE_SECRET_KEY")
    supabase_bucket: str = Field(default="maadhyam-documents", validation_alias="MAADHYAM_SUPABASE_BUCKET")
    supabase_dns_fallback: bool = Field(default=False, validation_alias="MAADHYAM_SUPABASE_DNS_FALLBACK")


@lru_cache
def get_settings() -> Settings:
    return Settings()
