import pytest
from fastapi import HTTPException
from firebase_admin import auth
from maadhyam_api.m10 import auth as application_auth


@pytest.mark.parametrize('header', [None, '', 'Basic test', 'Bearer ', 'bearer token'])
def test_missing_or_wrong_auth_scheme_is_rejected(header):
    with pytest.raises(HTTPException) as exc:
        application_auth.authenticated_user(header)
    assert exc.value.status_code == 401


def test_identity_comes_only_from_verified_token(monkeypatch):
    app = object()
    monkeypatch.setattr(application_auth, '_firebase_app', lambda: app)
    calls = []
    def verify(token, **kwargs):
        calls.append((token, kwargs))
        return {'uid': 'verified-owner'}
    monkeypatch.setattr(auth, 'verify_id_token', verify)
    assert application_auth.authenticated_user('Bearer synthetic-token') == 'verified-owner'
    assert calls == [('synthetic-token', {'app': app, 'check_revoked': False})]


@pytest.mark.parametrize('decoded', [{}, {'uid': ''}, {'uid': 123}])
def test_invalid_verified_identity_is_rejected(monkeypatch, decoded):
    monkeypatch.setattr(application_auth, '_firebase_app', lambda: object())
    monkeypatch.setattr(auth, 'verify_id_token', lambda *args, **kwargs: decoded)
    with pytest.raises(HTTPException) as exc:
        application_auth.authenticated_user('Bearer synthetic-token')
    assert exc.value.status_code == 401


def test_token_failure_does_not_leak_provider_details(monkeypatch):
    monkeypatch.setattr(application_auth, '_firebase_app', lambda: object())
    def fail(*args, **kwargs):
        raise ValueError('SECRET_TOKEN_DETAILS')
    monkeypatch.setattr(auth, 'verify_id_token', fail)
    with pytest.raises(HTTPException) as exc:
        application_auth.authenticated_user('Bearer synthetic-token')
    assert exc.value.status_code == 401
    assert 'SECRET' not in exc.value.detail
