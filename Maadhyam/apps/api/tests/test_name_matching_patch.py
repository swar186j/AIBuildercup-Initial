from maadhyam_api.routes.intelligence import Document, Request, analyze, classify_name_variation


def test_initial_expansion():
    assert classify_name_variation('Rahul K Sharma', 'Rahul Kumar Sharma') == 'possible-initial-expansion'


def test_order_variation():
    assert classify_name_variation('Sharma Rahul Kumar', 'Rahul Kumar Sharma') == 'possible-name-order-variation'


def test_unrelated_names_not_accepted():
    assert classify_name_variation('Rahul Kumar Sharma', 'Rohan Kumar Sharma') == 'unresolved-difference'


def test_conflict_still_blocks_submission():
    req = Request(documents=[Document(id='a', reviewed=True, printedName='Rahul Kumar Sharma'), Document(id='b', reviewed=True, printedName='Rahul K Sharma')])
    result = analyze(req)
    finding = next(f for f in result['findings'] if f['id'] == 'printedName-conflict')
    assert finding['nameComparisons'][0]['classification'] == 'possible-initial-expansion'
    assert result['readyForOfficialSubmission'] is False
    assert 'resolve-printedName' in result['minimumReviewSet']
