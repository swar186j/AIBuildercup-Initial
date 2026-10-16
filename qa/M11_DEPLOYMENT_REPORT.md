# M11 deployment report — 16 October 2026 (IST)

M11 status: **PARTIAL**. The application is deployed and its principal hosted journeys pass. Full sign-off remains limited by pre-existing frontend lint errors and denied billing-account visibility. See the testing and limitations reports.

| Item | Verified value |
|---|---|
| Firebase Hosting | https://maadhyam-1610.web.app |
| Cloud Run | https://maadhyam-api-767722654590.asia-south1.run.app |
| Project / region | `maadhyam-1610` / `asia-south1` |
| Service / final revision | `maadhyam-api` / `maadhyam-api-00002-grr` |
| Previous tested revision | `maadhyam-api-00001-f64` |
| Runtime identity | `maadhyam-api@maadhyam-1610.iam.gserviceaccount.com` |
| Final image tag | `asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api:m11-06c59cb1c944` |
| Final image digest | `sha256:22997ae55fff8471d0a518b9e598d61d563487dfbd580ffbd6c9fe2342a06aac` |
| Backend source commit | `06c59cb1c94437907af7075f86dd6bc86c0d4242` |
| Branch | `release/m10-m12-recovery` |
| Hosting version | `sites/maadhyam-1610/versions/e354c084966d0cdd` |
| Hosting release | `sites/maadhyam-1610/releases/1792172321125000` |
| Firestore | Named database `maadhyam`; fictional record verified absent from `(default)` |
| Authentication | Existing Firebase Anonymous Authentication; backend verifies Firebase ID tokens |
| AI | Google Gen AI SDK 1.75.0, Vertex AI, `gemini-2.5-flash`, `global` |

The original UI, navigation, deterministic rules, household/planner models and eight citizen workflows were preserved. Changes add a shared Vertex client, bounded inference, production AI authentication and admission control, accurate upstream errors, upload protection, client request timeouts, container packaging and Hosting routing. Model-generated URLs are removed from assistant prose; official references remain supplied by source records. AI extraction stays fictional-only, opt-in and review-before-apply.

The final container is non-root, uses Python 3.13 and `uv sync --frozen --no-dev --no-editable`, and serves on `0.0.0.0:$PORT` without reload. Build-context allowlists exclude `.env`, credentials, virtualenvs, tests and uploads. Packaging inspection confirmed the five rule-data JSON files are included. Production upload bodies are bounded at 11 MiB; files remain limited to 10 MiB and accepted multipart files stay in memory during request processing.

## Configuration and access

Non-secret configuration lives in `Maadhyam/apps/api/runtime.env.yaml`. Names: `MAADHYAM_PRODUCTION`, `MAADHYAM_GOOGLE_CLOUD_PROJECT`, `MAADHYAM_FIRESTORE_DATABASE_ID`, `MAADHYAM_GEMINI_VERTEXAI`, `MAADHYAM_GOOGLE_CLOUD_LOCATION`, `MAADHYAM_GEMINI_MODEL`, `MAADHYAM_GEMINI_API_KEY` (empty), `MAADHYAM_AI_TIMEOUT_MS`, `MAADHYAM_CORS_ORIGINS`. No service-account keys or Cloud Run `GOOGLE_APPLICATION_CREDENTIALS` were created.

Existing runtime roles were reused: `roles/aiplatform.user` and `roles/datastore.user`. The existing default build account, `767722654590-compute@developer.gserviceaccount.com`, received Artifact Registry Writer on the existing repository, Storage Object Viewer on the regional source bucket, and project Log Writer. No Editor role was granted. Cloud Run has public HTTP invocation for Hosting integration; application records and paid AI routes retain Firebase authentication. Live missing/invalid tokens and cross-user access were rejected.

Firebase registration, Anonymous Auth enablement, Hosting site, billing activation, named Firestore, registry, runtime identity and required enabled APIs were read back. Budget API was enabled for requested cost visibility; billing-account budget access still returned `PERMISSION_DENIED`. The owner reports ₹28K credits, which could not be independently verified.

## Resource and cost bounds

- Service and revision minimum instances: **0**; omitted zero values in API responses represent the configured default zero. Both levels were explicitly deployed with zero.
- Service and revision maximum instances: **2**; one CPU, 512 MiB memory, concurrency four, 55-second request timeout, request-based CPU, startup CPU boost disabled.
- AI: 30-second timeout, one total SDK attempt, 2,048 output-token ceiling, bounded structured input, six admitted requests per UID/minute and 60 per instance/hour across anonymous identities.
- Four real model calls total: local `READY`, hosted chat, fictional PNG extraction, final-revision minimal chat. Other AI tests use mocks.
- Two successful regional builds (61 and 55 seconds), two Cloud Run revisions, one Hosting deployment. One earlier build submission was rejected before execution because a legacy build identity was unsupported; permissions and identity were diagnosed before resubmission.
- Reused the registry, service accounts, Firebase project and databases. Created the Cloud Run service, first Hosting release and regional build-source bucket. Two fictional acceptance records were retained. No VM, GPU, SQL, GKE, Agent Engine, additional database or custom domain was created.
- Alerts and instance caps are **not hard spending caps**. Admission counters are per instance and reset with process replacement. Actual currency charges and credit balance are unavailable with current billing permissions.

## Reproducible deployment commands

Run backend commands from `Maadhyam/apps/api`, using the matching tested source commit and a new immutable tag for future changes:

```powershell
gcloud builds submit . --project=maadhyam-1610 --region=asia-south1 --config=cloudbuild.yaml --substitutions=_IMAGE=asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api:m11-06c59cb1c944 --service-account=projects/maadhyam-1610/serviceAccounts/767722654590-compute@developer.gserviceaccount.com --default-buckets-behavior=regional-user-owned-bucket --quiet
gcloud run deploy maadhyam-api --project=maadhyam-1610 --region=asia-south1 --image=asia-south1-docker.pkg.dev/maadhyam-1610/maadhyam-api/maadhyam-api@sha256:22997ae55fff8471d0a518b9e598d61d563487dfbd580ffbd6c9fe2342a06aac --service-account=maadhyam-api@maadhyam-1610.iam.gserviceaccount.com --env-vars-file=runtime.env.yaml --min=0 --max=2 --min-instances=0 --max-instances=2 --cpu=1 --memory=512Mi --concurrency=4 --timeout=55 --cpu-throttling --no-cpu-boost --execution-environment=gen2 --allow-unauthenticated --quiet
```

The build configuration starts and tests the 512 MiB container before image push. It requires health `200` and unauthenticated AI `401`.

Run `npm run build` from `Maadhyam/apps/web`, then from `Maadhyam`:

```powershell
npm exec --yes --package=firebase-tools@15.34.0 -- firebase deploy --only hosting --project maadhyam-1610 --non-interactive
```

The existing ignored `.env.local` supplies public Firebase web configuration during build. Hosting rewrites `/api/**` before the SPA catch-all. No `pinTag` was enabled; backend traffic rollback is managed separately. Official references: [Gen AI SDK](https://googleapis.github.io/python-genai/genai.html), [Firebase Hosting and Cloud Run](https://firebase.google.com/docs/hosting/cloud-run).

Evidence: `qa/evidence/m11-release-summary.json`, build results, final live checks, Firestore readback and hosted results. The handoff documentation commit follows the backend source commit; the final response records the pushed branch head.
