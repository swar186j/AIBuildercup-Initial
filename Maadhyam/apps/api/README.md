# Phase 2C: safer official-source drift monitoring

Replace `apps/api/src/maadhyam_api/routes/passport_source_monitor.py`.
Add `apps/api/tests/test_passport_monitor.py`.

Run in `apps/api`:

    uv run pytest -q
    uv run python -m maadhyam_api.routes.passport_source_monitor

`review-required` is EXPECTED until an approved baseline exists. The monitor intentionally does NOT promote a fetched webpage into an approved government rule. A legitimate approval must review source content, validate actual document guidance, then store `passport_approved_baselines.json` separately with `sources: {source_id: {url, sha256, fingerprint_method, approved_at}}`.

For cloud deployment, set `MAADHYAM_PASSPORT_SOURCE_STATE` to a persistent writable mounted location or change the monitor to write object storage. The current default writes beside Python source and is not durable on Cloud Run. Do not schedule until persistent storage and alerting are configured.
