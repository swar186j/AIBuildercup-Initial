import hashlib
import io
import pytest
from maadhyam_api.routes import passport_source_monitor as m

DOC = '''<html><body><header>Passport Seva Wednesday, October 14, 2026 | 12:10:19 am</header>
<nav>Home About Login</nav><div class="news-ticker">Mobile van camp October 2025</div>
<main><h1>Proof of Address</h1><p>List of acceptable documents: Aadhaar, electricity bill,
rent agreement, water bill, bank passbook and other officially permitted proofs.</p>
<p>Applicants must submit present address proof. Verify the specific category and conditions before applying.</p></main>
<footer>Contact us</footer></body></html>'''

def test_clock_and_chrome_do_not_change_guidance_hash():
    changed = DOC.replace('12:10:19', '12:15:22').replace('Mobile van camp October 2025', 'Mobile van camp November 2026')
    assert m._fingerprint(DOC.encode(), 'text/html', 'official-documents') == m._fingerprint(changed.encode(), 'text/html', 'official-documents')

def test_substantive_guidance_change_is_detected():
    changed = DOC.replace('water bill, bank passbook', 'water bill, bank passbook, newly listed certificate')
    assert m._fingerprint(DOC.encode(), 'text/html', 'official-documents')[0] != m._fingerprint(changed.encode(), 'text/html', 'official-documents')[0]

def test_portal_shell_only_is_rejected():
    page = ('<html><body><header>Fresh Passport</header><nav>Home</nav><main>' +
            'Special passport mobile van camp is being organised. '*10 + '</main></body></html>').encode()
    with pytest.raises(ValueError, match='source-guidance-not-found'):
        m._validate_source('official-fresh', page, 'text/html')

def test_invalid_pdf_cannot_be_approved():
    with pytest.raises(ValueError, match='pdf-text-extraction-failed'):
        m._snapshot_text(b'%PDF-' + b'X'*1200, 'application/pdf', 'official-gazette')
