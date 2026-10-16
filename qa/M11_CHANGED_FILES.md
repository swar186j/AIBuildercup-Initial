> **17 October remediation:** Current status is **COMPLETE**; lint is 0/0 and fresh tests are 409 backend, 195 local and 26 hosted (two mocked AI UI cases). See [final remediation report](M11_FINAL_REMEDIATION_REPORT.md). The initial deployment/results below are historical; billing visibility remains permission-blocked with [owner instructions](M11_BILLING_OWNER_ACTIONS.md).

# M11 changed files

Intentional M11 files relative to original checkpoint `f2a0e4e`. The pre-existing tunnel log and local browser/generated files are excluded.

- `.gitignore`
- `Maadhyam/.firebaserc`
- `Maadhyam/apps/api/.dockerignore`
- `Maadhyam/apps/api/.env.example`
- `Maadhyam/apps/api/.gcloudignore`
- `Maadhyam/apps/api/Dockerfile`
- `Maadhyam/apps/api/cloudbuild.yaml`
- `Maadhyam/apps/api/pyproject.toml`
- `Maadhyam/apps/api/runtime.env.yaml`
- `Maadhyam/apps/api/src/maadhyam_api/config.py`
- `Maadhyam/apps/api/src/maadhyam_api/main.py`
- `Maadhyam/apps/api/src/maadhyam_api/routes/extraction.py`
- `Maadhyam/apps/api/src/maadhyam_api/routes/gemini.py`
- `Maadhyam/apps/api/src/maadhyam_api/routes/intelligence.py`
- `Maadhyam/apps/api/src/maadhyam_api/services/ai_guard.py`
- `Maadhyam/apps/api/src/maadhyam_api/services/gemini_provider.py`
- `Maadhyam/apps/api/tests/test_m4_m9_acceptance.py`
- `Maadhyam/apps/api/tests/test_vertex_provider.py`
- `Maadhyam/apps/api/uv.lock`
- `Maadhyam/apps/web/src/services/citizenIntelligence.ts`
- `Maadhyam/apps/web/src/services/cloudApplications.ts`
- `Maadhyam/apps/web/src/services/documentExtraction.ts`
- `Maadhyam/firebase.json`
- `qa/M11_CHANGED_FILES.md`
- `qa/M11_DEPLOYMENT_REPORT.md`
- `qa/M11_KNOWN_LIMITATIONS.md`
- `qa/M11_ROLLBACK.md`
- `qa/M11_TEST_MATRIX.csv`
- `qa/M11_TEST_RESULTS.md`
- `qa/conftest.py`
- `qa/evidence/m11-backend.xml`
- `qa/evidence/m11-build-final.json`
- `qa/evidence/m11-build.json`
- `qa/evidence/m11-cloud-readiness.json`
- `qa/evidence/m11-final-live.json`
- `qa/evidence/m11-final-regression/tests.xml`
- `qa/evidence/m11-firestore.json`
- `qa/evidence/m11-hosted-references.json`
- `qa/evidence/m11-hosted/results.json`
- `qa/evidence/m11-hosting-before.json`
- `qa/evidence/m11-hosting-final.json`
- `qa/evidence/m11-logs-summary.json`
- `qa/evidence/m11-release-summary.json`
- `qa/run_release_local.py`
- `qa/test_browser.py`
- `qa/test_completion.py`
- `qa/test_final_journeys.py`
- `qa/verify_hosted_references.py`
- `qa/verify_hosted_release.py`
