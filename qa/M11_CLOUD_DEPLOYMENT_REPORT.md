# M11 cloud and real AI acceptance

Status: PARTIAL. Public release: BLOCKED.

Date: 2026-10-16. Working tree on swar-initial, base 5d236e5; changes are uncommitted and no push/PR is claimed. Requirements are preserved under qa/requirements/m10-m12. Historical 627-test totals are not reused as current evidence.

Implemented: frozen-lock non-root container, allow-list build context, PORT/liveness startup, Hosting SPA/API routing and cache headers, Cloud Run deployment limits/Secret Manager references, CI tests/build/container/browser jobs, production AI authentication/quota, bounded provider retry/timeouts/output, thread-pool extraction and redacted request/error logs. Workflows are source files, not successful CI/deployment evidence. Docker is unavailable locally; container execution is NOT TESTED here.

Real Gemini assistant and fictional PDF extraction both passed against configured model gemini-3.8-flash (7.24s / 9.34s in final evidence). No personal document was transmitted. AI Studio Gemini API costs are not covered by the Google Cloud $300 trial credit; its existing free tier must be verified separately.

The first approved Cloud Run API activation attempt failed: project maadhyam-1610 has no linked billing account. The user then required no payment and selected a PC-independent free alternative. Added Firebase Hosting Spark + Render Free configuration, centralized HTTPS API origin, a bounded free-server wake-up gate and keyless user-token Firestore transport. Current Render service is Free/Docker but failed on older remote main; this working tree has not been uploaded/deployed there.

After an automatic approval rejection, the user explicitly approved owner-only rules publication and disposable live tests. All 21 inline owner/cross-user/anonymous rules cases passed. Current owner rules were published and real two-account persistence/private-file tests passed; fixtures were cleaned. Legacy deny-all rules are retained as a reference, but runtime user-rest requires the reviewed owner rules. No personal ADC refresh token or service-account key is uploaded to any host.

The user subsequently reported $300 credits and requested Cloud Run verification. One active billing account and INR 0 last-30-day spend were confirmed; the project remains unlinked. Google Console Overview failed to load, so trial type, remaining credit and expiry are NOT VERIFIED. No paid upgrade, Cloud Run service, Artifact Registry build, secret, budget or public Hosting release was created. Cloud deployment workflow is disabled pending trial verification; the local script requires explicit trial-credit confirmation.

Monitoring/budget alerts, WIF, runtime IAM, backup schedule and hosted authenticated E2E remain outstanding. Evidence: deployment-attempt.json, billing-verification.json, live-ai.json, firestore-rules-tests.json, free-firestore-live.json and verification.json. Runbooks: docs/DEPLOYMENT.md and docs/FREE_HOSTING.md.


Current storage selection (2026-10-16): user explicitly chose private Google Cloud Storage to replace Supabase. GCS adapter, private-policy enforcement, generation preconditions and owner-scoped verified migration/finalization endpoints are implemented. Supabase is retained only as a migration source; source files are not automatically purged. Cloud Run deployment now selects gcs and only includes legacy credentials when ENABLE_SUPABASE_MIGRATION=true. No GCS bucket or live GCS migration is claimed: project billing/trial verification remains outstanding. See docs/GCS_MIGRATION.md.
