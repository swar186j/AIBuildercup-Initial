"""Conservative deterministic reasoning over reviewed document metadata.

No official proof acceptance, processing duration or legal correction is inferred.

"""

from __future__ import annotations

from collections import defaultdict

from datetime import date

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .intelligence import Document, Request, analyze, build_passport_plan, canonical_dob

from .passport_rules import pack, normalize


class FamilyLink(BaseModel):

    documentId: str = Field(min_length=1)

    relation: Literal["parent", "guardian", "spouse", "child", "sibling", "other"]

    claimedByApplicant: bool = False

    relationshipEvidenceDocumentIds: list[str] = Field(default_factory=list)


class Simulation(BaseModel):

    id: str = Field(min_length=1, max_length=80)

    label: str = Field(min_length=1, max_length=150)

    removeDocumentIds: list[str] = Field(default_factory=list)

    markReviewedIds: list[str] = Field(default_factory=list)

    replaceFields: dict[
        str, dict[Literal["printedName", "dateOfBirth", "residentialAddress"], str]
    ] = Field(default_factory=dict)


class ReasoningRequest(Request):

    familyLinks: list[FamilyLink] = Field(default_factory=list, max_length=60)

    simulations: list[Simulation] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_references(self):

        ids = {d.id for d in self.documents}

        linked = set()

        for link in self.familyLinks:

            if link.documentId not in ids:

                raise ValueError(f"Unknown family document: {link.documentId}")

            if link.documentId in linked:

                raise ValueError(f"Duplicate family link: {link.documentId}")

            linked.add(link.documentId)

            if any(x not in ids for x in link.relationshipEvidenceDocumentIds):

                raise ValueError("Unknown relationship evidence document")

        sim_ids = set()

        for sim in self.simulations:

            if sim.id in sim_ids:

                raise ValueError("Duplicate simulation ID")

            sim_ids.add(sim.id)

            if any(x not in ids for x in sim.removeDocumentIds + sim.markReviewedIds):

                raise ValueError("Simulation references unknown document")

            if any(x not in ids for x in sim.replaceFields):

                raise ValueError("Simulation updates unknown document")

            if set(sim.removeDocumentIds) & (
                set(sim.markReviewedIds) | set(sim.replaceFields)
            ):

                raise ValueError("Cannot remove and update same document")

        return self


def _request(req: ReasoningRequest, docs: list[Document]) -> Request:

    return Request(
        documents=docs,
        assistanceType=req.assistanceType,
        applicantAgeGroup=req.applicantAgeGroup,
        targetDate=req.targetDate,
    )


def _summary(req: ReasoningRequest, docs: list[Document]) -> dict:

    base = _request(req, docs)

    assessment = analyze(base)

    plan = build_passport_plan(base, assessment)

    return {
        "assessment": assessment,
        "passportPlan": plan,
        "reviewFindings": sorted(
            f["id"] for f in assessment["findings"] if f["severity"] == "review"
        ),
        "blockers": plan["preparationBlockers"],
    }


def _family(req: ReasoningRequest) -> dict:

    docs = {d.id: d for d in req.documents}

    links = []

    for link in req.familyLinks:

        doc = docs[link.documentId]

        evidence = [docs[x] for x in link.relationshipEvidenceDocumentIds]

        links.append(
            {
                "documentId": doc.id,
                "relation": link.relation,
                "holder": doc.holder,
                "claimedByApplicant": link.claimedByApplicant,
                "relationshipEvidenceIds": [x.id for x in evidence],
                "reviewedRelationshipEvidenceIds": [
                    x.id for x in evidence if x.reviewed
                ],
                "requiresVerification": True,
                "officialRelationshipVerified": False,
                "warning": (
                    "Holder is self; check whether family link was entered correctly."
                    if doc.holder == "self"
                    else "Relationship and document acceptance require independent official verification."
                ),
            }
        )

    unlinked = [
        d.id
        for d in req.documents
        if d.holder != "self" and d.id not in {l.documentId for l in req.familyLinks}
    ]

    return {
        "links": links,
        "unlinkedFamilyDocumentIds": unlinked,
        "officialRelationshipVerified": False,
        "note": "A claimed family relationship is not independently verified by the Vault.",
    }


def _graph_diagnostics(tasks: list[dict]) -> dict:
    """Report missing references and real dependency cycles without claiming legal deadlock."""

    by_id = {task["id"]: task for task in tasks}

    missing = sorted(
        {dep for task in tasks for dep in task.get("dependsOn", []) if dep not in by_id}
    )

    state: dict[str, int] = {}

    stack: list[str] = []

    cycles: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:

        state[node] = 1

        stack.append(node)

        for dep in by_id[node].get("dependsOn", []):

            if dep not in by_id:

                continue

            if state.get(dep) == 1:

                path = stack[stack.index(dep) :] + [dep]

                core = path[:-1]

                rotations = [tuple(core[i:] + core[:i]) for i in range(len(core))]

                canonical = min(rotations)

                cycles.add(canonical + (canonical[0],))

            elif state.get(dep, 0) == 0:

                visit(dep)

        stack.pop()

        state[node] = 2

    for task_id in by_id:

        if state.get(task_id, 0) == 0:

            visit(task_id)

    return {
        "missingDependencyIds": missing,
        "cycles": [list(c) for c in sorted(cycles)],
        "cyclesDetected": bool(cycles),
    }


def _task_graph(assessment: dict) -> dict:

    tasks = assessment["tasks"]

    ids = {t["id"] for t in tasks}

    edges = [{"before": dep, "after": t["id"]} for t in tasks for dep in t["dependsOn"]]

    order = assessment["executionOrder"]

    positions = {key: i for i, key in enumerate(order)}

    diagnostics = _graph_diagnostics(tasks)

    invalid = [
        edge
        for edge in edges
        if edge["before"] not in ids
        or positions.get(edge["before"], 10**9) >= positions.get(edge["after"], -1)
    ]

    if invalid or len(order) != len(ids) or set(order) != ids:

        raise ValueError("Invalid dependency ordering")

    return {
        "nodes": [
            {"id": t["id"], "title": t["title"], "priority": t["priority"]}
            for t in tasks
        ],
        "edges": edges,
        "executionOrder": order,
        "cyclesDetected": diagnostics["cyclesDetected"],
        "diagnostics": diagnostics,
        "optimizationScope": "Deduplicated preparation tasks and dependency-safe ordering only; no legal or time-cost optimization.",
    }


def _minimum_review_path(assessment: dict) -> dict:
    """Exact minimal prerequisite closure for the critical review tasks.

    This minimizes *number of selected tasks* subject to the existing dependency graph,

    not government visits, cost, duration, or legally required corrections.

    """

    tasks = {t["id"]: t for t in assessment["tasks"]}

    seeds = [t["id"] for t in assessment["tasks"] if t["priority"] == 1]

    chosen: set[str] = set()

    def include(task_id: str) -> None:

        if task_id in chosen:

            return

        if task_id not in tasks:

            raise ValueError(f"Unknown prerequisite: {task_id}")

        chosen.add(task_id)

        for dependency in tasks[task_id]["dependsOn"]:

            include(dependency)

    for seed in seeds:

        include(seed)

    ordered = [task_id for task_id in assessment["executionOrder"] if task_id in chosen]

    return {
        "requiredReviewTaskIds": seeds,
        "selectedTaskIds": ordered,
        "selectedTaskCount": len(ordered),
        "totalTaskCount": len(tasks),
        "excludedOptionalTaskIds": [
            tid for tid in assessment["executionOrder"] if tid not in chosen
        ],
        "method": "Exact dependency closure for priority-1 preparation tasks",
        "optimizationScope": "Minimum number of prerequisite tasks for the specified critical review set; not minimum legal corrections, time, money or visits.",
        "officialAcceptanceVerified": False,
    }


def _deadlock_report(assessment: dict, graph: dict) -> dict:

    diag = graph["diagnostics"]

    issues = []

    for cycle in diag["cycles"]:

        issues.append(
            {
                "type": "dependency-cycle",
                "taskIds": cycle,
                "message": "Circular preparation-task prerequisites need human review.",
            }
        )

    for missing in diag["missingDependencyIds"]:

        issues.append(
            {
                "type": "missing-prerequisite",
                "taskIds": [missing],
                "message": "A referenced prerequisite task is missing.",
            }
        )

    return {
        "structuralDeadlockDetected": bool(issues),
        "issues": issues,
        "bureaucraticDeadlockVerified": False,
        "note": "This checks software task dependencies only. Government process deadlocks require verified authority-specific rules.",
    }


def _proof_candidates(req: ReasoningRequest) -> list[dict]:
    """Source-linked, rule-filtered proof candidates; never approve acceptance."""
    rules = {rule["id"]: rule for rule in pack()["rules"]}
    reviewed_self = [d for d in req.documents if d.reviewed and d.holder == "self"]
    dob_values = {
        canonical_dob(d.dateOfBirth) for d in reviewed_self if d.dateOfBirth.strip()
    }
    # Invalid or conflicting dates cannot safely select a birth-cutoff rule.
    reliable_dob = (
        next(iter(dob_values))
        if len(dob_values) == 1 and None not in dob_values
        else None
    )
    applicable = {
        "address": (
            rules["address"] if req.assistanceType in ("fresh", "documents") else None
        ),
        "birth": None,
        "identity": None,
    }
    if req.assistanceType == "fresh" and reliable_dob:
        applicable["birth"] = (
            rules["dob-new"]
            if date.fromisoformat(reliable_dob) >= date(2023, 10, 1)
            else rules["dob-old"]
        )

    def proof_key(kind: str, category: str) -> str:
        """Merge known display aliases, not distinct official proof types."""
        key = normalize(kind)
        if category == "address" and key in {
            normalize("Rental agreement"),
            normalize("Rent Agreement"),
        }:
            return "rent-agreement"
        return key

    candidates = []
    for category in ("identity", "address", "birth"):
        rule = applicable[category]
        options = []
        if rule:
            seen = set()
            for kind in rule["types"]:
                key = proof_key(kind, category)
                if key in seen:
                    continue
                seen.add(key)
                vault = [
                    d.id
                    for d in reviewed_self
                    if proof_key(d.documentType, category) == key
                ]
                options.append(
                    {
                        "documentType": (
                            "Rent Agreement"
                            if category == "address"
                            and normalize(kind)
                            in {
                                normalize("Rental agreement"),
                                normalize("Rent Agreement"),
                            }
                            else kind
                        ),
                        "matchingReviewedDocumentIds": vault,
                        "availability": (
                            "in-vault-for-review"
                            if vault
                            else "not-found-in-reviewed-vault"
                        ),
                        "officialAcceptanceVerified": False,
                    }
                )
            allowed_keys = seen
            matched = [
                d.id
                for d in reviewed_self
                if category in d.categories
                and proof_key(d.documentType, category) in allowed_keys
            ]
            status = "source-linked-options-for-review"
        else:
            matched = [d.id for d in reviewed_self if category in d.categories]
            status = (
                "dob-verification-required"
                if category == "birth" and req.assistanceType == "fresh"
                else "scenario-specific-rule-required"
            )
        candidates.append(
            {
                "category": category,
                "candidateDocumentIds": matched,
                "hasMultipleCandidates": len(matched) > 1,
                "substitutionApproved": False,
                "status": status,
                "ruleId": rule["id"] if rule else None,
                "sourceId": rule["source_id"] if rule else None,
                "sourceUrl": rule["source_url"] if rule else None,
                "alternatives": options,
                "note": "Listed proof types are candidates for official review, not interchangeable or approved proofs.",
            }
        )
    return candidates


def _deadline(req: ReasoningRequest, assessment: dict) -> dict:
    """Plan around declared expiry dates; never infer official acceptance or timelines."""
    today = date.today()
    target = None
    target_error = False
    if req.targetDate:
        try:
            target = date.fromisoformat(req.targetDate)
        except (ValueError, TypeError):
            target_error = True

    conflicts = []
    for doc in req.documents:
        raw = doc.expiryDate.strip()
        if not raw:
            continue  # Missing expiry is unknown, not proof of expiry.
        try:
            # Reject non-ISO representations rather than guessing day/month order.
            if len(raw) != 10 or raw[4] != '-' or raw[7] != '-':
                raise ValueError('Not ISO')
            expiry = date.fromisoformat(raw)
        except ValueError:
            conflicts.append({
                'documentId': doc.id, 'documentType': doc.documentType,
                'expiryDate': raw, 'type': 'invalid-expiry-date',
                'severity': 'review', 'daysUntilExpiry': None,
                'action': 'Check the printed expiry date and enter YYYY-MM-DD.',
                'officialAcceptanceVerified': False,
            })
            continue
        if expiry < today:
            kind, action = ('already-expired',
                'Check official document validity requirements and obtain updated evidence if necessary.')
        elif target and expiry < target:
            kind, action = ('expires-before-target',
                'Review renewal or alternative proof options before the planned target date.')
        elif target and expiry == target:
            kind, action = ('expires-on-target',
                'Verify whether the document remains acceptable on the planned target date.')
        elif (expiry - today).days <= 30:
            kind, action = ('expiring-soon',
                'Check validity requirements and prepare renewal or alternate evidence if necessary.')
        else:
            continue
        conflicts.append({
            'documentId': doc.id, 'documentType': doc.documentType,
            'expiryDate': expiry.isoformat(), 'type': kind,
            'severity': 'review', 'daysUntilExpiry': (expiry - today).days,
            'action': action, 'officialAcceptanceVerified': False,
        })

    # Link proposed corrective work to real preparation tasks; never invent durations.
    existing_task_ids = [t['id'] for t in assessment.get('tasks', [])]
    resolution_options = []
    for conflict in conflicts:
        resolution_options.append({
            'documentId': conflict['documentId'],
            'conflictType': conflict['type'],
            'action': conflict['action'],
            'prerequisiteTaskIds': existing_task_ids,
            'estimatedCompletionDays': None,
            'officialFeasibilityVerified': False,
        })

    actions = []
    if target_error:
        urgency, days_remaining = 'invalid-date', None
        actions.append('Enter a valid ISO target date (YYYY-MM-DD).')
    elif target is None:
        urgency, days_remaining = 'not-assessed', None
        actions.append('Confirm the actual deadline and processing requirements with the relevant authority.')
    else:
        days_remaining = (target - today).days
        urgency = ('past-target' if days_remaining < 0 else
                   'urgent' if days_remaining <= 7 else
                   'upcoming' if days_remaining <= 30 else 'planning')
        actions.append('Verify the actual deadline, appointment availability and required evidence on the official portal.')
        if assessment.get('minimumReviewSet'):
            actions.append('Review priority-1 preparation tasks before relying on any application plan.')
        if days_remaining <= 7:
            actions.append('Check official expedited or rescheduling options if applicable; none is assumed available.')
    if conflicts:
        actions.append('Review document expiry conflicts and verify acceptable proof or renewal routes with the authority.')

    return {
        'targetDate': req.targetDate if target_error else target.isoformat() if target else None,
        'daysRemaining': days_remaining,
        'urgency': urgency,
        'officialDeadlineVerified': False,
        'actions': actions,
        'note': 'User-entered planning target only; expiry warnings do not establish official document rejection or processing times.',
        'documentExpiryConflicts': conflicts,
        'expiryConflictDetected': bool(conflicts),
        'resolutionOptions': resolution_options,
        'officialDocumentValidityVerified': False,
    }

def _identity_evolution(req: ReasoningRequest) -> dict:
    """Observe name variations without inferring a legal name change."""

    names = {}

    for doc in req.documents:

        if not doc.reviewed or doc.holder != "self":

            continue

        name = " ".join(doc.printedName.split())

        if name:

            key = name.casefold()

            names.setdefault(
                key,
                {
                    "name": name,
                    "documentIds": [],
                },
            )

            names[key]["documentIds"].append(doc.id)

    variants = list(names.values())

    return {
        "variationDetected": len(variants) > 1,
        "observedNameVariants": variants,
        "legalNameChangeVerified": False,
        "requiresOfficialReview": len(variants) > 1,
        "note": (
            "Different printed names were observed. "
            "This does not establish a legal name change or identity mismatch."
        ),
    }


def _address_continuity(req: ReasoningRequest) -> dict:
    """Detect address variations without assuming migration history."""

    addresses = {}

    for doc in req.documents:

        if not doc.reviewed or doc.holder != "self":

            continue

        address = " ".join(doc.residentialAddress.split())

        if address:

            key = address.casefold()

            addresses.setdefault(
                key,
                {
                    "address": address,
                    "documentIds": [],
                },
            )

            addresses[key]["documentIds"].append(doc.id)

    observed = list(addresses.values())

    return {
        "differentAddressesDetected": len(observed) > 1,
        "observedAddresses": observed,
        "currentAddressVerified": False,
        "migrationHistoryVerified": False,
        "requiresReview": len(observed) > 1,
        "note": (
            "Different document addresses do not establish "
            "which address is current or whether the applicant migrated."
        ),
    }


def _visit_preparation(req: ReasoningRequest) -> dict:
    """Provide preparation guidance without claiming visits are eliminated."""

    reviewed = [doc for doc in req.documents if doc.reviewed and doc.holder == "self"]

    actions = [
        "Verify current requirements and appointment instructions "
        "through the official Passport Seva portal.",
        "Confirm which documents require original verification "
        "or physical attendance.",
    ]

    if not reviewed:

        actions.append("Review and organize supporting documents before applying.")

    else:

        actions.append(
            "Compare reviewed document details and resolve discrepancies "
            "before the appointment."
        )

    return {
        "governmentVisitEliminated": False,
        "digitalSubmissionVerified": False,
        "reviewedDocumentCount": len(reviewed),
        "actions": actions,
        "note": (
            "Digital preparation may reduce avoidable follow-ups, "
            "but no government visit elimination is verified."
        ),
    }


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

                updates["reviewed"] = True

            docs.append(original.model_copy(update=updates))

        outcome = _summary(req, docs)

        before = set(baseline["reviewFindings"])

        after = set(outcome["reviewFindings"])

        results.append(
            {
                "id": sim.id,
                "label": sim.label,
                "before": {
                    "reviewFindings": sorted(before),
                    "blockers": baseline["blockers"],
                },
                "after": {
                    "reviewFindings": sorted(after),
                    "blockers": outcome["blockers"],
                },
                "resolvedFindingIds": sorted(before - after),
                "newFindingIds": sorted(after - before),
                "remainingTaskIds": outcome["assessment"]["executionOrder"],
                "officialAcceptanceVerified": False,
                "caution": "Simulation changes metadata only; it does not correct official records.",
            }
        )

    graph = _task_graph(baseline["assessment"])

    return {
        "identityEvolution": _identity_evolution(req),
        "addressContinuity": _address_continuity(req),
        "visitPreparation": _visit_preparation(req),
        "mode": "local-deterministic",
        "baseline": baseline,
        "dependencyGraph": graph,
        "familyEvidence": _family(req),
        "simulations": results,
        "minimumCorrectionPath": _minimum_review_path(baseline["assessment"]),
        "deadlockAnalysis": _deadlock_report(baseline["assessment"], graph),
        "proofSubstitution": {
            "candidates": _proof_candidates(req),
            "officialSubstitutionApproved": False,
        },
        "deadlineRescue": _deadline(req, baseline["assessment"]),
        "officialEligibilityDetermined": False,
        "disclaimer": "Scenario planning only. Verify real evidence and current Passport Seva rules independently.",
    }
