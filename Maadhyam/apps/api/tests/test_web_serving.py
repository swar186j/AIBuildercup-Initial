from fastapi.testclient import TestClient
from maadhyam_api.config import get_settings
from maadhyam_api.main import create_app


def test_spa_direct_routes_api_boundary_and_asset_cache(tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<html><div id="root"></div></html>')
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'assets' / 'app-hash.js').write_text('console.log("fictional")')
    monkeypatch.setenv('MAADHYAM_WEB_DIST', str(tmp_path))
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
            for route in ['/', '/applications', '/services/passport/journey?type=fresh']:
                response = client.get(route)
                assert response.status_code == 200 and '<div id="root"' in response.text
                assert response.headers['cache-control'] == 'no-cache'
            assert client.get('/api/nonexistent').status_code == 404
            assert client.get('/.env').status_code == 404
            assert client.get('/assets/missing.js').status_code == 404
            assert 'immutable' in client.get('/assets/app-hash.js').headers['cache-control']
            assert client.get('/api/health').json()['status'] == 'healthy'
            assert client.get('/api/applications').status_code == 401
    finally:
        get_settings.cache_clear()
