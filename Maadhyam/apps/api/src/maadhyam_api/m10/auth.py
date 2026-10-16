"""Verify Firebase ID tokens; only the Firebase emulator is accepted in explicit test mode."""
from functools import lru_cache
from fastapi import Header, HTTPException
from maadhyam_api.config import get_settings

@lru_cache(maxsize=1)
def _certificate_request():
    import cachecontrol
    import requests
    from google.auth.transport.requests import Request
    return Request(session=cachecontrol.CacheControl(requests.Session()))

@lru_cache(maxsize=1)
def _firebase_app():
    import firebase_admin
    if not firebase_admin._apps:
        settings = get_settings()
        from firebase_admin import credentials
        credential = credentials.Certificate(settings.google_application_credentials) if settings.google_application_credentials else None
        return firebase_admin.initialize_app(credential, options={"projectId": settings.google_cloud_project or "maadhyam-local"})
    return firebase_admin.get_app()

def authenticated_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(401, "Authentication required")
    try:
        settings = get_settings()
        if settings.firestore_transport == 'user-rest':
            from functools import partial
            from google.oauth2.id_token import verify_firebase_token
            if not settings.google_cloud_project:
                raise ValueError('Firebase project required')
            decoded = verify_firebase_token(token, partial(_certificate_request(), timeout=10), audience=settings.google_cloud_project)
            if decoded.get('iss') != 'https://securetoken.google.com/' + settings.google_cloud_project:
                raise ValueError('Invalid issuer')
            subject = decoded.get('sub')
            if not isinstance(subject, str) or not 1 <= len(subject) <= 128:
                raise ValueError('Invalid subject')
            decoded = {**decoded, 'uid': subject}
        else:
            from firebase_admin import auth
            decoded = auth.verify_id_token(token, app=_firebase_app(), check_revoked=False)
        uid = decoded.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ValueError("Invalid identity")
        return uid
    except Exception:
        raise HTTPException(401, "Invalid or expired authentication token") from None
