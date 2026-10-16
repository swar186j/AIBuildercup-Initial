# External dependencies and production boundaries

Local acceptance uses fictional documents, local FastAPI HTTP, real Chromium and deterministic provider stubs. None of the following is counted as a passing local integration.

| Dependency | Status | Required next action |
|---|---|---|
| Live Gemini generation | NOT TESTED | In a separately authorized environment, configure a protected provider key and verify consent, current model access, latency, rate limits, grounding and billing. This run empties Gemini/Google key environment variables. |
| Live OCR extraction | NOT TESTED | Separately authorize a provider-backed accuracy evaluation on a labeled fictional PDF/PNG/JPEG corpus; measure fields, uncertainty and manual correction. Stubbed extraction proves the integration contract, not OCR accuracy. |
| Government rule freshness | NOT TESTED | An accountable reviewer must compare stored provenance and applicable requirements with current official sources, approve a complete versioned rule pack and operate the source-review process. A source hash is not a historic rule pack. Hypothetical UI proposals never change active rules. |
| Government submission integrations | NOT IMPLEMENTED | Obtain authority-supported interfaces, credentials, agreements and explicit submission authorization. Preparations and demo status cards are never government applications. |
| Real human support | NOT IMPLEMENTED | Connect an authorized helpdesk/agent workflow with consent, contact handling and operational ownership. The current feature prepares a helpdesk checklist and sends no message. |
| Real authentication and cross-account authorization | NOT IMPLEMENTED | Introduce identity, tenancy, server-side authorization, consent audit and account isolation before shared/private multi-user use. Local household labels and isolated browser contexts do not provide these controls. |
| Production hosting and security | NOT TESTED | Separately assess HTTPS, secret management, origin restrictions, dependency updates, abuse controls, monitoring, backups/deletion, data protection, capacity and an accessibility audit. No deployment occurred. |

## Local data boundaries

Vault files default to memory and require separate opt-in IndexedDB saving. Preparations default to memory and require explicit browser-local saving consent. Preparation records contain answers, applicant label/DOB, wizard progress and document IDs; they do not copy files. Both stores are unencrypted browser storage and are intended for fictional demo data. Revocation deletes the relevant saved copies while preserving the current session. Storage-denial errors remain visible; when local deletion is denied, the UI directs the user to browser site-data settings.

Household member labels, dependencies and relationship claims are session-only. One applicant label is fixed to the local `applicant` identity; its display label is editable. Multiple named members, including duplicate display names, have separate IDs. There are no independent household accounts or multiple persisted households. Reload resets the graph. Persisted Vault files retaining an unavailable owner are not silently relabeled as applicant identity. Unassigning/deleting a member keeps their file as other evidence.

Name matching, address consistency, proof substitution, root-cause categories, correction paths, deadlines and visit estimates are advisory models. They do not establish legal identity history, residency continuity, proof equivalence, authority acceptance, official fees, processing times or eliminated visits. Life-event and multi-department catalogs are explicitly illustrative. Live source monitoring was not exercised or certified by this run.
