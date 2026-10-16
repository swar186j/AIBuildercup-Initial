# Maadhyam M4–M9 acceptance report

Execution date: 15 October 2026 (Asia/Kolkata). Scope: current working tree, including the user's pre-existing uncommitted UI changes. No deployment, government submission, cloud credit use, or live paid provider call was performed.

## Executive summary

**Full M4–M9 sign-off is NOT recommended.** The implemented local preparation experience has been exercised in real Chromium, over real FastAPI HTTP, through backend regression, and through the TypeScript production build. Six application defects were found and fixed. Remaining gaps concern product scope and acceptance: saved questionnaire resume, frontend controls for some advanced engines, and a real household member/authorization model.

Final machine-readable counts are in `qa/evidence/final-summary.json`; the complete executed-test inventory and acceptance-gap rows are in `qa/M4-M9_TEST_MATRIX.csv`. Counts below describe the final regression set, not the sum of repeated debugging attempts. Failed intermediate runs remain available and are not represented as successful runs.

<!-- COUNTS -->
| Final regression set | Executed | Result |
|---|---:|---|
| Backend pytest | 339 | 339 passed, 0 failed, 0 skipped; 1 existing Starlette deprecation warning |
| Playwright Chromium (new + existing suites) | 127 | Browser cases recorded in final XML and legacy suite evidence |
| Separate real HTTP integration | 12 | Included in final acceptance XML |
| **Total final test cases** | **478** | **478 passed, 0 failed, 0 skipped** |
| Frontend TypeScript and Vite build | 1 build | PASS; `qa/evidence/frontend-build-final.log` |

The combined new browser/HTTP suite reports 94 passed and 0 failed. Existing browser suites contribute 45 additional cases. No live-provider test is counted as passed or as a pytest skip; it is explicitly NOT RUN.
<!-- END COUNTS -->

## Milestone status

| Milestone | Status | Acceptance conclusion |
|---|---|---|
| M4 — Document Vault / OCR | COMPLETE | Implemented local workspace passes PDF/PNG/JPEG upload, metadata correction, review, default memory storage, opt-in IndexedDB, clear/reload, negative uploads, stubbed OCR, and real missing-key fallback. Live OCR is not verified. |
| M5 — Passport journey | PARTIAL | Guided steps, actual checklist API, complete/incomplete evidence, provenance links, revisiting steps, and declared reload reset pass. A preparation card does not store and reopen an answered questionnaire. |
| M6 — Resolution Planner | COMPLETE | Implemented planner passes direct route, sidebar, reload, empty/one/multiple reviewed documents, mismatches, task dependencies, advanced panels, malformed response and outage checks. API-only advanced features remain under M7's partial status. |
| M7 — Advanced reasoning | PARTIAL | Deterministic engines and workflows pass their implemented API/UI tests; expiry entry, proposed-rule comparison, and weighted correction-option optimization lack full citizen UI entry points. |
| M8 — Household intelligence | PARTIAL | Family evidence associations, incomplete evidence, multiple holder labels, applicant exclusion, and unverified relationship warnings pass. A member-specific household dependency graph and cross-account authorization are absent. |
| M9 — AI Assistant | COMPLETE | Implemented global assistant dialog, local grounding, reviewed-evidence gates, fictional-data consent, invalid prompts, provider stubs, outages, rate limits, timeout failures, and malformed responses pass. Live Gemini: **NOT RUN**. |

“COMPLETE” above applies to implemented local functionality and documented fallbacks. It does not mean live OCR/Gemini or current government requirements have been independently verified.

## Feature-to-implementation acceptance

| Feature | API and frontend entry point | Result and limits |
|---|---|---|
| Vault / OCR | `/api/ai/extract-document`; `/documents` → AI extraction | COMPLETE for implemented local/mocked-provider scope. Explicit fictional consent, preview/apply, manual correction and real missing-key error exercised. |
| Passport guided preparation | `/api/passport/assess`; `/services/passport/journey` | PARTIAL overall. Current source-backed assessment and UI agree; full journey answer resume remains missing. |
| Correction plan | `/api/intelligence/passport-plan`; `/planner` | COMPLETE local plan. Task order, blockers and alternatives match API; no official acceptance claim. |
| Minimum-Correction Path Optimizer | `/api/intelligence/reasoning` → `minimumCorrectionPath`; `/planner` prerequisite review panel. `/api/intelligence/advanced-plan` for weighted options | PARTIAL feature scope. Prerequisite closure is displayed; full weighted option/cost/day/visit input is API-only. Valid acyclic and deadlock scenarios executed over HTTP. |
| Identity Evolution Engine | `/api/intelligence/reasoning` → `identityEvolution`; `/planner` name panel | COMPLETE implemented variation review. Conflicting and empty evidence tested. Names now render using the actual backend `name` field. Legal identity evolution is not verified. |
| Proof Substitution Engine | `/api/intelligence/reasoning` → `proofSubstitution`; `/planner` alternative evidence panel | COMPLETE implemented candidate review. Reviewed/self-held categories, multiple candidates, empty evidence, and unapproved substitution flags tested. Candidate labels do not establish interchangeability. |
| Deadline / expiry conflict solver | `/api/intelligence/reasoning` → `deadlineRescue` | PARTIAL. Target-date UI exists; expiry is API-only. Already expired, before/on target, invalid and absent dates tested. No processing-time or legal-validity guarantee. |
| Government Rule Change Impact Analyzer | `/api/passport/rules/compare` | PARTIAL; API-only comparison. Valid proposed removal, invalid version/types, duplicate IDs and no-change semantics covered by HTTP/backend tests. No comparison UI and no live rule-change certification. |
| What-if Application Simulator | `/api/intelligence/reasoning` → `simulations`; `/planner` → “See the impact” | COMPLETE implemented hypothetical preview. Real API resolves a synthetic name conflict; baseline remains unchanged; invalid references and new findings tested. |
| Bureaucratic Deadlock Detector | `/api/intelligence/reasoning` → `deadlockAnalysis`; `/planner` diagnostics; advanced-plan and workflow cycles | COMPLETE for software dependency diagnostics. A real government process deadlock is not verified; explicit warning preserved. |
| Rejection Root-Cause Intelligence | `/api/citizen-workflows/rejection-diagnosis`; `/workflows` | COMPLETE advisory workflow. Synthetic name-mismatch category and unknown cause tested, with real payload/result validation and API outage UI. Root cause is not officially confirmed. |
| Deadline Rescue Engine | `/api/citizen-workflows/deadline-rescue`; `/workflows` and planner target date | COMPLETE advisory workflow. Past target, missing target, cyclic tasks, estimates and warnings checked. |
| Multi-Authority Bottleneck Navigator | `/api/citizen-workflows/authority-bottlenecks`; `/workflows` | COMPLETE estimate workflow. Dependency execution order and seven-day critical path verified; cyclic and invalid-reference scenarios covered. |
| Government Visit Eliminator | `/api/citizen-workflows/visit-eliminator`; `/workflows`; planner preparation advice | COMPLETE advisory estimates. Conditional online availability, estimated avoidable visits and actual-elimination false flags tested. No real visit claimed eliminated. |
| Family / household evidence | `/api/intelligence/reasoning` → `familyEvidence`; `/planner` → family document situation | PARTIAL household scope. Multiple family labels, claimed relations, missing/reviewed relationship evidence, invalid references, and exclusion from applicant identity covered. No authenticated household membership or cross-user permissions. |
| AI Assistant | `/api/intelligence/chat`; global “Ask Maadhyam AI” dialog | COMPLETE deterministic scope. Natural language, reviewed-context grounding, false-official-claim fallback, consent, missing key, SDK 429, timeout exception, empty output, and invalid UI response tested. No dedicated assistant page is implemented; the global dialog is the actual entry point. |

## All eight citizen workflows

Every workflow was selected through its citizen-friendly UI and submitted to the running backend. Tests captured and validated request payloads, meaningful response fields, readable guidance, optional technical JSON, and recoverable 503 behavior. No workflow requires citizen-entered JSON.

| UI workflow | Endpoint suffix under `/api/citizen-workflows/` | Acceptance |
|---|---|---|
| Human assistance | `human-support` | PASS; blocker text and preparation checklist, no real agent assignment |
| Life-event discovery | `life-event-discovery` | PASS; illustrative catalog matches, not a complete official catalog |
| Multi-department guidance | `multi-department-rules` | PASS; sample rule packs explicitly unverified |
| Rejection diagnosis | `rejection-diagnosis` | PASS; “Name mismatch in identity proof” produces `identity_mismatch` |
| Legacy record recovery | `legacy-reconstruction` | PASS; school/hospital evidence preserved, document reconstruction remains false |
| Authority bottlenecks | `authority-bottlenecks` | PASS; dependency order and critical path match backend |
| Deadline rescue | `deadline-rescue` | PASS; past target is at risk, input validation and cyclic plan handled |
| Visit reduction planner | `visit-eliminator` | PASS; estimates and official-online-verification caveat preserved |

## Defects discovered and fixed

| ID | Severity | Reproduction / cause | Targeted fix and evidence |
|---|---|---|---|
| QA-01 | Medium | A `.png` with arbitrary bytes passed extension/MIME validation and entered Vault. | Check file signatures before creating local records; malformed, empty, unsupported and oversize browser regressions. Signature checks are not full forensic file validation. |
| QA-02 | High | Successful but incomplete planner/reasoning responses caused `.find`, `.some` or nested-array render failures; boundary recovery replaced the planner. | Validate render-critical response structures before setting React state. Malformed root and nested advanced fields produce usable error UI; no planner capability removed. |
| QA-03 | Medium | Chat HTTP 200 with `{}` created an empty assistant bubble. A stalled fetch also had no client deadline. | Require a nonblank answer; use a 15-second request deadline. Malformed answer and network-timeout regressions preserve local guidance usability. Real long-running provider latency was not benchmarked. |
| QA-04 | Medium | “Clear all” emptied React before queued IndexedDB deletion committed; immediate reload could restore saved records. | Publish the empty state only after deletion completes. Immediate reload and original IndexedDB count checks confirm removal. |
| QA-05 | Medium | Planner expected `displayName` and `addressVariants`, while backend returns `name` and `observedAddresses`. Names/addresses were omitted; stricter response checks exposed the mismatch. | Align frontend types, rendering and validation with existing API contract. Reviewed variant panels and build verified. |
| QA-06 | Low | API accepted whitespace-only assistant questions despite the UI blocking them. | Reject blank/whitespace prompts using Pydantic validation. Empty, spaces, newline and overlong regressions pass. |

Test maintenance: existing functional/Vault scripts expected the removed `Personalized Passport checklist` and old journey API. They now check `/api/passport/assess` and the actual checklist. Planner conflict tests still call the planner's real endpoint. Reasoning selectors now use the citizen-friendly correction/family flows. Assertions were migrated to actual behavior; no tests were skipped or disabled to obtain a green result.

## Execution and evidence

- Backend baseline: **297 passed, 1 warning** before edits (`qa/evidence/backend-baseline.log`).
- New regression file: `Maadhyam/apps/api/tests/test_m4_m9_acceptance.py`; provider calls are deterministic stubs.
- Real-browser suite: `qa/test_browser.py`; isolated contexts, screenshots, console/runtime/network evidence and synthetic request/response assertions. Real HTTP routes go to a dedicated API on port 8001 with Gemini credentials empty. Production frontend remains on port 5173.
- Real HTTP integration: `qa/test_http.py`; rule comparison, weighted optimization/deadlock, workflow cycles, invalid chat requests, missing-key and expiry behavior.
- Existing browser regression: functional, reasoning, M9, Vault and smoke scripts all executed. Final logs/JSON are under `qa/evidence/legacy-*-final.*`.
- Targeted final Passport follow-up: both complete/incomplete cases passed after explicitly waiting for the entered DOB to reach the applicable `dob-old` checklist rule (`qa/evidence/passport-final.xml`); these are repeats of existing cases, not additional unique cases. Completed screenshots are `qa/evidence/passport-completed-True.png` and `qa/evidence/passport-completed-False.png`.
- Frontend: `npm run build` includes `tsc -b` and Vite production compilation; final log `qa/evidence/frontend-build-final.log`.
- Browser errors: final successful cases assert no uncaught runtime exceptions. Planner malformed-response cases explicitly reject error-boundary fallback. Injected outages intentionally produce failed requests/HTTP errors; those are expected test evidence, not normal-path defects. Console checks reject synthetic identity metadata disclosure.
- Cross-page checks: dashboard, services, Vault, preparations, planner, workflows, Passport detail and journey at 1440px and 390px; no horizontal overflow, preserved headings/navy heroes, readable controls and original preparation-note/button ordering. Screenshots were visually inspected. This is targeted accessibility/responsive checking, not a comprehensive WCAG certification or cross-browser/device audit.
- Fixtures: all three requested identities/discrepancies generated in PDF, PNG and JPEG under `qa/fixtures/`, visibly marked FICTIONAL; no identity numbers. OCR success is a provider stub, not an extraction-accuracy claim.
- Intermediate evidence: `browser-initial.*`, `browser-rerun.*`, `acceptance-intermediate.*`, and `legacy-functional-initial.json` retain actual failure results. Some intermediate failures were selector/race defects; one run was interrupted by restarting the dedicated QA API. Only final stable runs support acceptance counts.

## Remaining acceptance gaps / blockers

1. **Saved journey resume:** questionnaire answers, active step and DOB belong to the wizard component; leaving/reopening does not resume a linked preparation record. My Preparations drafts work within the SPA session and intentionally disappear on reload, as its UI documents. Durable saving and a preparation-to-questionnaire link are not implemented. No corruption or fake submitted application was observed.
2. **Advanced UI coverage:** document expiry is absent from the Vault metadata editor/payload; proposed rule-pack comparison and full weighted correction-option inputs are API-only. Tests establish API correctness, not frontend acceptance for these features.
3. **Household model:** parent/guardian/spouse labels and claimed evidence links are a local prototype. There is no account identity, authenticated member authorization, member-specific consent model, or member-level dependency graph. Cross-account document-access denial cannot be tested because accounts do not exist. No external household sharing was performed; isolated browser contexts have independent Vault data.
4. **Live AI verification:** Gemini **NOT RUN**. The task permits live acceptance only with configured credentials and explicit project permission; no such permission was exercised. Existing live-test scripts require a deliberate opt-in. Missing credentials and provider failures were tested with synthetic inputs; credentials were never printed.
5. **Government-source verification:** stored packs/provenance and safeguard behavior were tested locally. Source links are references, not proof of current legal applicability. No live government monitoring job, new baseline approval, or legal acceptance verification was performed. Workflow catalogs and estimates remain illustrative. No authority accepted or rejected any synthetic document.

## Files changed by this execution

Application fixes:

- `Maadhyam/apps/web/src/pages/DocumentVault.tsx`
- `Maadhyam/apps/web/src/context/DocumentContext.tsx`
- `Maadhyam/apps/web/src/pages/ResolutionPlanner.tsx`
- `Maadhyam/apps/web/src/services/citizenIntelligence.ts`
- `Maadhyam/apps/web/src/services/responseValidation.ts` (new)
- `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py`

Tests/artifacts:

- `Maadhyam/apps/api/tests/test_m4_m9_acceptance.py` (new)
- `Maadhyam/apps/api/tests/run_frontend_functional.py`
- `Maadhyam/apps/api/tests/run_reasoning_e2e.py`
- `Maadhyam/apps/api/tests/run_vault_e2e.py`
- `qa/test_browser.py`, `qa/test_http.py`, `qa/generate_fixtures.py`, `qa/write_report.py`, `qa/README.md`
- This report, `qa/M4-M9_TEST_MATRIX.csv`, fictional fixtures, and sanitized screenshots/logs under `qa/evidence/`.

Existing user edits to layout, page heroes, citizen workflows, navigation, Passport flow, archives and metadata were preserved. No commit or deployment was made. The temporary no-credentials QA API was stopped after testing; the original application servers were left running.

## Release recommendation

The tested local demonstration can be reviewed with its preparation-only disclaimers and the passing implemented paths. **Do not sign off all of M4–M9 as complete.** Finish saved preparation resume, citizen interfaces for the API-only engines, and the household member/authorization model; then execute their missing acceptance tests. Keep live provider integration and current government-source verification explicitly separate from deterministic local acceptance.
