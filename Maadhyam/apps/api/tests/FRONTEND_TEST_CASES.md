# Maadhyam — Frontend Test Cases (M4–M9)

**Scope:** Browser smoke tests for the latest frontend, including Batch 2 `GuidedJourney.tsx` and `ResolutionPlanner.tsx`.

**Safety:** Use only fictional data. The runner does not call Gemini, submit government applications, or upload personal documents. It checks browser behavior against the local Vite/FastAPI servers.

## Automated browser cases

| ID | Area | Steps | Pass criteria |
|---|---|---|---|
| FE01 | Dashboard | Open `/` | Dashboard renders without 404 |
| FE02 | Document Vault | Open `/documents` | Vault heading and accessible file upload control exist |
| FE03 | Vault upload | Upload generated 1×1 fictional PNG | Filename visible; document starts needing review |
| FE04 | Passport Journey | Open `/services/passport/journey` | Passport content renders without 404 |
| FE05 | Resolution Planner | Open `/planner`, wait for API response | API-driven steps and document situation render; duplicate old demo banner absent |
| FE06 | AI Assistant | Open assistant on Planner, send “Show my documents” | Assistant dialog and submitted message appear |
| FE07 | Frontend stability | Navigate four core routes | No uncaught JavaScript page exceptions |

## Manual integration / acceptance cases (not automated by this runner)

| ID | Milestone | Scenario | Expected |
|---|---|---|---|
| MA01 | M4 | Upload fictional PNG/PDF, manually edit holder/name/DOB/address and mark reviewed | Reviewed metadata persists during navigation in the same tab |
| MA02 | M4/M6 | Two self-held reviewed fictional documents with different name spellings | Planner flags possible name discrepancy; never decides which spelling is correct |
| MA03 | M5 | Open Passport Journey after reviewing documents | Journey reads reviewed Vault context, without declaring official eligibility |
| MA04 | M6/M7 | Inspect suggested preparation steps after mismatch | Tasks show reasons and prerequisites; no automatic government-status update |
| MA05 | M8 | Mark one document as parent/guardian or spouse | Family-held identity is not silently treated as the applicant's identity |
| MA06 | M9 | Ask assistant about a mismatch | Assistant uses reviewed metadata or clearly says it lacks evidence |
| MA07 | Privacy | Reload the browser | In-memory Vault documents disappear as disclosed; do not expect persistence yet |
| MA08 | Safety | Use Gemini toggle only with fictional data and explicit consent | No automatic Gemini upload from merely opening a page |
| MA09 | Responsive | Open at 390px width | Assistant opens/closes; primary controls remain usable without covering critical form actions |
| MA10 | Backend integration | Stop API, visit planner | Visible error instead of fake readiness or stale success |

## Interpretation

Automated smoke success does **not** prove full M4–M9 completion. It verifies routes, key controls, basic browser stability, and API-driven planner rendering. Full document extraction, Gemini grounding, persistence, accessibility, rules accuracy, and end-to-end family reasoning need separate tests.

## Reporting

Share `frontend-test-results.json` plus `uv run pytest -q` and `npm run build` results. The runner exits with code 0 when all cases pass, 1 for failed cases, 2 for setup/browser errors.
