# Maadhyam Phase 2C — install

Copy files to these exact destinations:

- `passport_rules.py` → `apps/api/src/maadhyam_api/routes/passport_rules.py` (replace)
- `passport_rules_pack.json` → `apps/api/src/maadhyam_api/routes/passport_rules_pack.json` (new)
- `passport_source_monitor.py` → `apps/api/src/maadhyam_api/routes/passport_source_monitor.py` (new)
- `main.py` → `apps/api/src/maadhyam_api/main.py` (replace; same as step 1)
- `test_passport_rules.py` → `apps/api/tests/test_passport_rules.py` (replace existing step-1 tests)
- `test_passport_official.py` → `apps/api/tests/test_passport_official.py` (new)
- `passportAssessment.ts` → `apps/web/src/services/passportAssessment.ts` (new)
- `GuidedJourney.tsx` → `apps/web/src/pages/GuidedJourney.tsx` (replace; IMPORTANT: generated from previously uploaded Maadhyam.zip, compare with current file first if it has newer edits)

From `apps/api`: `uv run pytest -q` and `uv run python -m maadhyam_api.routes.passport_source_monitor`
From `apps/web`: `npm run build` and `npm run dev`.

## Source freshness & safety

Monitor detects changed/unreachable official pages, but DOES NOT auto-update the legal rules. Blind auto-updating is unsafe: HTML banners, redirects and site design changes do not necessarily mean a legal rule changed. Status remains `review-required` until a person reviews official changes and updates the rule pack. The monitor creates `passport_source_state.json` on first run. The first run is `unreviewed-baseline`, not automatically approved. To approve a baseline, compare the actual downloaded government documents with the rules, then set each `baseline_sha256` to the corresponding `observed_sha256` in the state file. Re-run monitor; `current` only if source hashes match. Schedule monitor daily (cron / Cloud Scheduler + secured Cloud Run Job). Do not expose a public rule-edit or baseline-approval API. For reliable deployment, persist monitor state outside the ephemeral Cloud Run filesystem (Cloud Storage), configure `MAADHYAM_PASSPORT_SOURCE_STATE` accordingly, and alert on `review-required`. This prototype is NOT yet wired to persistent cloud storage or alerts.

Document type matching is an advisory candidate match, not a guarantee: scanned contents, issuing authority, full DOB, validity, applicant identity, current address and case-specific conditions require additional validation. Missing or uncertain rules fail closed to `needs-confirmation`.
