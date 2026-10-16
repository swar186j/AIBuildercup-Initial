"""Shared bounded Google Gen AI client. Vertex uses ADC, never a JSON key."""
from google.genai import types
from google.auth.exceptions import DefaultCredentialsError
from fastapi import HTTPException
import httpx
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


def provider_http_error(error: Exception, default_status: int = 502) -> HTTPException:
    """Translate upstream failures without exposing provider messages or document data."""
    code = getattr(error, "code", None)
    if code == 429:
        return HTTPException(429, "Gemini quota exhausted; retry later or use local guidance.",
                             headers={"Retry-After": "60"})
    if code in (401, 403):
        return HTTPException(503, "Vertex AI access unavailable; check API enablement and runtime IAM.")
    if code == 404:
        return HTTPException(503, "Configured Gemini model is unavailable.")
    if isinstance(error, (TimeoutError, httpx.TimeoutException)):
        return HTTPException(504, "Gemini request timed out; retry later or use local guidance.")
    if isinstance(error, httpx.TransportError) or code in (500, 502, 503, 504):
        return HTTPException(503, "Gemini is temporarily unavailable; retry later or use local guidance.")
    return HTTPException(default_status, "Gemini provider request failed.")
