
from maadhyam_api.routes.rule_change_impact import (
    ImpactDocument,
    compare_packs,
)


def rule(rule_id, types, action="Review evidence"):
    return {
        "id": rule_id,
        "title": rule_id,
        "types": types,
        "action": action,
        "source_url": "https://example.org/rules",
    }


def test_removed_proof_is_directly_impacted():
    old = {
        "version": "v1",
        "rules": [rule("address", ["Aadhaar card", "Rent Agreement"])],
    }
    new = {
        "version": "v2",
        "rules": [rule("address", ["Aadhaar card"])],
    }
    docs = [
        ImpactDocument(id="aadhaar_01", documentType="Aadhaar card"),
        ImpactDocument(id="rent_01", documentType="Rent Agreement"),
    ]

    result = compare_packs(old, new, docs)

    assert result["directlyImpactedDocumentIds"] == ["rent_01"]
    assert result["reviewRecommendedDocumentIds"] == ["aadhaar_01"]
    assert result["affectedDocumentIds"] == ["aadhaar_01", "rent_01"]


def test_removed_rule_impacts_matching_document():
    old = {
        "version": "v1",
        "rules": [rule("dob-old", ["PAN card"])],
    }
    new = {"version": "v2", "rules": []}

    result = compare_packs(
        old,
        new,
        [ImpactDocument(id="pan_01", documentType="PAN card")],
    )

    assert result["directlyImpactedDocumentIds"] == ["pan_01"]
    assert result["reviewRecommendedDocumentIds"] == []


def test_added_proof_requires_review_not_direct_impact():
    old = {
        "version": "v1",
        "rules": [rule("address", ["Aadhaar card"])],
    }
    new = {
        "version": "v2",
        "rules": [rule("address", ["Aadhaar card", "Electricity bill"])],
    }

    result = compare_packs(
        old,
        new,
        [ImpactDocument(id="bill_01", documentType="Electricity bill")],
    )

    assert result["directlyImpactedDocumentIds"] == []
    assert result["reviewRecommendedDocumentIds"] == ["bill_01"]


def test_metadata_only_change_requires_review():
    old = {
        "version": "v1",
        "rules": [rule("address", ["Aadhaar card"], "Old instructions")],
    }
    new = {
        "version": "v2",
        "rules": [rule("address", ["Aadhaar card"], "Updated instructions")],
    }

    result = compare_packs(
        old,
        new,
        [ImpactDocument(id="aadhaar_01", documentType="Aadhaar card")],
    )

    assert result["directlyImpactedDocumentIds"] == []
    assert result["reviewRecommendedDocumentIds"] == ["aadhaar_01"]


def test_unchanged_rules_have_no_impact():
    old = {
        "version": "v1",
        "rules": [rule("address", ["Aadhaar card"])],
    }
    new = {
        "version": "v2",
        "rules": [rule("address", ["Aadhaar card"])],
    }

    result = compare_packs(
        old,
        new,
        [ImpactDocument(id="aadhaar_01", documentType="Aadhaar card")],
    )

    assert result["changesDetected"] is False
    assert result["directlyImpactedDocumentIds"] == []
    assert result["reviewRecommendedDocumentIds"] == []


def test_hypothetical_changes_never_claim_official_verification():
    old = {
        "version": "v1",
        "rules": [rule("address", ["Rent Agreement"])],
    }
    new = {"version": "v2", "rules": []}

    result = compare_packs(old, new)

    assert result["officialChangeVerified"] is False
    assert result["currentRulePackModified"] is False
    assert all(
        change["officialChangeVerified"] is False
        for change in result["changes"]
    )
