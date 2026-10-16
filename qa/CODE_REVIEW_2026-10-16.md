# Code review and verification — 16 October 2026

Historical review snapshot. The planner revision bug and missing backend credential configuration were subsequently fixed. See `m10/IMPLEMENTATION_STATUS.md` for the later implementation and verification results.

Reviewed the current workspace, including uncommitted M10 authentication and Firestore changes. The referenced ChatGPT conversation was accessible, but its assistant replies were content-reference placeholders, so exact prior implementation requirements could not be recovered.

## Verified results

- Backend regression: 392 passed, one Starlette TestClient deprecation warning. Executed outside the sandbox after TestClient stalled inside it.
- M10 schema smoke tests: 6 passed.
- Production frontend build: passed; emitted a JavaScript chunk size warning (611.82 kB).
- ESLint: failed, 22 errors and 3 warnings across existing and newly changed files.
- Production Chromium login smoke: sign-in form visible, button enabled, no alerts or uncaught runtime errors. Screenshot: `review-login.png`.

## Actionable finding

**P1: First workspace planner update is rejected.** `get_workspace_planner` returns revision 0 for a user without saved planner settings, and WorkspaceContext forwards that revision to PUT `/api/applications/workspace/planner`. Its `PlannerPatch` model requires revision >= 1, so the request fails validation with HTTP 422 before the transaction can create the initial settings. Use a workspace-specific request model allowing revision 0 while preserving revision >= 1 for existing application records, and add a first-save regression test.

## Coverage limits

The full M1–M9 acceptance runner was stopped after its backend stage stalled in sandboxed TestClient execution. Historical browser-suite results in `qa/evidence/final` are not fresh verification of this workspace. Those browser fixtures do not authenticate, whereas the current app requires Firebase sign-in. Authenticated journeys, Firestore persistence, concurrent edits, migration and account isolation still require emulator-backed integration coverage. No live account sign-in or provider calls were performed. Production source was not changed during this review.
