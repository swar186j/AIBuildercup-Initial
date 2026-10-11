# Draft1 backend

FastAPI backend for the AI Builder Cup evidence workflow. This is an intake MVP, **not** a production-grade case management system. Uploaded documents are saved locally under `data/uploads`; metadata is returned in the response but not persisted. No AI analysis, officer review, authentication, or Firestore is implemented yet.

## Start

From this directory:

```bash
uv sync --extra dev
uv run python -m uvicorn api.main:app --reload --port 8000
```

If you already have `apps/api/src/api`, merge the files under `src/api/` into that directory instead of nesting another backend.

Check:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/api/health
- http://127.0.0.1:8000/docs

## APIs

- `GET /api/health` — health status, compatible with the existing frontend.
- `POST /api/evidence/submit` — multipart form: `scheme` (`ESIC`, `PMAY-G`, `GENERAL`), `applicant_name`, optional `reference_id`, and `document` (PDF/PNG/JPEG, 10 MB maximum). Returns a receipt, not an eligibility decision.

Example:

```bash
curl -X POST http://localhost:8000/api/evidence/submit \
  -F 'scheme=ESIC' -F 'applicant_name=Demo User' \
  -F 'reference_id=TEST-001' -F 'document=@sample.pdf'
```

## Tests

```bash
uv run pytest -q
```

## Security / limitations

Use synthetic documents only. This demo stores files unencrypted on local disk; it does not authenticate users, inspect for malware, enforce retention/deletion policies, or provide durable database records. Do not deploy with real citizen documents until those safeguards are implemented. Content signature checks are basic and not a substitute for full document validation.
