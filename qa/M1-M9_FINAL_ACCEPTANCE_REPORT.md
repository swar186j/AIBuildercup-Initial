# M1–M9 final local acceptance report

Execution date: 15 October 2026, Asia/Kolkata. Branch: `swar-initial`. No commit, push, cloud deployment, paid API request, live provider call or government submission was made.

## Executive summary

Final local demo acceptance: **COMPLETE**. Final unique test cases: **627 executed; 627 passed; 0 failed; 0 skipped**. TypeScript and Vite production build: **PASSED**. Live integrations are separate, unexecuted external acceptance work. See `REMAINING_EXTERNAL_DEPENDENCIES.md`.

A green local acceptance is not production readiness. Feature names below map to the actual conservative local implementation; examples include helpdesk preparation rather than an agent connection, address-variant review rather than verified migration history, and visit estimates rather than actual visit elimination.

## Repository baseline and recovery

- The checkout contained substantial modified and untracked implementation, a pre-existing deleted `Maadhyam.zip`, OS metadata changes and archives. These were preserved. Baseline status and diff summary: `evidence/final/recovery-status.txt` and `recovery-diff-stat.txt`.
- Reestablished backend baseline: 369 passed. Baseline TypeScript/Vite build passed. After completing fixture recovery and enabling the required local execution permissions, the existing browser/HTTP baseline passed 130 cases. Earlier sandbox launch/network failures remain in `browser-http-baseline.log` and are not counted as application failures or passing final cases.
- Shared session Chromium / per-test isolated page fixtures moved into `qa/conftest.py`; fixture imports removed from test modules; `qa/__init__.py` added. Tests collect before execution.
- Fixed legacy working directories and report paths; replaced browser sleeps with observable conditions. Added `qa/run_final.py` with owned temporary servers, readiness polling and guaranteed teardown. No existing developer server is restarted by the runner.
- Recovery browser baseline: `evidence/final/recovery-browser-http.xml`. Intermediate application/test failures and the subsequent green recovery run are retained under `evidence/final/intermediate/`. Final counts do not include retries.

## Milestone acceptance

| Milestone | Local status | Verified scope |
|---|---|---|
| M1 | COMPLETE | API startup, configuration, CORS and safe errors |
| M2 | COMPLETE | Navigation and service discovery |
| M3 | COMPLETE | Passport stored rules, provenance and checklist |
| M4 | COMPLETE | Vault, upload validation, manual review and deterministic OCR |
| M5 | COMPLETE | Independent saved Passport preparations and consent |
| M6 | COMPLETE | Resolution Planner and recoverable failures |
| M7 | COMPLETE | Advanced local reasoning and eight citizen workflows |
| M8 | COMPLETE | Session household graph, consent and ownership |
| M9 | COMPLETE | Global local/deterministic AI assistant |

## 23-feature acceptance

| # | Canonical feature | Milestone | Local status |
|---|---|---|---|
| 1 | Document OCR & Intelligent Extraction | M4 | COMPLETE |
| 2 | Indian Name Matching | M4/M7 | COMPLETE |
| 3 | Government Service Document Checklist | M3/M5 | COMPLETE |
| 4 | Human-Assisted Application Support | M7 | COMPLETE |
| 5 | Life-Event Based Service Discovery | M2/M7 | COMPLETE |
| 6 | Rules-as-Code Engine | M3 | COMPLETE |
| 7 | Cross-Document Discrepancy Detection & Rule Citations | M4/M6 | COMPLETE |
| 8 | Dependency-Aware Correction Planner | M6 | COMPLETE |
| 9 | Migrant Address Continuity Builder | M7 | COMPLETE |
| 10 | Multi-Department Rule Packs | M7 | COMPLETE |
| 11 | Minimum-Correction Path Optimizer | M7 | COMPLETE |
| 12 | Identity Evolution Engine | M7 | COMPLETE |
| 13 | Proof Substitution Engine | M7 | COMPLETE |
| 14 | Deadline & Document Expiry Conflict Solver | M7 | COMPLETE |
| 15 | Government Rule Change Impact Analyzer | M7 | COMPLETE |
| 16 | Rejection Root-Cause Intelligence | M7 | COMPLETE |
| 17 | What-if Application Simulator | M7 | COMPLETE |
| 18 | Bureaucratic Deadlock Detector | M7 | COMPLETE |
| 19 | Family & Household Dependency Graph | M8 | COMPLETE |
| 20 | Multi-Authority Bottleneck Navigator | M7 | COMPLETE |
| 21 | Deadline Rescue Engine | M7 | COMPLETE |
| 22 | Government Visit Eliminator | M7 | COMPLETE |
| 23 | AI-Assisted Preparation and Guidance | M9 | COMPLETE |

Detailed backend/frontend entry points, endpoints, positive and negative scenarios, limitations and evidence paths are in `FEATURE_ACCEPTANCE_INVENTORY.md` and `evidence/final/feature-inventory.json`. Each area has executed browser-facing coverage; backend-only existence is not used as the completion criterion.

## Final execution results

| Suite | Executed | Passed | Failed | Skipped | Evidence |
|---|---:|---:|---:|---:|---|
| backend | 392 | 392 | 0 | 0 | `evidence/final/backend.xml` |
| browser | 172 | 172 | 0 | 0 | `evidence/final/browser.xml` |
| http | 18 | 18 | 0 | 0 | `evidence/final/http.xml` |
| legacy-functional | 24 | 24 | 0 | 0 | `evidence/final/legacy-functional.json` |
| legacy-m9 | 5 | 5 | 0 | 0 | `evidence/final/legacy-m9.json` |
| legacy-reasoning | 5 | 5 | 0 | 0 | `evidence/final/legacy-reasoning.json` |
| legacy-smoke | 7 | 7 | 0 | 0 | `evidence/final/legacy-smoke.json` |
| legacy-vault | 4 | 4 | 0 | 0 | `evidence/final/legacy-vault.log` |

Build: `evidence/final/frontend-build.log` includes `tsc -b` and Vite bundling. Backend output retains one existing Starlette/httpx deprecation warning. No dependency install was required. No intentionally disabled or weakened tests were introduced.

## Cross-feature journeys and all eight workflows

| Journey | Executed browser scenario | Status |
|---|---|---|
| A | Dashboard → services → Passport → Vault review → selected evidence → checklist → planner → save/reopen (`test_journey_a_passport_full`) | PASSED |
| B | Name discrepancy → identity variants → correction alternatives → hypothetical fix (`test_journey_b_identity_whatif`) | PASSED |
| C | Conflicting addresses → continuity review → Passport checklist → correction guidance (`test_journey_c_address_continuity`) | PASSED |
| D | Expiry and target → conflict → prerequisites → weighted alternatives (`test_journey_d_deadline_dependencies_expiry`) | PASSED |
| E | Members → explicit ownership → missing evidence → withdrawal → safe applicant reassignment (`test_journey_e_household_consent_withdrawal`) | PASSED |
| F | Saved preparation → stored baseline → hypothetical removed rule → unchanged saved answers (`test_journey_f_rule_saved_preparation`) | PASSED |
| G | Reviewed applicant + parent evidence → permitted AI grounding → provider failure fallback (`test_journey_g_assistant_grounding_provider_failure`) | PASSED |
| H | All eight real-HTTP workflow forms at 390px → readable/JSON results → unrelated preparation preserved (`test_journey_h_all_workflows_mobile`) | PASSED |

Human assistance, life-event discovery, multi-department guidance, rejection diagnosis, legacy recovery, bottlenecks, deadline rescue and visit reduction each execute their real endpoint and validate readable guidance, captured request/response data and optional JSON. Each also has outage, malformed response, invalid-input response, loading and retry coverage. Mobile workflow coverage is Journey H. Required-field validation is exercised where the form requires citizen text or a target date. Selector waits and intercepted-request release use explicit browser/network conditions.

## Defects discovered and fixed in this recovery

| ID | Defect / fix | Acceptance evidence (browser.xml unless noted) |
|---|---|---|
| R01 | Saved preparations used the global Vault without retained per-record references. Added selected document IDs, missing-reference feedback and separate file consent. | test_m5_document_references_isolated_and_missing; test_m5_both_persistence_consents_and_delete_reload |
| R02 | Successful malformed Passport/workflow/nested expiry/optimizer responses could crash or mislead. Added render-boundary validation and recoverable errors. | test_passport_malformed_response; test_workflow_contract_error_retry; test_m7_malformed_expiry_conflict; test_nested_invalid_results_recover |
| R03 | Denied storage could crash layout/Vault initialization or leave failed opt-in enabled. Guarded browser storage and roll back failed Vault saving. | test_storage_failure_usable_workspace |
| R04 | Synchronous repeated create clicks could create multiple drafts. Added an immediate creation guard and modal state disabling. | test_m5_repeated_create_click |
| R05 | Reasoning validation exceptions echoed input document metadata. Removed Pydantic input/context/URL details. | backend.xml: test_household_owner_mismatch_rejected_every_intelligence_entry |
| R06 | Late citizen-workflow responses could render after switching workflows. Added generation checks, request deadline and disabled in-flight fields. | test_workflow_stale_response_after_switch |
| R07 | Late assistant replies could repopulate a cleared chat or use superseded evidence. Added generations for reset and document changes. | test_assistant_focus_escape_and_stale_reset; test_cross_milestone_household_assistant |
| R08 | Modal dialogs lacked keyboard focus containment/return. Added shared focus handling and assistant Escape/focus behavior. | test_keyboard_modal_focus_escape; test_assistant_focus_escape_and_stale_reset |
| R09 | An empty optimizer request was reported as one planned path. Return empty with zero candidates. | backend.xml: test_empty_optimizer_has_no_feasible_candidate |
| R10 | Opening a saved preparation without type in its URL could overwrite a reissue as fresh. Fall back to the saved service type. | test_m5_saved_service_not_overwritten_by_missing_url_type |
| R11 | Denied IndexedDB deletion prevented clearing session-only files. Clear memory and show a specific warning about undeleted browser copies. | test_session_clear_when_indexeddb_denied |
| R12 | Malformed/future applicant DOBs were treated as missing or could appear saved. Reject them in the API and block invalid saves in the UI. | test_m5_future_birth_date_not_saved; backend.xml: test_passport_invalid_applicant_birth_dates_rejected |
| R13 | Family-held address candidates lacked an explicit distinction from applicant identity. Preserve possible-proof behavior with permission/category and ownership caveats. | test_m8_owned_payloads_passport_planner_family; backend.xml: test_family_address_candidate_keeps_ownership_caveat |

Thirteen recovery defects fixed. The six fixes recorded in the previous M4–M9 report are preserved and are not counted again. Fixture extraction, working-directory/report repairs and test wait corrections are infrastructure work, not additional application defect counts. A temporary over-strict response validator and several new-test synchronization assumptions were corrected during execution; their failed intermediate runs remain recorded. Family address candidates are legitimate advisory inputs: a test initially forbidding all family address candidates was corrected to require identity exclusion and ownership caveats, rather than removing supported behavior.

## Privacy, responsiveness and limitations

- Chromium contexts are isolated per test. The suite checks runtime errors and synthetic metadata disclosure in console logs. Sanitized fictional request/response captures are aggregated in `evidence/final/requests-responses.json`.
- Vault files and preparation records have separate reversible local-saving choices. Session mode is the default. Storage denial, malformed preparation schemas, missing files, reload, deletion and independent records are exercised. Household graph/member data remain session-only; this is explicitly stated in the interface.
- Applicant, parent and spouse evidence retain owner labels through Passport, planner, family reasoning and AI. Household graph changes invalidate stale analysis. Parent address proof can be a potential proof to review under category conditions; it is not applicant identity or proof of a legally verified relationship.
- Keyboard focus, labels, Escape behavior and modal return focus are tested. Core routes and advanced forms run at approximately 390px and 1440px with horizontal-overflow checks. This is targeted local Chromium/accessibility validation, not WCAG certification or cross-browser/device qualification.
- Screenshot evidence is under `evidence/final/screenshots/`. Visual review samples include the planner, household graph, completed Passport journey and mobile workflow results. Navy hero banners, existing layout and citizen forms are retained.
- Local AI tests cover deterministic grounding, reviewed-evidence restrictions, consent, provider stubs, missing key, malformed output, rate-limit and timeout failure behavior. They do not prove live model accuracy or universal prompt-injection protection.
- Government source citations and stored provenance are exercised. Current rules, historical official versions, live monitoring and legal eligibility are not certified. Compare UI proposals are explicitly hypothetical.

## Remaining blockers and release recommendation

No unresolved critical/high local defect was observed in the executed acceptance set. **Ready for a local hackathon demonstration using fictional data and the disclosed advisory scope.** Live integrations and production release remain subject to `REMAINING_EXTERNAL_DEPENDENCIES.md`.

**Maadhyam M1–M9 LOCAL DEMO ACCEPTANCE: COMPLETE.**

Machine summary: `evidence/final/final-summary.json`. Complete case matrix: `M1-M9_FINAL_TEST_MATRIX.csv`. Setup, changed files, maintenance and commands: `IMPLEMENTATION_HANDOVER.md`.
