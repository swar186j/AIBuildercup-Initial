"""Gemini connectivity check. No personal documents are transmitted here."""
import logging
from fastapi import APIRouter, HTTPException
from maadhyam_api.config import get_settings
from maadhyam_api.services.gemini_provider import create_client, configured, generation_config, provider_http_error

router = APIRouter(tags=["ai"])
logger = logging.getLogger(__name__)


def check_gemini_connection(api_key: str, model: str) -> str:
    client = create_client(api_key)
    try:
        result = client.models.generate_content(
            model=model,
            contents="Reply with only the word READY.",
            config=generation_config(),
        )
        return (result.text or "").strip()
    finally:
        client.close()


@router.post("/ai/connection-test")
def gemini_connection_test():
    settings = get_settings()
    if not configured(settings):
        raise HTTPException(status_code=503, detail="Gemini provider is not configured")
    try:
        answer = check_gemini_connection(settings.gemini_api_key, settings.gemini_model)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Gemini connection test failed")
        raise provider_http_error(exc) from None
    if not answer:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")
    return {"status": "connected", "model": settings.gemini_model, "reply": answer, "provider": "vertex-ai" if getattr(settings, "gemini_vertexai", False) else "gemini-api"}
