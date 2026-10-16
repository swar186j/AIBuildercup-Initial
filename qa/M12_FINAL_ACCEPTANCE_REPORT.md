# M12 QA and submission acceptance

Status: PARTIAL. Public hosted acceptance: BLOCKED.

Date: 2026-10-16. Working tree on swar-initial, base 5d236e5; changes are uncommitted and no push/PR is claimed. Requirements are preserved under qa/requirements/m10-m12. Historical 627-test totals are not reused as current evidence.

Current automated evidence: 450 backend tests passed; frontend lint/build passed; offline paid/free configuration validation passed; six API client checks, four API-origin checks and blank-draft grouping checks passed. Chromium passed 23 scenario groups, including preparation/file/household recovery and two-account isolation, all eight citizen workflows with success/failure at 1440px and 390px, five workspace routes at both sizes, assistant consent/provider failures, keyboard Escape and external-host cold-start retry gating. No uncaught runtime errors were recorded.

Backend coverage retains M1–M9 name/checklist/reasoning/household/dependency/rule/workflow contracts. Historical browser cases that require removed local saving are not counted as current passes. The 23-feature inventory remains a scope reference, not proof of broader official verification or unimplemented real-world guarantees. Real Gemini calls passed independently. All 21 inline Firestore rule scenarios and real synthetic Firebase/Firestore/Supabase lifecycle passed; the temporary users and records were cleaned.

Read-only local SPA/API smoke passed. A modest 12-request/concurrency-4 health sample is recorded separately; it is process liveness, not hosted database/AI throughput. Frontend bundle is about 618 kB uncompressed, with a size warning. No expensive load test was run.

Architecture, deployment/free-host guides, demo/video storyboard, submission narrative, privacy/cost review, handover and current matrix are delivered. Outstanding: public release and two-account hosted E2E, actual video, independent assistive-technology/contrast review, container execution, cloud IAM/monitoring/backup acceptance and automated retention/account-wide erasure. These are not claimed complete.

Evidence: qa/evidence/m10-m12. No production certification, government affiliation or guaranteed eligibility is claimed.
