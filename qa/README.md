# Local M1–M9 acceptance

Run from any working directory using the repository's existing API virtualenv:

```sh
/absolute/path/to/repo/Maadhyam/apps/api/.venv/bin/python /absolute/path/to/repo/qa/run_final.py
```

The runner builds the frontend, runs backend pytest, starts its own no-credentials API and production preview on temporary localhost ports, checks readiness, collects pytest cases, runs Chromium and HTTP suites, executes all five historical browser suites and stops only its own server process groups in `finally`. It installs nothing and runs no live providers or government submissions. The existing dependencies are sufficient: Python 3.13, Node/npm, API `.venv` with pytest/httpx/Playwright, cached Chromium and web `node_modules`.

Evidence is written to `qa/evidence/final/`. `runner.log` is the top-level execution log when redirected there. `backend.xml`, `browser.xml`, `http.xml`, legacy JSON/logs and `execution.json` are source evidence. `write_final_report.py` regenerates the feature inventory, test matrix, final summary and report from those artifacts. Historical intermediate failures are retained in `final/intermediate/`; they are excluded from final unique-case totals.

For a targeted suite with already-running servers:

```sh
MAADHYAM_TEST_API=http://127.0.0.1:8002 MAADHYAM_TEST_WEB=http://127.0.0.1:5173 \
  Maadhyam/apps/api/.venv/bin/python -m pytest qa -q --tb=short
```

Use a dedicated no-credentials API, never a developer API with live provider credentials. Browser fixtures forward actual request methods/bodies to FastAPI via real HTTP. Only named synthetic failure/provider cases stub responses. Each test has its own context and teardown captures screenshots, runtime/console/network diagnostics and asserted fictional request/response evidence.

Shared fixtures live in `qa/conftest.py`; test modules import only helper functions. `qa/run_legacy.py` resolves scripts and working directories from its own file and forwards all API calls to `MAADHYAM_TEST_API`. The reasoning runner supports `--report`, avoiding working-directory-dependent output. Backend regression must run with the API directory as cwd; the final runner does this automatically.

To run the demo manually, start the API on port 8000 and Vite on 5173. See `IMPLEMENTATION_HANDOVER.md` for commands and data behavior.

## M12.1 consolidated release verification

```sh
MAADHYAM_FINAL_QA_OUTPUT=qa/evidence/m12-1-verification \
  Maadhyam/apps/api/.venv/bin/python qa/run_final.py
```

The current runner also executes zero-warning frontend lint and every `qa` browser module, including M12 persistence, remediation and the M12.1/wireframe regressions. It clears provider settings for local servers; browser authentication is fictional and intercepted, including in the five historical runners. The real-FastAPI household round-trip test overrides persistence with a local memory store while retaining actual request validation/serialization. No production cloud write or paid Gemini call is needed.

`qa/evidence/m12-1-verification/` contains portable final XML/execution/lint/build/legacy receipts. Screenshots, network logs and intermediate failure receipts stay local. See `M12_1_FINAL_BUGFIX_REPORT.md` and `M12_1_MANUAL_CLOUD_DEPLOYMENT_HANDOFF.md` for the release and owner-only deployment checklist.
