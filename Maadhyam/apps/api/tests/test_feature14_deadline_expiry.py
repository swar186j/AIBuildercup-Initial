from datetime import date, timedelta
from maadhyam_api.routes.reasoning_engine import ReasoningRequest, reason


def check(expiry='', target=None, reviewed=True):
    return reason(ReasoningRequest.model_validate({
        'targetDate': target,
        'documents': [{
            'id': 'proof-1', 'documentType': 'Passport', 'holder': 'self',
            'reviewed': reviewed, 'categories': ['identity'], 'expiryDate': expiry,
        }],
    }))['deadlineRescue']


def test_expired_document_is_review_only():
    x = check((date.today() - timedelta(days=1)).isoformat())
    assert x['expiryConflictDetected']
    assert x['documentExpiryConflicts'][0]['type'] == 'already-expired'
    assert x['officialDocumentValidityVerified'] is False
    assert x['resolutionOptions'][0]['estimatedCompletionDays'] is None


def test_expiry_before_target():
    expiry = (date.today() + timedelta(days=40)).isoformat()
    target = (date.today() + timedelta(days=50)).isoformat()
    x = check(expiry, target)
    assert x['documentExpiryConflicts'][0]['type'] == 'expires-before-target'
    assert x['resolutionOptions'][0]['prerequisiteTaskIds']


def test_expiry_on_target():
    expiry = (date.today() + timedelta(days=40)).isoformat()
    assert check(expiry, expiry)['documentExpiryConflicts'][0]['type'] == 'expires-on-target'


def test_invalid_expiry_and_invalid_target_do_not_crash():
    x = check('31/12/2026', 'not-a-date')
    assert x['urgency'] == 'invalid-date'
    assert x['documentExpiryConflicts'][0]['type'] == 'invalid-expiry-date'


def test_missing_expiry_is_not_assumed_expired():
    x = check('')
    assert x['documentExpiryConflicts'] == []
    assert x['expiryConflictDetected'] is False
    assert x['urgency'] == 'not-assessed'


def test_expiring_soon_without_target():
    x = check((date.today() + timedelta(days=10)).isoformat())
    assert x['documentExpiryConflicts'][0]['type'] == 'expiring-soon'


def test_far_future_expiry_no_conflict():
    x = check((date.today() + timedelta(days=200)).isoformat())
    assert x['documentExpiryConflicts'] == []
