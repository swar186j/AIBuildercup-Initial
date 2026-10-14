# Maadhyam M4 — actual implementation hardening (Batch 4)

This batch changes production code, not only tests. It keeps existing API routes and payloads backward-compatible, except **duplicate document IDs now correctly return HTTP 422**.

## Replace files individually

1. `intelligence.py` → `apps\api\src\maadhyam_api\routes\intelligence.py`
2. `test_intelligence_hardening.py` → `apps\api\tests\test_intelligence_hardening.py` (new)
3. `test_passport_integration.py` → `apps\api\tests\test_passport_integration.py` (replace old characterization test; required to avoid an intentionally outdated expectation)

**Before replacing** back up your current `intelligence.py` and `test_passport_integration.py` in a folder outside `apps/api/tests`.

From Windows CMD in `apps\api`:

```cmd
uv run pytest tests\test_intelligence_hardening.py -v
uv run pytest -q
```

Frontend smoke suite after starting API and web dev servers:

```cmd
uv run python -u tests\run_frontend_tests.py
```

## Functionality added

- Rejects duplicate document IDs (including casing and whitespace differences) and blank/whitespace IDs.
- Normalizes valid DOB formats `YYYY-MM-DD` and `DD/MM/YYYY` before comparing documents.
- Flags invalid or ambiguous DOB formats instead of silently treating them as valid.
- Accepts optional extraction provenance (`extractionSource`: `manual`/`ocr`/`gemini`, `extractionConfidence`: 0–1) and flags low-confidence reviewed machine extractions for manual recheck.
- Returns `executionOrder`, a dependency-safe topological task order; keeps `tasks` unchanged for existing clients.
- Does **not** automatically decide document validity or passport eligibility.

## Honest test status

Python syntax was checked here. Your local project test run is still required; do not mark these tests passed until you run them. Previous baseline: 119 backend and 7 frontend passing. This batch does not implement M5–M9 advanced functionality, OCR of real PDF bytes, or production storage.
