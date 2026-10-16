Current storage target: private Google Cloud Storage, replacing Supabase. Follow docs/GCS_MIGRATION.md for bucket IAM/privacy and verified source preservation. Supabase settings below are temporary migration-source settings only.

# Deployment runbook

Status: PARTIAL. Offline configuration is validated; no public revision is claimed. Run from the repository root.

## Prepare and review

1. Run `python scripts/validate_deployment.py`, the backend pytest suite, frontend lint/build and `qa/m10/run_browser.py --m12` using the API Python. The browser suite needs Vite on 127.0.0.1:5173 and Playwright Chromium. It uses isolated synthetic auth/storage, not the user's account.
2. Review `qa/CLOUD_COST_AND_OPERATIONS.md`. Obtain explicit approval for billing and the deployment. No setup command in this repository automatically enables billing or services.
3. In project `maadhyam-1610`, verify Cloud Run, Artifact Registry, Cloud Build, Secret Manager, Firestore and Firebase Hosting availability. Create an Artifact Registry Docker repository `maadhyam` in `asia-south1` only after approval.
4. Create a dedicated runtime service account with Secret Manager accessor on only `maadhyam-gemini-key` and `maadhyam-supabase-key`. Store the existing provider secrets through the secure Console; do not put them in command arguments or commit them. Do not grant Editor/Owner to the runtime identity.
5. Configure a deployment identity with the necessary narrowly scoped build, Artifact Registry write, Run deployment, runtime service-account use, Hosting and Firestore rules deployment permissions. For optional legacy admin mode, Firestore roles/datastore.user is additionally required. Configure GitHub OIDC workload identity restricted to this repository and production environment; avoid exported keys. Review the Cloud Build identity's repository permissions separately.
6. Configure GitHub's `production` environment with required reviewers, GCP_WORKLOAD_IDENTITY_PROVIDER, GCP_DEPLOY_SERVICE_ACCOUNT, GCP_RUNTIME_SERVICE_ACCOUNT, SUPABASE_URL and the four public VITE_FIREBASE_* configuration variables used by the deployment workflow. Firebase web configuration is public; never place Supabase or Gemini secrets in VITE_*.
7. Confirm the Supabase `maadhyam-documents` bucket is private. Add the exact Hosting domain to Firebase Authentication's authorized domains and verify email/password authentication is enabled. The reviewed owner-only rules have been explicitly approved and published; preserve them for user-rest runtime.

## Deploy

The Cloud Run workflow is currently disabled pending active free-trial-credit verification and project linkage. After that verification, use the manually triggered `Approved cloud deployment` workflow on a reviewed commit. Its explicit cost_approval input must be APPROVED and the protected production environment must approve. It verifies tests/build, builds the container, deploys Cloud Run and then Hosting with pinned revision routing. It does not create a billing account, budget, workload identity or secrets for you.

Equivalent reviewed local deployment: authenticate the Cloud SDK, export COST_APPROVED=APPROVED, RUNTIME_SERVICE_ACCOUNT, GCS_BUCKET, GEMINI_MODEL and TRIAL_CREDIT_CONFIRMED=true, then run `bash scripts/deploy.sh` from the root. Build the frontend with public Firebase configuration, then `npx firebase-tools@15 deploy --only hosting,firestore --project maadhyam-1610`. Never run deployment from a dirty or unreviewed commit.

Cloud Run settings: region asia-south1, 1 CPU, 512 MiB, concurrency 8, min instances 0, max instances 1, request timeout 55 seconds. The public service accepts platform traffic; protected application routes and production AI verify Firebase tokens. The `/api/**` Hosting rewrite precedes SPA fallback and pins the backend revision. Firebase Hosting's 60-second timeout is why the API uses a shorter timeout ([official documentation](https://firebase.google.com/docs/hosting/cloud-run)).

## Acceptance and rollback

Run `python scripts/hosted_smoke.py --url https://maadhyam-1610.web.app`. This checks public pages and anonymous rejection only. Separately execute `docs/DEMO_SCRIPT.md` with two synthetic Firebase accounts against the public URL, record revision/commit and results, then clean up test data. Do not substitute the synthetic local browser suite for real hosted auth acceptance.

Before changing traffic, record the existing Run revision and Hosting release. Use Cloud Run's Revisions page to route 100% back to the known-good revision; roll back the paired Firebase Hosting release in its release history so pinned routing matches. Do not roll back Firestore data blindly; preserve/export before a schema change and use an explicit migration plan. No schema-destructive migration is included here.
