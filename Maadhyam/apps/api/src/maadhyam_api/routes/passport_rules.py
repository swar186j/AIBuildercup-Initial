"""Source-linked passport preparation rules; changes require verified review, never silent AI rewriting."""
from __future__ import annotations
import hashlib
import json
import os
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Literal
from urllib.request import Request, urlopen
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix='/passport', tags=['Passport Preparation'])
ROOT = Path(__file__).resolve().parent
PACK = ROOT / 'passport_rules_pack.json'
STATE = Path(os.getenv('MAADHYAM_PASSPORT_SOURCE_STATE', str(ROOT / 'passport_source_state.json')))

class VaultDocument(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    categories: list[Literal['identity','address','birth','education','employment','other']] = Field(default_factory=list)
    holder: Literal['self','parent-guardian','spouse','other'] = 'self'
    reviewed: bool = False
    documentType: str = ''
    printedName: str = ''
    dateOfBirth: str = ''
    residentialAddress: str = ''

class PassportAssessmentRequest(BaseModel):
    assistanceType: Literal['fresh','reissue','correction','documents','police'] = 'fresh'
    applicantAgeGroup: Literal['adult','minor',''] = ''
    applicantDateOfBirth: str = ''
    currentAddressMatches: Literal['yes','no','unsure',''] = ''
    hasIdentityDocument: Literal['yes','no','unsure',''] = ''
    hasAddressDocument: Literal['yes','no','unsure',''] = ''
    hasDateOfBirthDocument: Literal['yes','no','unsure',''] = ''
    nameConsistent: Literal['yes','no','unsure',''] = ''
    policeVerificationStatus: Literal['not-started','pending','completed','delayed','adverse','unknown',''] = ''
    addressChanged: Literal['yes','no','unsure',''] = ''
    nameChanged: Literal['yes','no','unsure',''] = ''
    nonEcrEligible: Literal['yes','no','unsure',''] = ''
    tatkaal: bool = False
    documents: list[VaultDocument] = Field(default_factory=list, max_length=100)

class Check(BaseModel):
    id: str
    title: str
    status: Literal['available-for-review','needs-attention','needs-confirmation']
    reason: str
    next_action: str
    matching_document_ids: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    source_url: str = ''
    source_id: str = ''

class AssessmentResponse(BaseModel):
    service: str = 'passport'
    ruleset_version: str
    official_requirements_verified: bool
    source_health: str
    checks: list[Check]
    sources: list[dict]
    disclaimer: str = 'Official sources are referenced, but this is a preparation aid, not government acceptance or approval. Confirm your case in the Passport Seva Document Advisor and jurisdictional Passport Office.'

def pack():
    return json.loads(PACK.read_text(encoding='utf-8'))

def monitored_state():
    """Fail closed on missing, malformed, or expired monitoring results."""
    try:
        from .passport_source_monitor import _read_state_bytes
        state = json.loads(_read_state_bytes(os.getenv('MAADHYAM_PASSPORT_SOURCE_STATE', str(STATE))).decode('utf-8'))
        if not isinstance(state, dict):
            return {'overall': 'not-monitored', 'sources': {}}
        checked = datetime.fromisoformat(state.get('last_checked', ''))
        if checked.tzinfo is None:
            raise ValueError('naive monitoring timestamp')
        if checked > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError('future monitoring timestamp')
        if datetime.now(timezone.utc) - checked > timedelta(hours=48):
            state['overall'] = 'stale-monitoring'
        return state
    except (OSError, ValueError, TypeError, OverflowError):
        return {'overall': 'not-monitored', 'sources': {}}


def source_health():
    return monitored_state()['overall']

def normalize(s):
    return ' '.join(''.join(c for c in s.casefold() if c.isalnum() or c.isspace()).split())

def make_check(rule, docs, answer='', allowed=None):
    allowed = allowed or rule['types']
    matches = [d for d in docs if normalize(d.documentType) in {normalize(t) for t in allowed} and (d.holder == 'self' or (rule['id']=='address' and d.holder=='parent-guardian'))]
    reviewed = [d for d in matches if d.reviewed]
    if answer == 'no':
        status, reason = 'needs-attention', 'Applicant reports this evidence is unavailable.'
    elif reviewed:
        status, reason = 'available-for-review', 'Matching self-reviewed vault document found; authenticity, details and acceptance still need confirmation.'
    else:
        status, reason = 'needs-confirmation', 'No self-reviewed vault document matches the listed proof types; confirm actual evidence and document details.'
    return Check(id=rule['id'], title=rule['title'], status=status, reason=reason,
                 next_action=rule['action'], matching_document_ids=[d.id for d in matches],
                 alternatives=allowed, source_url=rule['source_url'], source_id=rule['source_id'])

@router.post('/assess', response_model=AssessmentResponse)
def assess_passport(request: PassportAssessmentRequest):
    p = pack()
    rules = {r['id']: r for r in p['rules']}
    checks = []
    needs_core = request.assistanceType in ('fresh','reissue','correction','documents')
    if needs_core:
        if request.assistanceType == 'fresh' or request.currentAddressMatches == 'no' or request.addressChanged == 'yes':
            checks.append(make_check(rules['address'], request.documents, request.hasAddressDocument))
        elif request.assistanceType in ('reissue','correction'):
            checks.append(Check(id='address-reissue', title='Address proof for reissue',status='needs-confirmation',
                reason='Whether new address evidence is needed depends on changes to the existing passport.',
                next_action='Confirm whether the current address differs from the existing passport.',source_url=rules['address']['source_url'],source_id=rules['address']['source_id']))
        if request.assistanceType == 'fresh':
            try:
                dob = date.fromisoformat(request.applicantDateOfBirth)
            except ValueError:
                dob = None
            rule = rules['dob-new'] if dob and dob >= date(2023,10,1) else rules['dob-old']
            if not dob:
                checks.append(Check(id='dob-cutoff',title='Confirm DOB to select the legal evidence rule',status='needs-confirmation',
                    reason='Birth date is required to determine which official DOB-proof rule applies.',
                    next_action='Enter applicant date of birth (YYYY-MM-DD).',source_url=rule['source_url'],source_id=rule['source_id']))
            else:
                checks.append(make_check(rule,request.documents,request.hasDateOfBirthDocument))
            if request.nonEcrEligible != 'no':
                checks.append(Check(id='non-ecr',title='Non-ECR supporting proof',status='needs-confirmation',
                    reason='Non-ECR documentary evidence depends on eligibility category.',next_action='Check your category in the official Document Advisor and prepare supporting evidence where applicable.',
                    source_url=rules['non-ecr']['source_url'],source_id=rules['non-ecr']['source_id']))
        if request.assistanceType in ('reissue','correction'):
            checks.append(make_check(rules['old-passport'],request.documents))
        if request.applicantAgeGroup == 'minor':
            checks.append(Check(id='minor',title='Minor applicant and parental consent',status='needs-confirmation',
                reason='Parent/guardian evidence and consent vary by circumstances.',next_action='Use the official minor Document Advisor; parent-address proof may be used where applicable.',
                source_url=rules['minor']['source_url'],source_id=rules['minor']['source_id']))
        if request.nameConsistent == 'no' or request.nameChanged == 'yes':
            checks.append(Check(id='name-change',title='Name mismatch or change',status='needs-attention',
                reason='Name change is case-dependent; do not assume a simple spelling correction is sufficient.',
                next_action='Compare names and follow official change-of-name instructions for the specific case.',
                source_url=rules['name-change']['source_url'],source_id=rules['name-change']['source_id']))
        if request.tatkaal:
            checks.append(Check(id='tatkaal',title='Tatkaal application requirements',status='needs-confirmation',
                reason='Tatkaal eligibility and additional document requirements must be checked separately.',
                next_action='Complete the official Tatkaal Document Advisor before proceeding.',source_url=rules['tatkaal']['source_url'],source_id=rules['tatkaal']['source_id']))
    if request.policeVerificationStatus in ('delayed','adverse','pending','unknown'):
        checks.append(Check(id='police',title='Police verification follow-up',status='needs-attention' if request.policeVerificationStatus in ('delayed','adverse') else 'needs-confirmation',
            reason='Police verification status requires checking official tracking.',next_action='Use Passport Seva tracking and contact RPO through official channels if needed.',
            source_url='https://www.passportindia.gov.in/',source_id='passport-portal'))
    health = source_health()
    return AssessmentResponse(ruleset_version=p['version'],official_requirements_verified=False,
        source_health=health,checks=checks,sources=p['sources'])

@router.get('/rules/status')
def rules_status():
    p = pack()
    state = monitored_state()
    return {'version':p['version'],'verified_on':p['verified_on'],'source_health':state.get('overall','not-monitored'),
            'monitor':state,'sources':p['sources'],'note':'Source monitoring detects possible changes. It never silently modifies legal rules.'}

@router.post('/rules/check-sources')
def check_sources():
    """Do not expose this unauthenticated endpoint: monitoring must run from trusted scheduled CLI."""
    from fastapi import HTTPException
    raise HTTPException(status_code=403,detail='Run python -m maadhyam_api.routes.passport_source_monitor from a trusted scheduled job.')
