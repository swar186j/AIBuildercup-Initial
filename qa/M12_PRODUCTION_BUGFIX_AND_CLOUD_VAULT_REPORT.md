# M12 production fixes, cloud Vault and timestamp release

## 1. Executive summary

- **Status: PARTIAL — implementation/local QA complete; deployment and hosted acceptance pending.**
- Date: 17 October 2026 (Asia/Kolkata).
- Branch: `release/m10-m12-recovery`.
- Implementation commit / remote verification: recorded in the deployment receipt after commit/push; this report is updated after hosted verification.
- Baseline: fast-forwarded `f2a0e4e` to actual M11 release `51ab10f`; preserved the user's unrelated five-blank-line edit in `Maadhyam/apps/api/tests/test_cloud_applications.py` and excluded it from staging.

## 2. Severity-ranked defect register

CONFIRMED means source-established or reproduced. A reported symptom is not automatically a confirmed defect.

| ID / severity | Page/API and reproduction | Confirmed? / root cause | Fix | Regression / verification |
|---|---|---|---|---|
| P01 / P0 suspected | Save Passport Step 3, refresh | Reported loss **not reproduced** in initial four-step browser baseline; exact ID/step restored. Existing M11 restoration was present. | Retain existing restoration; validate complete save acknowledgment, protect newer edits, preserve exact IDs/revisions. | `test_confirmed_save_hard_refresh_exact_step[0..3]` now navigates from Step 1 before saving; reload never manually navigates to expected step. Hosted verification pending. |
| P02 / P1 | Repeated click during slow save | CONFIRMED source: button remained enabled; provider rejected overlapping writes but UI could replace Saving with a misleading duplicate notice. | Disable while pending; explicit acknowledgment; preserve edits/conflict notice; targeted unload warning. | Slow acknowledgment/network failure and conflict tests. |
| P03 / P1 | Duplicate household names / removed member | CONFIRMED source: first matching name selected a stable identity ambiguously. | Persist optional `applicantHouseholdMemberId`; legacy names map only when unique; missing saved members retain snapshot and show recovery warning. | Duplicate-name stable-ID refresh and existing Other/name/household tests. |
| P04 / P1 | Edit stale local preparation while cloud hydration is delayed | CONFIRMED source: wizard hydration could replace fields typed while restore was pending. | Mark local wizard edits and avoid replacing them with incoming older fields. | M11 delayed-hydration regressions retained; new save tests. |
| V01 / P0 requirement | Uploaded files disappear after refresh/cross-session | CONFIRMED architecture: session-only files by default; optional IndexedDB, no cloud Vault bytes/metadata. | Private GCS + named Firestore metadata, authenticated backend APIs, automatic listing, on-demand bytes. | Backend lifecycle/UID tests; browser cloud upload/refresh/preview/delete. |
| V02 / P1 requirement | Existing IndexedDB files migrate | New requirement, not an existing cloud defect. | Explicit informed migration; retain UUID, reviewed fields/associations and original local time; verify downloaded SHA-256; keep originals. | Success/failure browser migration cases; immutable retry/backend tests. |
| V03 / P1 | Clear All confirmation | Existing `window.confirm` CONFIRMED in source, so missing confirmation was not reproduced. | Preserve native accessible confirmation; distinguish local cache clearing from permanent own-account cloud deletion. | Existing cancel/clear/reload cases plus cloud cancel/confirmed deletion and backend partial-failure retry. |
| V04 / P1 | Upload or delete interrupted between databases | New architecture consistency risk established by source review/failure injection. | Pending reservation, create-only object generation, immutable retry, ready acknowledgment, deleting tombstone, generation-matched cleanup. | Storage failure, final metadata failure, retry, partial clear and upload/delete race unit tests. |
| V07 / P0 | PATCH only a review status | CONFIRMED by failing regression: omitted metadata received schema defaults and erased saved fields. Caught before deployment. | Partial PATCH preserves omitted fields and merges supplied metadata inside the revision transaction; no creation/upload timestamp updates. | `test_status_only_patch_preserves_reviewed_metadata`; 442 backend tests pass. First built image was held undeployed; corrective backend rebuild required. |
| V05 / P1 | Delayed preview/upload replaces newer metadata | CONFIRMED during implementation source review. | Merge file response into current document, protect account identity, preserve newer unsaved metadata, block duplicate mutations while busy. | Full final browser regression and lifecycle tests. |
| V06 / P1 | Account change/caching | CONFIRMED implementation risk caught before release: snapshot cache replacement could remove hidden accounts' originals; offline cloud error could prevent bound cache restore. | Cache uses explicit deletes, owner binding, independent offline hydration; cloud requests check expected UID; late responses guarded. | Existing cache restoration and new migration/refresh; cross-user APIs tested separately. |
| R01 / P1 suspected | User hard-refreshes between pages | A refresh alone did not establish a production Context bug. | Keep Context; merge delayed hydration, stable identity references, live acknowledgment timestamps; no forced reload workaround. | Existing household/planner/navigation regression retained. |
| U01 / P2 | UUID / `__other__` dropdown values | Raw visible UUID labels **not reproduced**; existing labels were human readable. | Keep stable internal IDs and labels; fix ambiguous name restoration. | Household/applicant browser cases. |
| U02 / P2 | Next action after upload/save | UX requirement rather than confirmed routing failure. | Inline cloud saving/result guidance and existing Passport/My Applications links; retain multi-upload Vault. | Existing route/navigation tests; hosted check pending. |
| W01 / P2 | Generic address-proof blocker | CONFIRMED source: human-support used generic checklist; rejection only accepted optional record IDs. | Explicit selection/consent for a minimal reviewed proof subset; deterministic possible checks, no new Gemini call. | Consent/decline/unreviewed/other-holder/injection backend tests. |
| T01 / P1 requirement | Missing dates on three pages | CONFIRMED source: no authoritative Vault dates; household lacked creation/edit times; preparations showed generic status strings. | Shared local-time formatter; server Vault/application acknowledgment timestamps; clearly client-recorded nested member times; absent legacy values remain Not recorded. | Document pending/edit/UTC tests, household creation/edit/restore, preparation acknowledgment/conflict/refresh tests. |
| T02 / P1 | Refresh equivalent Firestore workspace with reordered map fields | CONFIRMED source: raw JSON string comparison depended on map-key order and could advance timestamps through an unchanged write. | Canonical recursive map serialization for workspace comparison; backend image unchanged. | `test_restoration_map_key_order_does_not_write_or_advance_saved_time`; final suite. |
| Q01 / test infrastructure | Held Playwright `route.fetch()` requests | Reproduced 8 workflow retry failures: preview proxy forwarded to port 8000 instead of runner's temporary API. | Configurable QA API proxy; local fictional auth avoids external Firebase writes/provider delays. | All eight workflows retained and rerun; no tests removed. |

## 3. Frontend changes

- `context/DocumentContext.ts`, `DocumentProvider.tsx`, `services/cloudDocuments.ts`, `firebaseClient.ts`: consent, account-scoped listing, upload/migration status, revisions, on-demand files, identity checks, object-URL cleanup, optional IndexedDB cache and explicit deletion.
- `pages/DocumentVault.tsx`: private cloud controls; separate local/cloud confirmations; per-file save state; upload/update times; reviewed metadata editor/comparison retained; explicit next actions.
- `context/WorkspaceProvider.tsx`, `WorkspaceContext.ts`, `preparationStorage.ts`, `services/cloudPreparation.ts`, `cloudApplications.ts`, `pages/GuidedJourney.tsx`, `MyApplications.tsx`: stable household applicant reference, complete ack verification, duplicate-save protection, local-edit protection, created/saved dates and exact current step; React Context preserved.
- `context/HouseholdContext.ts`, `HouseholdProvider.tsx`, `pages/HouseholdIntelligence.tsx`: additive client UTC creation/edit dates, unchanged IDs/dependency/consent structure.
- `utils/dateTime.ts`: `Intl.DateTimeFormat` local-zone `DD MMM YYYY, hh:mm AM/PM`; invalid/missing timestamps return Not recorded.
- `pages/CitizenWorkflows.tsx`: selected reviewed address proof, explicit minimal metadata-sharing consent and contextual deterministic checks. No names, raw addresses, dates or file bytes sent by this feature.
- `vite.config.ts`, `qa/conftest.py`, existing QA selectors/auth helper: accurate temporary API routing, fictional local authentication, explicit local-clear action name. Existing assertions remain active.

## 4. Backend changes

- `routes/documents.py`: authenticated upload/list/get/file/patch/delete/own-account-clear; strict metadata contracts and bounded IDs/files.
- `services/document_store.py`: named database `maadhyam`, private generation-protected GCS objects, reservation/finalization/delete state machine and optimistic metadata revisions.
- `routes/applications.py`, `routes/household.py`: backward-compatible optional nested household timestamps.
- `services/firestore_store.py`: new application writes use server `created_at`, `updated_at`, `lastSavedAt`; preserve creation on edits; read back committed timestamps before acknowledgment; mixed legacy timestamps remain sortable.
- `routes/citizen_workflows.py`: bounded enum/boolean reviewed context and consent; no AI invocation or invented eligibility/date window.
- `services/ai_guard.py`: authenticate before Vault multipart parsing; actual entire request bounded to 11 MiB; 10 MiB file limit; per-instance admission up to 60 uploads/hour and six/UID/minute. Counters reset per process and are not a hard spending cap.
- `config.py`, `runtime.env.yaml`, `pyproject.toml`, `uv.lock`: explicit bucket setting and direct Cloud Storage dependency; existing Vertex/runtime configuration retained.

## 5. Database changes and timestamps

Reuse `projects/maadhyam-1610/databases/maadhyam` in `asia-south1`. It is a named Standard database, `freeTier=false`; no default-database writes or new database created. Existing application and user records are not migrated destructively.

New collection path: `users/{verifiedUid}/documents/{uuid}`. Record fields: `id`, `filename`, `contentType`, `sizeBytes`, nested existing `metadata`, review `status`, `revision`, `sha256`, `storagePath`, `storageStatus`, committed object `generation`, `createdAt`, `uploadedAt`, `updatedAt`, optional `originalLocalAddedAt`. File bytes/base64/public URLs are absent. Simple owner-collection scans/direct lookups require no composite indexes; no unrelated index configuration was changed.

`createdAt` records initial server metadata creation. `uploadedAt` is set only when object availability is finalized. `updatedAt` is set by successful server changes. Metadata patch cannot replace creation/upload/original-local timestamps. Pending records have no successful upload timestamp.

Applications retain existing `created_at`/`updated_at` keys and add `lastSavedAt`. Old ISO strings and new Firestore Timestamp serialization both become UTC JSON strings. Missing historical fields are not backfilled with invented times. Local draft creation is initially client-recorded; first cloud record creation supplies the authoritative cloud creation date. Failed/conflicting saves leave confirmed dates unchanged.

Household `createdAt`/`updatedAt` remain client-recorded UTC strings in the existing `household_state.members` snapshot; enclosing application server `lastSavedAt` confirms snapshot save time. No extra household collection. Default workspace applicant/legacy member creation remains Not recorded. Rename changes only edit time, preserving stable IDs and associations.

Firestore access is mediated by the existing token verifier and runtime identity. Owner authority comes exclusively from verified Firebase UID, not submitted metadata. All added fields are additive; rollback must preserve data.

## 6. Cloud Storage

- Created `gs://maadhyam-1610-private-vault`, `ASIA-SOUTH1`, Standard, uniform bucket access, enforced public access prevention.
- Soft delete duration 0; no retention lock, active-file lifecycle deletion or extra replication. Confirmed user deletions are permanent.
- Final bucket IAM: runtime `maadhyam-api@maadhyam-1610.iam.gserviceaccount.com` has `roles/storage.objectUser`; project owners retain `roles/storage.legacyBucketOwner` management. No allUsers/allAuthenticatedUsers and no broad viewer/editor object grant.
- Paths: `users/{verifiedUid}/documents/{uuid}/original`. No signed/public URLs.
- Upload reserves pending metadata, writes with `if_generation_match=0`, then finalizes ready with server timestamp. Retry preserves original identity/content and rejects incompatible fields. Final metadata failure leaves recoverable pending state; no unsafe blanket cleanup.
- Preview validates owner/status and reads exact generation through backend, with private no-store response. File signatures are validation checks, **not malware scanning or a guarantee that every PDF/image is structurally readable**.
- Delete tombstones first, deletes exact generation and then metadata; failed deletion remains retryable and cannot be previewed. Bulk clear reports each failed ID. Unrelated applications and collections remain intact.

Evidence: `evidence/m12-cloud/bucket.json`, `bucket-iam.json`, `iam-recovery.json`.

## 7. API documentation

All `/api/documents` operations require `Authorization: Bearer <Firebase ID token>`; `uid` is never accepted as authorization. IDs are canonical UUID strings; filenames cannot contain path separators/control characters. PATCH preserves omitted status/metadata fields and merges supplied metadata atomically. Metadata fields use bounded strings/categories/holder enums and valid ISO dates. Files: PDF, PNG, JPEG; matching extension/MIME/signature; nonempty; actual file size ≤10 MiB, request ≤11 MiB. Multipart truncation/missing required fields is rejected. No sensitive bytes are logged or sent to AI.

| Method / URL | Request | Success | Failures / source |
|---|---|---|---|
| POST `/api/documents` | Multipart `document_id`, `cloud_storage_consent=true`, `fields` JSON, `file` | 201 metadata `{id, revision:2, storageStatus:"ready", uploadedAt:..., ...}` | 400 empty; 401 token; 403 consent; 409 immutable ID/content conflict; 413 size; 415 type/signature; 422 schema/multipart/ID; 429 admission; 503 missing config. `routes/documents.py` |
| GET `/api/documents` | No body | 200 own metadata array, including recoverable pending/deleting states | 401/503/upstream error; same source |
| GET `/api/documents/{id}` | Canonical UUID | 200 own metadata | 401/404/422/503; same source |
| GET `/api/documents/{id}/file` | No body | 200 private binary, exact stored MIME, no-store | 401/404 ownership; 409 unavailable/not-ready; 422 UUID; upstream error; same source |
| PATCH `/api/documents/{id}` | `{revision:2,status:"reviewed",metadata:{category:"address",documentType:"Utility bill",holder:"self"}}` | 200 revision 3, updatedAt advanced, createdAt/uploadedAt preserved | 401/404/409/422/503; same source |
| DELETE `/api/documents/{id}?revision=3` | Revision query | 204; absent own record is idempotent 204 without touching foreign objects | 401/409/422/upstream failure; same source |
| DELETE `/api/documents` | No body; UI explicit confirmation | 200 `{deleted:[...],failed:[...]}` scoped snapshot | 401/503; per-record partial failures reported; same source |

Upload fields example:

```json
{"metadata":{"category":"address","categories":["address"],"documentType":"Utility bill","holder":"self","printedName":"Fictional Applicant","residentialAddress":"Fictional Sample Address"},"status":"reviewed","originalLocalAddedAt":"2026-10-16T08:00:00Z"}
```

Additive existing endpoints:

- POST/PATCH/GET `/api/applications`: existing token/revision validation unchanged; response adds persisted `lastSavedAt`. Household member objects accept optional `createdAt`/`updatedAt`. Existing create/patch examples and 401/404/409/422 semantics remain in `routes/applications.py`. Save response is used only after full payload/ID acknowledgment matches.
- POST `/api/household/assess`: accepts optional timestamp fields on existing member objects; graph/consent checks unchanged; no persistence or AI added.
- POST `/api/citizen-workflows/human-support` and `/rejection-diagnosis`: optional `consentToShareReviewedMetadata` and ≤3 `documentContext` items. Existing public deterministic workflows remain public and do not read cloud records themselves. No personal identity fields accepted in the added context.

```json
{"service":"Passport","blocker":"My address proof was not accepted","consentToShareReviewedMetadata":true,"documentContext":[{"category":"address","documentType":"Utility bill","holderRelationship":"self","addressPresent":true,"datePresent":false,"reviewed":true}]}
```

Human-support response retains `supportChecklist` and adds possible checks to that checklist; rejection retains existing contract and adds `reviewedMetadataGuidance`. Without consent, added context is ignored for guidance. Unreviewed/non-address context yields a request to review/select relevant evidence. No age/expiry acceptance window or official rejection reason is invented. Prompt-like arbitrary document-type text/extra identity fields is rejected (422).

## 8. QA

| Check | Current actual result |
|---|---|
| Backend | **442 passed**; one existing Starlette/httpx deprecation warning; `evidence/m12-backend.xml` |
| Frontend lint | **0 errors, 0 warnings** |
| Frontend build | PASS; existing >500 kB bundle-size advisory remains |
| Full local browser/HTTP | **208 passed**, including unordered-map timestamp regression; `evidence/m12-final/tests.xml` |
| New focused cases | 12 passed in latest focused run; overlap the full total, do not add |
| Initial four-step reproduction | 4 passed against M11 baseline; not a production-hosted result |
| Production hosted | Pending deployment |
| Security/Storage/Firestore | 33 new backend cases included in 442; local browser transport mocked, real cloud verification pending |
| Actual Gemini calls in M12 | **0** so far |

No existing tests removed/disabled. Intermediate full runs found proxy/auth test isolation, timestamp model and offline cache problems; fixes were verified, not counted as success before rerunning. Screenshots/logs stay local; small JUnit/result receipts are portable. The user's pre-existing whitespace change causes working-tree `git diff --check` to report that unrelated file; intended staged changes must pass separately.

## 9. Google Cloud change log

Executed so far, in order:

1. Read actual Run service/revision/config, Storage bucket inventory, named Firestore, registry, billing linkage. Reused existing project/service/registry/database/identity/Vertex configuration. Prior revision confirmed `maadhyam-api-00002-grr`.
2. Attempted Hosting release REST read: 403 quota-project error. Retried with `x-goog-user-project: maadhyam-1610`, succeeded. No API enabled. Previous Hosting release `sites/maadhyam-1610/releases/1792177518101000`, version `cf7df81ce2fc24a9`.
3. Verified candidate bucket absence (404). Created one regional private Standard bucket with uniform access, public access prevention and soft delete 0. Granted runtime bucket-only Object User.
4. Removed automatic legacy viewer/editor object grants. First replacement also removed owner bucket-management convenience grant. Actual 403 exposed that mistake; recovered using existing project-owner IAM authority and a temporary Storage Admin binding conditioned **only** to the new bucket. Restored projectOwner legacyBucketOwner management and runtime Object User. Removed temporary project binding and verified it absent. Final bucket/config readback succeeded. No runtime administrative grant or unrelated policy change remains.
5. Budget read now succeeds: existing INR 500 monthly project budget, 50%/90%/100% current-spend thresholds, credits included. Alert recipient delivery, actual spend and credit balance/expiry remain unverified. No billing budget change performed.

Cloud Build `7a0ba752-16ff-43b8-b582-f30e2a56df03` succeeded for backend source `d191ee8714e9479c9909d252ce2bfb51bd8a931c`. Image tag `m12-d191ee8714e9`, digest `sha256:9e7927073ebd39f0b27f5e28c1691a3557b1fef6899ea5591375c99cbd7f1521`. First build passed container checks but remains undeployed after the partial-PATCH review found a data-integrity defect. Corrective source will receive a second immutable build. Run/Hosting deployment pending. No paid Gemini invocation. Bucket storage and operation charges, build/registry charges and named Firestore operations are billable. Small fictional test objects will be removed explicitly; no active-file lifecycle job or always-on service created. Min/max Run instances remain 0/2.

Every procedure, including the IAM recovery and quota-project REST read, is in the manual guide. Local evidence captures final IAM/config and rollback references; no credentials/tokens were committed.

## 10. Deployment and rollback

Predeployment Run: `maadhyam-api-00002-grr`, image digest `sha256:22997ae55fff8471d0a518b9e598d61d563487dfbd580ffbd6c9fe2342a06aac`. Previous Hosting version `cf7df81ce2fc24a9`. No revision/version deleted. Deployment must use a new immutable source tag/digest and preserve runtime account, database, Gemini, CPU/memory/concurrency and 0/2 scaling. Coordinate frontend/backend rollback because the previous app lacks cloud Vault APIs; retain all new metadata/objects, users and old records.

## 11. GitHub

Source: [reviewed release branch](https://github.com/swar186j/AIBuildercup-Initial/tree/release/m10-m12-recovery). Initial source `d191ee8714e9479c9909d252ce2bfb51bd8a931c` was pushed with remote equality verified; final corrective source and final remote HEAD are recorded in the deployment receipt. No main merge/default-branch change/force-push authorized or performed.

## 12. Remaining issues / honest evidence limits

- Deployment, hosted acceptance and real bucket operations remain pending at this checkpoint; do not label complete yet.
- Anonymous identity requires retained browser authentication; no account linking/recovery was introduced.
- IndexedDB remains unencrypted optional local cache. Legacy unbound originals require explicit migration to an authenticated identity.
- File signature/MIME/size checks are not malware scanning or complete file-integrity parsing.
- No official government submission/acceptance or invented proof-expiry rule. Existing source freshness limitations remain.
- Per-process upload/AI rate counters reset and do not enforce a project-wide spending cap.
- Historical timestamps remain absent when genuinely unknown; household times are client-recorded, with server-confirmed enclosing saves.

## 13. Manual deployment handoff

[Complete Console, PowerShell/macOS/Linux deployment, database/timestamp inspection, IAM recovery and rollback guide](MAADHYAM_MANUAL_GOOGLE_CLOUD_DEPLOYMENT_GUIDE.md).

## 14. Final release recommendation

**Hold submission sign-off pending the authorized controlled deployment and hosted acceptance.** Local implementation and regression are green, but readiness for the October 18 hackathon cannot be claimed from local results alone.
