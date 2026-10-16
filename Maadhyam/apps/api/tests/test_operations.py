import logging
from fastapi.testclient import TestClient
from maadhyam_api.config import get_settings
from maadhyam_api.main import create_app


def test_private_responses_do_not_cache_and_logs_omit_identifiers(caplog):
    with caplog.at_level(logging.INFO, logger='maadhyam.operations'), TestClient(create_app()) as client:
        response = client.get('/api/applications/SECRET_IDENTIFIER?token=SECRET_QUERY')
    assert response.status_code == 401
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.headers['x-request-id']) == 32
    assert 'SECRET_IDENTIFIER' not in caplog.text
    assert 'SECRET_QUERY' not in caplog.text


def test_chunked_body_limit():
    with TestClient(create_app()) as client:
        response = client.post('/api/ai/extract-document', content=iter([b'x' * (1024 * 1024)] * 12))
    assert response.status_code == 413


def test_production_ai_auth_and_rate_limit(monkeypatch):
    from maadhyam_api.m10 import auth
    monkeypatch.setenv('MAADHYAM_ENVIRONMENT', 'production')
    monkeypatch.setenv('MAADHYAM_GEMINI_API_KEY', '')
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            assert client.post('/api/ai/connection-test').status_code == 401
            monkeypatch.setattr(auth, 'authenticated_user', lambda token: 'fictional-user')
            for _ in range(10):
                assert client.post('/api/ai/connection-test').status_code != 429
            response = client.post('/api/ai/connection-test')
            assert response.status_code == 429 and response.headers['retry-after'] == '60'
    finally:
        get_settings.cache_clear()
