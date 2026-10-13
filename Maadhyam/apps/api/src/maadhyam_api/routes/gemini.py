"""Gemini connectivity check. No personal documents are transmitted here."""
import logging
from fastapi import APIRouter, HTTPException
from maadhyam_api.config import get_settings

router = APIRouter(tags=["ai"])
logger = logging.getLogger(__name__)


def check_gemini_connection(api_key: str, model: str) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    try:
        result = client.models.generate_content(
            model=model,
            contents="Reply with only the word READY.",
        )
        return (result.text or "").strip()
    finally:
        client.close()


@router.post("/ai/connection-test")
def gemini_connection_test():
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini API key is not configured")
    try:
        answer = check_gemini_connection(settings.gemini_api_key, settings.gemini_model)
    except Exception:
        logger.exception("Gemini connection test failed")
        raise HTTPException(status_code=502, detail="Gemini provider request failed") from None
    if not answer:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response")
    return {"status": "connected", "model": settings.gemini_model, "reply": answer}
