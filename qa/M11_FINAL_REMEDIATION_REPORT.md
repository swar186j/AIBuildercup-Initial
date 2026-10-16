# M11 final remediation — 17 October 2026 (IST)

**Status: COMPLETE.** All P0 stabilization requirements and hosted acceptance checks pass. Billing budget/credit visibility remains a documented permission blocker, allowed by the requested definition of done. No release-blocking functional issue was observed.

## Actual fixes

| File | Finding | Fix | Regression evidence |
|---|---|---|---|
| WorkspaceContext / WorkspaceProvider | Render refs, effect state updates, dependency warnings, mixed exports | Separate context from provider; commit refs in layout effects; stable callbacks; explicit active ID state; subscribed storage failure state | Cloud restore, revisions, consent, delayed local edits and storage retry pass |
| DocumentContext / DocumentProvider | Render ref updates, unused fields, mixed exports | Provider split; layout ref synchronization; explicit persisted DTO fields | Upload, metadata, consent, IndexedDB reload and clear/reload pass |
| HouseholdContext / HouseholdProvider | Effect/dependency/export issues | Stable restore callback; explicit dependencies; edit revision protects local household changes during restore | Distinct holder IDs, ownership consent, removal, self-dependency and cycles pass |
| ResolutionPlanner | Effect state resets, impure render, callback dependencies | Keyed asynchronous resource; stable assessment callback; stale response guard; initialized clock | Dynamic deadlines, target restoration and no duplicate assessment pass |
| GuidedJourney | Mirrored state and missing dependencies | Derive member name; guarded one-time cloud hydration before commit; stable activation/save dependencies; abortable debounced assessment | Selected/Other names, DOB, exact ID, completion and delayed cloud restore pass |
| AIAssistant | Effect reset | Derive thinking from input snapshot; invalidate stale responses after commit | Floating assistant, keyboard focus, reset and stale responses pass |
| ReasoningWorkspace / Services | Synchronous effect resets | Shared keyed request state and explicit retry revision | Loading, malformed/error responses, retry and eight workflows pass |
| HouseholdIntelligence / useDialogFocus | Effect resets / render ref assignment | Input-keyed analysis visibility; committed latest close callback | Household analysis and modal keyboard checks pass |
| DocumentVault / GuidedJourney text | Misleading provider/storage wording | Clarify selected-file transmission and browser-local bytes; current-answer cloud save wording | Hosted extraction UI and refresh/save flows pass |

No lint configuration, TypeScript strictness, backend source, layout, styles, navigation, rule engines or database schema changed. No new suppressions or `any` substitutions were introduced. Before/after lint summary: [evidence](evidence/m11-remediation-lint-summary.json).

## Fresh validation

| Check | Result |
|---|---|
| ESLint | **0 errors, 0 warnings**, `npm run lint -- --max-warnings 0` |
| TypeScript / Vite | PASS; existing advisory about bundle size >500 kB remains |
| Backend | **409 passed, 0 failed**, one existing Starlette deprecation warning |
| Local browser / HTTP | **195 passed, 0 failed**: original 190 plus five focused state/persistence regressions |
| Hosted release | **26 passed**: 24 real hosted checks and two explicitly mocked provider/UI checks |
| Hosted references | PASS: reissue type, exact document IDs, empty optional DOB, stable UID and consented Vault reload |
| Live security subset | **7 passed**, included in the 26: missing/malformed token, cross-user GET/PATCH/DELETE, direct Firestore isolation, revision conflict |
| New actual Gemini calls | **0**; comprehensive mocked checks avoid paid calls |

JUnit: [backend](evidence/m11-remediation-backend.xml), [local](evidence/m11-remediation-green/tests.xml). Hosted: [cases](evidence/m11-remediation-hosted/results.json), [references](evidence/m11-remediation-hosted-references.json). The earlier failed full run was a new test's Playwright injection error; it was corrected, all five targeted tests passed, and the complete 195-case suite was rerun green. No tests were removed.

Real Vertex chat/extraction success is historical evidence in the initial M11 reports, not a new live-provider test. Provider/backend implementation, model and Cloud Run revision remain unchanged. New hosted AI UI cases are labeled mocked and do not claim new model inference. No uncaught browser errors or localhost requests were observed. Only new fictional test records were created/updated; no existing user records, identities or Vault data were reset.

## Deployment and source consistency

- Frontend: https://maadhyam-1610.web.app
- Hosting release: `sites/maadhyam-1610/releases/1792177518101000`
- Hosting version: `sites/maadhyam-1610/versions/cf7df81ce2fc24a9`
- Tested/deployed source checkpoint: `5b87bfe05d63da4f0b29085613d1f10a0d4f3ad9`.
- Every hosted build file matched local SHA-256; [deployment receipt](evidence/m11-remediation-deployment.json).
- Backend: https://maadhyam-api-767722654590.asia-south1.run.app
- Unchanged Cloud Run revision: `maadhyam-api-00002-grr`; backend source `06c59cb1c94437907af7075f86dd6bc86c0d4242`.
- Unchanged image: `sha256:22997ae55fff8471d0a518b9e598d61d563487dfbd580ffbd6c9fe2342a06aac`.
- Project `maadhyam-1610`, region `asia-south1`, Firestore named database `maadhyam`, Vertex `gemini-2.5-flash` in `global`.
- Minimum instances **0**, maximum **2** at service/revision levels; concurrency 4, timeout 55s, 512Mi, CPU 1.
- **No backend build, Cloud Run deployment, new infrastructure or paid AI call.** Only Firebase Hosting was deployed. Previous Hosting version remains the rollback target; no rollback performed.

## Billing and repository audit

Billing is enabled and linked to `016C3C-CA523C-27545A`. Budget reads return `PERMISSION_DENIED`; credit balance, expiry, current charges and alert recipients/thresholds are not verified. Owner-reported ₹28K credit is not treated as independently confirmed. Exact owner actions: [billing handoff](M11_BILLING_OWNER_ACTIONS.md). Minimum zero scales idle Cloud Run to zero; it and budget alerts are not hard currency caps. Two existing registry images were observed; neither was deleted.

Initial local and remote release HEAD both matched `e9906c5301521dd3cb093ae29af288dfffe5922d`. The pre-existing dirty `.demo/tunnel.err.log` was preserved and excluded. Backend diff is empty. Staged files were reviewed for credentials/tokens, private keys, uploads, profiles and unrelated diagnostics; only portable sanitized evidence is committed. Public Firebase client configuration remains legitimate client configuration.

Root README now explains the actual product, architecture, setup, demo, limitations and source branch. GitHub default branch is still `main` at `b1c0cdcdc055b285933b63ec91eddf7adaa9e425`, containing only `test`. Judge-facing source: [release branch](https://github.com/swar186j/AIBuildercup-Initial/tree/release/m10-m12-recovery). Owner may choose this release as default or review a safe integration PR later; neither change was performed. The final documentation commit follows the deployed source checkpoint and changes no application assets. Final local/remote HEAD equality is verified after push and reported in the handoff response; this report avoids a self-referential commit hash.

## M12 handoff and remaining limits

No observed release blocker remains. Non-blocking prototype limits: anonymous identity depends on retained browser storage; files do not move across devices; rate counters are per-instance; official rule/source freshness needs human review; no government submission/approval integration exists. Account recovery, durable distributed limiting and additional integrations remain future work.

M12: use the release-branch link, record a short fictional-data demo showing Passport name restoration, household holder consent and deadline changes, select sanitized screenshots, and complete submission fields. The owner should independently verify billing credits and budget notifications. No architecture expansion is required for submission.
