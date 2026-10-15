# Executed commands

Commands ran in this workspace on 2026-10-15. Backend/browser dependencies and Chromium were already installed. No local testing dependency was installed.

- Baseline: from `Maadhyam/apps/api`, `.venv/bin/python -m pytest -q` -> `backend-baseline.log`.
- Final backend: from root, `MAADHYAM_GEMINI_API_KEY='' Maadhyam/apps/api/.venv/bin/python -m pytest Maadhyam/apps/api/tests -q --junitxml=qa/evidence/backend-final.xml` -> `backend-final.log`.
- Dedicated backend: from `Maadhyam/apps/api`, `MAADHYAM_GEMINI_API_KEY='' .venv/bin/python -m uvicorn maadhyam_api.main:app --host 127.0.0.1 --port 8001`.
- Frontend/server: existing localhost:5173 Vite instance reused after sandbox restrictions initially hid it. Original localhost:8000 backend also reused for older local-only browser scripts. Both servers were left under their original owner's control.
- Browser + HTTP: from root, `Maadhyam/apps/api/.venv/bin/python -m pytest qa/test_browser.py qa/test_http.py -q --tb=short --junitxml=qa/evidence/acceptance-final.xml` -> `acceptance-final.log`.
- Legacy suites: from `Maadhyam/apps/api`, `.venv/bin/python tests/run_frontend_functional.py`, `tests/run_reasoning_e2e.py`, `tests/run_vault_e2e.py`, `tests/run_m9_browser_e2e.py`, `tests/run_frontend_tests.py`. JSON-output scripts received `--report ../../../qa/evidence/legacy-*-final.json`; logs captured under the same prefix. No live flags were passed.
- Build: from `Maadhyam/apps/web`, `npm run build` -> `frontend-build-final.log`.
- Fixture generation: bundled Python `qa/generate_fixtures.py`; PDFs rendered with Poppler for visual inspection; `pypdf` confirmed fictional warnings on all three pages.
- Whitespace verification: `git diff --check` passed.
- Matrix/results: `python3 qa/write_report.py` reads the actual final test artifacts.
