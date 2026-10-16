"""Mocked-cloud browser regressions for React synchronization; no cloud writes or AI calls."""
import base64
import json
import time
from playwright.sync_api import expect
from qa.test_completion import add_member


def answers():
    return {"assistanceType": "fresh", "applicantAgeGroup": "adult", "currentAddressMatches": "",
            "hasIdentityDocument": "", "hasAddressDocument": "", "hasDateOfBirthDocument": "",
            "nameConsistent": "", "policeVerificationStatus": ""}


def cloud_record(record_id="LOCAL-remediation-12345678", name="Fictional Cloud Applicant"):
    return {"id": record_id, "service_type": "passport", "application_type": "fresh", "status": "in-progress",
            "revision": 4, "applicant_details": {"name": name, "date_of_birth": "1998-06-15"},
            "questionnaire_answers": answers(), "current_step": 1, "selected_document_ids": [],
            "rule_pack_version": "unverified", "created_at": "2026-10-16T10:00:00Z", "updated_at": "2026-10-16T10:00:00Z",
            "household_state": {"members": [{"id": "applicant", "label": "Applicant (this workspace)", "relationship": "self",
                                            "dependsOnMemberIds": [], "dependsOnDocumentIds": [], "relationshipEvidenceDocumentIds": []}]},
            "planner_state": {"manual_task_ids": [], "target_date": "2027-12-31", "generated_plan": {}},
            "assessment_history": []}


def mocked_auth(page):
    """Client-only fictional token; API routes below are mocked and do not verify it."""
    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()
    now = int(time.time())
    token = encode({"alg": "none"}) + "." + encode({
        "sub": "fictional-remediation-uid", "user_id": "fictional-remediation-uid", "iat": now, "exp": now + 3600,
        "auth_time": now, "aud": "maadhyam-1610", "iss": "https://securetoken.google.com/maadhyam-1610",
        "firebase": {"sign_in_provider": "anonymous", "identities": {}},
    }) + ".fictional"
    def auth(route):
        data = {"idToken": token, "refreshToken": "fictional-refresh", "localId": "fictional-remediation-uid", "expiresIn": "3600"}
        if "accounts:lookup" in route.request.url:
            data = {"users": [{"localId": "fictional-remediation-uid", "providerUserInfo": []}]}
        route.fulfill(json=data, headers={"Access-Control-Allow-Origin": "*"})
    page.route("**/identitytoolkit.googleapis.com/**", auth)
    page.add_init_script("localStorage.setItem('maadhyam-cloud-preparations-consent-v1','yes')")


def hold_cloud(page):
    held, writes = [], []
    def handle(route):
        if route.request.method == "GET":
            held.append(route)
            page.evaluate("window.__cloudRequestHeld=true")
        else:
            writes.append(route.request.post_data_json)
            route.fulfill(status=409, json={"error": {"message": "Unexpected mocked cloud write"}})
    page.route("**/api/applications**", handle)
    return held, writes


def wait_for_held(page, held):
    # Let Playwright dispatch network callbacks while waiting for a visible test marker.
    page.wait_for_function("window.__cloudRequestHeld === true")
    assert held


def test_cloud_hydration_replaces_stale_browser_name_without_writing_blanks(page):
    mocked_auth(page)
    held, writes = hold_cloud(page)
    record = cloud_record()
    stale = {"id": record["id"], "journey": {"schemaVersion": 1, "service": "passport", "assistanceType": "fresh",
             "answers": answers(), "stepIndex": 0, "applicantDob": "", "applicantName": "Fictional Stale Name", "documentIds": []}}
    page.add_init_script("localStorage.setItem('maadhyam-preparations-save-consent','yes');localStorage.setItem('maadhyam-preparations-v1'," +
                         json.dumps(json.dumps({"schemaVersion": 1, "records": [stale]})) + ")")
    page.goto("/services/passport/journey?preparation=" + record["id"])
    expect(page.get_by_label("Applicant name", exact=True)).to_have_value("Fictional Stale Name")
    wait_for_held(page, held)
    held.pop(0).fulfill(json=[record])
    expect(page.get_by_label("Applicant name", exact=True)).to_have_value("Fictional Cloud Applicant")
    expect(page.get_by_label("Applicant date of birth (for document guidance)")).to_have_value("1998-06-15")
    expect(page.get_by_role("radio", name="An adult", exact=True)).to_be_checked()
    assert not writes, "Restoration must not write without workspace cloud-save consent"


def test_delayed_cloud_restore_preserves_local_household_edit(page):
    mocked_auth(page)
    held, writes = hold_cloud(page)
    page.goto("/household")
    wait_for_held(page, held)
    add_member(page, "Fictional Local Parent")
    held.pop(0).fulfill(json=[cloud_record()])
    expect(page.get_by_text("Cloud preparations restored (1).", exact=False)).to_have_count(0)
    # Cloud-list settlement is observed through the provider's saving controls.
    page.locator('a[href="/applications"]').first.click()
    expect(page.get_by_text("Cloud preparations restored (1).", exact=False)).to_be_visible()
    page.locator('a[href="/household"]').first.click()
    expect(page.get_by_label("Household member Fictional Local Parent", exact=True)).to_be_visible()
    assert not writes


def test_delayed_cloud_restore_preserves_entered_passport_name(page):
    mocked_auth(page)
    held, writes = hold_cloud(page)
    page.goto("/applications")
    wait_for_held(page, held)
    page.get_by_role("button", name="Start new preparation", exact=True).click()
    page.get_by_role("link", name="Continue passport journey", exact=True).click()
    record_id = page.url.split("preparation=")[1]
    page.get_by_label("Applicant name", exact=True).fill("Fictional Local Edit")
    held.pop(0).fulfill(json=[cloud_record(record_id, "Fictional Incoming Old Name")])
    expect(page.get_by_label("Applicant name", exact=True)).to_have_value("Fictional Local Edit")
    page.locator('a[href="/applications"]').first.click()
    expect(page.get_by_text("Cloud preparations restored (1).", exact=False)).to_be_visible()
    page.locator("article").filter(has_text=record_id).get_by_role("button", name="Continue preparation", exact=True).click()
    page.get_by_role("link", name="Continue passport journey", exact=True).click()
    expect(page.get_by_label("Applicant name", exact=True)).to_have_value("Fictional Local Edit")
    assert not writes


def test_planner_does_not_refetch_assessment_on_context_updates(page):
    assessment_requests = []
    page.on("request", lambda request: assessment_requests.append(request.url)
            if request.url.endswith("/api/intelligence/passport-plan") else None)
    page.goto("/planner")
    expect(page.get_by_label("Your deadline and action plan")).to_be_visible()
    with page.expect_response(lambda response: response.url.endswith("/api/intelligence/reasoning")
                              and response.request.post_data_json.get("targetDate") == "2027-12-31"):
        page.locator("#planning-date").fill("2027-12-31")
    expect(page.get_by_text("Urgency:", exact=False).first).to_be_visible()
    assert len(assessment_requests) == 1, "Recording a plan snapshot must not trigger an assessment loop"


def test_failed_preparation_storage_retry_does_not_claim_saving_is_enabled(page):
    from qa.test_completion import new_preparation
    new_preparation(page)
    page.locator('a[href="/applications"]').first.click()
    controls = page.get_by_label("Preparation storage controls")
    controls.get_by_role("checkbox").check()
    controls.get_by_role("button", name="Enable preparation saving", exact=True).click()
    expect(controls.get_by_role("button", name="Disable preparation saving and delete local copies", exact=True)).to_be_visible()
    page.evaluate("() => { Storage.prototype.setItem=()=>{throw new DOMException('Full','QuotaExceededError')}; }")
    page.locator("article").filter(has_text="LOCAL-").get_by_role("button", name="Continue preparation", exact=True).click()
    page.get_by_role("link", name="Continue passport journey", exact=True).click()
    page.get_by_label("Applicant name", exact=True).fill("Fictional Storage Failure")
    page.locator('a[href="/applications"]').first.click()
    controls.get_by_role("checkbox").check()
    controls.get_by_role("button", name="Enable preparation saving", exact=True).click()
    expect(controls.get_by_role("button", name="Enable preparation saving", exact=True)).to_be_visible()
    expect(controls.get_by_text("Browser-local preparation saving failed.", exact=False)).to_be_visible()
