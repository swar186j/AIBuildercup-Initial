from maadhyam_api.routes.reasoning_engine import ReasoningRequest, reason


def candidate(documents, category='birth', **kwargs):
    result = reason(ReasoningRequest(documents=documents, **kwargs))
    return next(x for x in result['proofSubstitution']['candidates'] if x['category'] == category)


def doc(id, kind, dob='', categories=None, reviewed=True, holder='self'):
    return {'id': id, 'documentType': kind, 'dateOfBirth': dob, 'categories': categories or ['birth'], 'reviewed': reviewed, 'holder': holder}


def test_pre_cutoff_dob_has_conditional_options():
    x = candidate([doc('pan', 'PAN card', '1998-05-14')])
    assert x['ruleId'] == 'dob-old'
    assert any(o['documentType'] == 'PAN card' and o['matchingReviewedDocumentIds'] == ['pan'] for o in x['alternatives'])
    assert not x['substitutionApproved']


def test_post_cutoff_birth_certificate_only():
    x = candidate([doc('b', 'Birth certificate', '2023-10-01')])
    assert x['ruleId'] == 'dob-new'
    assert [o['documentType'] for o in x['alternatives']] == ['Birth certificate']


def test_conflicting_dob_does_not_pick_rule():
    x = candidate([doc('a', 'PAN card', '1998-05-14'), doc('b', 'Voter ID', '1998-05-15')])
    assert x['ruleId'] is None and x['alternatives'] == []


def test_unknown_dob_does_not_pick_rule():
    x = candidate([doc('a', 'PAN card')])
    assert x['status'] == 'dob-verification-required'


def test_unreviewed_and_family_docs_are_not_matches():
    x = candidate([doc('a', 'PAN card', '1998-05-14'), doc('b', 'PAN card', '1998-05-14', reviewed=False), doc('c', 'PAN card', '1998-05-14', holder='spouse')])
    assert next(o for o in x['alternatives'] if o['documentType'] == 'PAN card')['matchingReviewedDocumentIds'] == ['a']


def test_address_options_are_source_linked_and_deduplicated():
    x = candidate([doc('a', 'Aadhaar card', categories=['address'])], category='address')
    assert x['ruleId'] == 'address' and x['sourceUrl'].startswith('https://')
    assert len([o for o in x['alternatives'] if o['documentType'].casefold() == 'rent agreement']) == 1


def test_reissue_does_not_assume_fresh_address_requirement():
    x = candidate([doc('a', 'Aadhaar card', categories=['address'])], category='address', assistanceType='reissue')
    assert x['ruleId'] is None
