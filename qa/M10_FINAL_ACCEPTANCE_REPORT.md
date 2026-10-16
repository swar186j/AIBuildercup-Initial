# M10 acceptance

Status: PARTIAL; local/cloud lifecycle accepted within the scope below, hosted browser acceptance pending.

Date: 2026-10-16. Working tree on swar-initial, base 5d236e5; changes are uncommitted and no push/PR is claimed. Requirements are preserved under qa/requirements/m10-m12. Historical 627-test totals are not reused as current evidence.

Owner-scoped Firebase sign-in, Firestore applications/progress, optimistic revisions, stable draft IDs, planner, household consent and private Supabase upload/download/delete are implemented. Browser-local document/preparation persistence and import controls stay removed per the user's override. Empty drafts remain grouped without silent deletion or creation. Failed saves/uploads/deletes retain retryable state and unsaved changes guard sign-out/unload.

Current evidence: 450 backend cases, 23 local Chromium scenario groups, six API client checks, four API-origin checks and grouping checks pass. The local Chromium suite uses a synthetic Firebase SDK and in-memory cloud adapters; it is not represented as live cloud E2E. Separately, real Firebase users, user-token Firestore REST, actual owner rules and private Supabase files passed a create/edit/conflict/restore/isolation/delete lifecycle; both disposable accounts and all fixtures were removed.

Assessment history and per-application section APIs are present; complete automatic history integration into every panel is not independently accepted here. Full public hosted browser acceptance remains BLOCKED. Evidence: qa/evidence/m10-m12/backend.xml, browser.json, free-firestore-live.json; historical M10 details in qa/m10/CLOUD_STORAGE_HANDOVER.md.
