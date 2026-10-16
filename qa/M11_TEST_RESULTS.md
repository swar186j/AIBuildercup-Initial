> **17 October remediation:** Current status is **COMPLETE**; lint is 0/0 and fresh tests are 409 backend, 195 local and 26 hosted (two mocked AI UI cases). See [final remediation report](M11_FINAL_REMEDIATION_REPORT.md). The initial deployment/results below are historical; billing visibility remains permission-blocked with [owner instructions](M11_BILLING_OWNER_ACTIONS.md).

# M11 test results

Functional hosted acceptance passed. Overall M11 remains **PARTIAL** for lint and billing visibility; no overall completion claim is made.

| Check | Final observed result | Evidence |
|---|---|---|
| Backend | **409 passed**, zero failed; one Starlette deprecation warning | `evidence/m11-backend.xml` |
| Frontend | TypeScript and Vite production build passed | Tool command output; production assets deployed |
| Lint | **27 errors, 5 warnings**; baseline was 28 errors, 5 warnings | `evidence/m11-lint.json` (local artifact) |
| Local HTTP/browser | **190 passed**, zero failed | `evidence/m11-final-regression/tests.xml` |
| Hosted major journeys | **26 PASS cases** | `evidence/m11-hosted/results.json` |
| Hosted reference/type restore | PASS; five related assertions | `evidence/m11-hosted-references.json` |
| Final corrected revision | **5 PASS checks**, including actual Vertex inference | `evidence/m11-final-live.json` |
| Live security | Seven named cases passed: cross-user GET/PATCH/DELETE, missing token, malformed token, direct Firestore denial, revision conflict | Hosted JSON; final missing-token rechecks also passed |
| Named Firestore readback | Completed record, planner target and three household members verified in `maadhyam`; absent from `(default)` | `evidence/m11-firestore.json` |
| Containers | Two successful builds; health and unauthenticated AI checks run before push | `evidence/m11-build.json`, `evidence/m11-build-final.json` |
| Runtime logs | 131 entries reviewed; no ERROR+ entries; no fictional applicant name or private-key marker | `evidence/m11-logs-summary.json` |

The [complete case matrix](M11_TEST_MATRIX.csv) contains 633 rows: 631 PASS, one FAIL (lint) and one BLOCKED (billing visibility). Each row records Test ID, Feature, Method, Expected, Observed, Status and Evidence. Counts overlap by purpose and must not be added into an invented unique-feature count. Most automated AI tests mock the provider; the four real calls are separately documented.

## Acceptance checkpoints

| Checkpoint | Status | Actual evidence |
|---|---|---|
| M11.1 Audit | PARTIAL | Branch `release/m10-m12-recovery`, initial HEAD `f2a0e4e`; only tunnel log dirty; build passed, lint baseline failed. Existing 398 backend tests preserved and passing in final suite. |
| M11.2 Cloud readiness | PARTIAL | Project, enabled APIs, active billing, registry, runtime IAM, Firebase registration/Anonymous Auth and named Firestore verified. Budget/credit visibility denied. Vertex quota API readable; snapshot is paginated, not an exhaustive capacity guarantee. |
| M11.3 Gemini | PASS | Real local ADC `READY`; real hosted chat and PNG OCR; real final-revision chat. Mocked quota/IAM/model/timeout/missing-ADC paths pass. |
| M11.4 Backend | PASS | 409 tests; wheel/sdist inspection; non-root container starts within 512 MiB; auth and request limits verified. |
| M11.5 Cloud Run | PASS | `maadhyam-api-00002-grr`, correct service account and image digest, health 200, protected access 401, actual Vertex answer. |
| M11.6 Hosting | PASS | Live HTTPS release, JSON API rewrite, SPA routes, actual same-origin cloud saves and no localhost requests. |
| M11.7 Hosted E2E | PASS | Actual UI save/resume/completion, household/holder identities, planner persistence, real assistant and extraction; exact IDs/type/UID restored in separate live check. |
| M11.8 Security/cost QA | PARTIAL | Functional security and bounds pass; lint and billing visibility remain unresolved. Large billable load/failure-injection tests intentionally not run. |
| M11.9 Handoff | Source/report checkpoint prepared | Deployment, testing, limitations, rollback and changed-file manifest supplied; final response records remote push verification. |

## What was actually exercised

- Real browser navigation and refresh on `/`, `/services`, `/applications`, `/documents`, `/planner`, `/household`, `/workflows` and Passport journey. Unsaved preparation URLs show the existing restore-protection warning after refresh, rather than silently creating replacement records.
- Fictional Passport preparation saved through consent to Firestore. Name, DOB, adult answer and step restored; completed status kept the same ID and exposed “View preparation summary.” A separate reissue record restored its exact selected Vault ID and accepted an empty optional DOB.
- Cross-user API reads, updates and deletes returned 404; missing/malformed tokens returned 401; direct cross-user named-Firestore REST access returned 403; wrong revision returned 409.
- Real Vertex answer rendered inside the existing floating assistant. Fictional PNG extraction returned validated fields, required review/apply and did not mark them self-reviewed automatically.
- Two distinct parent identities were added, self-dependencies disabled, household save consent accepted, exact holder ID restored from IndexedDB, and both names plus Other appeared in Passport selection.
- Planner target-dependent text changed and the cloud target restored after refresh. The named-database readback confirmed completed status, target `2027-12-31` and three members.
- Existing automated browser/HTTP cases cover all eight citizen workflows, discrepancy handling, dependencies, cycles, weighted paths, source records, name matching, expiration, planner failures, local consent/storage failures, malformed responses and ownership isolation. These are local regression results, not a claim that every advanced feature received a separate production session.

## Commands and limitations of evidence

```powershell
# apps/api
uv run --extra dev python -m pytest tests -q --junitxml=../../../qa/evidence/m11-backend.xml
# apps/web
npm run build
npm run lint
# repository root, Windows API virtualenv
Maadhyam/apps/api/.venv/Scripts/python.exe qa/run_release_local.py
Maadhyam/apps/api/.venv/Scripts/python.exe qa/verify_hosted_release.py --base https://maadhyam-1610.web.app
Maadhyam/apps/api/.venv/Scripts/python.exe qa/verify_hosted_references.py
```

Python asyncio socketpair initialization hung inside the execution sandbox; tests passed with ordinary local-socket access outside that restriction. Initial QA failures were diagnosed as obsolete pre-M10 holder values, completed-action labels and unsaved-ID replacement expectations. Assertions were updated to the current behavior, without deleting tests. Intercepted requests are drained before browser teardown. The final full suite passed after all corrections.

Live screenshots remain local under `qa/evidence/m11-hosted/`; browser profiles, tokens, raw uploads and screenshots are not staged. Raw lint and quota snapshots also remain local. The committed matrix and small sanitized result artifacts provide portable evidence.
