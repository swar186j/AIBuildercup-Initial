# M12.1 consolidated release — owner deployment handoff

17 October 2026 (Asia/Kolkata). Branch: `release/m10-m12-recovery`.

**No deployment was executed by this task.** No Cloud Build, image push, Cloud Run/Firebase Hosting deployment, IAM/configuration change, production Firestore mutation or Storage-object operation was executed. The owner-supplied historical revision is `maadhyam-api-00003-t6s`; no traffic changes were requested. This is not a production readback or production acceptance certificate.

## Release and configuration inventory

The final combined release commit is the commit containing this handoff and `M12_1_SERVICE_CATALOGUE_EXPANSION_REPORT.md`. The prior consolidated M12.1 commit is `986984198366c8ffab222eb160558217f7d016d5`. Its exact SHA and successful remote-HEAD comparison are supplied in the final delivery message. From this checkout, obtain the immutable SHA using `git log -1 --format=%H -- qa/M12_1_MANUAL_CLOUD_DEPLOYMENT_HANDOFF.md` and verify against the release branch before deploying.

| Item | Changed / required |
|---|---|
| Frontend | YES — M12.1 fixes plus the final 256-tile Services catalogue, local search, 18 category filters and Load More |
| Backend | YES for M12.1 — deterministic readiness, contextual findings, optional extraction provenance. Backend application source/config is unchanged by the catalogue expansion since `9869841`; two historical browser tests now wait for completed local hydration/upload rendering. |
| Firestore collection paths/database | NO — existing named database `maadhyam`, existing UID-scoped paths |
| Firestore stored document schema | YES, additive only: optional `metadata.extractionSource`: `manual`, `ocr`, `gemini`; legacy defaults to manual. No required field or migration. |
| Application/household/planner schema | NO — existing application snapshots and revisions reused |
| Cloud Storage paths/bucket/configuration | NO — `maadhyam-1610-private-vault`, existing private generation-protected objects |
| Environment variables or Firebase Auth settings | NO |
| Dockerfile/runtime dependencies/lockfiles | NO |
| New backend image needed | YES — the owner must still build/deploy the M12.1 backend image. The catalogue adds no backend change. |
| Services owner updates | Existing Cloud Run service and Firebase Hosting only |
| New infrastructure/data migration | NONE |

The owner must deploy the complete M12.1 backend and latest combined frontend together after review. Build Firebase Hosting from the latest combined Git commit, including the catalogue; do not use the older frontend build. No new endpoints, routes, dependencies, Firestore schema, bucket or environment changes accompany the catalogue. See `M12_1_SERVICE_CATALOGUE_EXPANSION_REPORT.md` for coverage, research, screenshots and regression evidence.

## Owner-only preflight

The commands below are instructions only; they were **not run** by Codex. Use the existing authenticated Google Cloud/Firebase CLIs and existing project permissions. Preserve the current runtime identity, environment, CORS, named Firestore database, private Vault bucket and Vertex settings. Do not replace them from an unverified environment file.

```bash
# Repository root. Verify the delivered commit and clean intended source first.
git branch --show-current
git rev-parse HEAD
git ls-remote origin refs/heads/release/m10-m12-recovery
git diff --check

# Save the existing revision/image/traffic configuration for rollback.
gcloud run services describe maadhyam-api --project=maadhyam-1610 --region=asia-south1 --format=json
```

Record the current Firebase Hosting release/version from its release history. Review the final report and the portable QA receipts before any paid build or deployment. Test fixtures use fictional data; never upload real identity documents as acceptance evidence.

## Owner-only backend build and deployment

Run from `Maadhyam/apps/api`. Reuse the existing repository Cloud Build configuration and registry. Confirm your approved build service account and regional build settings from the existing deployment guide; the command below uses the existing source configuration and does not grant IAM roles.

```bash
RELEASE_SHA=$(git rev-parse --short=12 HEAD)
RELEASE_IMAGE="asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api:m12-1-${RELEASE_SHA}"
gcloud builds submit . --project=maadhyam-1610 --region=asia-south1 --config=cloudbuild.yaml --substitutions="_IMAGE=${RELEASE_IMAGE}"
gcloud artifacts docker images describe "$RELEASE_IMAGE" --project=maadhyam-1610 --format=json

# Replace the placeholder with the newly verified image digest, not an old tag.
IMMUTABLE_IMAGE='asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api@sha256:REPLACE_WITH_VERIFIED_DIGEST'
gcloud run deploy maadhyam-api --project=maadhyam-1610 --region=asia-south1 --image="$IMMUTABLE_IMAGE" --no-traffic --tag=m12-1-review
```

Inspect the new revision's image digest, attached identity and unchanged environment before directing traffic to it. `--no-traffic` keeps production traffic on its existing revision while the owner reviews the tagged revision. After owner acceptance, replace the revision placeholder:

```bash
gcloud run services update-traffic maadhyam-api --project=maadhyam-1610 --region=asia-south1 --to-revisions=REPLACE_WITH_NEW_REVISION=100
```

## Owner-only frontend release

Run `npm ci`, lint and build from `Maadhyam/apps/web` using the existing public Firebase configuration. Keep the API base same-origin for Hosting. Then deploy from `Maadhyam`:

```bash
npm ci
npm run lint -- --max-warnings 0
npm run build
# Change directory from apps/web back to Maadhyam:
cd ../..
firebase deploy --only hosting --project maadhyam-1610
```

Do not deploy Firestore rules, database provisioning or Storage/IAM changes: this release requires none. Verify the existing `/api/**` rewrite still targets `maadhyam-api` in `asia-south1` before publishing.

## Manual production verification — owner only

Use a dedicated fictional test identity and its own test records. These checks were deliberately deferred; this task did not write production acceptance data.

- Discover Passport through landing search; confirm Passport says Guided preview available and Aadhaar/EPFO say Coming Soon. Check all 18 category options, RTO/ITR/PM Kisan searches, combined filters, empty-state reset and Load More. Unsupported cards must have no action. Confirm the existing sidebar, mobile layout and floating assistant remain usable.
- Add and edit a household member; save and wait for actual success. Hard refresh in the **same browser profile/Firebase UID**. Verify UUID, name, relationship, dependencies and member timestamps. Check the selected preparation destination.
- With a network interruption, verify visible failure, unchanged local edits and Retry. Test a second-tab revision conflict without silently replacing newer records.
- Save Passport Step 3; hard refresh and resume the exact preparation ID, applicant/member ID, answers, selected documents, created/last-saved timestamps and wizard step. Repeat with Other/manual applicant and an optional blank DOB.
- Save planner target/checklist progress; refresh. Verify prerequisites and cascade removal. Confirm What-If values, optimizer routes and hypothetical rule proposals remain previews.
- Upload one small fictional Vault document; wait for server acknowledgment, refresh, preview/download, review/edit metadata and confirm owner/source/timestamps. Confirm another test UID cannot list/read/update/delete it.
- Explicitly migrate a fictional IndexedDB file; verify its checksum and retained original. Confirm single deletion and Clear All require confirmation and report partial failures accurately.
- Compare different members and generic unassigned Parent/Guardian records: no personal identity conflict. Check missing name/DOB and provisional extraction remain separate from reviewed differences.
- Check readiness changes after selecting relevant evidence and citizen review; unrelated files must not increase completion. Inspect the displayed formula and pending official-acceptance checks. Readiness is not wizard progress, government approval, submission, appointment booking or official tracking.
- Verify one-version historical comparison is unavailable; a hypothetical proposal is clearly labeled and does not change active rules or source citations.
- Inspect only necessary error logs. Do not log document contents, tokens or private applicant metadata. Paid Gemini accuracy testing is not needed to verify storage or deterministic readiness.

## Rollback

Preserve both the pre-release Cloud Run revision/image and the previous Hosting release. If the owner chooses to roll back traffic, first verify the historical revision still exists:

```bash
gcloud run revisions describe maadhyam-api-00003-t6s --project=maadhyam-1610 --region=asia-south1
gcloud run services update-traffic maadhyam-api --project=maadhyam-1610 --region=asia-south1 --to-revisions=maadhyam-api-00003-t6s=100
```

Use Firebase Hosting release history to roll back the frontend to its recorded prior release. Do not delete Firestore records, household snapshots or Vault objects, reset authentication, rotate UIDs or run a destructive migration.

Compatibility caution: the historical backend's strict metadata model predates optional `extractionSource`. If the new version has saved that field, retain the new backend's optional-field support when reverting problematic behavior; a historical backend may reject later metadata edits containing the new key. Do not remove provenance from production records as an automated rollback workaround. All existing records without that optional key remain supported by this release.

Local limits: anonymous access depends on retained browser authentication, source monitoring does not establish legal rule freshness, and live Gemini accuracy/government acceptance were not tested. The existing Vite bundle-size advisory and Starlette test-client deprecation are recorded in the final report.
