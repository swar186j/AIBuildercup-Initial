from maadhyam_api.routes.intelligence import Document, Request, analyze


def test_official_guidance_attached_without_acceptance_claims():
    docs = [
        Document(id='a', reviewed=True, printedName='Rahul Kumar Sharma', dateOfBirth='1998-05-14', residentialAddress='Pune'),
        Document(id='b', reviewed=True, printedName='Rahul K Sharma', dateOfBirth='1998-05-15', residentialAddress='Mumbai'),
    ]
    result = analyze(Request(documents=docs))
    for field in ('printedName', 'dateOfBirth', 'residentialAddress'):
        finding = next(f for f in result['findings'] if f['field'] == field and f['type'] == 'conflict')
        refs = finding['officialGuidance']
        assert len(refs) == 1
        assert refs[0]['url'].startswith('https://')
        assert refs[0]['applicabilityVerified'] is False
        assert refs[0]['violationDetermined'] is False
    assert result['readyForOfficialSubmission'] is False
    assert len(result['minimumReviewSet']) == 3


def test_no_invented_citation_for_extraction_quality():
    doc = Document(id='ocr', reviewed=True, extractionSource='ocr', extractionConfidence=0.3)
    result = analyze(Request(documents=[doc]))
    quality = next(f for f in result['findings'] if f['id'] == 'extraction-low-confidence')
    assert 'officialGuidance' not in quality


def test_existing_name_comparisons_preserved():
    docs = [Document(id='a', reviewed=True, printedName='Rahul Kumar Sharma'),
            Document(id='b', reviewed=True, printedName='Rahul K Sharma')]
    result = analyze(Request(documents=docs))
    finding = next(f for f in result['findings'] if f['id'] == 'printedName-conflict')
    assert finding['nameComparisons'][0]['classification'] == 'possible-initial-expansion'
