import json
from types import SimpleNamespace
import pytest
import socket
import ssl
from urllib.request import HTTPSHandler, HTTPRedirectHandler
from fastapi import HTTPException
from maadhyam_api.m10 import supabase_files


class Response:
    def __init__(self, value):
        self.value = value
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def read(self, limit):
        return self.value[:limit]


def configure(monkeypatch):
    monkeypatch.setattr(supabase_files, 'get_settings', lambda: SimpleNamespace(supabase_url='https://fictional.supabase.co', supabase_secret_key='sb_secret_synthetic', supabase_bucket='maadhyam-documents'))
    monkeypatch.setattr(supabase_files, 'private_opener', lambda *args: SimpleNamespace(open=lambda request, timeout: supabase_files.urlopen(request, timeout=timeout)))


def test_secret_stays_in_backend_apikey_and_objects_are_private(monkeypatch):
    configure(monkeypatch)
    calls = []
    def transport(request, timeout):
        calls.append(request)
        return Response(json.dumps({'public': False}).encode() if '/bucket/' in request.full_url else b'file')
    monkeypatch.setattr(supabase_files, 'urlopen', transport)
    files = supabase_files.SupabaseFiles()
    files.download('users/fictional/vault/doc-123')
    assert calls[0].get_header('Apikey') == 'sb_secret_synthetic'
    assert calls[0].get_header('Authorization') is None
    assert '/object/authenticated/' in calls[1].full_url
    assert all('sb_secret' not in request.full_url for request in calls)


def test_public_bucket_rejected_before_any_upload(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(supabase_files, 'urlopen', lambda *args, **kwargs: Response(b'{"public":true}'))
    with pytest.raises(HTTPException) as error:
        supabase_files.SupabaseFiles()
    assert error.value.status_code == 503


def test_missing_config_fails_without_network(monkeypatch):
    monkeypatch.setattr(supabase_files, 'get_settings', lambda: SimpleNamespace(supabase_url='', supabase_secret_key='', supabase_bucket='maadhyam-documents'))
    with pytest.raises(HTTPException) as error:
        supabase_files.SupabaseFiles()
    assert error.value.status_code == 503


def test_retry_upload_never_overwrites_other_bytes(monkeypatch):
    files = object.__new__(supabase_files.SupabaseFiles)
    files.bucket = 'maadhyam-documents'
    monkeypatch.setattr(files, 'request', lambda *args, **kwargs: (_ for _ in ()).throw(FileExistsError()))
    monkeypatch.setattr(files, 'download', lambda key: b'first file')
    files.upload('users/a/vault/id', b'first file', 'image/png')
    with pytest.raises(HTTPException) as error:
        files.upload('users/a/vault/id', b'different file', 'image/png')
    assert error.value.status_code == 409


def connection_class(monkeypatch, expected_host):
    opener = supabase_files.private_opener(expected_host, True)
    handler = next(handler for handler in opener.handlers if isinstance(handler, HTTPSHandler))
    monkeypatch.setattr(handler, 'do_open', lambda cls, request, **kwargs: cls)
    return handler.https_open(None)


def test_dns_fallback_keeps_original_tls_hostname(monkeypatch):
    calls = []
    sentinel = object()
    def connect(address, *args, **kwargs):
        calls.append(address)
        if address[0] == 'fictional.supabase.co':
            raise socket.gaierror('Synthetic local DNS failure')
        return sentinel
    monkeypatch.setattr(socket, 'create_connection', connect)
    monkeypatch.setattr(supabase_files, 'public_addresses', lambda host: ['203.0.113.1'])
    connection = connection_class(monkeypatch, 'fictional.supabase.co')('fictional.supabase.co')
    assert connection._create_connection(('fictional.supabase.co', 443)) is sentinel
    assert calls == [('fictional.supabase.co', 443), ('203.0.113.1', 443)]
    assert connection.host == 'fictional.supabase.co'
    assert connection._context.verify_mode == ssl.CERT_REQUIRED
    assert connection._context.check_hostname is True


def test_dns_fallback_does_not_handle_other_hosts_or_tls_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise socket.gaierror('Synthetic proxy DNS failure')
    monkeypatch.setattr(socket, 'create_connection', fail)
    monkeypatch.setattr(supabase_files, 'public_addresses', lambda host: pytest.fail('Unrelated destination must not use fallback'))
    connection = connection_class(monkeypatch, 'fictional.supabase.co')('proxy.example')
    with pytest.raises(socket.gaierror):
        connection._create_connection(('proxy.example', 443))
    def bad_certificate(*args, **kwargs):
        raise ssl.SSLCertVerificationError('Synthetic certificate failure')
    monkeypatch.setattr(socket, 'create_connection', bad_certificate)
    connection = connection_class(monkeypatch, 'fictional.supabase.co')('fictional.supabase.co')
    with pytest.raises(ssl.SSLCertVerificationError):
        connection._create_connection(('fictional.supabase.co', 443))


def test_backend_secret_is_never_forwarded_by_redirect():
    opener = supabase_files.private_opener('fictional.supabase.co', False)
    redirect = next(handler for handler in opener.handlers if isinstance(handler, HTTPRedirectHandler))
    assert redirect.redirect_request(None, None, 302, '', {}, 'https://other.example') is None
