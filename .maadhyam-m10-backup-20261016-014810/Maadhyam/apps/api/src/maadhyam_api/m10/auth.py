"""Verify Firebase ID tokens; only the Firebase emulator is accepted in explicit test mode."""
import os
from functools import lru_cache
from fastapi import Header, HTTPException

@lru_cache(maxsize=1)
def _firebase_app():
    import firebase_admin
    if not firebase_admin._apps:
        return firebase_admin.initialize_app(options={"projectId": os.getenv("GOOGLE_CLOUD_PROJECT", "maadhyam-local")})
    return firebase_admin.get_app()

def authenticated_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(401, "Authentication required")
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token, app=_firebase_app(), check_revoked=False)
        uid = decoded.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("Invalid identity")
        return uid
    except Exception:
        raise HTTPException(401, "Invalid or expired authentication token") from None
