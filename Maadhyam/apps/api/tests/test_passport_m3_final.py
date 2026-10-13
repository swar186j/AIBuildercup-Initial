import json
import pytest
from maadhyam_api.routes import passport_source_monitor as m

SOURCE = {'id':'official-documents','url':'https://www.passportindia.gov.in/psp/ListDocuments'}
TEXT = 'proof of address aadhaar electricity rent agreement ' * 12

def setup(monkeypatch, tmp_path):
    for key, file in [('MAADHYAM_PASSPORT_SOURCE_SNAPSHOTS','snap.json'),('MAADHYAM_PASSPORT_APPROVED_BASELINES','base.json'),('MAADHYAM_PASSPORT_RULE_PROPOSALS','proposals.json'),('MAADHYAM_PASSPORT_SOURCE_STATE','state.json')]:
        monkeypatch.setenv(key,str(tmp_path/file))
    monkeypatch.setattr(m,'PACK',tmp_path/'pack.json')
    (tmp_path/'pack.json').write_text(json.dumps({'version':'test','sources':[SOURCE]}))
    monkeypatch.setattr(m,'_fetch_source',lambda source, fetcher: (f'<html><main>{TEXT}</main></html>'.encode(),'text/html',SOURCE['url'],SOURCE['url']))

def test_migration_history_preserves_prior_approval(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    m._save_json(m.baseline_path(),{'sources':{'official-documents':{'url':SOURCE['url'],'sha256':'legacy','fingerprint_method':'html-text'}}})
    m.approve('official-documents','reviewer',True)
    data=m._load_json(m.baseline_path())
    assert data['approval_history'][0]['event']=='fingerprint-method-migration'
    assert data['approval_history'][0]['previous_sha256']=='legacy'
    assert data['sources']['official-documents']['fingerprint_method']=='html-guidance-v2'

def test_compare_rejects_incompatible_method(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    m.approve('official-documents','reviewer',True)
    data=m._load_json(m.baseline_path())
    data['sources']['official-documents']['fingerprint_method']='html-text'
    m._save_json(m.baseline_path(),data)
    with pytest.raises(ValueError,match='metadata-mismatch'):
        m.compare('official-documents')

def test_gazette_relevance_requires_specific_context(monkeypatch):
    monkeypatch.setattr(m,'_guidance_text',lambda *args: ('general gazette notification about birth certificate only '*20,'pdf-text-v2'))
    with pytest.raises(ValueError,match='pdf-source-content-mismatch'):
        m._validate_source('official-gazette',b'%PDF-','application/pdf')
    monkeypatch.setattr(m,'_guidance_text',lambda *args: ('ministry of external affairs passport rules date of birth '*20,'pdf-text-v2'))
    m._validate_source('official-gazette',b'%PDF-','application/pdf')

def test_gemini_failure_does_not_discard_human_proposal(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    m.approve('official-documents','reviewer',True)
    monkeypatch.setattr(m,'_fetch_source',lambda source,fetcher:(f'<html><main>{TEXT} new mandatory certificate</main></html>'.encode(),'text/html',SOURCE['url'],SOURCE['url']))
    from maadhyam_api.routes import passport_rule_change_ai
    monkeypatch.setattr(passport_rule_change_ai,'analyze_public_source',lambda *args: (_ for _ in ()).throw(RuntimeError('offline')))
    proposal=m.compare('official-documents',use_gemini=True)
    assert proposal['status']=='needs-human-review'
    assert proposal['ai_analysis']['status']=='unavailable'
    assert len(m._load_json(m.proposals_path())['proposals'])==1

def test_unavailable_booklet_never_falls_back_to_unrelated_page():
    url='https://portal4.passportindia.gov.in/Online/pdf/ApplicationformInstructionBooklet-V3.0.pdf'
    result=m.evaluate([{'id':'official-booklet','url':url}],{},lambda u:(b'<html><body>Welcome to Passport Seva home page</body></html>','text/html',u))
    assert result['sources']['official-booklet']['status']=='fetch-failed'


def test_approved_observed_snapshot_becomes_rollback_eligible(monkeypatch,tmp_path):
    setup(monkeypatch,tmp_path)
    m.approve('official-documents','reviewer',True)
    baseline=m._load_json(m.baseline_path())['sources']['official-documents']
    digest=baseline['sha256']
    m._save_snapshot('official-documents',digest,TEXT,SOURCE['url'],'observed-unapproved')
    assert m._snapshot('official-documents',digest)['status']=='approved-source-content'
    m._save_json(m.snapshots_path(),{'sources':{'official-documents':{digest:{'sha256':digest,'text':TEXT,'official_url':SOURCE['url'],'status':'observed-unapproved'}}}})
    m._save_snapshot('official-documents',digest,TEXT,SOURCE['url'],'approved-source-content')
    assert m._snapshot('official-documents',digest)['status']=='approved-source-content'
