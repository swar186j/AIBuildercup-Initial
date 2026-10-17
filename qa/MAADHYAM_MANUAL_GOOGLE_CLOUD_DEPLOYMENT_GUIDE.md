# Maadhyam manual Google Cloud deployment guide

17 October 2026, Asia/Kolkata. Release branch: `release/m10-m12-recovery`.
This is a reproducible procedure; the M12 report records which operations were actually executed and their receipts. Do not interpret instructions below as deployment evidence.

## A. Console walkthrough

1. Open [Google Cloud Console](https://console.cloud.google.com/), click the project selector in the top bar, search for **maadhyam-1610**, and select its project ID (rather than a similarly named project).
2. Navigation menu → **APIs & Services → Enabled APIs & services**. Inspect Cloud Run Admin, Cloud Build, Artifact Registry, Firestore, Cloud Storage, Identity Toolkit and Vertex AI. Reuse enabled APIs. Only enable an API if a deployment operation requires it.
3. Navigation menu → **Firestore → Databases → maadhyam → Data**. Explicitly choose `maadhyam`, never `(default)`. Inspect `users / <verified Firebase UID> / applications / <LOCAL-ID>` and `users / <UID> / documents / <UUID>`. Household members remain inside an application's `household_state.members` array. Do not create a duplicate household collection.
4. Vault timestamps: `createdAt` is the initial metadata reservation, `uploadedAt` is the successful object/final-metadata commit, and `updatedAt` is the last successful change. Pending records do not have `uploadedAt`. `originalLocalAddedAt` is the original browser timestamp supplied during migration; it is not a server upload time.
5. Application timestamps: existing `created_at`, `updated_at` remain backward compatible. New `lastSavedAt` records successful persistence. New writes use Firestore server timestamps. Old ISO strings still load. Nested household `createdAt`/`updatedAt` are client-recorded UTC ISO timestamps. The enclosing application's server `lastSavedAt` confirms when that snapshot was saved; it does not prove the client's clock was correct. Missing legacy values remain **Not recorded**.
6. Navigation menu → **Cloud Storage → Buckets → private Vault bucket → Objects**. Paths are `users/<UID>/documents/<UUID>/original`. Open **Configuration** to inspect location (`asia-south1`), Standard class, uniform access, public access prevention, soft delete, retention and lifecycle configuration. Open **Permissions**, switch to IAM view, and inspect runtime account access. There must be no `allUsers` or `allAuthenticatedUsers` object access.
7. **Artifact Registry → Repositories → maadhyam-api (asia-south1) → maadhyam-api**: inspect immutable release tag, digest and creation time.
8. **Cloud Build → History**, select region `asia-south1`, select the build ID, inspect build logs and test/push steps. A failed build is not a deployment.
9. **Cloud Run → Services → maadhyam-api → Revisions**: inspect image digest, service account, environment, CPU/memory/concurrency, revision min/max instances and traffic percentages. **Logs** opens Logs Explorer for that service/revision. Do not copy tokens or document contents into logs or reports.
10. [Firebase Console](https://console.firebase.google.com/) → **maadhyam-1610 → Hosting → Release history**: inspect the live version and prior releases. This is Firebase Hosting, not Firebase App Hosting. Authentication → Users shows anonymous UIDs; do not delete existing users.
11. Google Cloud **Billing → linked billing account → Reports / Cost table / Credits / Budgets & alerts**: filter project `maadhyam-1610`. Inspect Storage capacity/operations/egress, Run requests, Artifact Registry and build charges. An IAM denial means costs/credits are unverified. Instance limits and alerts are not hard spending caps.

## B. CLI setup and read-only inventory

Install Git, Node/npm, Python 3.13+, uv, Google Cloud CLI, and the Firebase CLI version used by the release. Run from the repository root in PowerShell. These variables are local shell variables, not credentials.

```powershell
$Project = 'maadhyam-1610'
$Region = 'asia-south1'
$Runtime = 'maadhyam-api@maadhyam-1610.iam.gserviceaccount.com'
$Repo = (Get-Location).Path
$Bucket = 'maadhyam-1610-private-vault'
gcloud auth login
gcloud config set project $Project
gcloud auth list --filter=status:ACTIVE
gcloud projects describe $Project
gcloud services list --enabled --project=$Project
gcloud iam service-accounts describe $Runtime --project=$Project
gcloud firestore databases describe --database=maadhyam --project=$Project
gcloud artifacts repositories describe maadhyam-api --location=$Region --project=$Project
gcloud storage buckets list --project=$Project
gcloud run services describe maadhyam-api --region=$Region --project=$Project --format=json
```

`auth login` authorizes the CLI; `config set` selects a default, while explicit `--project` guards the commands. The remaining commands verify resources and permissions without creating them. Inspect the service output to record current traffic revision, image, service identity and environment before changes. Avoid broad Owner/Editor grants to resolve access errors.

For **local Python cloud integration tests only**, use Application Default Credentials:

```powershell
gcloud auth application-default login
gcloud auth application-default set-quota-project $Project
```

ADC lets local Google libraries authenticate. Cloud Run uses its attached runtime service account automatically; never generate a service-account JSON key or copy ADC into the image/frontend/repository. Firebase client configuration is public web configuration; it does not grant server permissions.

## C. Private bucket and IAM (one-time, after local release gates)

First inspect existing buckets. Reuse a suitable dedicated private Vault bucket if one exists; do not repurpose the build-source bucket. The name below is a candidate until creation/readback is documented in the M12 report. Bucket names are globally unique. A `403` when describing a name is not evidence that the name is available; resolve the denial before proceeding. Only create after absence is established.

```powershell
gcloud storage buckets describe "gs://$Bucket" --project=$Project
# Only if absent and no existing suitable private Vault bucket exists:
gcloud storage buckets create "gs://$Bucket" --project=$Project --location=$Region --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention --soft-delete-duration=0
gcloud storage buckets add-iam-policy-binding "gs://$Bucket" --member="serviceAccount:$Runtime" --role=roles/storage.objectUser --project=$Project
gcloud storage buckets describe "gs://$Bucket" --project=$Project --format=json
gcloud storage buckets get-iam-policy "gs://$Bucket" --project=$Project --format=json
```

Creation selects one regional Standard bucket with uniform access and enforced public access prevention. Disabling soft delete avoids silently retaining deleted identity-file copies and their storage charges; user-confirmed deletion is permanent. No retention lock, replication expansion or active-document deletion lifecycle is added. Bucket-scoped Object User permits object read/create/update/delete required by the backend; no project Storage Admin role is granted. The readbacks must confirm the intended private configuration. Do not grant public access to work around an API failure.

Capacity, create/read/list/delete operations, data transfer and retained copies can incur charges; a small fictional acceptance fixture has negligible capacity but does not establish a spending cap. Check actual rates and trial credits in Billing before broader usage. See [Storage pricing](https://cloud.google.com/storage/pricing).

## D. Local gates and backend build

Preserve unrelated changes. The supplied working tree includes an unrelated user edit in `test_cloud_applications.py`; do not stage it accidentally.

```powershell
git status -sb
git branch --show-current
git fetch origin
git diff --check
Set-Location "$Repo/Maadhyam/apps/api"
uv sync --extra dev
uv run --extra dev python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed' }
Set-Location "$Repo/Maadhyam/apps/web"
npm ci
npm run lint -- --max-warnings 0
if ($LASTEXITCODE -ne 0) { throw 'Lint failed' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
Set-Location $Repo
# Use the virtualenv interpreter with Playwright and its Chromium installed:
$env:MAADHYAM_RELEASE_QA_OUTPUT = 'qa/evidence/manual-release'
& "$Repo/Maadhyam/apps/api/.venv/Scripts/python.exe" qa/run_release_local.py qa/test_http.py qa/test_browser.py qa/test_completion.py qa/test_final_journeys.py qa/test_remediation.py qa/test_m12_persistence.py
if ($LASTEXITCODE -ne 0) { throw 'Browser gates failed' }
```

The QA runner starts owned temporary API/preview servers, uses fictional mocked Firebase auth for local browser checks, and avoids real Gemini calls. Its proxy uses the runner's temporary API address. For Linux/macOS the interpreter is `.venv/bin/python`; use `export MAADHYAM_RELEASE_QA_OUTPUT=qa/evidence/manual-release`. Never deploy while any release-blocking check is failing.

Review intended files, run a credential scan, stage explicit paths, commit and push only `release/m10-m12-recovery`. Confirm local `git rev-parse HEAD` equals `git ls-remote origin refs/heads/release/m10-m12-recovery`. Do not force-push, merge main, or change the default branch.

Set `MAADHYAM_DOCUMENT_BUCKET` in `runtime.env.yaml` to the verified bucket. Preserve Vertex model/location/key configuration, named Firestore, CORS and production settings. The backend image has a non-root runtime and excludes `.env`, credentials, uploads and local caches. Build from the committed tested source:

```powershell
Set-Location "$Repo/Maadhyam/apps/api"
$Commit = (git rev-parse --short=12 HEAD).Trim()
$Image = "asia-south1-docker.pkg.dev/$Project/maadhyam-api/maadhyam-api:m12-$Commit"
gcloud builds submit . --project=$Project --region=$Region --config=cloudbuild.yaml --substitutions="_IMAGE=$Image" --service-account="projects/$Project/serviceAccounts/767722654590-compute@developer.gserviceaccount.com" --default-buckets-behavior=regional-user-owned-bucket --quiet
if ($LASTEXITCODE -ne 0) { throw 'Cloud Build failed' }
gcloud builds list --project=$Project --region=$Region --limit=5
gcloud builds log BUILD_ID --project=$Project --region=$Region
gcloud artifacts docker images describe $Image --project=$Project --format=json
```

The build uses the existing regional Cloud Build and Artifact Registry workflow, tests the container health and unauthenticated AI rejection, then pushes. Replace `BUILD_ID` with the just-returned ID, inspect its successful result, and obtain the digest from the registry description. Never reuse an old release digest in a new build command.

Bash equivalents for build variables: `Commit=$(git rev-parse --short=12 HEAD)` and `Image="asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api:m12-$Commit"`; use `"$Image"` in the same gcloud commands. Use the exact commit tested and pushed, not an unrelated checkout.

## E. Controlled Cloud Run deployment

Before deployment save a read-only `gcloud run services describe ... --format=json` snapshot and the current Firebase Hosting release/version. Verify that the image digest corresponds to the tested source tag. Deploy with the **newly observed digest**, leaving old revisions intact:

```powershell
# Replace NEW_VERIFIED_DIGEST with the new image's sha256:... value.
$ImmutableImage = "asia-south1-docker.pkg.dev/$Project/maadhyam-api/maadhyam-api@NEW_VERIFIED_DIGEST"
gcloud run deploy maadhyam-api --project=$Project --region=$Region --image=$ImmutableImage --service-account=$Runtime --env-vars-file=runtime.env.yaml --min=0 --max=2 --min-instances=0 --max-instances=2 --cpu=1 --memory=512Mi --concurrency=4 --timeout=55 --cpu-throttling --no-cpu-boost --execution-environment=gen2 --allow-unauthenticated --quiet
if ($LASTEXITCODE -ne 0) { throw 'Cloud Run deploy failed' }
gcloud run services describe maadhyam-api --project=$Project --region=$Region --format=json
gcloud run revisions list --service=maadhyam-api --project=$Project --region=$Region
gcloud run services get-iam-policy maadhyam-api --project=$Project --region=$Region
Invoke-RestMethod 'https://maadhyam-api-767722654590.asia-south1.run.app/api/health'
```

Zero minimum and two maximum instances preserve cost bounds at service and revision levels. Public HTTP invocation allows Firebase Hosting to forward requests, while all Vault/application operations still require valid Firebase ID tokens. Inspect the attached runtime account, `MAADHYAM_FIRESTORE_DATABASE_ID=maadhyam`, Vault bucket, unchanged Vertex configuration, traffic and image digest. CLI exit code alone is insufficient. Test missing-token rejection, authenticated small fictional upload/list/preview/update/delete, cross-user separation, and Passport refresh. Use `Authorization: Bearer <Firebase ID token from the test browser>` for application APIs, not a gcloud OAuth token; do not paste tokens into reports or shared command history.

Inspect logs with:

```powershell
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="maadhyam-api" AND severity>=ERROR' --project=$Project --freshness=30m --limit=30 --format=json
```

The filter selects recent errors for this service. Diagnose before repeating a paid build/deploy. Do not log document contents or identity metadata to debug failures.

## F. Frontend build and Firebase Hosting

Use the existing ignored `.env.local` public Firebase web configuration. Production Vite API base must remain same-origin (empty), never localhost. Hosting's `/api/**` rewrite must precede the SPA catch-all and target the existing Run service/region.

```powershell
Set-Location "$Repo/Maadhyam/apps/web"
npm ci
npm run lint -- --max-warnings 0
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
Set-Location "$Repo/Maadhyam"
Get-Content .firebaserc
Get-Content firebase.json
npm exec --yes --package=firebase-tools@15.34.0 -- firebase projects:list
npm exec --yes --package=firebase-tools@15.34.0 -- firebase deploy --only hosting --project maadhyam-1610 --non-interactive
if ($LASTEXITCODE -ne 0) { throw 'Hosting deploy failed' }
Invoke-RestMethod 'https://maadhyam-1610.web.app/api/health'
Start-Process 'https://maadhyam-1610.web.app'
```

`Get-Content` is `cat` in Bash; `Start-Process` is `open` on macOS or `xdg-open` on Linux. Every command's project is explicit. Hosting publishes built `apps/web/dist`; it does not compile Vite or deploy the backend. Inspect Firebase Console Hosting Release history for the version/release ID and previous rollback target. Confirm actual deployed JS/CSS hashes and perform real browser acceptance: deep routes, token identity after refresh, Step 3 save/resume, metadata/file timestamps, household associations, private preview, deletion, planner and workflows. Generic AI provider failures can be mocked locally; do not repeatedly invoke paid Gemini to demonstrate unrelated storage changes.

## G. Data lifecycle and inspection

Firestore stores small structured metadata and revisions. Cloud Storage stores PDF/image bytes. A verified Firebase UID, obtained by backend token verification, scopes all paths. No request-supplied UID authorizes ownership. The browser receives no public object URL or service credentials. File retrieval goes through an authenticated backend response with no-store caching and MIME protections.

Upload reserves a `pending` metadata record, writes a generation-protected object, then commits `ready`, `uploadedAt` and revision. A failed final metadata write leaves a recoverable pending record; retry the same immutable ID/content/metadata. Different content is rejected. A delete marks `deleting`, removes the exact object generation, and removes metadata. Failed deletes remain retryable and inaccessible for preview. Clear All reports successes/failures for only the requesting UID; it does not delete application/household records. Deleted Passport references show a warning.

Existing IndexedDB files migrate only after explicit informed confirmation. UUIDs and metadata remain intact; a controlled download/checksum verifies bytes. Local originals remain until explicitly cleared. Anonymous identities depend on retained browser authentication storage; this is not account recovery or a cross-browser login system.

To investigate a suspected orphan, compare a **single user's** Storage object path/generation/hash with the named database's record and status. Pending/deleting records may represent recoverable interrupted operations. Do not delete objects merely because a list/UI is delayed, and do not run a global destructive cleanup. Reconcile with a verified record/owner and retain originals until consistency is established.

Privacy check: inspect bucket IAM and public access prevention, then verify a small fictional object's anonymous Storage GET is denied. A protected API GET without a Firebase token must return 401. A second user's GET/PATCH/file preview returns 404 (idempotent deletion may return 204 for an absent own record without touching another user's file). Check actual objects after deletion, not only the UI.

All timestamps are stored UTC, then formatted in the viewer's local timezone with a shared `Intl.DateTimeFormat` helper: `DD MMM YYYY, hh:mm AM/PM`. Rendering never generates a new creation/save date. Files previewed after refresh retain their persisted upload time. Client household timestamps are explicitly labeled and are not replaced with a fake time for the default applicant or legacy members.

## H. Rollback

The historical pre-M12 backend revision is `maadhyam-api-00002-grr`; verify the actual predeployment revision in the M12 report/readback. Preserve the previous Hosting version and all user data. To route traffic back:

```powershell
gcloud run services update-traffic maadhyam-api --project=maadhyam-1610 --region=asia-south1 --to-revisions=PREVIOUS_VERIFIED_REVISION=100
```

Replace the placeholder with the recorded previous revision, then recheck traffic, health and major journeys. This routes traffic without rebuilding or deleting the newer revision.

For Hosting, Firebase Console → project → Hosting → Release history → previous verified release → menu → **Roll back**. Alternatively clone the recorded version to live:

```powershell
npm exec --yes --package=firebase-tools@15.34.0 -- firebase hosting:clone "maadhyam-1610:@PREVIOUS_VERSION_ID" maadhyam-1610:live --project maadhyam-1610
```

Replace `PREVIOUS_VERSION_ID` with the version ID recorded before deployment, not a release number. Verify the resulting new live release and assets. See [Hosting versions and releases](https://firebase.google.com/docs/hosting/manage-hosting-resources).

Old applications remain backward compatible with additive fields and legacy ISO timestamps. The old backend/frontend do not support the new cloud Vault API/UI; rolling back one side alone can leave Cloud Vault unavailable. Coordinate both rollbacks. Existing private objects and metadata must remain intact for roll-forward/recovery; never delete the bucket, Firestore documents or Firebase users as a rollback step. Restoring application code cannot reverse a user-confirmed permanent file deletion.

Security references: [Uniform bucket access](https://docs.cloud.google.com/storage/docs/uniform-bucket-level-access), [Public access prevention](https://docs.cloud.google.com/storage/docs/public-access-prevention), [generation-protected uploads](https://docs.cloud.google.com/storage/docs/uploading-objects).

## I. Owner management and the M12 IAM recovery

A new bucket automatically received project convenience bindings. M12 removed broad legacy viewer/editor object bindings. The first policy replacement also removed `projectOwner:maadhyam-1610`'s legacy bucket-management binding; project Owner by itself did not retain the necessary Storage bucket permissions in this project. This was diagnosed from actual `403` responses, not treated as successful verification.

The intended final bucket policy retains:

- `roles/storage.objectUser`: the runtime service account only.
- `roles/storage.legacyBucketOwner`: `projectOwner:maadhyam-1610`, for owner bucket management.

Do not remove the owner management binding. To remove broad object grants safely, get the current policy and preserve its etag and owner management entry before setting it:

```powershell
$Policy = gcloud storage buckets get-iam-policy "gs://$Bucket" --project=$Project --format=json | ConvertFrom-Json
$Policy.bindings = @($Policy.bindings | Where-Object { $_.role -in @('roles/storage.objectUser','roles/storage.legacyBucketOwner') })
# Verify legacyBucketOwner members are projectOwner only, never projectEditor.
foreach ($Binding in $Policy.bindings) {
  if ($Binding.role -eq 'roles/storage.legacyBucketOwner') { $Binding.members = @('projectOwner:maadhyam-1610') }
}
$Policy | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 bucket-policy.json
gcloud storage buckets set-iam-policy "gs://$Bucket" bucket-policy.json --project=$Project
gcloud storage buckets get-iam-policy "gs://$Bucket" --project=$Project --format=json
```

For the accidental loss of management access, the existing project owner used a temporary **project IAM binding conditioned to exactly this one bucket**, restored the owner bucket binding, then removed the temporary binding. This is a recovery log, not a routine deployment prerequisite:

```powershell
$Condition = "expression=resource.name == 'projects/_/buckets/maadhyam-1610-private-vault',title=m12-vault-management-recovery,description=Temporary access only to the newly created private Vault bucket"
gcloud projects add-iam-policy-binding maadhyam-1610 --member=user:swarjal2311@gmail.com --role=roles/storage.admin --condition=$Condition --quiet
# Restore the two-entry intended bucket policy above, using the observed current etag.
gcloud storage buckets set-iam-policy "gs://$Bucket" bucket-policy.json --project=$Project
gcloud projects remove-iam-policy-binding maadhyam-1610 --member=user:swarjal2311@gmail.com --role=roles/storage.admin --condition=$Condition --quiet
```

Verify removal in project IAM and read back bucket configuration/IAM. The temporary role was scoped by resource condition, not unrestricted project-wide Storage Admin. No runtime account received administrative privileges. IAM changes can take time to propagate; diagnose a denial before repeatedly mutating policies.

Hosting REST inventory initially returned a quota-project error. The corrected request used the existing `maadhyam-1610` project in `x-goog-user-project`:

```powershell
$AccessToken = (gcloud auth print-access-token).Trim()
$Headers = @{ Authorization = "Bearer $AccessToken"; 'x-goog-user-project' = 'maadhyam-1610' }
$Releases = Invoke-RestMethod -Headers $Headers -Uri 'https://firebasehosting.googleapis.com/v1beta1/sites/maadhyam-1610/releases?pageSize=3'
$Releases.releases | Select-Object name,releaseTime,version
Remove-Variable AccessToken,Headers
```

Keep tokens in memory and out of command output/reports. This inventories releases; it does not enable an API or deploy Hosting.
