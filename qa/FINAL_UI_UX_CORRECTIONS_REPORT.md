# Maadhyam consolidated UI/UX corrections

Release branch: `release/m10-m12-recovery`. Baseline: `4efdb011e4b82b8b55429f290ae16295c5e30df9`. Date: 18 October 2026 (Asia/Kolkata).

## Changes and root causes

| Acceptance | Root cause | Result and validation |
|---|---|---|
| UX-01 Dashboard hero | Resume/start action used preparation state unnecessarily; heading relied on inline wrapping. | Only Explore services remains, linking to `/services`. Two block spans intentionally separate the heading; responsive type preserves wrapping at narrow widths. Navy background, teal accent and decorative ring remain. Chromium checks 375/768/1024/1440px. |
| UX-02 Quick links | Explanatory availability copy occupied the quick-navigation label. | Replaced with a semantic Quick links heading. Existing Passport/Aadhaar/EPFO links and destinations retained. |
| UX-03 Assistant | Suggestions were permanently expanded; route detection omitted Services, Household and Workflows. Common product questions always went through evidence-oriented backend chat. | Accessible toggle with expanded state, controls association and rotating chevron; collapse choice and conversation persist across routes/reopening. Eight route contexts and 24 deterministic local product prompts; free-form Passport preparation request handled locally. Optional Gemini still uses existing consent and authenticated API path. One close control; independently scrolling messages and suggestions; small-height default collapse. |
| UX-04 Services | Flat discovery cards treated umbrella and individual actions equally. | Added an in-memory family projection; retained flat contract and all source IDs. Native keyboard-operable details expose children within Services. Matching children auto-expand within parent context; category filters, pagination, empty/reset states and official reference remain. Passport is the sole guided route; other parents/children display Coming Soon without launch actions. |
| UX-05 Page widths | Three page roots imposed max-w-5xl/6xl inside the shared layout; Vault also had a separate 1560px cap revealed at 1920px. | Removed nested caps, including Vault’s redundant cap; all affected content now inherits AppLayout's max-w-[1800px] and px-5/md:px-9/xl:px-12. Household inputs retain the established max-w-2xl readable field width. Boundary checks compare actual page roots across Dashboard, Vault, Workflows and all three affected pages at 375/768/1024/1280/1440/1920px. |
| UX-06 Related regressions | Short panels could scroll their outer ancestor when adding chat messages; duplicate floating close control consumed space. | Message scrolling is limited to the message scroller; one close button and Escape restore focus. Composer, history, draft input, narrow-height layout and responsive overflow are regression checked. Existing persistence, ownership, Vault and Passport suites retained. |

UX-06 denotes the related consistency checks in section 7 of the request; there was no separately defined sixth defect.

## Catalogue migration

Before: **256 unique flat records** (including three explicitly prominent umbrella services), 18 category filters. After: **30 unique parent families, 250 unique children**. Six existing records (Passport, Aadhaar, EPFO, Birth Registration, Death Registration and Marriage Registration) serve as parent summaries. Thus 250 children + six source-backed summaries preserve all 256 source records; the other 24 families are discovery groupings, not new government services.

The compatibility export `governmentServices` and `filterGovernmentServices` remain intact. The Services page consumes `serviceFamilies` and `filterServiceFamilies`. No API, backend catalogue, route, dependency or cloud data schema changed. [Complete source-ID mapping](evidence/ui-ux-corrections/catalogue-mapping.json) records every assignment. Specific families take priority; remaining entries map once to their existing primary editorial category. PAN–Aadhaar linking belongs to Income Tax; voter entries belong to Voter Services; EPF/EPS entries belong to EPFO. No child is duplicated across families. Existing source titles, descriptions, scope and official portal attribution are retained; no authorities, fees or government eligibility rules were invented.

Search regressions cover every source title and Aadhaar, PVC, birth certificate, driving licence, PAN, Passport, PM Kisan, category combinations, whitespace, reset and no results. Tests prove unique family IDs/titles, unique child IDs, valid parent assignment, exact source coverage and no standalone duplicate child tiles.

## Validation and evidence

All local automated acceptance checks for **UX-01, UX-02, UX-03, UX-04, UX-05 and UX-06 PASS**. Physical-device keyboard behavior remains a manual verification limitation below. Portable receipts: `qa/evidence/ui-ux-corrections/`; full local per-test diagnostics: `qa/evidence/ui-ux-corrections/screenshots/`. Curated screenshots cover the four dashboard sizes, catalogue columns, eight assistant contexts, five assistant viewport sizes and eighteen affected-page width comparisons. `review/` contains the visual inspection captures.

Security audit: `npm audit --omit=dev` reports **4 high**, 0 critical, 0 moderate. The affected chain is firebase → @firebase/firestore / @firebase/firestore-compat → @grpc/grpc-js, advisories GHSA-m9gg-hp2v-232j and GHSA-f596-whhp-79r4. npm proposes Firebase 9.14.0, a major downgrade; it was not applied. Locked Firebase 13 and all dependency versions are preserved. Full machine-readable findings: [npm-audit.json](evidence/ui-ux-corrections/npm-audit.json).

Limitations: Chromium viewport resizing checks small-height behavior but does not constitute a physical-device keyboard test. Local cloud regressions use fictional isolated providers; production smoke uses a fresh browser account and does not mutate production Firestore/Storage records. No paid Gemini calls are used. Production cloud-write round trips and other browser engines are outside this run.

## Exact modified source and QA files

- `.gitignore` — keep portable release receipts and curated screenshots; retain raw local diagnostics without committing them.
- `Maadhyam/apps/web/src/pages/Dashboard.tsx` — hero and Quick links.
- `Maadhyam/apps/web/src/pages/Services.tsx` — family cards and child discovery/search.
- `Maadhyam/apps/web/src/data/governmentServices.ts` — compatibility-preserving family projection.
- `Maadhyam/apps/web/src/data/assistantGuidance.ts` — eight route contexts and deterministic product guidance.
- `Maadhyam/apps/web/src/services/citizenIntelligence.ts` — local guidance through existing assistant service entry point.
- `Maadhyam/apps/web/src/components/AIAssistant.tsx` — accessible collapse, route suggestions, links, focus and contained scrolling.
- `Maadhyam/apps/web/src/index.css` — responsive hero and assistant sizing.
- `Maadhyam/apps/web/src/pages/MyApplications.tsx` — shared page width.
- `Maadhyam/apps/web/src/pages/ResolutionPlanner.tsx` — shared page width.
- `Maadhyam/apps/web/src/pages/HouseholdIntelligence.tsx` — shared width and readable fields.
- `Maadhyam/apps/web/src/pages/DocumentVault.tsx` — remove redundant width cap to match shared layout at 1920px.
- `Maadhyam/apps/api/tests/run_frontend_functional.py` — exercise API failure with a metadata question, since Passport product guidance now intentionally works offline.
- `qa/test_service_catalogue.py` — retain flat catalogue/seed/route checks; test the new hierarchy and search UI.
- `qa/test_ui_ux_corrections.py` — dashboard, all route prompts, local responses, focus/collapse/history, viewport and boundary regressions.
- `qa/verify_ui_ux_hosted.py` — fresh-profile hosted smoke.
- `qa/FINAL_UI_UX_CORRECTIONS_REPORT.md` and `qa/FINAL_DEPLOYMENT_AND_SMOKE_TEST_REPORT.md` — acceptance and deployment handoff.
- Intended release receipts and curated public screenshots under `qa/evidence/ui-ux-corrections/`.

No package manifest/lock, Firebase configuration, backend application source, Dockerfile, Cloud Build configuration or application routes were modified. `.DS_Store` and `Maadhyam_M12_source.zip` were preserved and excluded.

## Executed final checks

| Command/check | Result |
|---|---|
| `cd Maadhyam/apps/web && npm ci` | PASS; locked dependencies installed, Firebase 13.0.0 retained. Initial restricted-network attempt failed; the authorized retry succeeded. |
| `npm run lint -- --max-warnings 0` | PASS, zero warnings. |
| `npm run build` | PASS, TypeScript and Vite; existing large-chunk advisory (750.37 kB JS). |
| `npm audit --omit=dev` | FINDINGS: exit 1, four high advisories, documented above; not treated as a correctness-test pass. |
| `uv sync --extra dev --cache-dir /tmp/maadhyam-uv-cache` | PASS; 70 resolved, 69 installed packages checked. |
| API virtualenv `python -m pytest -q` via full runner | PASS: 463 tests; one existing Starlette/httpx deprecation warning. |
| `MAADHYAM_FINAL_QA_OUTPUT=qa/evidence/ui-ux-corrections/final Maadhyam/apps/api/.venv/bin/python qa/run_final.py` | PASS: backend 463, browser/catalogue 284, HTTP 18; all five historical runners exit 0; owned servers stopped, live providers disabled. |
| Final compact-toggle polish: lint/build plus `qa/run_release_local.py qa/test_ui_ux_corrections.py qa/test_service_catalogue.py qa/test_final_journeys.py::test_assistant_focus_escape_and_stale_reset` | PASS: 59 tests, including all new UI tests, complete hierarchy/search tests and stale-reset/focus regression. Expanded suggestions cannot clip the composer or header. |
| `git diff --check` | PASS before staging; staged validation also required before commit. |

The first exploratory run identified focus restoration, a stale toggle test locator and Vault’s 1920px cap. Those were repaired; a household-copy mismatch occurred while its final wording was being updated. A historical API-failure test used the now-offline Passport question; it now uses a metadata question to preserve real transport-failure coverage. Exploratory logs remain local. Final suite receipts are under `qa/evidence/ui-ux-corrections/final/`; `polish-tests.xml` is the final 59-case focused run. Curated final screenshots are committed under `qa/evidence/ui-ux-corrections/comparison/`.
