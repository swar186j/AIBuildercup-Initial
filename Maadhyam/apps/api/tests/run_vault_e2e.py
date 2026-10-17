
#!/usr/bin/env python3
"""Real browser + real backend checks. No API mocking. Fictional documents only."""

import traceback
import os
from playwright.sync_api import sync_playwright

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082"
)

BASE = os.environ.get("MAADHYAM_TEST_WEB", "http://127.0.0.1:5173")
DB_NAME = "maadhyam-local-vault-v1"
DB_STORE = "documents"


def upload(page, name, doc_type, printed_name, dob):
    page.get_by_label("Choose documents to add").set_input_files(
        {"name": name, "mimeType": "image/png", "buffer": PNG}
    )

    card = page.locator("article").filter(has_text=name)
    card.wait_for(timeout=10000)

    card.get_by_role("button", name="Edit details").click()

    modal = page.get_by_role("dialog", name="Edit document details")
    modal.locator("#metadata-type").select_option(label=doc_type)
    modal.locator("#metadata-printed-name").fill(printed_name)
    modal.locator("#metadata-dob").fill(dob)
    modal.get_by_role("button", name="Save details").click()

    card.get_by_role("button", name="Mark self-reviewed").click()


def vault_count(page):
    """Count actual documents in browser IndexedDB."""
    return page.evaluate(
        """async ({dbName, storeName}) => {
            const db = await new Promise((resolve, reject) => {
                const req = indexedDB.open(dbName, 1);
                req.onsuccess = () => resolve(req.result);
                req.onerror = () => reject(req.error);
            });

            try {
                if (!db.objectStoreNames.contains(storeName)) {
                    throw new Error("Vault IndexedDB store missing");
                }

                return await new Promise((resolve, reject) => {
                    const tx = db.transaction(storeName, "readonly");
                    const req = tx.objectStore(storeName).count();

                    req.onsuccess = () => resolve(req.result);
                    req.onerror = () => reject(req.error);
                });
            } finally {
                db.close();
            }
        }""",
        {"dbName": DB_NAME, "storeName": DB_STORE},
    )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(base_url=BASE)
        page = context.new_page()
        failures = []

        def run(name, fn):
            try:
                fn()
                print("PASS", name, flush=True)
            except Exception:
                failures.append(name)
                print("FAIL", name, flush=True)
                traceback.print_exc()

        # --------------------------------------------------
        # VE01 — Upload, edit metadata, review
        # --------------------------------------------------

        def setup():
            page.goto("/documents")

            page.get_by_role(
                "button", name="Enable local saving"
            ).click()

            upload(
                page,
                "fictional_aadhaar.png",
                "Aadhaar card",
                "Rahul Kumar Sharma",
                "2000-05-12",
            )

            upload(
                page,
                "fictional_pan.png",
                "PAN card",
                "Rahul K Sharma",
                "2000-05-12",
            )

        run(
            "VE01 Metadata editor creates reviewed fictional Aadhaar and PAN",
            setup,
        )

        # --------------------------------------------------
        # VE02 — Actual Passport API name-conflict detection
        # --------------------------------------------------

        def api_check():
            captures = []

            def capture(response):
                if (
                    "/api/intelligence/passport-plan" in response.url
                    and response.request.method == "POST"
                ):
                    captures.append(
                        (
                            response.request.post_data_json,
                            response.json(),
                        )
                    )

            page.on("response", capture)

            services = page.get_by_role("link", name="Services")
            if services.count():
                services.first.click()

            page.goto("/planner")

            page.get_by_label(
                "Passport correction alternatives"
            ).wait_for(timeout=15000)

            assert captures, "No passport-plan API request"

            docs = captures[-1][0]["documents"]

            assert len(docs) == 2, (
                f"Expected 2 reviewed documents, got {len(docs)}"
            )

            assert {d["printedName"] for d in docs} == {
                "Rahul Kumar Sharma",
                "Rahul K Sharma",
            }

            assert all(
                d["dateOfBirth"] == "2000-05-12" and d["reviewed"]
                for d in docs
            )

            findings = captures[-1][1]["assessment"]["findings"]

            assert any(
                finding["field"] == "printedName"
                for finding in findings
            ), f"Name conflict not detected: {findings}"

        run(
            "VE02 Real Passport API detects reviewed name conflict",
            api_check,
        )

        # --------------------------------------------------
        # VE03 — IndexedDB persists documents after reload
        # --------------------------------------------------

        def refresh_check():
            page.goto("/documents")
            page.reload()

            page.get_by_text(
                "fictional_aadhaar.png"
            ).first.wait_for(timeout=10000)

            page.get_by_text(
                "fictional_pan.png"
            ).first.wait_for(timeout=10000)

            assert page.get_by_role(
                "button", name="Disable local saving"
            ).count() == 1

            count = vault_count(page)

            assert count == 2, (
                f"Expected 2 documents in IndexedDB, got {count}"
            )

        run(
            "VE03 Opt-in IndexedDB restores files and metadata after reload",
            refresh_check,
        )

        # --------------------------------------------------
        # VE04 — Clear All must delete persisted documents
        # --------------------------------------------------

        def clear_check():
            page.once(
                "dialog",
                lambda dialog: dialog.accept(),
            )

            page.get_by_role(
                "button", name="Clear local browser Vault copies"
            ).click()

            # First verify React UI cleared.
            page.get_by_text(
                "fictional_aadhaar.png"
            ).first.wait_for(
                state="detached",
                timeout=10000,
            )

            page.get_by_text(
                "fictional_pan.png"
            ).first.wait_for(
                state="detached",
                timeout=10000,
            )

            # Wait for the actual IndexedDB deletion.
            # This checks storage, not just the visible UI.
            page.wait_for_function(
                """async ({dbName, storeName}) => {
                    const db = await new Promise((resolve, reject) => {
                        const req = indexedDB.open(dbName, 1);
                        req.onsuccess = () => resolve(req.result);
                        req.onerror = () => reject(req.error);
                    });

                    try {
                        if (!db.objectStoreNames.contains(storeName)) {
                            return false;
                        }

                        const count = await new Promise((resolve, reject) => {
                            const tx = db.transaction(
                                storeName,
                                "readonly"
                            );

                            const req = tx.objectStore(
                                storeName
                            ).count();

                            req.onsuccess = () => resolve(req.result);
                            req.onerror = () => reject(req.error);
                        });

                        return count === 0;
                    } finally {
                        db.close();
                    }
                }""",
                arg={
                    "dbName": DB_NAME,
                    "storeName": DB_STORE,
                },
                timeout=15000,
            )

            print(
                "DEBUG VE04: IndexedDB empty before reload",
                flush=True,
            )

            # Reload to ensure deleted records stay deleted.
            page.reload()

            page.get_by_role(
                "button", name="Clear local browser Vault copies"
            ).wait_for(timeout=10000)

            # Allow hydration and any pending autosave to settle.
            page.get_by_text("No documents yet", exact=True).wait_for()

            aadhaar_count = page.get_by_text(
                "fictional_aadhaar.png"
            ).count()

            pan_count = page.get_by_text(
                "fictional_pan.png"
            ).count()

            stored_count = vault_count(page)

            print(
                "DEBUG VE04: "
                f"Aadhaar={aadhaar_count}, "
                f"PAN={pan_count}, "
                f"IndexedDB={stored_count}",
                flush=True,
            )

            assert aadhaar_count == 0, (
                "Aadhaar restored after Clear All"
            )

            assert pan_count == 0, (
                "PAN restored after Clear All"
            )

            assert stored_count == 0, (
                "IndexedDB repopulated after Clear All"
            )

        run(
            "VE04 Clear all deletes persisted documents",
            clear_check,
        )

        context.close()
        browser.close()

        print(
            f"{4 - len(failures)} passed, "
            f"{len(failures)} failed",
            flush=True,
        )

        raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
