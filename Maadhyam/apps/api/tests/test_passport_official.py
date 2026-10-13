from maadhyam_api.routes.passport_rules import assess_passport, PassportAssessmentRequest

def test_birth_cutoff_birth_certificate_only():
    r=assess_passport(PassportAssessmentRequest(applicantDateOfBirth='2023-10-01',documents=[{'id':'pan','categories':['birth'],'documentType':'PAN card','reviewed':True}]))
    check=next(x for x in r.checks if x.id=='dob-new')
    assert check.status!='available-for-review'
    assert check.alternatives==['Birth certificate']

def test_before_cutoff_pan_possible():
    r=assess_passport(PassportAssessmentRequest(applicantDateOfBirth='2000-01-01',documents=[{'id':'pan','categories':['birth'],'documentType':'PAN card','reviewed':True}]))
    assert next(x for x in r.checks if x.id=='dob-old').status=='available-for-review'

def test_unknown_birth_date_fails_closed():
    r=assess_passport(PassportAssessmentRequest())
    assert any(x.id=='dob-cutoff' for x in r.checks)

def test_reissue_old_passport():
    r=assess_passport(PassportAssessmentRequest(assistanceType='reissue',documents=[{'id':'p','documentType':'Passport','reviewed':True}]))
    assert any(x.id=='old-passport' for x in r.checks)

def test_tatkaal_no_unverified_auto_approval():
    r=assess_passport(PassportAssessmentRequest(tatkaal=True))
    assert any(x.id=='tatkaal' and x.status=='needs-confirmation' for x in r.checks)
