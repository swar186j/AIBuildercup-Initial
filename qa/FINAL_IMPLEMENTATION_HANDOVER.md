# Implementation handover

M10 PARTIAL; M11 PARTIAL; M12 PARTIAL. Public deployment is BLOCKED; all recorded current local checks pass.

Date: 2026-10-16. Working tree on swar-initial, base 5d236e5; changes are uncommitted and no push/PR is claimed. Requirements are preserved under qa/requirements/m10-m12. Historical 627-test totals are not reused as current evidence.

Current authorization: owner-only Firestore rules and disposable tests were explicitly approved and completed. Paid-upgrade permission is absent: the user requires no out-of-pocket payment and subsequently reported $300 trial credits. Active billing account and INR 0 recent spend were verified, but remaining credit/trial type/expiry were not because Google Console Overview failed to load. The project is unlinked. Do not assume INR 0 spend means $300 available. Do not upgrade billing automatically.

Once trial status is verified and the appropriate account is linked, continue Cloud Run provisioning, Secret Manager/runtime identity, budget alerts, build/Hosting deployment and real public acceptance. If trial cannot be used, docs/FREE_HOSTING.md describes Firebase Hosting Spark + Render Free, with no Google credentials uploaded. Existing Render service uses old main and has a failed Docker deploy; the current reviewed source must be published before retrying it.

Commands: API directory `.venv/Scripts/python.exe -m pytest -q`; web directory `npm run lint` and `npm run build`; root `python scripts/validate_deployment.py`, `node qa/m10/test_client.cjs`, `node qa/m10/test_api_origin.cjs`, `node qa/m10/test_preparation_list.cjs`; authenticated synthetic browser suite `Maadhyam/apps/api/.venv/Scripts/python.exe qa/m10/run_browser.py --m12` with Vite on 127.0.0.1:5173. Live scripts send fictional data only and explicitly mutate disposable QA fixtures; do not rerun rules publication or cloud identity mutations without their authorized context.

Current results: 450 backend cases; 23 Chromium groups; 21 inline rules cases; real two-account Firebase/Firestore/Supabase lifecycle; real Gemini assistant/extraction. Logs and safe metadata evidence are under qa/evidence/m10-m12. No new Git commit, push or PR was made. Existing M10 edits and historical evidence remain intact; backups and real environment files are ignored.


Current storage selection (2026-10-16): user explicitly chose private Google Cloud Storage to replace Supabase. GCS adapter, private-policy enforcement, generation preconditions and owner-scoped verified migration/finalization endpoints are implemented. Supabase is retained only as a migration source; source files are not automatically purged. Cloud Run deployment now selects gcs and only includes legacy credentials when ENABLE_SUPABASE_MIGRATION=true. No GCS bucket or live GCS migration is claimed: project billing/trial verification remains outstanding. See docs/GCS_MIGRATION.md.
