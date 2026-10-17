# Maadhyam — hackathon guide

Maadhyam helps Indian citizens prepare documents and plan the next steps for government services. It combines a document workspace, evidence comparisons, deterministic checklists, household dependencies and optional Gemini assistance.

- **Demo:** https://maadhyam-1610.web.app
- **Application branch:** `main`
- **Setup and architecture:** [README](README.md)
- **Tests and evidence:** [QA guide](qa/README.md)

## Three-minute walkthrough

1. Open the demo and explore Services and the Passport guided journey.
2. Add a fictional household member and upload a sample from [qa/fixtures](qa/fixtures).
3. Review the document metadata and inspect identity discrepancies.
4. Complete Passport questions and view the source-linked checklist.
5. Open Resolution Planner to inspect blockers, dependencies and next steps.
6. Optionally demonstrate Gemini extraction with explicit fictional-file consent, or cloud saving with its separate consent.

The deterministic preparation flow works without Gemini credentials. Gemini and cloud persistence require configured services. Use fictional data for judging.

## Repository map

| Path | Purpose |
| --- | --- |
| `Maadhyam/apps/web` | React and TypeScript frontend |
| `Maadhyam/apps/api` | FastAPI backend, rules and backend tests |
| `Maadhyam/firebase.json` | Hosting configuration |
| `qa` | Browser tests, fictional fixtures and release evidence |

## Before sending the submission

- Share the application branch link in the README; verify that judges can access it.
- Check the live demo manually and record a short walkthrough if the event requires one.
- Use the setup and verification commands in the README for a fresh checkout.
- Describe Gemini as optional assistance and disclose the prototype limitations in the README.
- Include team details, video and event-specific requirements in the event submission form.

Local dependencies, repair backups, demo sessions and downloaded tools are excluded from Git. Historical Git commits can still contain previously tracked files; this cleanup does not rewrite history.
