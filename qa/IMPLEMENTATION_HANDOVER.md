# Maadhyam implementation handover

15 October 2026. Checkout: `swar-initial`, with pre-existing uncommitted implementation preserved. No commit/push/deployment was requested or performed. The authoritative final results are in `M1-M9_FINAL_ACCEPTANCE_REPORT.md` and `evidence/final/final-summary.json`.

## Outcome

Recovered the interrupted M5/M7/M8 implementation and test fixture migration. Added independent document references for saved Passport preparations, safe browser-storage failure behavior, response validation, ownership messaging, race protection and dialog keyboard behavior. Final suite: 627 passed, zero failed/skipped; TypeScript/Vite build passed. All A–H cross-feature journeys and all eight workflow forms run in real Chromium against local FastAPI. Provider-success/error cases use explicit deterministic stubs.

## File ownership and changes

The recovery-start snapshot is `evidence/final/recovery-status.txt`; `recovery-diff-stat.txt` records the original tracked diff. The user's archive deletions/additions and OS metadata files remain untouched. Git status includes both recovered work and this recovery's changes; do not interpret every uncommitted file as newly authored in this run.

### Application files edited during this recovery

| File relative to repository root | Change |
|---|---|
| `Maadhyam/apps/api/src/maadhyam_api/routes/advanced_planning.py` | Empty optimization is an empty result, not a planned zero-action path. Preserves recovered weighted bounded search and alternatives. |
| `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py` | Exclude submitted input from manually generated reasoning validation errors. Preserves recovered household ownership gates. |
| `Maadhyam/apps/api/src/maadhyam_api/routes/passport_rules.py` | Reject invalid/future applicant DOB; explain the ownership/permission limits of family-held address candidates. |
| `Maadhyam/apps/web/src/components/AppLayout.tsx` | Guard appearance storage reads/writes when the browser denies storage. |
| `Maadhyam/apps/web/src/components/AIAssistant.tsx` | Invalidate superseded replies after reset/evidence changes; focus input on open and support Escape. |
| `Maadhyam/apps/web/src/components/WeightedOptimizer.tsx` | Reject malformed deadlock messages/disclaimers before rendering. |
| `Maadhyam/apps/web/src/context/DocumentContext.tsx` | Guard denied storage, filter malformed stored records, roll back failed saving, clear session data even if browser-copy deletion is denied with an honest warning. |
| `Maadhyam/apps/web/src/context/WorkspaceContext.tsx` | Seed each new preparation with its own document-reference snapshot. Existing records are independently updated. |
| `Maadhyam/apps/web/src/context/preparationStorage.ts` | Validate bounded unique document IDs and accept earlier version-1 records without references as an empty reference list. |
| `Maadhyam/apps/web/src/hooks/useDialogFocus.ts` | New shared modal keyboard focus containment and return-focus hook. |
| `Maadhyam/apps/web/src/pages/DocumentVault.tsx` | Apply modal keyboard handling to review, preview and extraction dialogs. |
| `Maadhyam/apps/web/src/pages/GuidedJourney.tsx` | Per-preparation selected documents, saved/missing reference UI, correct saved type fallback, DOB save validation and stale checklist reset. |
| `Maadhyam/apps/web/src/pages/MyApplications.tsx` | Immediate repeated-click guard and preparation dialog keyboard behavior. |
| `Maadhyam/apps/web/src/pages/HouseholdIntelligence.tsx` | Generation-aware household result invalidation and notice cleanup. |
| `Maadhyam/apps/web/src/pages/ResolutionPlanner.tsx` | Remove the preceding summary while evidence is being reassessed. |
| `Maadhyam/apps/web/src/pages/CitizenWorkflows.tsx` | Validate every workflow response, prevent stale results after workflow switches, add request timeout and lock active form fields. |
| `Maadhyam/apps/web/src/services/passportAssessment.ts` | Validate unknown successful assessment responses before exposing them to React. |
| `Maadhyam/apps/web/src/services/responseValidation.ts` | Add Passport response validation and strengthen nested advanced response checks. |

### Recovered components, routes and APIs

The interrupted implementation already supplied `PageHero`, `PreparationStorageControls`, `RuleImpactAnalyzer`, `WeightedOptimizer`, `HouseholdContext`, `HouseholdIntelligence`, and `preparationStorage`. These remain in use; they were not discarded or replaced.

- `/applications` and `/services/passport/journey?preparation=LOCAL-…` implement saved preparation resume. The `type` query selects a service type when explicitly supplied; without it, the saved type is retained.
- `/household` uses the recovered `POST /api/household/assess` for a transient ownership/dependency graph.
- `/planner` exposes recovered expiry input/results, weighted paths and stored/hypothetical rule comparison.
- Recovered `GET /api/passport/rules/versions` exposes complete locally stored rule packs. `POST /api/passport/rules/compare` validates the selected baseline and never modifies active rules.
- `POST /api/intelligence/advanced-plan` retains the recovered bounded exhaustive search and alternative paths.
- No additional production route or external service was introduced in this recovery.

### Tests, runner and reports

| File | Purpose |
|---|---|
| `qa/__init__.py`, `qa/conftest.py` | Complete package/fixture migration; session browser and per-test isolated context/page with evidence teardown. |
| `qa/test_browser.py`, `qa/test_completion.py`, `qa/test_http.py` | Preserve/recover original assertions, helper-only imports, configurable server URLs, deterministic waits and mobile sidebar navigation. |
| `qa/test_final_journeys.py` | A–H cross-feature journeys; workflows at mobile width; malformed/input/outage/retry/loading coverage; document persistence, storage denial, ownership, stale async replies, keyboard focus, expiry and DOB boundary regressions. |
| `Maadhyam/apps/api/tests/test_m4_m9_acceptance.py` | Give binary-upload cases short explicit pytest IDs so oversized fixture bytes do not inflate JUnit/matrix artifacts; assertions remain intact. |
| `Maadhyam/apps/api/tests/test_release_regressions.py` | 23 added backend cases: optimizer empty input, owner validation across APIs, safe AI context, untrusted CORS, deduplicated edges, invalid workflow shapes, birth dates and family address caveats. |
| `qa/run_legacy.py` | Stable script/cwd resolution and real HTTP API forwarding. |
| `Maadhyam/apps/api/tests/run_frontend_functional.py` | Update synchronization around the actual Guided Preparation/checklist and rendered assistant reply. |
| `Maadhyam/apps/api/tests/run_frontend_tests.py` | Wait for route content rather than fixed sleeps. |
| `Maadhyam/apps/api/tests/run_reasoning_e2e.py` | Explicit `--report` output path. |
| `Maadhyam/apps/api/tests/run_vault_e2e.py` | Configurable frontend URL and observable clear/reload waits. |
| `qa/run_final.py` | End-to-end reproducible local acceptance, owned temporary servers and cleanup. |
| `qa/write_final_report.py` | Derive counts, 23-feature mapping, matrix, sanitized request captures and release report from real artifacts. |
| `qa/README.md` | Execution and environment instructions. |
| `qa/M1-M9_FINAL_ACCEPTANCE_REPORT.md` | Milestone/feature decisions, defects, journey evidence and verdict. |
| `qa/M1-M9_FINAL_TEST_MATRIX.csv` | One row per final executed case plus separate build/external rows. |
| `qa/FEATURE_ACCEPTANCE_INVENTORY.md` | Every canonical feature's implementation, endpoint, positive/negative evidence and boundaries. |
| `qa/REMAINING_EXTERNAL_DEPENDENCIES.md` | Live-provider, official-rule, human support, authentication and production requirements. |

## Existing environment and setup

No packages were installed. Observed runtimes: Python 3.13.1, Node 26.11.1, npm 11.20.0; `uv` is available. API `.venv`, web `node_modules`, Python Playwright and cached Chromium were already present. `pyproject.toml` declares pytest/httpx/Playwright developer dependencies; web `package.json` owns TypeScript/Vite scripts. Use the existing lockfiles and environments; dependency upgrades were outside this recovery.

From the repository root, run the fictional-data demo in separate terminals:

```sh
cd Maadhyam/apps/api
MAADHYAM_GEMINI_API_KEY='' .venv/bin/python -m uvicorn maadhyam_api.main:app --host 127.0.0.1 --port 8000
```

```sh
cd Maadhyam/apps/web
npm run dev -- --host 127.0.0.1 --port 5173
```

The demo requires no live provider. Keep Gemini mode off except for explicitly authorized fictional provider verification. Manual AI extraction with no key should show a recoverable missing-configuration message.

## Test and build commands

Run the complete suite from any directory:

```sh
/absolute/path/to/repo/Maadhyam/apps/api/.venv/bin/python /absolute/path/to/repo/qa/run_final.py
/absolute/path/to/repo/Maadhyam/apps/api/.venv/bin/python /absolute/path/to/repo/qa/write_final_report.py
```

The runner creates its own API and Vite **production preview** on available localhost ports. It disables provider keys, collects before testing and always cleans up owned server process groups. A host policy may require local network/Chromium execution permission. The code does not install dependencies or start cloud work.

For individual backend/build checks:

```sh
cd Maadhyam/apps/api
MAADHYAM_GEMINI_API_KEY='' .venv/bin/python -m pytest -q
```

```sh
cd Maadhyam/apps/web
npm run build
```

For browser/HTTP development, point `MAADHYAM_TEST_API` and `MAADHYAM_TEST_WEB` at dedicated local test services, then run API `.venv/bin/python -m pytest qa -q`. Tests intentionally forward real API traffic; named failure/provider cases stub only their endpoint. Keep existing developer services separate from QA services.

## Persistence behavior and compatibility

- Default document/preparation state is memory, survives client-side navigation and resets on reload.
- Vault consent controls IndexedDB file/metadata copies. Preparation consent separately controls localStorage answers, DOB, applicant label, wizard step, service type and document IDs.
- New preparations take a snapshot of the currently available Vault IDs, displayed as editable selected references. Later uploads do not silently join existing preparations. Unselect unrelated evidence when starting a new applicant's preparation in a shared local Vault. Records do not copy or mutate one another's answers/references.
- Preparation schema version remains 1; earlier valid version-1 records with no `documentIds` restore with no selected evidence. Unknown versions/malformed records produce a visible recovery notice and leave saving off. Do not silently coerce personal fields from arbitrary stored data.
- Missing file references are preserved for explanation until removed explicitly. Reload with only preparation consent does not restore document bytes. Both consents are required for both record and file restoration.
- Revoking a store's consent deletes its browser copies and preserves the current session. Denied deletion is reported, including browser site-data removal instructions; it is never presented as confirmed deletion.
- Household members/dependencies remain session-only. Persisted file ownership may outlive a member label; it is never silently changed to applicant identity. Unassignment/member removal conservatively leaves a file as other evidence.
- There is one local applicant identity with an editable display label. Duplicate household display names have unique IDs. There are no independent household accounts or cross-account permissions.

## Maintenance and limits

Preserve the three distinct layers: local organizational metadata, hypothetical preparation reasoning, and unverified external/official claims. Do not turn a possible proof, category, matching name, deadline estimate or visit estimate into verified eligibility/acceptance. Keep source provenance, hypothetical labels and consent messaging intact.

When adding a response field rendered by React, update the boundary validator and add a malformed-response regression. When changing ownership, exercise Passport, planner, family reasoning and AI grounding together. When adding an asynchronous workflow, use cancellation/generations and test a held request released after a state change. Keep modal focus/return behavior when changing dialog markup.

Use the report's named positive and negative acceptance cases as the maintenance map. Do not count historical artifacts or reruns as additional passing cases. Keep failure evidence when iterating. Browser/mobile tests cover Chromium and targeted keyboard behavior; a formal accessibility/cross-device audit remains separate.

One existing Starlette/httpx deprecation warning remains. No local high/critical defect was observed in the final executed suite. External integrations, current government-rule certification, real human support, production auth and hosting remain explicitly unimplemented or untested as detailed in `REMAINING_EXTERNAL_DEPENDENCIES.md`.
