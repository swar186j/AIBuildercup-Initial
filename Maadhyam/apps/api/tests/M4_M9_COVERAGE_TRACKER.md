# Maadhyam M4–M9: deep coverage tracker

**Baseline reported by user:** 63 backend tests passing; 7/7 frontend smoke tests passing. This is *not* full feature coverage. The new deep tests below are **not yet executed on the user's Windows checkout**.

| ID | Area | Scenario | Automation | Status |
|---|---|---|---|---|
| M4-01 | Vault | Empty vault / no records | New backend | Not yet run |
| M4-02 | Vault | Unreviewed metadata excluded | New backend | Not yet run |
| M4-03 | Vault | Reviewed self-holder count | New backend | Not yet run |
| M4-04 | Vault | Name, DOB, address mismatches | New backend | Not yet run |
| M4-05 | Vault | Cosmetic whitespace, case, punctuation | New backend | Not yet run |
| M4-06 | Vault | Family records excluded from self matching | New backend | Not yet run |
| M4-07 | Vault | OCR accuracy on fictional image/PDF | Manual/integration | Pending |
| M4-08 | Vault | File validation, size, format, malicious content | Integration/security | Pending |
| M4-09 | Vault | Refresh/persistence/deletion and privacy | Integration | Pending |
| M5-01 | Journey | Missing identity/address/birth categories | New backend | Not yet run |
| M5-02 | Journey | Reissue-specific review | New backend | Not yet run |
| M5-03 | Journey | Minor guardian review | New backend | Not yet run |
| M5-04 | Journey | Correct official eligibility/checklist by scenario | Rule-backed integration | Pending |
| M5-05 | Journey | Current source version, effective date, provenance | Integration | Pending |
| M6-01 | Planner | Conflict resolution tasks | New backend | Not yet run |
| M6-02 | Planner | Task dependencies valid | New backend | Not yet run |
| M6-03 | Planner | Official verification before appointment prep | New backend | Not yet run |
| M6-04 | Planner | Alternative proof paths and costs | Functional | Pending |
| M7-01 | Reasoning | Conservative what-if summary | Existing implementation, shallow | Needs deep testing |
| M7-02 | Reasoning | True minimal-correction optimizer | Not implemented | Pending |
| M7-03 | Reasoning | Cycles/deadlocks and deadline rescue | Not implemented | Pending |
| M8-01 | Family | Family-only proof not applicant proof | New backend | Not yet run |
| M8-02 | Family | Parent/spouse/other grouping | New backend | Not yet run |
| M8-03 | Family | Relationship verification, guardian scenarios | Not implemented | Pending |
| M9-01 | Assistant | Local chat on documents/family | New backend | Not yet run |
| M9-02 | Assistant | Gemini fictional-data consent enforced | New backend | Not yet run |
| M9-03 | Assistant | Injection resistance, cited sources, uncertainty | Integration | Pending |
| M9-04 | Assistant | Multi-turn memory and tool-grounded answers | Not implemented | Pending |
| SEC-01 | Cross-cutting | Invalid enum, lengths, 60-doc limit | New backend | Not yet run |
| SEC-02 | Cross-cutting | No automatic official approval | New backend | Not yet run |
| SEC-03 | Cross-cutting | No fabricated deadline | New backend | Not yet run |
| E2E-01 | Full journey | Fictional Aadhaar/PAN/birth certificate → assessment → resolution → assistant | Manual + browser | Pending |
| E2E-02 | Full journey | Conflicting DOB and name with multiple family members | Manual + browser | Pending |
| E2E-03 | Full journey | Refresh, edit metadata, rerun, verify changes propagate | Browser | Pending |

## Definition of done for each milestone

Feature implementation + valid input + invalid input + edge cases + cross-module behavior + privacy/security + regression test + evidence of observed PASS. Mark **Done** only after these checks pass. Do not infer real-world Passport Seva acceptance from metadata categories.

## Run new backend tests (Windows CMD)

Copy `test_intelligence_deep.py` to `apps\api\tests\test_intelligence_deep.py` and run from `apps\api`:

```cmd
uv run pytest tests\test_intelligence_deep.py -q
uv run pytest -q
```

**If tests fail:** share exact failures. A failed test can reveal a bug *or* a test assumption that needs correction; don't blindly change working behavior.
