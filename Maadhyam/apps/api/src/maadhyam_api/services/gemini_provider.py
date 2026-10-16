"""Shared bounded Google Gen AI client. Vertex uses ADC, never a JSON key."""
from google.genai import types
from google.auth.exceptions import DefaultCredentialsError
from fastapi import HTTPException
from maadhyam_api.config import get_settings


def configured(settings) -> bool:
    return bool(getattr(settings, "gemini_vertexai", False) and settings.google_cloud_project
                or settings.gemini_api_key)


def create_client(api_key: str = ""):
    from google import genai
    settings = get_settings()
    options = types.HttpOptions(
        api_version="v1", timeout=settings.ai_timeout_ms,
        retry_options=types.HttpRetryOptions(attempts=1),
    )
    if settings.gemini_vertexai:
        if not settings.google_cloud_project:
            raise ValueError("Vertex project is required")
        try:
            return genai.Client(vertexai=True, project=settings.google_cloud_project,
                                location=settings.google_cloud_location, http_options=options)
        except DefaultCredentialsError:
            raise HTTPException(503, "Vertex AI credentials are unavailable") from None
    return genai.Client(api_key=api_key or settings.gemini_api_key, http_options=options)


def generation_config(**kwargs):
    return types.GenerateContentConfig(max_output_tokens=2048,
                                      thinking_config=types.ThinkingConfig(thinking_budget=0),
                                      **kwargs)
