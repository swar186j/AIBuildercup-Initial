
"""Verified Firebase identity for private Maadhyam API routes."""

import logging
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, exceptions as firebase_exceptions
from fastapi import Header, HTTPException

from maadhyam_api.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def firebase_app():
    settings = get_settings()
    project_id = settings.google_cloud_project

    if not project_id:
        raise RuntimeError("MAADHYAM_GOOGLE_CLOUD_PROJECT is required")

    try:
        return firebase_admin.get_app("maadhyam-backend")
    except ValueError:
        return firebase_admin.initialize_app(
            options={"projectId": project_id},
            name="maadhyam-backend",
        )


def require_uid(
    authorization: str | None = Header(default=None),
) -> str:
    """Reject missing/invalid tokens; return verified Firebase UID."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Firebase authentication required",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Firebase authentication required",
        )

    try:
        decoded = auth.verify_id_token(
            token,
            app=firebase_app(),
            check_revoked=False,
        )
    except (ValueError, firebase_exceptions.FirebaseError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase token",
        ) from None
    except Exception:
        logger.exception("Firebase token verification unavailable")
        raise HTTPException(
            status_code=503,
            detail="Authentication service temporarily unavailable",
        ) from None

    uid = decoded.get("uid")

    if not isinstance(uid, str) or not uid:
        raise HTTPException(
            status_code=401,
            detail="Invalid Firebase identity",
        )

    return uid
