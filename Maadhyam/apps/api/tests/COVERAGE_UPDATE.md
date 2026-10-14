# Maadhyam M4–M9 Coverage Update — Batch 3

**Observed user-reported baseline:** 99 backend tests passed, 7 frontend smoke tests passed; one non-failing backend warning. **New batch status:** not run on user's machine.

| Coverage area | Batch 3 tests | Status |
|---|---|---|
| M4 fictional metadata, review gate, mismatches | E2E-01–06, 17–18 | New automated checks, not yet executed |
| M5 fresh/reissue/minor branches | E2E-09 | Branch tests only; official rule completeness pending |
| M6 planner dependencies | E2E-10, 15 | New automated checks, not yet executed |
| M7 conservative what-if and deadline | E2E-11, 16 | New automated checks; real optimizer/deadlock pending |
| M8 family document isolation | E2E-07–08 | New automated checks; relationship proof pending |
| M9 assistant local assessment and consent | E2E-12–14 | New automated checks; Gemini grounded response pending |
| Full browser/document journey | Not covered by this batch | Pending |

**Known limitation:** Duplicate document IDs currently appear accepted by the intelligence endpoint. E2E-17 records the current behavior, not a successful security validation. **No real document files or Gemini network calls** are used in this batch.

Next priorities: actual fictional PDF/image extraction, browser upload-to-chat workflow, duplicate-ID validation, source-grounded passport rules, adversarial assistant tests.
