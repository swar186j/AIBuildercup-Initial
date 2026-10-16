"""Real cloud reference/type restoration without any AI inference."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://maadhyam-1610.web.app"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    context = browser.new_context(base_url=BASE)
    page = context.new_page()
    page.goto("/documents")
    page.get_by_role("button", name="Enable local saving", exact=True).click()
    page.get_by_label("Choose documents to add").set_input_files(str(ROOT / "qa/fixtures/fictional_address.png"))
    page.locator('a[href="/applications"]').first.click()
    page.get_by_role("button", name="Start new preparation", exact=True).click()
    page.get_by_role("link", name="Continue passport journey", exact=True).click()
    page.locator('a[href*="?type=reissue&preparation="]').first.click()
    page.get_by_label("Select household applicant").select_option("__other__")
    page.get_by_label("Applicant name", exact=True).fill("Fictional M11 Reference Applicant")
    references = page.get_by_label("Preparation document references")
    expect(references.get_by_role("checkbox")).to_be_checked()
    page.once("dialog", lambda dialog: dialog.accept())
    with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/applications")) as saved:
        page.get_by_role("button", name="Save preparation", exact=True).click()
    assert saved.value.status == 201
    record = saved.value.json()
    assert record["application_type"] == "reissue" and len(record["selected_document_ids"]) == 1
    assert record["applicant_details"]["date_of_birth"] == ""
    with page.expect_response(lambda r: r.request.method == "GET" and r.url.endswith("/api/applications")) as restored:
        page.reload()
    assert restored.value.status == 200
    remote = next(r for r in restored.value.json() if r["id"] == record["id"])
    assert remote["owner_uid"] == record["owner_uid"]
    assert remote["selected_document_ids"] == record["selected_document_ids"]
    assert remote["application_type"] == "reissue"
    expect(page.get_by_label("Applicant name", exact=True)).to_have_value("Fictional M11 Reference Applicant")
    expect(page.get_by_label("Preparation document references").get_by_role("checkbox")).to_be_checked()
    result = {"status": "PASS", "recordId": record["id"], "selectedIds": record["selected_document_ids"],
              "assistanceTypeRestored": "reissue", "optionalEmptyDobAccepted": True,
              "anonymousUidStableOnRefresh": True, "vaultFilesRestoredWithConsent": True}
    (ROOT / "qa/evidence/m11-hosted-references.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    context.close()
    browser.close()
