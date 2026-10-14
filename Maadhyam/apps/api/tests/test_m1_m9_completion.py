from maadhyam_api.routes.reasoning_engine import ReasoningRequest, reason

def _request():
    return ReasoningRequest.model_validate({
        "documents": [
            {"id": "a", "documentType": "Aadhaar", "holder": "self", "reviewed": True,
             "categories": ["identity", "address"], "printedName": "Asha Rao",
             "residentialAddress": "Pune"},
            {"id": "b", "documentType": "School record", "holder": "self", "reviewed": True,
             "categories": ["birth"], "printedName": "Asha R Rao",
             "residentialAddress": "Mumbai"},
        ]
    })

def test_identity_variants_are_not_officially_verified():
    result = reason(_request())
    assert result["identityEvolution"]["variationDetected"] is True
    assert len(result["identityEvolution"]["observedNameVariants"]) == 2
    assert result["identityEvolution"]["legalNameChangeVerified"] is False

def test_address_continuity_is_not_inferred_from_two_addresses():
    result = reason(_request())
    assert result["addressContinuity"]["differentAddressesDetected"] is True
    assert result["addressContinuity"]["currentAddressVerified"] is False

def test_visit_guidance_never_claims_government_visit_eliminated():
    result = reason(_request())
    assert result["visitPreparation"]["governmentVisitEliminated"] is False
    assert result["visitPreparation"]["digitalSubmissionVerified"] is False
    assert result["visitPreparation"]["actions"]
