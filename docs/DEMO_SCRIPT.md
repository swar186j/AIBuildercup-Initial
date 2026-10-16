# Synthetic demo and acceptance script

Use fictional names and generated test files only. No government affiliation, eligibility guarantee or official document verification is claimed.

1. Open the app at the verified deployment URL (currently localhost:5173; public deployment BLOCKED). Sign in with synthetic account A. Show the problem: different evidence, spelling and office dependencies create confusion.
2. Find Services → Passport → fresh journey. Enter a fictional applicant name and date, answer questions, navigate away, return and reload. Confirm the same preparation ID and saved values; opening a deleted ID must not create a new preparation.
3. Upload `qa/fixtures/fictional_aadhaar.pdf` to the private cloud vault. Explicitly confirm fictional data before Gemini extraction. Review and edit extracted metadata; mark it reviewed. Explain that extraction is a candidate, not official verification.
4. Compare a second fictional record with a name mismatch, show discrepancy reasoning and the source-linked passport checklist. Only select reviewed applicant evidence.
5. Complete planner prerequisites, show dependent tasks, save and reload. Add a fictional household member and document-sharing consent, then withdraw consent and verify excluded evidence.
6. Ask Gemini what preparation is missing after explicit fictional-metadata confirmation. Show grounded guidance and the official source reference. A provider failure must show a recoverable error and local guidance remains available.
7. Show all eight citizen workflows: human assistance, life event, multi-department rules, rejection diagnosis, legacy recovery, authority bottlenecks, deadline rescue and visit reduction. Explain their advisory/sample boundaries.
8. Sign out; account B must not see A's applications, documents or household. Sign back into A and resume. Repeat on mobile and use Tab/Escape for the assistant dialog.
9. Delete the test document and preparation, reload and confirm removal. Verify a previously copied private download URL fails without the owner's token. Remove all synthetic account data created for the demo.

Video storyboard (3 minutes): 0:00 problem; 0:20 architecture/login; 0:40 passport preparation; 1:05 cloud upload/Gemini review; 1:40 discrepancy/planner; 2:10 household/privacy; 2:35 save/resume and mobile; 2:50 limitations and next steps. Use screenshots under qa/evidence/m10-m12, clearly labelled as local synthetic acceptance. A recorded video is NOT IMPLEMENTED.
