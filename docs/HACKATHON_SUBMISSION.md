# Maadhyam — citizen preparation workspace

Maadhyam helps citizens organize evidence, understand possible inconsistencies and prepare next steps before interacting with government services. The implementation combines a source-linked passport journey, a private document vault, reviewed metadata, explainable comparisons, dependency planning, household consent and eight advisory citizen workflows.

React/TypeScript provides the citizen UI; FastAPI provides deterministic assessment and authenticated persistence. Firebase Authentication identifies users, Firestore stores owner-scoped metadata and Google Cloud Storage is the selected private file target; Supabase remains a preserved legacy source until verified migration. Gemini supplies opt-in fictional-document extraction and grounded assistant guidance. The intended public architecture uses Firebase Hosting and Cloud Run with Secret Manager and managed identities.

Repository: https://github.com/swar186j/AIBuildercup-Initial . Public deployment URL: BLOCKED pending deployment identity, approved billing and provisioning. Setup and deployment: docs/DEPLOYMENT.md. Demo: docs/DEMO_SCRIPT.md. Architecture: docs/ARCHITECTURE.md.

Evidence: 450 backend tests, frontend lint/build, 23 local browser scenario groups, real synthetic Gemini assistant/extraction checks and local HTTP smoke are recorded under qa/evidence/m10-m12. These demonstrate the recorded local scope; they are not a claim of production certification or public hosted acceptance.

Limitations: passport-specific source-linked preparation is broader than other catalog cards; rules need ongoing authority review. Names, relationships and evidence are not officially verified. AI extraction is restricted to fictional demo documents. Cloud deployment, hosted authenticated E2E, assistive-technology review and recorded demo video remain outstanding. User data must be treated as sensitive; provider context is minimized and document review is mandatory.

Roadmap: approved public pilot, hosted two-account acceptance, centralized durable quotas, rule freshness operations, account-wide erasure orchestration and additional authority-reviewed service journeys.
