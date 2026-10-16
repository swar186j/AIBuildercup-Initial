# M10 implementation verification — 16 October 2026

Later update: document/household cloud storage and removal of local saving are implemented. Full lint now passes. See `CLOUD_STORAGE_HANDOVER.md` for current behavior, test results and the pending Supabase project configuration; the earlier snapshot below is historical.

Implemented and verified the scoped M10 login/Firestore preparation lifecycle, saved planner and explicit local-preparation migration. Details, setup and reproducible commands are in `README.md`.

## Results

- Full backend regression: **413 passed**, one existing Starlette TestClient deprecation warning.
- Final targeted M10 auth/configuration/lifecycle run after creation-retry hardening: **21 passed** (included in the full suite's test inventory).
- Existing standalone M10 schema smoke suite: **6 passed** in the initial review.
- API client transport checks: **6 passed**, including hung response-body timeout.
- Isolated Chromium acceptance: **12 scenario groups passed**, with no uncaught page errors. Evidence: `evidence/browser.json`, `evidence/saved-journey.png`.
- Production TypeScript/Vite build: passed, with the existing large-JavaScript-chunk warning.
- Targeted lint for AuthContext, WorkspaceContext, DocumentContext, AccountPlanner, API client and AppLayout: passed. Full project lint still reports **13 errors and 2 warnings** in other/pre-existing code paths; exact diagnostics are in `evidence/lint.json`. This is not a claim that the full project lint is green.

## What changed

Backend Firebase/Firestore clients read the same project/credential settings from `.env`; this machine now uses ADC with the correct project instead of requiring a private key. The first planner write accepts revision zero, explicit null application updates are rejected, and progress transitions retain a bounded audit history.

Draft creation waits for confirmation and reuses the same idempotency key if the creation response is lost. Saves track dirty edits, serialize changes and preserve them on failure. Pending/failed edits block sign-out and warn on tab closure; the user can retry or explicitly discard local unsaved changes. Delete failures retain the card. Old session responses do not overwrite a new account's workspace.

The planner now has a working saved checklist UI with prerequisites and cascade/reset behavior confirmed by the server. Vault databases/preferences are account-scoped and provider state remounts when the account changes. Legacy shared Vault files stay in their old database; no silent migration or deletion occurs. Legacy preparation import remains consent-based and idempotent.

## Verification boundaries

Applications-list follow-up: hard-coded demo cards and the synthetic Vault application card were removed. Older unfilled saved drafts with identical assistance type and document selections are now grouped behind “Show older empty drafts”; records with names/answers or different document selections remain separate. Search includes grouped records. Revisiting a fresh journey resumes an existing unfilled draft instead of creating another. These changes do not delete Firestore records. Grouping unit checks and the browser list/search/resume scenario pass.

Follow-up fix: the user reported an indefinite “Opening your preparation…” screen. Vault restoration can change the draft-creation callback while its request is pending, cancelling the effect's navigation subscriber. The journey now retains the creation promise and re-subscribes on effect replay without starting another request. The browser suite delays Vault hydration and the create response to exercise this race. Vault upload controls also wait for restoration, and restoration preserves files already added in memory. The updated browser suite and production build pass.

Browser tests use a synthetic Firebase SDK identity only inside their isolated test context, real HTTP to a test-owned API, and the production repository logic with an in-memory Firestore adapter. They do not create/delete live users or Firestore documents. Auth tests verify the SDK boundary with synthetic verifier outcomes, not Google's token signature implementation. Actual ADC token refresh and a real Firestore read were verified during setup, and the user's app successfully opened a preparation after login.

Raw document files remain browser-local; household UI data remains session-local. M10's section/history API coverage does not claim automatic cloud synchronization of those UI features. Historical unauthenticated M1–M9 browser suites were not rerun as authenticated acceptance.
