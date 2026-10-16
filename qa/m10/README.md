# M10: authenticated preparation storage

The web app requires Firebase email/password sign-in. The API verifies the Firebase ID token and scopes every preparation and workspace planner record to its verified user ID. Browser callers cannot choose a record owner. Revision checks prevent silent overwrites from another tab/session.

## Local configuration

Frontend `Maadhyam/apps/web/.env.local` needs `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, and `VITE_FIREBASE_APP_ID` from the project's web app configuration. Enable Email/Password in Firebase Authentication and use an existing account.

Backend `Maadhyam/apps/api/.env` needs `GOOGLE_CLOUD_PROJECT=maadhyam-1610` for this workspace. Both Firebase Admin and Firestore now read this file through the API settings. `.env` files are ignored by Git.

This machine uses Google Application Default Credentials, so service-account key creation is unnecessary:

```powershell
gcloud auth application-default login --project=maadhyam-1610
```

Use an account already authorized for the project and Firestore. Do not disable organisation key restrictions. Google Cloud CLI was installed at `C:/Users/S/AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd`. If it is not on PATH, invoke that full path. On deployed Google Cloud services, use the attached service account/ADC. An existing service-account file can optionally be configured through `GOOGLE_APPLICATION_CREDENTIALS`; never put the key in source code or chat.

Run the API from `Maadhyam/apps/api` using `.venv/Scripts/python.exe -m uvicorn maadhyam_api.main:app --reload --port 8000`. Run `npm.cmd run dev` from `Maadhyam/apps/web`; Vite proxies `/api` to port 8000.

## Implemented behavior

- Drafts open only after creation is confirmed. Failed creation offers retry without showing a phantom draft.
- Preparation answers, applicant details, selected document IDs, current step, status and bounded progress history are saved in Firestore. Reopening a preparation restores its saved values.
- Saves are serialized per preparation. Dirty edits remain visible on failure, can be retried, and block sign-out until saved or explicitly discarded. Closing/reloading while unsaved triggers the browser's native warning where supported.
- Deletion removes the card only after API confirmation. A failed delete retains the card for retry.
- The Resolution Planner exposes a saved checklist with server-enforced prerequisites, dependent-step reset and revision checks. A new user's first update accepts revision zero.
- Older browser-local preparation records require explicit import consent. Stable migration IDs make replay idempotent and leave the original local copies intact.
- Every account has its own browser-local Vault database and persistence preference. Switching accounts remounts document/household/workspace state. Legacy shared Vault files are not automatically imported into an account; they remain in the old browser database.
- Connection errors and timeouts cover token acquisition, response headers and response bodies. There is no authentication bypass or fallback from Firestore to a shared cloud account.

Document bytes remain browser-local with opt-in persistence. Household UI remains session-local. The API supports per-preparation household/documents sections and assessment history, but those endpoints do not imply that the household UI or raw files are automatically cloud-synced. Government submission is outside this milestone.

## Reproducible verification

From `Maadhyam/apps/api`, run `.venv/Scripts/python.exe -m pytest -q`. Lifecycle tests exercise the production routes and repository logic with an isolated in-memory Firestore adapter. Auth unit tests exercise the verifier boundary with synthetic SDK outcomes; they are not live Firebase token tests.

With the Vite development server running on port 5173, run `Maadhyam/apps/api/.venv/Scripts/python.exe qa/m10/run_browser.py` from the repository root. It starts/stops its own API, injects a synthetic Firebase SDK only into its isolated Chromium context, and uses real HTTP plus production repository logic. It covers create/save/reload, planner dependencies, Vault isolation, sign-out, import replay and failed create/save/delete recovery. Evidence is written to `qa/m10/evidence/`. It does not change live Firestore documents or users.

The real configured Google credentials and Firestore read were verified separately during setup. Full historical M1–M9 browser suites need authenticated fixtures before their results can be applied to this version.
