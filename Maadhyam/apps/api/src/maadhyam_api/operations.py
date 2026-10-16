"""Bounded request admission and metadata-only operational logs."""
import json
import logging
import time
from collections import OrderedDict, deque
from uuid import uuid4

from starlette.responses import JSONResponse

log = logging.getLogger('maadhyam.operations')


class OperationalMiddleware:
    def __init__(self, app):
        self.app = app
        from maadhyam_api.config import get_settings
        self.production = get_settings().environment == 'production'
        self.calls = OrderedDict()
        self.ai_calls = deque()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started = time.monotonic()
        request_id = uuid4().hex
        path = scope['path']
        ai = path.startswith('/api/ai/') or path == '/api/intelligence/chat'
        if self.production and ai and scope['method'] == 'POST':
            from fastapi import HTTPException
            from starlette.concurrency import run_in_threadpool
            from maadhyam_api.m10.auth import authenticated_user
            authorization = dict(scope.get('headers', [])).get(b'authorization', b'').decode('latin1')
            try:
                key = await run_in_threadpool(authenticated_user, authorization)
            except HTTPException:
                return await JSONResponse({'error': {'code': 'authentication_required', 'message': 'Sign in required.'}},
                    status_code=401, headers={'Cache-Control': 'no-store'})(scope, receive, send)
            now = time.monotonic()
            # Process-local limits complement the deployment's single instance.
            window = self.calls.setdefault(key, deque())
            self.calls.move_to_end(key)
            while window and now - window[0] >= 60:
                window.popleft()
            while self.ai_calls and now - self.ai_calls[0] >= 86400:
                self.ai_calls.popleft()
            if len(window) >= 10 or len(self.ai_calls) >= 200:
                return await JSONResponse({'error': {'code': 'rate_limit', 'message': 'AI request limit reached; retry later.'}},
                    status_code=429, headers={'Retry-After': '60', 'Cache-Control': 'no-store'})(scope, receive, send)
            window.append(now)
            self.ai_calls.append(now)
            if len(self.calls) > 1024:
                self.calls.popitem(last=False)
        # Bound the complete body, including chunked uploads, before parsing multipart.
        parts, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            size += len(message.get('body', b''))
            if size > 11 * 1024 * 1024:
                return await JSONResponse({'error': {'code': 'body_too_large', 'message': 'Request exceeds 11 MB.'}},
                    status_code=413, headers={'Cache-Control': 'no-store'})(scope, receive, send)
            parts.append(message)
            if not message.get('more_body', False):
                break
        index = 0

        async def replay():
            nonlocal index
            if index < len(parts):
                item = parts[index]
                index += 1
                return item
            return await receive()

        status = 500
        response_started = False

        async def safe_send(message):
            nonlocal status, response_started
            if message['type'] == 'http.response.start':
                response_started = True
                status = message['status']
                headers = list(message.get('headers', []))
                headers = [(k, v) for k, v in headers if k.lower() not in (b'x-request-id', b'x-content-type-options')]
                headers += [(b'x-request-id', request_id.encode()), (b'x-content-type-options', b'nosniff')]
                if path.startswith('/api/'):
                    headers = [(k, v) for k, v in headers if k.lower() != b'cache-control']
                    headers.append((b'cache-control', b'no-store'))
                message = {**message, 'headers': headers}
            await send(message)

        try:
            await self.app(scope, replay, safe_send)
        except Exception as exc:
            log.error(json.dumps({'event': 'request_error', 'request_id': request_id, 'type': type(exc).__name__}))
            if not response_started:
                await JSONResponse({'error': {'code': 'internal_error', 'message': 'An unexpected server error occurred'}},
                    status_code=500)(scope, replay, safe_send)
        finally:
            # Omit URLs, queries, identifiers, authorization, bodies and exception text.
            log.info(json.dumps({'event': 'request', 'request_id': request_id,
                'method': scope['method'], 'status': status, 'ai': ai,
                'elapsed_ms': round((time.monotonic() - started) * 1000)}))
