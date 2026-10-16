"""Private Supabase objects. Backend-only secret, no public URLs or frontend keys."""
import hashlib
import json
import socket
import time
import ipaddress
from http.client import HTTPSConnection
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse, urlencode
from urllib.request import Request, urlopen, HTTPSHandler, HTTPRedirectHandler, build_opener
from fastapi import HTTPException
from maadhyam_api.config import get_settings

_dns_cache = {}


def public_addresses(host):
    cached = _dns_cache.get(host)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    # Only the public configured hostname is sent; no API key accompanies DNS.
    with urlopen('https://dns.google/resolve?' + urlencode({'name': host, 'type': 'A'}), timeout=10) as response:
        answers = json.loads(response.read(65536)).get('Answer', [])
    addresses = [str(ipaddress.IPv4Address(answer['data'])) for answer in answers if answer.get('type') == 1]
    if not addresses:
        raise socket.gaierror('Supabase hostname has no public IPv4 record')
    _dns_cache[host] = (time.monotonic() + 60, addresses)
    return addresses


def private_opener(expected_host, fallback):
    class Connection(HTTPSConnection):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            original = self._create_connection
            def connect(address, *connection_args, **connection_kwargs):
                try:
                    return original(address, *connection_args, **connection_kwargs)
                except socket.gaierror:
                    if not fallback or address[0] != expected_host:
                        raise
                    for ip in public_addresses(expected_host):
                        try:
                            return original((ip, address[1]), *connection_args, **connection_kwargs)
                        except OSError:
                            continue
                    raise OSError('Supabase addresses were unreachable')
            self._create_connection = connect
            # HTTPSConnection still verifies the certificate against self.host,
            # and still sends the original hostname as TLS SNI.
    class Handler(HTTPSHandler):
        def https_open(self, request):
            return self.do_open(Connection, request, context=self._context)
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None  # Never forward a backend secret to another destination.
    return build_opener(Handler(), NoRedirect())


class SupabaseFiles:
    def __init__(self):
        config = get_settings()
        self.url = config.supabase_url.rstrip('/')
        self.key = config.supabase_secret_key
        self.bucket = config.supabase_bucket
        if not self.url or not self.key:
            raise HTTPException(503, 'Private file storage is not configured. Set backend Supabase URL and secret key.')
        if urlparse(self.url).scheme != 'https':
            raise HTTPException(503, 'Supabase URL must use HTTPS')
        self.opener = private_opener(urlparse(self.url).hostname, getattr(config, 'supabase_dns_fallback', False))
        details = json.loads(self.request('GET', '/bucket/' + quote(self.bucket, safe='')))
        if details.get('public') is not False:
            raise HTTPException(503, 'Document bucket must be private. Disable Public bucket in Supabase.')

    def request(self, method, path, data=None, mime='application/json', extra=None):
        headers = {'apikey': self.key, 'Content-Type': mime, **(extra or {})}
        # New secret keys belong only in apikey; legacy JWT service-role keys also need Authorization.
        if self.key.startswith('eyJ'):
            headers['Authorization'] = 'Bearer ' + self.key
        request = Request(self.url + '/storage/v1' + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.read(10 * 1024 * 1024 + 1)
        except HTTPError as error:
            if error.code == 404:
                raise HTTPException(404, 'Cloud object or bucket not found') from None
            if error.code in (400, 409):
                # Storage may encode Duplicate as 400. Only classify a true duplicate.
                try:
                    body = json.loads(error.read(4096))
                except ValueError:
                    body = {}
                if error.code == 409 or body.get('error') in ('Duplicate', 'ResourceAlreadyExists'):
                    raise FileExistsError('Object already exists') from None
            raise HTTPException(503, 'Private storage request failed. Check Supabase configuration and quota.') from None
        except (URLError, TimeoutError):
            raise HTTPException(503, 'Private file storage is unavailable; retry later') from None

    def object_path(self, key):
        return '/' + quote(self.bucket, safe='') + '/' + quote(key, safe='/')

    def upload(self, key, data, mime):
        try:
            self.request('POST', '/object' + self.object_path(key), data, mime, {'x-upsert': 'false', 'Cache-Control': 'no-store'})
        except FileExistsError:
            existing = self.download(key)
            if hashlib.sha256(existing).digest() != hashlib.sha256(data).digest():
                raise HTTPException(409, 'Upload conflicts with an existing object') from None

    def download(self, key):
        return self.request('GET', '/object/authenticated' + self.object_path(key))

    def delete(self, key):
        try:
            self.request('DELETE', '/object/' + quote(self.bucket, safe=''), json.dumps({'prefixes': [key]}).encode())
        except HTTPException as error:
            if error.status_code != 404:
                raise
