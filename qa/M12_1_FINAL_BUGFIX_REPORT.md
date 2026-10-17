# Maadhyam M12.1 — consolidated stabilization and wireframe integration

17 October 2026, Asia/Kolkata. Repository: `swar186j/AIBuildercup-Initial`; branch: `release/m10-m12-recovery`.

## Executive summary

Status: **COMPLETE — local implementation and acceptance gates passed; GitHub checkpoint is verified in the delivery receipt**.

This release preserves the existing routes, visual identity, floating assistant, state providers, deterministic reasoning, optional Gemini integration, UID-based ownership and private Vault paths. It addresses the reported persistence/evidence defects and connects the eight functional wireframe stages inside the existing application. No new route, persistence provider, collection, dependency, deployment configuration or government integration was introduced.

Starting local and remote HEAD: `b74aa414eb6e7fa023986becccf892e9e473b7fd`, on the requested release branch. The older `721e362...` reference was not used as the source snapshot. The supplied ZIP and unrelated `.DS_Store` change were left untouched and excluded from the release.

No Cloud Build, Cloud Run/Firebase Hosting deployment, image push, IAM/environment/authentication-setting change, production Firestore mutation or Storage-object operation was executed. No paid Gemini QA was run. The historical revision `maadhyam-api-00003-t6s` is owner-supplied context, not a new production inspection.

## Defect matrix

| ID | Observation / reproducible cause | Implementation | Files / regression evidence |
|---|---|---|---|
| M12-HH-001 | Household save returned early when no cloud Passport destination existed. Feedback did not expose saving/retry. Active destination was not retained across reload; in-flight edits could be marked as included in an older snapshot. Strict acknowledgment checking also needed to account for API-added null timestamps and equivalent ISO representations. | Consented first save reuses the existing application snapshot contract with an idempotent client ID. Retain the active preparation ID; await and validate acknowledgment; retain edits and acknowledged revisions; queue newer snapshots; block failed background retries; show saving/failure/retry. Canonical comparison handles nullable legacy timestamps without hiding substantive differences. | `WorkspaceProvider.tsx`, `HouseholdIntelligence.tsx`, `workspaceSnapshot.ts`, cloud application service. `test_household_first_save_reload_exact_identity_and_timestamps`, `test_household_real_fastapi_contract_save_reload_and_server_defaults`, slow/no-ack/auth/401/404/409/503 cases. |
| M12-WIF-001 | Expanded frontend comparison included generic/unreviewed evidence while headline counts used reviewed applicant findings. Missing-field completion was described as a correction, and live draft text could move a previously submitted preview. | Shared applicant/owner scope; submitted simulation snapshot; equal before/after comparison rules; distinct reviewed/provisional/missing/unavailable metrics and blocker explanations; fill versus replace wording; reset and invalidated draft results. Real metadata remains untouched. | `ReasoningWorkspace.tsx`, shared comparison/applicant helpers, citizen intelligence service. Missing name/DOB, same/different owner, reviewed/provisional, reset and no-PATCH assertions in `test_m12_1_regressions.py`; backend simulation tests. |
| M12-DOC-001 | `unassigned:<holder category>` grouped distinct generic Parent/Guardian/Other records as one identity. Missing pairs could look like completed analysis. | Compare confirmed stable member IDs; exclude uncertain/orphaned assignments and distinct owners. Preserve the legacy single-workspace self mapping. Show actual uploaded/reviewed/eligible/excluded counts, missing fields, provisional evidence, field-level results and ownership/review actions; recompute from live state. | `documentComparison.ts`, `DocumentVault.tsx`, Dashboard. Comparison engine cases, orphaned-owner case, household owner/reassignment/browser cases. |
| M12-PLAN-001 | Default UI exposed weights and issue/option structures, offered self-dependency, and populated arbitrary-looking estimates. | Default plain-language priorities mapped to the existing weights; citizen problem descriptions and reviewed issue prefill; Advanced mode retains estimates, actions, authorities and prerequisites. Unknown estimates stay blank. Self-dependency is absent and cyclic choices are disabled. Backend adversarial deadlock detection and ranked alternatives remain. | `WeightedOptimizer.tsx`. Four priority cases, advanced/invalid weights, disabled self/cycle controls and backend deadlock tests. |
| M12-RULE-001 | A single stored pack was selected against itself. Saved-preparation selection did not scope the evidence used for impact. | Disable same-version comparison; explicitly explain single-version unavailability. Hypothetical proposals are separate clones with persistent hypothetical labeling, preserved citations and no active-pack mutation. Scope to the selected preparation/applicant's reviewed evidence. | `RuleImpactAnalyzer.tsx`; stored version, unsupported/malformed payload, hypothetical/no-change and active-pack preservation tests. |
| M12-FIND-001 | Raw fields, missing-data grammar, generic family warnings and missing-age warnings obscured the actual applicant evidence. | Friendly labels and categories, filenames, missing/awaiting-review explanations and review actions. Use saved applicant answers and selected evidence; exclude unrelated family documents from applicant reasoning. No-conflict wording explicitly allows incomplete comparisons. | `friendlyLabel.ts`, `ResolutionPlanner.tsx`, `intelligence.py`, shared applicant helper. Missing DOB/address, provisional/confirmed evidence, known age and unrelated-person/family cases. |
| M12-UX-001 | Independent notices could imply success before persistence or leave background errors unclear. | Shared accessible mutation lifecycle with validation before success, stable operation keys, persistent dismissible failures, visible long-running status and module retry controls. Migration reports checksum-verified aggregate success/partial failure. | `saveNotifications.ts`, `SaveNotifications.tsx`, cloud services/providers and layout. Success/failure/retry, duplicate click, held response, malformed acknowledgment, no-spam and migration/deletion tests. |
| M12-PASS-001 / Bug 8 | Previously reported Step 3 loss required protection; applicant/step/document/timestamp data must remain exact. | Existing preparation serialization/IDs remain; tested cloud acknowledgment, exact-step restoration, optional DOB, household/manual applicant and selected references. Active preparation changes cannot hydrate over edits made during loading. | Existing cloud preparation boundary and workspace/wizard. `test_confirmed_save_hard_refresh_exact_step[0..3]`, saved/manual applicant, slow/failed save, conflict and legacy tests. |
| M12-PLANNER-001 / Bug 9 | Planner state needed visible task controls, prerequisite-safe restoration and accurate acknowledgment of newer snapshots. | Existing planner snapshot fields reused for target/manual task IDs/history. Existing checklist actions are exposed within Planner, respect dependencies, derive objective Vault steps from current applicant evidence and cascade removal. Simulations/routes/proposals are labeled temporary. | Workspace provider, Planner and connected progress component. `test_planner_saved_checklist_target_and_dependency_cascade`, target restore and persistence suites. |
| M12-VAULT-001 / Bug 10 | Cloud Vault functionality needed protection; an older metadata acknowledgment could replace a newer household association. | Private storage/auth/generation paths retained. Validate cloud response shapes, preserve local originals, apply acknowledgment revisions/timestamps without replacing newer fields, and serialize subsequent revisions. Retain extraction provenance as an optional metadata field. | Document provider/service, `documents.py`, `DocumentContext.ts`. Upload/refresh/preview/delete, partial deletion, migration, cross-user authorization, malformed response and slow ownership-change tests. |

The observed production incident was not reproduced by writing production data. Local tests establish the source failure modes and corrected behavior; they do not prove which network/authentication condition occurred in the owner's historical browser session.

## Functional wireframe integration

| Stage | Existing route | Delivered behavior |
|---|---|---|
| 1. Landing/discover | `/` | Service search forwarded to existing service results, supported/advisory labels, actual start/resume destination, live evidence summary and connected journey links. |
| 2. Select service | `/services`, `/services/passport` | Search, available assistance descriptions, Passport selection and truthful Aadhaar/EPFO advisory navigation. |
| 3. Upload | `/documents` | Existing upload/indeterminate status, cloud acknowledgment/retry, category/holder/file timestamps, contextual review/planner/readiness links. No fabricated upload percentage. |
| 4. Extract/review | `/documents` | Existing structured editable extraction and explicit apply/review remain; missing fields and extraction source are visible; workspace application is distinguished from acknowledged cloud persistence. |
| 5. Detect issues | `/documents` | Live same-person field comparisons and distinct reviewed/provisional/missing/excluded counters with next actions. |
| 6. Guidance/plan | `/planner` | Numbered reasoning, readable prerequisites/why this order, saved checklist, target date, Simple/Advanced optimizer and temporary-preview labels. |
| 7. Readiness | Existing Passport journey | Deterministic percentage and checklist from actual applicable stored rule checks, applicant facts, selected ownership and reviewed fields; missing/review/difference/official checks remain distinct. |
| 8. Final next steps | Passport completion, `/applications` | Saved preparation summary, questionnaire status versus evidence readiness, pending checks, resume, official portal, Planner and existing AI assistant actions. |

`PreparationJourneyProgress` derives recorded actions from existing providers and live comparison results. It does not create another global wizard or treat visiting a page as completion. Sidebar navigation remains unrestricted. The original 23 capability areas remain present; the existing `FEATURE_ACCEPTANCE_INVENTORY.md` is retained and the new receipts cover the current source. Live-agent connections, official government submission/tracking, legal acceptance and guaranteed visit elimination are not introduced or claimed.

## Deterministic readiness formula

For the applicable `/api/passport/assess` result:

1. Include the applicant-name check and, except for the police guidance scenario, applicant age-group check.
2. Include each check selected from the stored Passport rule pack by the actual scenario, DOB cutoff, answers and applicable minor/name-change/Tatkaal/police conditions.
3. An evidence requirement completes only with matching selected applicant evidence, citizen-reviewed status and all needed fields on a qualifying candidate. Missing values, unrelated owners, unreviewed records, unresolved reviewed differences and contradictory availability answers do not complete it. Family evidence remains an official-applicability check unless it is explicitly the selected household applicant's own evidence.
4. Rule checks requiring official applicability/acceptance confirmation remain pending when there is no implemented confirmation mechanism.

`percentage = round(100 × completed_checks / total_applicable_checks)` with equal weights. The response includes the numerator, denominator, item states, reasons and next actions. The frontend validates their consistency before rendering. The formula is deterministic Python code; Gemini never generates this number. A computed 100% describes these preparation checks only, not government approval, wizard navigation or application submission.

## Persistence/API/database compatibility

- Existing application, document and household IDs, consent, UID scoping, Firestore revisions, server saved timestamps and Storage object paths remain intact.
- Household/planner/history data remain nested in existing `users/<UID>/applications/<ID>` snapshots. No new collection, database or destructive migration.
- Canonical acknowledgment comparison treats only absent/null optional member timestamps and equivalent UTC timestamp formats as semantically equal. Different IDs, fields, dependencies, answers or revisions still fail validation.
- `/api/passport/assess` gains optional applicant-name/member inputs and an additive `readiness` result. Existing checks, statuses and source citations remain available. Legacy responses without readiness remain readable and show an unavailable status instead of inventing a number.
- Optional Vault `metadata.extractionSource` accepts `manual`, `ocr`, `gemini`; old metadata defaults to manual. Existing IndexedDB records remain readable. This is the only additive stored metadata field; no migration is required.
- Firestore database remains `maadhyam`. Private bucket configuration, generation-protected operations, authentication settings and runtime environment are unchanged.
- A historical backend rollback may reject the optional new metadata key because its model forbids unknown fields. The handoff describes retaining optional-field support rather than removing production provenance records.

## Executed tests and evidence

All final execution exit codes are zero. Historical baseline counts are not used as new acceptance evidence.

```text
Backend tests: 463 passed (original 443 retained + 20 new)
Frontend lint: PASS; 0 errors, 0 warnings (--max-warnings 0)
Frontend build: PASS; TypeScript and production Vite build
Browser/helper suite: 226 passed; HTTP suite: 18 passed (244 combined)
Historical suites: 45 passed (functional 24, reasoning 5, M9 5, Vault 4, smoke 7)
New regressions: 55 cases (20 backend + 35 browser/helper), included above
Existing tests removed: 0
Failed/skipped final tests: 0 failed, 0 skipped
```

Total executed tests/checks across these suites: **752 passed**. The backend and browser suite each report the same Starlette/httpx deprecation warning; Vite emits its bundle-size advisory. These are not ESLint warnings. No tests were disabled, deleted or marked skipped.

The new household contract test drives actual FastAPI request models/routes from a real browser with a local memory persistence dependency, including server-added null timestamps and normalized timestamp formats. Other cloud/browser cases use explicit fictional providers; backend persistence suites exercise UID isolation/revisions/private-object generations with local doubles. No emulator provisioning or paid cloud acceptance was performed.

The complete runner executes backend, zero-warning lint, production build, all `qa` browser modules, HTTP tests and the five historical scripts. Historical assertions were updated for renamed controls, scoped applicant payloads, duplicate checklist titles and async rendering; no tests or cases were removed. The legacy wrapper now mocks Firebase authentication and drains request routes before closing contexts. Earlier historical-wrapper runs lacked explicit Firebase interception; their authentication-network behavior cannot be certified from those receipts. Final verification intercepts authentication and disables cloud storage/persistence/Gemini providers.

Intermediate failures are retained locally under the verification evidence's `intermediate` directory and other ignored diagnostic runs. They included outdated raw-label/default-estimate assertions, a preview rebuild during an early run, timestamp-string formatting assumptions, trying to edit a deliberately locked Vault control, and historical-runner timing/teardown issues. They are not counted as passing final evidence.

Portable evidence: `qa/evidence/m12-1-verification/` (XML, execution receipt, lint/build and historical receipts). Raw fictional screenshots/network diagnostics remain local and excluded from Git. Portable frontend logs have trailing whitespace normalized for `git diff --check`; raw final stdout copies remain in the ignored intermediate directory. Mobile landing/service screenshots were visually inspected; responsive browser assertions also check overflow and core navigation.

## Required regression mapping

- Household identity/timestamps/dependencies: first-save, real FastAPI schema round trip, slow acknowledgment/new edits, delayed auth, failed saves/retry and conflict tests.
- What-If/missing DOB/name/provisional evidence/reset/source immutability: dedicated M12.1 browser cases and backend simulation cases.
- Same/different/unknown/orphaned owners, same relationship and reanalysis: shared comparison cases plus existing household browser and backend tests.
- Four optimizer priorities, blank estimates, Advanced mode, disabled self/cycle controls and backend malformed-input deadlock: dedicated planner tests.
- Single/same/distinct fixture rule versions, hypothetical/no change, unsupported/malformed data and active/citation preservation: browser and backend rule tests.
- Friendly missing/contextual findings, actual applicant age, optional DOB and no unrelated family blocker: M12.1 plus original Passport/reasoning suites.
- Notification acknowledgment, failure, Retry, duplicate click, no premature success, persistent errors and de-duplication: held-response, malformed-response and repeated-save cases.
- Passport Steps 1–4, exact ID/applicant/answers/documents/timestamps, manual/household applicant, revision conflicts and legacy optional fields: M12 persistence/remediation and full-journey tests.
- Planner target/checklist/dependency restoration: M12.1 saved-checklist case plus original snapshot/API tests.
- Vault upload/preview/metadata/delete/partial failure/migration and cross-user rejection: browser suites and `test_cloud_documents.py` / `test_cloud_applications.py`.
- Wireframe discovery/search/service selection, dynamic readiness, applicable rule changes, review/owner exclusion, unchanged routes and floating assistant: dedicated wireframe tests, mobile navigation and original journey suites.

## GitHub checkpoint

Branch: `release/m10-m12-recovery`. The final commit is the single release checkpoint containing this report and the handoff. Its exact immutable SHA and remote-HEAD verification are recorded in the final delivery message after commit/push. Resolve the report's commit using:

```bash
git log -1 --format=%H -- qa/M12_1_FINAL_BUGFIX_REPORT.md
git ls-remote origin refs/heads/release/m10-m12-recovery
```

No force push, default-branch change, branch deletion or main merge. No credentials, source archive, real identity documents, raw browser profiles or unrelated `.DS_Store` changes are included.

## Remaining limits

- Production deployment and production write-based acceptance are owner-only and were not performed. Anonymous identity continuity depends on retaining the same browser profile and Firebase UID.
- Only one complete stored historical Passport rule pack currently exists. Hypothetical versions are scenarios; the two-version browser fixture is fictional test data.
- Official source freshness, government document acceptance and paid live Gemini extraction accuracy are not established by local tests. The existing eight citizen workflows and 23 capability boundaries remain advisory as documented in the retained inventory.
- Unknown optimizer estimates require citizen input before numeric ranking; no government fee or processing-time guarantee is inferred.
- Vite reports its existing large-bundle advisory. Pytest reports a Starlette/httpx test-client deprecation; lint must have zero warnings. Negative tests intentionally produce HTTP error console messages; uncaught page errors remain test failures.
- See the handoff for the optional-provenance rollback compatibility caveat. No claim of perfect or zero-bug software is made.

## Actual changed files

- `.gitignore`
- `Maadhyam/apps/api/src/maadhyam_api/routes/documents.py`
- `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py`
- `Maadhyam/apps/api/src/maadhyam_api/routes/passport_rules.py`
- `Maadhyam/apps/api/tests/run_frontend_functional.py`
- `Maadhyam/apps/api/tests/run_frontend_tests.py`
- `Maadhyam/apps/api/tests/run_reasoning_e2e.py`
- `Maadhyam/apps/api/tests/run_vault_e2e.py`
- `Maadhyam/apps/api/tests/test_m12_1_stabilization.py`
- `Maadhyam/apps/web/src/components/AIAssistant.tsx`
- `Maadhyam/apps/web/src/components/AppLayout.tsx`
- `Maadhyam/apps/web/src/components/PassportReadiness.tsx`
- `Maadhyam/apps/web/src/components/PreparationJourneyProgress.tsx`
- `Maadhyam/apps/web/src/components/ReasoningWorkspace.tsx`
- `Maadhyam/apps/web/src/components/RuleImpactAnalyzer.tsx`
- `Maadhyam/apps/web/src/components/SaveNotifications.tsx`
- `Maadhyam/apps/web/src/components/WeightedOptimizer.tsx`
- `Maadhyam/apps/web/src/context/DocumentContext.ts`
- `Maadhyam/apps/web/src/context/DocumentProvider.tsx`
- `Maadhyam/apps/web/src/context/WorkspaceProvider.tsx`
- `Maadhyam/apps/web/src/pages/Dashboard.tsx`
- `Maadhyam/apps/web/src/pages/DocumentVault.tsx`
- `Maadhyam/apps/web/src/pages/GuidedJourney.tsx`
- `Maadhyam/apps/web/src/pages/HouseholdIntelligence.tsx`
- `Maadhyam/apps/web/src/pages/MyApplications.tsx`
- `Maadhyam/apps/web/src/pages/ResolutionPlanner.tsx`
- `Maadhyam/apps/web/src/pages/Services.tsx`
- `Maadhyam/apps/web/src/services/citizenIntelligence.ts`
- `Maadhyam/apps/web/src/services/cloudApplications.ts`
- `Maadhyam/apps/web/src/services/cloudDocuments.ts`
- `Maadhyam/apps/web/src/services/passportAssessment.ts`
- `Maadhyam/apps/web/src/services/saveNotifications.ts`
- `Maadhyam/apps/web/src/utils/applicantEvidence.ts`
- `Maadhyam/apps/web/src/utils/documentComparison.ts`
- `Maadhyam/apps/web/src/utils/friendlyLabel.ts`
- `Maadhyam/apps/web/src/utils/workspaceSnapshot.ts`
- `qa/M12_1_FINAL_BUGFIX_REPORT.md`
- `qa/M12_1_MANUAL_CLOUD_DEPLOYMENT_HANDOFF.md`
- `qa/README.md`
- `qa/evidence/m12-1-verification/backend.xml`
- `qa/evidence/m12-1-verification/browser.xml`
- `qa/evidence/m12-1-verification/execution.json`
- `qa/evidence/m12-1-verification/frontend-build.log`
- `qa/evidence/m12-1-verification/frontend-lint.log`
- `qa/evidence/m12-1-verification/http.xml`
- `qa/evidence/m12-1-verification/legacy-functional.json`
- `qa/evidence/m12-1-verification/legacy-functional.log`
- `qa/evidence/m12-1-verification/legacy-m9.json`
- `qa/evidence/m12-1-verification/legacy-m9.log`
- `qa/evidence/m12-1-verification/legacy-reasoning.json`
- `qa/evidence/m12-1-verification/legacy-reasoning.log`
- `qa/evidence/m12-1-verification/legacy-smoke.json`
- `qa/evidence/m12-1-verification/legacy-smoke.log`
- `qa/evidence/m12-1-verification/legacy-vault.log`
- `qa/run_final.py`
- `qa/run_legacy.py`
- `qa/run_release_local.py`
- `qa/test_browser.py`
- `qa/test_completion.py`
- `qa/test_final_journeys.py`
- `qa/test_m12_1_regressions.py`
