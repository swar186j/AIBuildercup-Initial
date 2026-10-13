import importlib.util
from pathlib import Path
import pytest

MODULE = Path(__file__).resolve().parents[1] / 'src' / 'maadhyam_api' / 'routes' / 'passport_source_monitor.py'
spec = importlib.util.spec_from_file_location('spa_monitor_test', MODULE)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

SHELL = b'<!doctype html><html><head><script src="/psp/static/js/main.abc.js"></script></head><body><div id="root"></div></body></html>'
VALID = b'<html><body>' + (b'Passport fresh passport proof of address aadhaar application requirements. ' * 8) + b'</body></html>'
URL = 'https://www.passportindia.gov.in/psp/ListDocuments'

def test_shell_detected():
    assert monitor._is_spa_shell(SHELL, 'text/html')
    assert not monitor._is_spa_shell(VALID, 'text/html')

def test_browser_used_only_for_shell():
    calls = []
    def render(url):
        calls.append(url)
        return VALID, 'text/html', url
    assert monitor._fetch_with_browser_fallback(URL, lambda _: (SHELL, 'text/html', URL), render)[0] == VALID
    assert calls == [URL]
    calls.clear()
    assert monitor._fetch_with_browser_fallback(URL, lambda _: (VALID, 'text/html', URL), render)[0] == VALID
    assert not calls

def test_shell_still_empty_is_rejected():
    with pytest.raises(ValueError, match='empty-shell'):
        monitor._fetch_with_browser_fallback(URL, lambda _: (SHELL, 'text/html', URL), lambda _: (SHELL, 'text/html', URL))

def test_offsite_redirect_is_rejected():
    with pytest.raises(ValueError, match='unexpected-redirect'):
        monitor._fetch_with_browser_fallback(URL, lambda _: (SHELL, 'text/html', URL), lambda _: (VALID, 'text/html', 'https://example.com/'))

def test_rendered_content_must_still_pass_source_validation():
    source = {'id': 'official-documents', 'url': URL}
    body, _, _, _ = monitor._fetch_source(source, lambda _: (SHELL, 'text/html', URL), lambda _: (VALID, 'text/html', URL))
    assert body == VALID
    with pytest.raises(ValueError, match='all-source-candidates-failed'):
        monitor._fetch_source(source, lambda _: (SHELL, 'text/html', URL), lambda _: (b'<html>login</html>', 'text/html', URL))
