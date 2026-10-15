
"""Read-only comparison of passport rule-pack proposals; never verifies legal changes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .passport_rules import pack, normalize


router = APIRouter(
    prefix="/passport/rules",
    tags=["Passport Preparation"],
)


class ImpactDocument(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    documentType: str = Field(default="", max_length=120)
    reviewed: bool = False


class CompareRequest(BaseModel):
    baselineVersion: str | None = None
    proposedPack: dict[str, Any]
    documents: list[ImpactDocument] = Field(default_factory=list, max_length=60)


def _indexed(rules: Any) -> dict[str, dict]:
    if not isinstance(rules, list) or len(rules) > 100:
        raise ValueError("rules must be a list of at most 100 items")

    result = {}

    for rule in rules:
        if (
            not isinstance(rule, dict)
            or not isinstance(rule.get("id"), str)
            or not rule["id"].strip()
            or rule["id"] in result
        ):
            raise ValueError("rule IDs must be unique nonblank strings")

        if not isinstance(rule.get("types"), list) or not all(
            isinstance(t, str) for t in rule["types"]
        ):
            raise ValueError("rule types must be a list of strings")

        result[rule["id"]] = rule

    return result


def compare_packs(
    old: dict,
    proposed: dict,
    documents: list[ImpactDocument] | None = None,
) -> dict:
    """Compare rule packs without modifying or approving either version."""

    if (
        not isinstance(proposed, dict)
        or not isinstance(proposed.get("version"), str)
        or not proposed["version"].strip()
    ):
        raise ValueError("proposedPack requires a nonblank version")

    before = _indexed(old.get("rules"))
    after = _indexed(proposed.get("rules"))

    docs = documents or []
    changes = []

    for rule_id in sorted(before.keys() | after.keys()):
        previous = before.get(rule_id)
        current = after.get(rule_id)

        if previous == current:
            continue

        change_type = (
            "added"
            if previous is None
            else "removed"
            if current is None
            else "modified"
        )

        old_types = (
            {normalize(t): t for t in previous.get("types", [])}
            if previous
            else {}
        )

        new_types = (
            {normalize(t): t for t in current.get("types", [])}
            if current
            else {}
        )

        removed_keys = old_types.keys() - new_types.keys()
        added_keys = new_types.keys() - old_types.keys()
        retained_keys = old_types.keys() & new_types.keys()

        removed_proof_types = [
            old_types[key] for key in sorted(removed_keys)
        ]

        added_proof_types = [
            new_types[key] for key in sorted(added_keys)
        ]

        directly_impacted = []
        review_recommended = []

        for document in docs:
            document_type = normalize(document.documentType)

            if not document_type:
                continue

            if document_type in removed_keys:
                directly_impacted.append(document.id)

            elif document_type in retained_keys:
                review_recommended.append(document.id)

            elif document_type in added_keys:
                # Newly listed proof types are candidates for review,
                # not automatically accepted evidence.
                review_recommended.append(document.id)

        # Preserve the original affectedDocumentIds behavior:
        # all documents matching either old or proposed proof types.
        relevant_types = set(old_types) | set(new_types)

        affected_document_ids = list(
            dict.fromkeys(
                document.id
                for document in docs
                if normalize(document.documentType) in relevant_types
            )
        )

        changes.append(
            {
                "ruleId": rule_id,
                "changeType": change_type,
                "addedProofTypes": added_proof_types,
                "removedProofTypes": removed_proof_types,
                "affectedDocumentIds": affected_document_ids,
                "directlyImpactedDocumentIds": list(
                    dict.fromkeys(directly_impacted)
                ),
                "reviewRecommendedDocumentIds": list(
                    dict.fromkeys(review_recommended)
                ),
                "sourceUrl": (current or previous).get("source_url"),
                "action": (
                    "Recheck this rule and any matching documents against "
                    "current official guidance before relying on the "
                    "proposed change."
                ),
                "officialChangeVerified": False,
            }
        )

    return {
        "baselineVersion": old.get("version"),
        "proposedVersion": proposed["version"],
        "changesDetected": bool(changes),
        "changes": changes,
        "affectedDocumentIds": list(
            dict.fromkeys(
                document_id
                for change in changes
                for document_id in change["affectedDocumentIds"]
            )
        ),
        "directlyImpactedDocumentIds": list(
            dict.fromkeys(
                document_id
                for change in changes
                for document_id in change["directlyImpactedDocumentIds"]
            )
        ),
        "reviewRecommendedDocumentIds": list(
            dict.fromkeys(
                document_id
                for change in changes
                for document_id in change["reviewRecommendedDocumentIds"]
            )
        ),
        "officialChangeVerified": False,
        "currentRulePackModified": False,
        "note": (
            "Hypothetical read-only comparison. "
            "Direct impact means a proof type was removed from a proposed "
            "rule, not that a government authority has rejected the document. "
            "No official change, legal eligibility, or document acceptance "
            "is established."
        ),
    }


@router.get('/versions')
def available_versions():
    current = pack()
    return {'versions': [{'version': current['version'], 'kind': 'stored-reference', 'pack': current}],
            'officialChangeVerified': False,
            'note': 'Only locally stored complete rule packs are available. Source content hashes are not historical rule packs. No live update is implied.'}


@router.post("/compare")
def compare_rules(request: CompareRequest):
    try:
        if request.baselineVersion is not None and request.baselineVersion != pack()['version']:
            raise ValueError('Requested comparison baseline is unavailable; refresh available versions')
        return compare_packs(
            pack(),
            request.proposedPack,
            request.documents,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
