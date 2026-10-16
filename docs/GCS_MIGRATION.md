# Private Google Cloud Storage cutover

The user selected Google Cloud Storage to replace Supabase. The deployment target is Firebase Hosting/Auth + Cloud Run API + Firestore metadata + private GCS file objects. Supabase code/configuration remains only as a temporary legacy migration bridge; it is not the primary Cloud Run deployment store.

## Prerequisites

Active free-trial credit/type/expiry and project billing linkage must be verified before provisioning. No bucket was created by this implementation. Create the chosen document bucket in the reviewed region with uniform bucket-level access and enforced public access prevention. Do not grant allUsers/allAuthenticatedUsers. The adapter checks both settings and fails closed if either is missing. Keep object lifecycle deletion disabled until a retention policy is approved.

Grant the dedicated Cloud Run runtime identity a bucket-scoped custom role containing storage.buckets.get, storage.objects.create, storage.objects.get and storage.objects.delete. No public object URL, signed URL, service-account JSON or browser GCS credentials are needed. Application authentication and UID-derived object paths gate downloads/deletion. The API never trusts a stored object_key to choose another account's object.

Cloud Run uses MAADHYAM_FILE_STORAGE=gcs and MAADHYAM_GCS_BUCKET; scripts/deploy.sh requires GCS_BUCKET. New objects use create-only generation preconditions, and duplicate retries must have identical SHA-256 bytes. Deletes use the observed generation to avoid deleting a replacement object. The tested SDK is locked in uv.lock. Local configuration remains on the existing working Supabase store until GCS is provisioned, to avoid breaking access to existing documents prematurely.

## Owner-scoped migration

Enable the temporary bridge only when needed: ENABLE_SUPABASE_MIGRATION=true adds the source URL and existing Supabase secret reference to Cloud Run. Never put backend secrets in VITE_* or terminal command arguments. Without this bridge, a fully finalized GCS deployment requires only the Gemini backend secret, not Supabase.

For each signed-in owner's document, explicitly POST `/api/workspace/documents/{id}/migrate-storage` with `{ "revision": CURRENT_REVISION, "confirmed": true }`. The endpoint reads only that owner's record and derives the object path from verified UID. Legacy records without storage_provider remain Supabase-backed until successful migration. It verifies the source SHA-256, performs a create-only GCS upload, downloads and verifies the copy, then changes metadata using revision/update-time concurrency guards. Originals stay intact. A concurrent metadata change returns 409 rather than overwriting it; a copied but unreferenced GCS object can remain after that conflict and needs an owner-scoped retry/reconciliation, not a broad deletion.

After confirming the migrated document opens correctly, explicitly POST `/api/workspace/documents/{id}/finalize-storage-migration` with its current revision and confirmed=true. This verifies the GCS bytes again before removing the retained Supabase original and clears the retained-source metadata. Retry after conflicts; the original deletion is idempotent. Explicit ordinary document deletion also removes both the current object and a retained source copy. No bulk cross-account scan/migration or automatic source purge is included.

Only after every required owner's files have been verified and finalized may the legacy source secret/URL be removed. Keep the Supabase account/bucket itself until its owner confirms no other application uses it. Do not delete that service automatically.

## Evidence and limits

GCS adapter tests cover policy fail-closed behavior, create-only generations, same-byte retries, different-byte conflicts, missing objects and generation-aware deletion. Migration tests cover consent, owner isolation, source integrity, retained originals, active GCS download and verified finalization. These tests use isolated adapters; live GCS upload/migration and public Cloud Run acceptance are BLOCKED by billing/trial provisioning prerequisites. Existing real Supabase/Firebase lifecycle evidence remains historical source-store verification, not GCS evidence.
