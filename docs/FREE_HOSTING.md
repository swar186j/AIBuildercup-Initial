# No-payment deployment alternative

Firebase Hosting's Spark plan can serve the React production build without a payment method. FastAPI needs a separate backend host; Render offers a Free web service that continues independently of the user's PC. It sleeps after inactivity, so the frontend waits for health before mounting the workspace and offers a bounded retry. Free allowances are service limits, not guaranteed unlimited availability. Do not add a card, upgrade compute, create a paid database or enable automatic paid deployment for this path.

Existing resources are preserved: Firebase Authentication, Firestore and the private Supabase bucket. `MAADHYAM_FIRESTORE_TRANSPORT=user-rest` verifies Firebase signatures/audience/issuer/subject with Google's public keys and forwards the same user token to Firestore REST. Owner-only rules enforce the same account boundary. Atomic update-time preconditions preserve revision conflicts. No Google service-account key or personal ADC refresh token is uploaded to Render. Download/delete object paths are recomputed from the authenticated UID, so a forged metadata object_key cannot redirect private storage access.

The 21 inline owner/anonymous/cross-user rules cases passed. The owner-only rules were published with explicit user approval. A real two-account Firebase/Firestore/Supabase lifecycle passed and both disposable accounts/files/settings/applications were removed. Evidence: qa/evidence/m10-m12/free-firestore-live.json. This does not claim that the Render service is deployed.

Render service configuration:

- Runtime Docker; plan Free; root directory `Maadhyam/apps/api`; Dockerfile `./Dockerfile`; health `/api/health`.
- Use the reviewed branch containing the M10–M12 code. Current remote main has older code; deploying it does not deploy this working tree.
- Set GOOGLE_CLOUD_PROJECT=maadhyam-1610, MAADHYAM_ENVIRONMENT=production, MAADHYAM_FIRESTORE_TRANSPORT=user-rest.
- Set MAADHYAM_CORS_ORIGINS to the JSON array containing https://maadhyam-1610.web.app and https://maadhyam-1610.firebaseapp.com.
- Put the existing Supabase secret and Gemini key into backend-only secret environment settings, plus the Supabase URL/bucket and tested Gemini model. Never use VITE_* for these secrets. Verify Gemini's free tier separately: Google Cloud $300 trial credit does not cover AI Studio Gemini API costs.
- `render.yaml` describes this free configuration. Do not enable auto-deploy until the correct branch and secrets are ready.

Frontend: build with VITE_API_BASE_URL set to the verified Render HTTPS origin and the public Firebase config. Run frontend lint/build and origin checks, then deploy only the static site using `firebase.free.json`. It has SPA fallback without a Cloud Run rewrite. Keep local .env.local's API origin blank so localhost continues using its proxy; inject the hosted origin for the deployment build.

Cloud Run alternative: the user reported $300 credits and asked to use them. An active billing account exists, but maadhyam-1610 remains unlinked. Trial type, remaining balance and expiry were not confirmed because the account Overview page failed to load. Do not upgrade billing or provision paid services until the active free-trial status is verified. The Cloud Run workflow is disabled pending that verification; its local deployment script additionally requires TRIAL_CREDIT_CONFIRMED=true. Read docs/DEPLOYMENT.md for the reviewed Cloud Run configuration.

Sources checked 2026-10-16: https://firebase.google.com/pricing ; https://render.com/docs/free ; https://firebase.google.com/docs/firestore/use-rest-api ; https://docs.cloud.google.com/free/docs/free-cloud-features .
