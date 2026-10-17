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

Pending local QA completion; no deployment success is claimed by this pre-deployment checkpoint. Exact source SHA, push receipt, Hosting release and smoke results will be appended after execution. The implementation commit can be resolved with `git log -1 --format=%H -- Maadhyam/apps/web/src/data/assistantGuidance.ts`; any later evidence-only commit does not change the deployed frontend bundle.
