#!/usr/bin/env bash
set -euo pipefail
: "${COST_APPROVED:?Deployment approval required}"
[ "$COST_APPROVED" = APPROVED ] || exit 1
: "${TRIAL_CREDIT_CONFIRMED:?Verify active free-trial credit first}"
[ "$TRIAL_CREDIT_CONFIRMED" = true ] || exit 1
: "${RUNTIME_SERVICE_ACCOUNT:?Dedicated runtime identity required}"
: "${GCS_BUCKET:?Reviewed private document bucket required}"
: "${GEMINI_MODEL:?Verified provider model required}"
python scripts/cloud_preflight.py
PROJECT=maadhyam-1610
REGION=asia-south1
IMAGE="$REGION-docker.pkg.dev/$PROJECT/maadhyam/api:$(git rev-parse HEAD)"
ENVVARS="MAADHYAM_ENVIRONMENT=production,MAADHYAM_FIRESTORE_TRANSPORT=user-rest,MAADHYAM_FILE_STORAGE=gcs,MAADHYAM_GCS_BUCKET=$GCS_BUCKET,MAADHYAM_GEMINI_MODEL=$GEMINI_MODEL,GOOGLE_CLOUD_PROJECT=$PROJECT"
SECRETS='MAADHYAM_GEMINI_API_KEY=maadhyam-gemini-key:latest'
# Temporary bridge only while owner-confirmed legacy migration is outstanding.
if [ "${ENABLE_SUPABASE_MIGRATION:-false}" = true ]; then
  : "${SUPABASE_URL:?Legacy migration source URL required}"
  ENVVARS="$ENVVARS,MAADHYAM_SUPABASE_URL=$SUPABASE_URL,MAADHYAM_SUPABASE_BUCKET=maadhyam-documents"
  SECRETS="$SECRETS,MAADHYAM_SUPABASE_SECRET_KEY=maadhyam-supabase-key:latest"
fi
gcloud builds submit Maadhyam/apps/api --project "$PROJECT" --tag "$IMAGE" --quiet
gcloud run deploy maadhyam-api --project "$PROJECT" --region "$REGION" --image "$IMAGE" \
  --service-account "$RUNTIME_SERVICE_ACCOUNT" --allow-unauthenticated \
  --min-instances 0 --max-instances 1 --concurrency 8 --cpu 1 --memory 512Mi \
  --timeout 55 --port 8080 --set-env-vars "$ENVVARS" --set-secrets "$SECRETS" --quiet
