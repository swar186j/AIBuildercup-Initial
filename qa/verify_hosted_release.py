"""Small real hosted acceptance run. Fictional data only; never store auth tokens."""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlparse
from uuid import uuid4
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa/evidence/m11-hosted"
OUT.mkdir(parents=True, exist_ok=True)
CASES = []


def record(name, observed):
    CASES.append({"testId": name, "status": "PASS", "observed": observed})
    (OUT / "results.json").write_text(json.dumps(CASES, indent=2), encoding="utf-8")
    print(f"PASS {name}: {observed}", flush=True)


def main(base):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(base_url=base, viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.set_default_timeout(15000)
        runtime_errors, local_requests = [], []
        page.on("pageerror", lambda error: runtime_errors.append(str(error)))
        page.on("request", lambda request: local_requests.append(request.url)
                if urlparse(request.url).hostname in {"localhost", "127.0.0.1"} else None)
        health = context.request.get(base + "/api/health")
        assert health.status == 200 and health.json()["status"] == "healthy"
        record("hosting-api-rewrite", "HTTP 200 JSON health, not SPA HTML")
        for path in ["/", "/services", "/applications", "/documents", "/planner", "/household", "/workflows", "/services/passport/journey"]:
            response = page.goto(base + path)
            assert response.status == 200
            expect(page.locator("h1")).to_be_visible()
            page.reload()
            if path.endswith("/journey"):
                expect(page.get_by_role("alert")).to_contain_text("could not be restored")
                record("deep-link:" + path, "Loads; refreshing unsaved ID safely prevents replacement")
            else:
                expect(page.locator("h1")).to_be_visible()
                record("deep-link:" + path, "Loads and refreshes with visible heading")

        # Create the record through the actual UI and consent dialog.
        page.goto(base + "/applications")
        page.get_by_role("button", name="Start new preparation", exact=True).click()
        page.get_by_role("link", name="Continue passport journey", exact=True).click()
        expect(page.get_by_label("Select household applicant")).to_contain_text("Other")
        page.get_by_label("Select household applicant").select_option("__other__")
        name = "Fictional M11 Applicant " + uuid4().hex[:6]
        page.get_by_label("Applicant name", exact=True).fill(name)
        page.get_by_label("Applicant date of birth (for document guidance)").fill("1998-06-15")
        page.get_by_role("button", name="Continue", exact=True).click()
        page.get_by_role("radio", name="An adult", exact=True).check()
        page.once("dialog", lambda dialog: dialog.accept())
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/applications")) as saved_response:
            page.get_by_role("button", name="Save preparation", exact=True).click()
        saved = saved_response.value
        assert saved.status == 201, saved.text()
        application = saved.json()
        token_header = saved.request.headers["authorization"]
        uid = application["owner_uid"]
        app_id = application["id"]
        assert application["applicant_details"]["name"] == name
        assert application["current_step"] == 1
        record("passport-cloud-create", "Actual UI save returned HTTP 201 with verified owner and name")
        page.reload()
        expect(page.get_by_label("Applicant name", exact=True)).to_have_value(name)
        expect(page.get_by_role("radio", name="An adult", exact=True)).to_be_checked()
        expect(page.get_by_text("Step 2 of 4", exact=True)).to_be_visible()
        expect(page.get_by_label("Applicant date of birth (for document guidance)")).to_have_value("1998-06-15")
        listed = context.request.get(base + "/api/applications", headers={"Authorization": token_header})
        assert listed.status == 200
        restored = next(item for item in listed.json() if item["id"] == app_id)
        assert restored["owner_uid"] == uid
        record("passport-refresh-resume", "Exact record, name, DOB, adult answer and step restored")
        page.screenshot(path=str(OUT / "passport-restored.png"), full_page=True)

        # Separate anonymous identities and owner-scoped lifecycle security.
        env = dict(line.split("=", 1) for line in (ROOT / "Maadhyam/apps/web/.env.local").read_text().splitlines()
                   if line and not line.startswith("#") and "=" in line)
        public_key = env["VITE_FIREBASE_API_KEY"].strip("\"'")
        anonymous = context.request.post("https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + public_key,
                                         data={"returnSecureToken": True})
        assert anonymous.status == 200
        other = anonymous.json()
        assert other["localId"] != uid
        other_headers = {"Authorization": "Bearer " + other["idToken"]}
        for method in ["get", "patch", "delete"]:
            url = base + "/api/applications/" + app_id
            if method == "delete":
                result = context.request.delete(url + "?revision=" + str(restored["revision"]), headers=other_headers)
            elif method == "patch":
                result = context.request.patch(url, headers=other_headers,
                                               data={"revision": restored["revision"], "status": "completed"})
            else:
                result = context.request.get(url, headers=other_headers)
            assert result.status == 404, (method, result.status)
            record("cross-user:" + method, "Other verified anonymous identity receives HTTP 404")
        for label, headers in [("missing", {}), ("malformed", {"Authorization": "Bearer invalid.token"})]:
            result = context.request.get(base + "/api/applications", headers=headers)
            assert result.status == 401
            record("auth:" + label, "HTTP 401")
        direct = context.request.get(
            "https://firestore.googleapis.com/v1/projects/maadhyam-1610/databases/maadhyam/documents/users/"
            + uid + "/applications/" + app_id, headers=other_headers)
        assert direct.status == 403, direct.status
        record("firestore-direct-isolation", "Cross-user direct named-database REST read denied with HTTP 403")
        conflict = context.request.patch(base + "/api/applications/" + app_id,
                                         headers={"Authorization": token_header},
                                         data={"revision": restored["revision"] + 100, "status": "completed"})
        assert conflict.status == 409
        record("revision-conflict", "Stale/incorrect revision rejected with HTTP 409")

        # Complete and save using the real journey, retaining the same ID.
        for _ in range(2):
            for field in page.locator("fieldset").all():
                radios = field.locator("input[type=radio]")
                if radios.count():
                    radios.first.check()
            page.get_by_role("button", name="Continue", exact=True).click()
        expect(page.get_by_text("Preparation questionnaire completed", exact=True)).to_be_visible()
        with page.expect_response(lambda r: r.request.method == "PATCH" and "/api/applications/" in r.url) as completed_response:
            page.get_by_role("button", name="Save preparation", exact=True).click()
        completed = completed_response.value
        assert completed.status == 200
        assert completed.json()["id"] == app_id and completed.json()["status"] == "completed"
        page.goto(base + "/applications")
        row = page.locator("article").filter(has_text=app_id)
        expect(row.get_by_role("button", name="View preparation summary", exact=True)).to_be_visible()
        record("passport-completed", "Same cloud ID completed; View preparation action visible")
        page.screenshot(path=str(OUT / "passport-completed.png"), full_page=True)

        # One actual hosted chat call from the preserved floating assistant.
        page.get_by_role("button", name="Open Maadhyam AI", exact=True).click()
        assistant = page.get_by_role("dialog", name="Maadhyam AI assistant")
        assistant.get_by_label("Use Gemini (fictional demo metadata only)").check()
        assistant.get_by_label("Confirm all metadata is fictional").check()
        assistant.get_by_label("Message to Maadhyam AI").fill("Give one short preparation reminder without claiming approval.")
        with page.expect_response(lambda r: r.url.endswith("/api/intelligence/chat"), timeout=45000) as chat_response:
            assistant.get_by_role("button", name="Send message").click()
        chat = chat_response.value
        assert chat.status == 200, chat.text()
        answer = chat.json()
        assert answer["mode"] == "gemini-vertex" and answer["answer"]
        expect(assistant.get_by_text(answer["answer"], exact=True)).to_be_visible()
        record("live-gemini-chat", "Real Vertex answer returned and rendered in floating assistant")
        page.screenshot(path=str(OUT / "gemini-chat.png"), full_page=True)
        assistant.get_by_role("button", name="Close AI assistant").click()

        # One fictional OCR request, with explicit review before application.
        page.goto(base + "/documents")
        page.get_by_role("button", name="Enable local saving", exact=True).click()
        page.get_by_label("Choose documents to add").set_input_files(str(ROOT / "qa/fixtures/fictional_pan.png"))
        page.get_by_role("button", name="AI extraction", exact=True).click()
        preview = page.get_by_role("dialog", name="Document extraction preview")
        expect(preview.get_by_role("button", name="Extract with Gemini")).to_be_disabled()
        preview.get_by_role("checkbox").check()
        with page.expect_response(lambda r: r.url.endswith("/api/ai/extract-document"), timeout=45000) as extraction_response:
            preview.get_by_role("button", name="Extract with Gemini").click()
        extraction = extraction_response.value
        assert extraction.status == 200, extraction.text()
        assert extraction.json()["printedName"]
        expect(preview.get_by_role("button", name="Review & apply extracted details")).to_be_visible()
        preview.get_by_role("button", name="Review & apply extracted details").click()
        expect(page.get_by_role("button", name="Mark self-reviewed")).to_be_visible()
        record("live-gemini-ocr", "Fictional PNG extracted; user reviewed/applied; remains unverified")
        page.screenshot(path=str(OUT / "ocr-reviewed.png"), full_page=True)
        page.get_by_role("button", name="Mark self-reviewed", exact=True).click()
        page.locator('a[href="/household"]').first.click()
        for member in ["Fictional M11 Parent One", "Fictional M11 Parent Two"]:
            page.get_by_label("New member name", exact=True).fill(member)
            page.get_by_label("New member relationship", exact=True).select_option("parent")
            page.get_by_role("button", name="Add member", exact=True).click()
            expect(page.get_by_label("Household member " + member, exact=True)).to_be_visible()
            expect(page.get_by_label(member + " depends on " + member, exact=True)).to_be_disabled()
        page.get_by_label("Fictional M11 Parent Two depends on Fictional M11 Parent One", exact=True).check()
        page.once("dialog", lambda dialog: dialog.accept())
        with page.expect_response(lambda r: r.request.method == "PATCH" and "/api/applications/" in r.url) as household_saved:
            page.get_by_role("button", name="Save household to cloud", exact=True).click()
        assert household_saved.value.status == 200
        record("household-cloud", "Two distinct parent identities, self-dependency disabled, consented cloud save")
        page.locator('a[href="/documents"]').first.click()
        page.get_by_role("button", name="Edit details", exact=True).click()
        holder = page.locator("#metadata-holder")
        holder.select_option(label="Fictional M11 Parent One — parent")
        selected_member = holder.input_value()
        assert selected_member.startswith("member:")
        assert holder.get_by_role("option", name="Fictional M11 Parent Two — parent", exact=True).count() == 1
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="Save details", exact=True).click()
        page.reload()
        page.get_by_role("button", name="Edit details", exact=True).click()
        expect(page.locator("#metadata-holder")).to_have_value(selected_member)
        page.get_by_role("button", name="Save details", exact=True).click()
        record("vault-owner-identity", "Exact member ID and distinct same-relationship options survive local reload")
        page.goto(base + "/services/passport/journey?preparation=" + app_id)
        applicant = page.get_by_label("Select household applicant")
        expect(applicant).to_contain_text("Fictional M11 Parent One")
        expect(applicant).to_contain_text("Fictional M11 Parent Two")
        expect(applicant).to_contain_text("Other")
        record("passport-household-options", "Both saved named household members and Other appear")
        page.locator('a[href="/planner"]').first.click()
        deadline = page.get_by_label("Your deadline and action plan", exact=True)
        page.locator("#planning-date").fill("2026-10-18")
        expect(deadline).to_contain_text("day(s) until your personal target")
        near_text = deadline.inner_text()
        with page.expect_response(lambda r: r.request.method == "PATCH" and "/api/applications/" in r.url
                                  and r.request.post_data_json.get("planner_state", {}).get("target_date") == "2027-12-31") as planner_saved:
            page.locator("#planning-date").fill("2027-12-31")
        assert planner_saved.value.status == 200
        assert deadline.inner_text() != near_text
        page.reload()
        expect(page.locator("#planning-date")).to_have_value("2027-12-31")
        record("planner-dynamic-persistence", "Target-dependent plan text changes; cloud target restores after refresh")
        page.screenshot(path=str(OUT / "planner-restored.png"), full_page=True)
        assert not runtime_errors, runtime_errors
        assert not local_requests, local_requests
        record("browser-runtime", "No uncaught JS errors or localhost requests")
        context.close()
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    try:
        main(args.base.rstrip("/"))
    except Exception as exc:
        CASES.append({"status": "FAIL", "observed": str(exc)[:2000]})
        (OUT / "results.json").write_text(json.dumps(CASES, indent=2), encoding="utf-8")
        raise
