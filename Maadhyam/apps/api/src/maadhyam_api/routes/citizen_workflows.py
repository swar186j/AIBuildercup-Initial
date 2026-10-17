"""Local-first citizen workflow helpers. Advisory only; no official action or eligibility claims."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, ConfigDict, model_validator

router = APIRouter(prefix='/citizen-workflows', tags=['Citizen Workflows'])

DISCLAIMER = 'Advisory scenario only. Confirm requirements, timelines, availability and acceptance with the responsible authority.'

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ReviewedContext(Strict):
    category: Literal['identity','address','birth','education','employment','other']
    documentType: Literal['Utility bill','Bank statement','Other address document','Other document'] = 'Other document'
    holderRelationship: Literal['self','parent-guardian','spouse','other'] = 'self'
    addressPresent: bool = False
    datePresent: bool = False
    reviewed: bool = False

class ContextConsent(Strict):
    consentToShareReviewedMetadata: bool = False
    documentContext: list[ReviewedContext] = Field(default_factory=list,max_length=3)

def reviewed_guidance(req):
    if not req.consentToShareReviewedMetadata:
        return []
    contexts=[d for d in req.documentContext if d.reviewed and d.category=='address']
    if not contexts:
        return ['No relevant reviewed address proof was selected. Check the written reason and review the proof first.']
    result=[]
    for doc in contexts:
        result.append(f'For the selected {doc.documentType.lower()}, compare the printed address with the application and ask the authority which proof types it accepts for your case.')
        if not doc.addressPresent:
            result.append('No address was recorded in reviewed metadata. Check the original document; this does not establish that the original lacks an address.')
        if not doc.datePresent:
            result.append('No document date was recorded. Check the original and any officially stated date requirements; no expiry window is assumed.')
        if doc.holderRelationship!='self':
            result.append('The selected proof is associated with another holder. Verify consent and whether relationship evidence is needed for your circumstances with the authority.')
    return list(dict.fromkeys(result))

class Rejection(ContextConsent):
    reason: str = Field(min_length=1, max_length=1000)
    authority: str = Field(min_length=1, max_length=120)
    applicationStage: str = Field(default='', max_length=120)
    evidenceDocumentIds: list[str] = Field(default_factory=list, max_length=60)

@router.post('/rejection-diagnosis')
def rejection_diagnosis(req: Rejection):
    text = req.reason.casefold()
    patterns = [
        ('identity_mismatch', ('name mismatch', 'dob mismatch', 'date of birth mismatch', 'identity mismatch'), 'Compare the exact printed fields and request the authority-specific correction process.'),
        ('missing_document', ('missing document', 'document not submitted', 'proof missing', 'incomplete documents'), 'Confirm the current document list and provide only officially accepted evidence.'),
        ('invalid_document', ('expired', 'illegible', 'invalid document', 'unreadable'), 'Check validity, legibility and the authority’s replacement requirements.'),
        ('address_mismatch', ('address mismatch', 'address proof', 'residential address'), 'Compare the address and verify which proof types are currently accepted.'),
        ('process_or_payment', ('fee', 'payment', 'appointment', 'signature'), 'Check the receipt, application instructions and official support channel.'),
    ]
    matches = [{'category': code, 'explanation': action} for code, terms, action in patterns if any(term in text for term in terms)]
    return {'possibleCauses': matches or [{'category': 'unclassified', 'explanation': 'Request the written rejection reason and consult the issuing authority.'}], 'authority': req.authority, 'applicationStage': req.applicationStage, 'referencedDocumentIds': req.evidenceDocumentIds, 'officialRootCauseConfirmed': False, 'reviewedMetadataGuidance': reviewed_guidance(req), 'disclaimer': DISCLAIMER}

class Legacy(Strict):
    documentType: str = Field(min_length=1, max_length=120)
    issuingAuthority: str = Field(default='', max_length=120)
    availableEvidence: list[str] = Field(default_factory=list, max_length=30)
    missingFields: list[str] = Field(default_factory=list, max_length=30)
    isOriginalAvailable: bool = False

@router.post('/legacy-reconstruction')
def legacy_reconstruction(req: Legacy):
    steps = ['Identify the original issuing office and request its official duplicate, certified copy or record-search procedure.', 'Gather existing reference numbers and available supporting evidence.', 'Check spelling, dates and record identifiers against originals before submission.', 'Ask the authority whether an affidavit, archival search or additional verification is required.']
    return {'documentType': req.documentType, 'issuingAuthority': req.issuingAuthority, 'originalAvailable': req.isOriginalAvailable, 'evidenceInventory': req.availableEvidence, 'fieldsToVerify': req.missingFields, 'suggestedSteps': steps, 'documentReconstructed': False, 'officialDuplicateIssued': False, 'disclaimer': DISCLAIMER}

class Service(Strict):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    lifeEvents: list[str] = Field(default_factory=list, max_length=20)
    department: str = Field(min_length=1, max_length=120)
    sourceUrl: str = ''

class Discover(Strict):
    lifeEvents: list[str] = Field(min_length=1, max_length=20)
    catalog: list[Service] = Field(default_factory=list, max_length=100)

@router.post('/life-event-discovery')
def life_event_discovery(req: Discover):
    keys = {x.strip().casefold() for x in req.lifeEvents if x.strip()}
    matches = [s.model_dump() for s in req.catalog if keys & {x.strip().casefold() for x in s.lifeEvents}]
    return {'matches': matches, 'matchCount': len(matches), 'catalogProvidedByCaller': True, 'officialEligibilityVerified': False, 'disclaimer': DISCLAIMER}

class Rule(Strict):
    id: str = Field(min_length=1, max_length=80)
    department: str = Field(min_length=1, max_length=120)
    service: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=100)
    sourceUrl: str = ''
    requiredDocumentTypes: list[str] = Field(default_factory=list, max_length=50)

class MultiRules(Strict):
    departments: list[str] = Field(default_factory=list, max_length=30)
    service: str = ''
    rulePacks: list[Rule] = Field(default_factory=list, max_length=100)

@router.post('/multi-department-rules')
def multi_department_rules(req: MultiRules):
    depts = {x.strip().casefold() for x in req.departments}
    selected = [r.model_dump() for r in req.rulePacks if (not depts or r.department.casefold() in depts) and (not req.service or r.service.casefold() == req.service.casefold())]
    return {'matchingRulePacks': selected, 'count': len(selected), 'sourceProvenanceRequired': True, 'officialRuleValidityVerified': False, 'disclaimer': DISCLAIMER}

class HumanSupport(ContextConsent):
    service: str = Field(min_length=1, max_length=120)
    blocker: str = Field(min_length=1, max_length=1000)
    preferredLanguage: str = Field(default='en', max_length=30)
    sharePersonalDocuments: bool = False

@router.post('/human-support')
def human_support(req: HumanSupport):
    return {'service': req.service, 'supportChecklist': ['Write down the exact blocker and reference number (avoid sensitive numbers in public messages).', 'Collect current official instructions and your reviewed document checklist.', 'Contact the authority’s official helpdesk or a trusted authorized assistance centre.', 'Ask for a written acknowledgment and next steps.'] + reviewed_guidance(req), 'preferredLanguage': req.preferredLanguage, 'documentSharingAuthorized': req.sharePersonalDocuments, 'caseAssignedToHuman': False, 'officialAgentConnected': False, 'disclaimer': DISCLAIMER}

class Step(Strict):
    id: str = Field(min_length=1, max_length=80)
    authority: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=160)
    dependsOn: list[str] = Field(default_factory=list, max_length=30)
    estimatedDays: int = Field(default=0, ge=0, le=3650)
    visits: int = Field(default=1, ge=0, le=30)
    onlinePossible: bool = False
    onlineOfficiallyVerified: bool = False
    completed: bool = False

class Workflow(Strict):
    steps: list[Step] = Field(default_factory=list, max_length=100)
    targetDate: date | None = None

    @model_validator(mode='after')
    def validate_steps(self):
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate step ID')
        for s in self.steps:
            if s.id in s.dependsOn or any(x not in ids for x in s.dependsOn):
                raise ValueError('Self or unknown dependency')
        return self

def inspect_graph(steps: list[Step]):
    lookup = {s.id: s for s in steps}
    indegree = {s.id: len(set(s.dependsOn)) for s in steps}
    downstream = defaultdict(list)
    for s in steps:
        for dep in set(s.dependsOn): downstream[dep].append(s.id)
    queue = deque(sorted(k for k,v in indegree.items() if v == 0))
    order = []
    while queue:
        node = queue.popleft(); order.append(node)
        for child in sorted(downstream[node]):
            indegree[child] -= 1
            if indegree[child] == 0: queue.append(child)
    cycles = sorted(set(lookup) - set(order))
    return order, cycles

@router.post('/authority-bottlenecks')
def authority_bottlenecks(req: Workflow):
    order, blocked = inspect_graph(req.steps)
    by_id = {s.id:s for s in req.steps}
    longest = {}
    for key in order:
        s = by_id[key]
        longest[key] = s.estimatedDays + max((longest[d] for d in s.dependsOn), default=0)
    authority_load = defaultdict(lambda: {'steps': [], 'estimatedVisits': 0})
    for s in req.steps:
        authority_load[s.authority]['steps'].append(s.id)
        authority_load[s.authority]['estimatedVisits'] += 0 if s.completed else s.visits
    return {'executionOrder': order, 'cycleOrCycleBlockedStepIds': blocked, 'estimatedCriticalPathDays': max(longest.values(), default=0) if not blocked else None, 'authoritySummary': dict(authority_load), 'bottleneckStepIds': sorted(k for k,v in longest.items() if v == max(longest.values(), default=-1)), 'officialTimelinesVerified': False, 'disclaimer': DISCLAIMER}

@router.post('/deadline-rescue')
def deadline_rescue(req: Workflow):
    order, blocked = inspect_graph(req.steps)
    by_id = {s.id:s for s in req.steps}
    lengths = {}
    for key in order:
        s = by_id[key]
        lengths[key] = (0 if s.completed else s.estimatedDays) + max((lengths[d] for d in s.dependsOn), default=0)
    required = max(lengths.values(), default=0) if not blocked else None
    days_left = (req.targetDate - date.today()).days if req.targetDate else None
    at_risk = bool(blocked) or (days_left is not None and required is not None and required > days_left)
    return {'targetDate': req.targetDate.isoformat() if req.targetDate else None, 'daysRemaining': days_left, 'estimatedCriticalPathDays': required, 'deadlineAtRiskUnderAssumptions': at_risk, 'cycleOrCycleBlockedStepIds': blocked, 'suggestions': (['Resolve the dependency cycle with the relevant authorities.'] if blocked else []) + (['Ask the responsible authority about urgent or alternative officially supported procedures.'] if at_risk else []) + ['Verify processing estimates and official deadlines before acting.'], 'officialDeadlineOrExpediteVerified': False, 'disclaimer': DISCLAIMER}

@router.post('/visit-eliminator')
def visit_eliminator(req: Workflow):
    order, blocked = inspect_graph(req.steps)
    eligible = [s.id for s in req.steps if not s.completed and s.visits and s.onlinePossible and s.onlineOfficiallyVerified]
    unverified = [s.id for s in req.steps if not s.completed and s.visits and s.onlinePossible and not s.onlineOfficiallyVerified]
    return {'baselineEstimatedVisits': sum(s.visits for s in req.steps if not s.completed), 'potentialAvoidableVisitsUnderAssumptions': sum(s.visits for s in req.steps if s.id in eligible), 'onlineVerifiedByCallerStepIds': eligible, 'onlineAvailabilityNeedsVerificationStepIds': unverified, 'remainingEstimatedVisitsUnderAssumptions': sum(s.visits for s in req.steps if not s.completed and s.id not in eligible), 'executionOrder': order, 'cycleOrCycleBlockedStepIds': blocked, 'governmentVisitsActuallyEliminated': False, 'disclaimer': DISCLAIMER}
