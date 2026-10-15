# All 23 feature areas: implementation and acceptance mapping

Canonical names follow the supplied final recovery request. No independent 23-feature PRD was found in the checkout. Historical `FRONTEND_TEST_CASES.md`, `M4_M9_COVERAGE_TRACKER.md`, `COVERAGE_UPDATE.md` and `M4-M9_ACCEPTANCE_REPORT.md` provide the earlier implementation boundaries; this inventory reconciles them with current executed evidence. COMPLETE means the stated local advisory behavior passed, not that external integrations or the broader real-world product promise exist.

## 1. Document OCR & Intelligent Extraction

- Milestone / local status: **M4 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/extraction.py`.
- Citizen entry: /documents → AI extraction.
- Endpoint: `/api/ai/extract-document`.
- Positive scenario: `test_ocr[success]`.
- Negative scenario: `test_ocr[malformed]`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Provider success is deterministic; live extraction accuracy is NOT TESTED. Manual review is mandatory.

## 2. Indian Name Matching

- Milestone / local status: **M4/M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py → classify_name_variation`.
- Citizen entry: /documents comparison; /planner names.
- Endpoint: `/api/intelligence/analyze; /api/intelligence/reasoning`.
- Positive scenario: `test_reasoning_whatif_family`.
- Negative scenario: `test_unrelated_names_not_accepted`.
- Executed coverage: 2 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Heuristics flag spelling, order and initials; they do not prove that two records identify the same person.

## 3. Government Service Document Checklist

- Milestone / local status: **M3/M5 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/passport_rules.py`.
- Citizen entry: /services/passport/journey.
- Endpoint: `/api/passport/assess`.
- Positive scenario: `test_passport_guided[True]`.
- Negative scenario: `test_passport_guided[False]`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Passport has the implemented source-linked checklist. Other service catalog cards are not equivalent application journeys; rule freshness is external.

## 4. Human-Assisted Application Support

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → human_support`.
- Citizen entry: /workflows → Human assistance.
- Endpoint: `/api/citizen-workflows/human-support`.
- Positive scenario: `test_citizen_workflow[False-human-support`.
- Negative scenario: `test_citizen_workflow[True-human-support`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Maps to helpdesk conversation preparation. No live agent is connected and no helpdesk message is sent.

## 5. Life-Event Based Service Discovery

- Milestone / local status: **M2/M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → life_event_discovery`.
- Citizen entry: /workflows → Life-event discovery.
- Endpoint: `/api/citizen-workflows/life-event-discovery`.
- Positive scenario: `test_citizen_workflow[False-life-event`.
- Negative scenario: `test_citizen_workflow[True-life-event`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: A small caller-supplied illustrative catalog, not a complete official directory.

## 6. Rules-as-Code Engine

- Milestone / local status: **M3 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/passport_rules.py; passport_rules_pack.json`.
- Citizen entry: Passport source-linked requirements.
- Endpoint: `/api/passport/assess`.
- Positive scenario: `test_passport_guided[True]`.
- Negative scenario: `test_invalid_category_rejected`.
- Executed coverage: 2 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Deterministic stored rules and cited sources; no official eligibility or current-rule certification.

## 7. Cross-Document Discrepancy Detection & Rule Citations

- Milestone / local status: **M4/M6 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py; routes/passport_rules.py`.
- Citizen entry: /documents comparison; /planner; Passport citations.
- Endpoint: `/api/intelligence/analyze; /api/passport/assess`.
- Positive scenario: `test_journey_b_identity_whatif`.
- Negative scenario: `test_planner_unexpected`.
- Executed coverage: 5 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Reviewed metadata only; a discrepancy is a review flag, not fraud, legal correction or automatic rejection.

## 8. Dependency-Aware Correction Planner

- Milestone / local status: **M6 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py; routes/reasoning_engine.py`.
- Citizen entry: /planner → Your next steps.
- Endpoint: `/api/intelligence/passport-plan; /api/intelligence/reasoning`.
- Positive scenario: `test_reasoning_whatif_family`.
- Negative scenario: `test_planner_api_failure`.
- Executed coverage: 3 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Dependency order covers preparation tasks, not a verified interdepartmental government process.

## 9. Migrant Address Continuity Builder

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py → addressContinuity`.
- Citizen entry: /planner → Address consistency.
- Endpoint: `/api/intelligence/reasoning`.
- Positive scenario: `test_journey_c_address_continuity`.
- Negative scenario: `test_address_continuity_is_not_inferred_from_two_addresses`.
- Executed coverage: 2 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Maps to address-variant evidence review and continuity follow-up guidance. No dated migration history or legal residency continuity is inferred.

## 10. Multi-Department Rule Packs

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → multi_department_rules`.
- Citizen entry: /workflows → Multi-department guidance.
- Endpoint: `/api/citizen-workflows/multi-department-rules`.
- Positive scenario: `test_citizen_workflow[False-multi-department`.
- Negative scenario: `test_citizen_workflow[True-multi-department`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: The supplied department packs are explicitly illustrative and unverified, not current official rules for all authorities.

## 11. Minimum-Correction Path Optimizer

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/advanced_planning.py; routes/reasoning_engine.py`.
- Citizen entry: /planner → Compare correction paths.
- Endpoint: `/api/intelligence/advanced-plan`.
- Positive scenario: `test_m7_weighted_paths`.
- Negative scenario: `test_m7_optimizer_cycle_invalid`.
- Executed coverage: 3 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Bounded exhaustive combinations with user estimates, sequential durations and explicit unit scaling. No guaranteed official route or fee.

## 12. Identity Evolution Engine

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py → identityEvolution`.
- Citizen entry: /planner → Identity name variations.
- Endpoint: `/api/intelligence/reasoning`.
- Positive scenario: `test_journey_b_identity_whatif`.
- Negative scenario: `test_identity_variants_are_not_officially_verified`.
- Executed coverage: 2 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Maps to observed name variants; legal name-change history is not established.

## 13. Proof Substitution Engine

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py → proofSubstitution`.
- Citizen entry: /planner → Alternative evidence candidates.
- Endpoint: `/api/intelligence/reasoning`.
- Positive scenario: `test_reasoning_whatif_family`.
- Negative scenario: `test_reasoning_capability_contract[True-proofSubstitution`.
- Executed coverage: 2 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Candidates by reviewed category are not officially interchangeable proofs.

## 14. Deadline & Document Expiry Conflict Solver

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py → deadlineRescue`.
- Citizen entry: /documents expiry; /planner target/conflicts.
- Endpoint: `/api/intelligence/reasoning`.
- Positive scenario: `test_journey_d_deadline_dependencies_expiry`.
- Negative scenario: `test_m7_malformed_expiry_conflict`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Printed dates and target dates drive preparation risks; missing expiry remains unknown and official document validity stays unverified.

## 15. Government Rule Change Impact Analyzer

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/rule_change_impact.py; routes/passport_rules.py`.
- Citizen entry: /planner → Review rule changes.
- Endpoint: `/api/passport/rules/versions; /api/passport/rules/compare`.
- Positive scenario: `test_journey_f_rule_saved_preparation`.
- Negative scenario: `test_m7_rule_errors`.
- Executed coverage: 4 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: One stored complete pack is available. Added/removed/modified scenarios are hypothetical and never change active rules. Source hashes are not historical packs.

## 16. Rejection Root-Cause Intelligence

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → rejection_diagnosis`.
- Citizen entry: /workflows → Rejection diagnosis.
- Endpoint: `/api/citizen-workflows/rejection-diagnosis`.
- Positive scenario: `test_citizen_workflow[False-rejection`.
- Negative scenario: `test_citizen_workflow[True-rejection`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Text categories suggest possible causes; only the authority can confirm the rejection reason.

## 17. What-if Application Simulator

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py → simulations`.
- Citizen entry: /planner → Try a correction.
- Endpoint: `/api/intelligence/reasoning`.
- Positive scenario: `test_journey_b_identity_whatif`.
- Negative scenario: `test_simulation_family_invalid_references`.
- Executed coverage: 5 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Hypothetical metadata changes do not mutate source documents or establish official acceptance.

## 18. Bureaucratic Deadlock Detector

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/reasoning_engine.py; routes/advanced_planning.py`.
- Citizen entry: /planner → Dependency diagnostics; optimizer.
- Endpoint: `/api/intelligence/reasoning; /api/intelligence/advanced-plan`.
- Positive scenario: `test_m7_optimizer_cycle_invalid`.
- Negative scenario: `test_optimizer_invalid_weights`.
- Executed coverage: 5 matching cases; qa/evidence/final/backend.xml, qa/evidence/final/browser.xml.
- Boundary / limitation: Detects software dependency cycles and infeasible supplied paths; not a certification of real bureaucratic deadlock.

## 19. Family & Household Dependency Graph

- Milestone / local status: **M8 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/household.py; routes/reasoning_engine.py`.
- Citizen entry: /household → Members, ownership, accessible graph.
- Endpoint: `/api/household/assess; /api/intelligence/reasoning`.
- Positive scenario: `test_journey_e_household_consent_withdrawal`.
- Negative scenario: `test_household_stale_response_after_edit`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: One session workspace; labels/relationships are user claims. No legal verification, household persistence or cross-account authorization.

## 20. Multi-Authority Bottleneck Navigator

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → authority_bottlenecks`.
- Citizen entry: /workflows → Authority bottlenecks.
- Endpoint: `/api/citizen-workflows/authority-bottlenecks`.
- Positive scenario: `test_citizen_workflow[False-authority`.
- Negative scenario: `test_citizen_workflow[True-authority`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Critical-path estimates use user inputs, not verified official processing times.

## 21. Deadline Rescue Engine

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → deadline_rescue`.
- Citizen entry: /workflows → Deadline rescue; /planner target.
- Endpoint: `/api/citizen-workflows/deadline-rescue`.
- Positive scenario: `test_citizen_workflow[False-deadline`.
- Negative scenario: `test_citizen_workflow[True-deadline`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Advisory risk and next steps, no official expedited service or actual deadline guarantee.

## 22. Government Visit Eliminator

- Milestone / local status: **M7 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/citizen_workflows.py → visit_eliminator`.
- Citizen entry: /workflows → Visit reduction planner.
- Endpoint: `/api/citizen-workflows/visit-eliminator`.
- Positive scenario: `test_citizen_workflow[False-visit`.
- Negative scenario: `test_citizen_workflow[True-visit`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Maps to estimated visit reduction with online-availability caveats. No real government visit is claimed eliminated.

## 23. AI-Assisted Preparation and Guidance

- Milestone / local status: **M9 / COMPLETE**
- Backend: `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py → chat; extraction/gemini adapters`.
- Citizen entry: Global Ask Maadhyam AI dialog.
- Endpoint: `/api/intelligence/chat`.
- Positive scenario: `test_journey_g_assistant_grounding_provider_failure`.
- Negative scenario: `test_assistant_focus_escape_and_stale_reset`.
- Executed coverage: 2 matching cases; qa/evidence/final/browser.xml.
- Boundary / limitation: Reviewed applicant grounding and deterministic/local stubs pass. Live Gemini and production prompt-injection resistance are not certified.

