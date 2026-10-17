"""Production-only authentication and bounded per-instance AI admission control."""
import json
import time
from collections import deque
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from maadhyam_api.services.firebase_auth import require_uid


def install_ai_guard(app, settings):
    # A global bound also limits abuse through creation of new anonymous users.
    admitted = deque(maxlen=60)
    vault_admitted = deque(maxlen=60)

    @app.middleware("http")
    async def guard(request, call_next):
        path = request.url.path
        vault_upload = path == '/api/documents' and request.method == 'POST'
        if vault_upload:
            try:
                vault_uid = require_uid(request.headers.get('authorization'))
            except HTTPException as exc:
                return JSONResponse({'error': {'message': exc.detail}}, exc.status_code)
            now = time.monotonic()
            while vault_admitted and now - vault_admitted[0][0] >= 3600:
                vault_admitted.popleft()
            if len(vault_admitted) >= 60 or sum(1 for stamp,owner in vault_admitted if owner == vault_uid and now-stamp < 60) >= 6:
                return JSONResponse({'error': {'message': 'Vault upload limit reached; retry later'}}, 429, headers={'Retry-After':'60'})
            vault_admitted.append((now,vault_uid))
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 11 * 1024 * 1024:
                    return JSONResponse({'error': {'message': 'Request exceeds upload limit'}}, 413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
        candidate = path in {"/api/ai/connection-test", "/api/ai/extract-document",
                             "/api/intelligence/chat"}
        if settings.production and candidate and request.method == "POST":
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 11 * 1024 * 1024:
                    return JSONResponse({"error": {"message": "Request exceeds upload limit"}}, 413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
            paid = path != "/api/intelligence/chat"
            if not paid:
                try:
                    paid = bool(json.loads(request._body).get("useGemini"))
                except (ValueError, AttributeError):
                    pass  # Pydantic handles malformed JSON below.
            if paid:
                try:
                    uid = require_uid(request.headers.get("authorization"))
                except HTTPException as exc:
                    return JSONResponse({"error": {"message": exc.detail}}, exc.status_code)
                now = time.monotonic()
                while admitted and now - admitted[0][0] >= 3600:
                    admitted.popleft()
                recent = sum(1 for stamp, owner in admitted if owner == uid and now - stamp < 60)
                if len(admitted) >= 60 or recent >= 6:
                    return JSONResponse({"error": {"message": "AI request limit reached; retry later"}},
                                        429, headers={"Retry-After": "60"})
                admitted.append((now, uid))
        return await call_next(request)
