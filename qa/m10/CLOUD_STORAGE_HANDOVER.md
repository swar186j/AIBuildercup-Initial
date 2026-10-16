# Cloud-only storage implementation — 16 October 2026

## Implemented

Document files use a private Supabase bucket through authenticated backend routes. Firebase sign-in still identifies the account; Firestore holds document metadata/revisions, preparations, planner state and household settings. Browser code never receives the Supabase secret. New `sb_secret_` keys are sent only in the backend `apikey` header; legacy service-role JWTs are also supported. Public buckets are rejected before any upload.

PDF, PNG and JPEG uploads are limited to 10 MB and validated by signature. Object keys are account-scoped, retries never overwrite different bytes, downloads require a verified owner and use `Cache-Control: no-store`. Document metadata uses revision checks. Deletion locks a record against concurrent edits, removes the private object, and then removes metadata. A failed deletion can be retried; pending records remain discoverable.

The Document Vault now uploads files and restores them from cloud on sign-in/refresh. Metadata/review changes and deletions are confirmed by the API. Failed uploads remain in memory for explicit retry. Pending/failed saves prevent sign-out and warn on tab closure. Preview object URLs are temporary in-memory views, not persistent browser saving.

Household members, relationships and dependency lists now persist per account with revision conflicts. Association metadata persists with its cloud document. Household fields remain editable while errors are visible; a failed household save can be retried. Relationship labels do not grant cross-account access or legal verification.

IndexedDB Vault read/write paths and browser-local preparation import controls were removed from the active app. It no longer writes document/preparation/household data to localStorage or IndexedDB. Existing browser copies were not silently uploaded or deleted. Appearance preference and Firebase's own sign-in session persistence are separate from document saving and remain unchanged.

## External setup

1. Create a Supabase Free project.
2. Create a **private** bucket named `maadhyam-documents`; Public bucket must remain OFF.
3. In the ignored backend file `Maadhyam/apps/api/.env`, set:

```dotenv
MAADHYAM_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
MAADHYAM_SUPABASE_SECRET_KEY=YOUR_BACKEND_SECRET_KEY
MAADHYAM_SUPABASE_BUCKET=maadhyam-documents
```

Copy the backend secret from Supabase Project Settings → API Keys. Never place it in `VITE_*`, source code, screenshots or chat. The API process must restart after editing `.env` because settings are cached. Existing Google ADC/Firestore configuration remains required.

The user subsequently configured the Supabase URL and backend secret in the ignored `.env`. The private bucket was verified live, and a tiny fictional object was uploaded, downloaded byte-for-byte and deleted successfully using the production storage adapter. The authenticated local Vault page also loaded successfully. No personal documents were read or changed during this probe. There is no browser-local fallback when Supabase is unavailable.

This machine's system DNS failed for the project hostname although public DNS returned valid records. Optional `MAADHYAM_SUPABASE_DNS_FALLBACK=true` was enabled in the local `.env`. The adapter first uses system DNS and falls back to Google's DNS-over-HTTPS only on a DNS-resolution failure for the configured Supabase hostname. TLS certificate/hostname verification and SNI are preserved; system network settings are unchanged. Results are cached for 60 seconds. Redirects are refused so a backend secret cannot be forwarded to a different destination. The fallback defaults to OFF in `.env.example`.

## Verification

- Full backend suite after DNS/TLS/redirect regressions: **430 passed**, one existing TestClient deprecation warning.
- Authenticated isolated browser suite: **16 scenario groups passed**, including cloud upload failure/retry, file restore, household restore/isolation, preparation save/delete/conflicts, deleted URLs and duplicate prevention.
- Full frontend lint: **passed**.
- TypeScript/Vite production build: **passed**, with the existing chunk-size warning.

Browser tests inject synthetic Firebase identities only into their isolated context and use a test-owned real HTTP API, production repository logic and in-memory Firestore/private-object adapters. Supabase transport/privacy behavior is separately covered by mocked HTTP unit tests. The separate live Supabase round-trip described above verifies the configured production adapter; it does not claim every failure scenario was exercised against the live provider.

Run backend tests from `Maadhyam/apps/api` with `.venv/Scripts/python.exe -m pytest -q`. With Vite on port 5173, run `Maadhyam/apps/api/.venv/Scripts/python.exe qa/m10/run_browser.py` from the repository root. Evidence is in `qa/m10/evidence/browser.json`.
