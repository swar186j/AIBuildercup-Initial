"""M7/M8 deterministic, conservative reasoning over reviewed fictional document metadata.

No legal proof acceptance is inferred. No document bytes or personal data are persisted.
"""
from __future__ import annotations
from collections import defaultdict
from pydantic import BaseModel, Field, model_validator
from typing import Literal

from .intelligence import Document, Request, analyze, build_passport_plan


class FamilyLink(BaseModel):
    documentId: str = Field(min_length=1)
    relation: Literal['parent','guardian','spouse','child','sibling','other']
    claimedByApplicant: bool = False
    relationshipEvidenceDocumentIds: list[str] = Field(default_factory=list)


class Simulation(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=150)
    removeDocumentIds: list[str] = Field(default_factory=list)
    markReviewedIds: list[str] = Field(default_factory=list)
    replaceFields: dict[str, dict[Literal['printedName','dateOfBirth','residentialAddress'], str]] = Field(default_factory=dict)


class ReasoningRequest(Request):
    familyLinks: list[FamilyLink] = Field(default_factory=list, max_length=60)
    simulations: list[Simulation] = Field(default_factory=list, max_length=12)

    @model_validator(mode='after')
    def validate_references(self):
        ids = {d.id for d in self.documents}
        linked = set()
        for link in self.familyLinks:
            if link.documentId not in ids:
                raise ValueError(f'Unknown family document: {link.documentId}')
            if link.documentId in linked:
                raise ValueError(f'Duplicate family link: {link.documentId}')
            linked.add(link.documentId)
            if any(x not in ids for x in link.relationshipEvidenceDocumentIds):
                raise ValueError('Unknown relationship evidence document')
        sim_ids = set()
        for sim in self.simulations:
            if sim.id in sim_ids:
                raise ValueError('Duplicate simulation ID')
            sim_ids.add(sim.id)
            if any(x not in ids for x in sim.removeDocumentIds + sim.markReviewedIds):
                raise ValueError('Simulation references unknown document')
            if any(x not in ids for x in sim.replaceFields):
                raise ValueError('Simulation updates unknown document')
            if set(sim.removeDocumentIds) & (set(sim.markReviewedIds) | set(sim.replaceFields)):
                raise ValueError('Cannot remove and update same document')
        return self


def _request(req: ReasoningRequest, docs: list[Document]) -> Request:
    return Request(documents=docs, assistanceType=req.assistanceType,
                   applicantAgeGroup=req.applicantAgeGroup, targetDate=req.targetDate)


def _summary(req: ReasoningRequest, docs: list[Document]) -> dict:
    base = _request(req, docs)
    assessment = analyze(base)
    plan = build_passport_plan(base, assessment)
    return {'assessment': assessment, 'passportPlan': plan,
            'reviewFindings': sorted(f['id'] for f in assessment['findings'] if f['severity'] == 'review'),
            'blockers': plan['preparationBlockers']}


def _family(req: ReasoningRequest) -> dict:
    docs = {d.id:d for d in req.documents}
    links = []
    for link in req.familyLinks:
        doc = docs[link.documentId]
        evidence = [docs[x] for x in link.relationshipEvidenceDocumentIds]
        # A self-declared relation is never treated as legally verified.
        links.append({'documentId': doc.id, 'relation': link.relation,
                      'holder': doc.holder, 'claimedByApplicant': link.claimedByApplicant,
                      'relationshipEvidenceIds': [x.id for x in evidence],
                      'reviewedRelationshipEvidenceIds': [x.id for x in evidence if x.reviewed],
                      'requiresVerification': True, 'officialRelationshipVerified': False,
                      'warning': ('Holder is self; check whether family link was entered correctly.' if doc.holder == 'self'
                                  else 'Relationship and document acceptance require independent official verification.')})
    unlinked = [d.id for d in req.documents if d.holder != 'self' and d.id not in {l.documentId for l in req.familyLinks}]
    return {'links':links,'unlinkedFamilyDocumentIds':unlinked,
            'officialRelationshipVerified':False,
            'note':'A claimed family relationship is not independently verified by the Vault.'}


def _task_graph(assessment: dict) -> dict:
    tasks = assessment['tasks']
    ids = {t['id'] for t in tasks}
    edges = [{'before': dep, 'after': t['id']} for t in tasks for dep in t['dependsOn']]
    # Explicitly verify graph invariants; don't silently return a misleading order.
    order = assessment['executionOrder']
    positions = {key: i for i,key in enumerate(order)}
    invalid = [edge for edge in edges if edge['before'] not in ids or positions.get(edge['before'], 10**9) >= positions.get(edge['after'], -1)]
    if invalid:
        raise ValueError('Invalid dependency ordering')
    return {'nodes':[{'id':t['id'],'title':t['title'],'priority':t['priority']} for t in tasks],
            'edges':edges,'executionOrder':order,'cyclesDetected':False,
            'optimizationScope':'Deduplicated preparation tasks and dependency-safe ordering only; no legal or time-cost optimization.'}


def reason(req: ReasoningRequest) -> dict:
    baseline = _summary(req, req.documents)
    results = []
    for sim in req.simulations:
        docs = []
        for original in req.documents:
            if original.id in sim.removeDocumentIds:
                continue
            updates = dict(sim.replaceFields.get(original.id, {}))
            if original.id in sim.markReviewedIds:
                updates['reviewed'] = True
            docs.append(original.model_copy(update=updates))
        outcome = _summary(req, docs)
        before = set(baseline['reviewFindings'])
        after = set(outcome['reviewFindings'])
        results.append({'id':sim.id,'label':sim.label,'before':{'reviewFindings':sorted(before),'blockers':baseline['blockers']},
                        'after':{'reviewFindings':sorted(after),'blockers':outcome['blockers']},
                        'resolvedFindingIds':sorted(before-after), 'newFindingIds':sorted(after-before),
                        'remainingTaskIds':outcome['assessment']['executionOrder'],
                        'officialAcceptanceVerified':False,
                        'caution':'Simulation changes metadata only; it does not correct official records.'})
    return {'mode':'local-deterministic','baseline':baseline,'dependencyGraph':_task_graph(baseline['assessment']),
            'familyEvidence':_family(req),'simulations':results,
            'officialEligibilityDetermined':False,
            'disclaimer':'Scenario planning only. Verify real evidence and current Passport Seva rules independently.'}
