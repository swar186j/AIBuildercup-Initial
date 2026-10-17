# Maadhyam UI/UX deployment and smoke test report

Branch: `release/m10-m12-recovery`. Baseline: `4efdb011e4b82b8b55429f290ae16295c5e30df9`.

Deployment gate: required local correctness checks must pass, source commit must be pushed, and rollback references must be recorded before Hosting deployment. npm audit findings are documented separately in the correction report; no breaking dependency changes are authorized by an audit finding.

## Recorded production state and rollback

Cloud Run `maadhyam-api` / `asia-south1`: revision **maadhyam-api-00004-xay**, **100%** traffic. Runtime identity `maadhyam-api@maadhyam-1610.iam.gserviceaccount.com`. Image:

`asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api@sha256:792a773d6ad164e24f26d3a4f6d02b8d2f8572397f0e363e70bb4bef1fa0dd73`

Prior successful Cloud Build **1fce4cf6-2013-43af-bfe3-89321bc6fd97** produced that exact digest, tagged `m12-1-4efdb011e4b8`, matching the release baseline. This correction changes no backend source, dependency or server-side contract, so a new backend build/deployment is unnecessary. No Cloud Run environment, service account, IAM, Firestore database (`maadhyam`), private storage configuration or traffic is changed.

Firebase Hosting rollback reference:

- Release: `sites/maadhyam-1610/releases/1792245340672000`
- Version: `sites/maadhyam-1610/versions/07aec11b7a59fa53`
- Released: `2026-10-17T13:55:40.672Z`

The release API required the explicit `x-goog-user-project: maadhyam-1610` quota header; retrying with it succeeded. Rollback receipts: `hosting-before.json`, `cloud-run-before.json`, `backend-deployed-build.json` under `qa/evidence/ui-ux-corrections/`.

If rollback is needed, use Firebase Console → Hosting → Release history → the above previous release → Roll back. The supported Hosting REST release-create operation may also release that existing version. Do not alter Firestore or Storage data. Cloud Run is unchanged; if a later backend incident requires restoring its recorded revision:

```sh
gcloud run services update-traffic maadhyam-api --project=maadhyam-1610 --region=asia-south1 --to-revisions=maadhyam-api-00004-xay=100
```

## Release and live results

Deployed source commit: **3a3e7fb858777a7542418914acc4cafa33757d70**. The exact remote release ref matched after its fast-forward push. All implementation fixes were consolidated in that commit with message `Polish dashboard, AI suggestions and hierarchical services UX`. Any subsequent QA/report commit records delivery evidence and does not alter the deployed application source.

All local correctness gates passed: zero-warning lint; TypeScript/Vite build; 463 backend tests; 284 browser/catalogue tests; 18 HTTP tests; all five historical browser runners; 59 focused tests after the final compact-toggle adjustment. `npm ci` succeeded with Firebase 13.0.0. Audit reports four existing high findings; no downgrade or forced fix was applied. Full details and exact modified source/QA files are in [the correction report](FINAL_UI_UX_CORRECTIONS_REPORT.md).

After the push, the frontend was rebuilt from the committed source and every output file SHA-256 matched the validated bundle recorded in `final/gates.json`. Then the following completed successfully:

```sh
cd Maadhyam
npx --yes firebase-tools deploy --only hosting --project maadhyam-1610
```

Hosting **VERIFIED**:

- Site: https://maadhyam-1610.web.app/
- Release: `sites/maadhyam-1610/releases/1792263366634000`
- Version: `sites/maadhyam-1610/versions/91190d38b5e68edd`
- Release time: `2026-10-17T18:56:06.634Z` (18 October 2026, 00:26:06 IST).
- Receipt: `qa/evidence/ui-ux-corrections/hosting-after.json`; deployment log: `final/firebase-deploy.log`.

Cloud Run **VERIFIED UNCHANGED**: `maadhyam-api-00004-xay` serves 100%, retaining the `m12-1-review` tag and recorded digest. No new Cloud Build ID exists because no backend build was needed. Post-deployment service inspection is saved in `final/cloud-run-after.json`.

Fresh-profile live smoke: **23 checks PASS**, command:

```sh
Maadhyam/apps/api/.venv/bin/python qa/verify_ui_ux_hosted.py
```

| Live check | Observed result |
|---|---|
| Firebase rewrite health and protection | `/api/health` 200; unauthenticated POST `/api/ai/connection-test` 401. |
| Dashboard | Exactly one hero CTA; both semantic heading lines; Quick links; Services navigation works. |
| Catalogue | Family cards, Aadhaar expansion, existing Passport navigation. |
| Searches | Aadhaar, PVC, birth certificate, driving licence, PAN and Passport all show the intended family and applicable child. |
| Assistant | Services, Household and Workflow contextual questions produce relevant local answers; collapse/expand works; free-form Passport preparation question gives grounded guidance. |
| Shared content boundaries | Dashboard/Vault/Workflows/My Preparations/Planner/Household match at 375, 768, 1024, 1280, 1440 and 1920px; no horizontal overflow. |
| Vault | Fresh authenticated private list returns 200; fictional session-only upload renders without enabling cloud saving. |
| Household | Fictional member can be added in the fresh session; no cloud save requested. |
| Runtime/network | No uncaught JavaScript errors or failed UI API responses. |

Machine-readable live results: [hosted/results.json](evidence/ui-ux-corrections/hosted/results.json). Hosted assistant screenshots: `hosted/services-assistant.png`, `hosted/household-assistant.png`, `hosted/workflows-assistant.png`. Release identity and bundle-match receipt: [release.json](evidence/ui-ux-corrections/release.json).

The initial hosted run stopped on a strict locator matching the suggestion chip and submitted question simultaneously. The test was scoped to the message scroller, strengthened to assert response text, and rerun successfully. No product regression or rollback was required.

## Explicit limitations and manual checks

- **BLOCKED: physical-device virtual keyboard verification.** Chromium 375×400 viewport checks pass, including un-clipped panel header/composer and collapse/history/focus. A physical keyboard-opening interaction is unavailable in this desktop QA environment. Manual check: on a phone, open the assistant, focus the composer, expand/collapse suggestions, type a long message, close with the header control and reopen; confirm input and conversation remain usable.
- **BLOCKED: production cloud-write smoke.** The request forbids automated mutations of production citizen records. Cloud Vault listing was verified under a fresh account, and upload/preparation/household persistence, consent, identity isolation, restore, conflicts and acknowledgements are covered by isolated fictional local regressions. No production Firestore record or Storage object was created, deleted or overwritten. An owner may separately run a consented synthetic cloud round trip in a non-production test project.
- No paid Gemini requests, physical government submissions, official eligibility verification or application tracking were performed or claimed.
- Existing npm audit findings and Vite bundle-size/Starlette deprecation advisories remain documented. Firebase 13 and locked dependencies are preserved.

UX-01 through UX-05 pass automated local checks and applicable hosted smoke checks. UX-06 automated checks pass with the physical-device keyboard/cloud-write limits explicitly recorded above. There is no unreported deployment blocker; Hosting release and the unchanged serving Cloud Run revision are verified.
