# M12.1 Services catalogue expansion

17 October 2026. Branch `release/m10-m12-recovery`. Baseline: `986984198366c8ffab222eb160558217f7d016d5`.

## Delivered scope

256 service tiles: **255 Coming Soon**, **1 guided preview** (Passport Seva). All **249 seed references** across groups A–R map to exactly one catalogue record per reference. The two repeated concepts are grouped; two preserved overview cards and seven researched additions account for the final count. This is a curated discovery catalogue, not a claim to list every government service.

Passport remains the only actionable card, with “Guided preview available” and its existing `/services/passport` link. Aadhaar and EPFO remain prominent overview cards with Coming Soon. Unsupported cards are semantic articles with no buttons, links, form fields, fake submission, release dates or supported routes. Platform/channel listings explicitly identify their role; Maadhyam does not claim integration or government affiliation.

## Categories and exact tile inventory

The following 18 citizen-facing groups map to the National Portal's 18 broad categories. Counts are primary assignments and sum to 256. Secondary assignments make overlapping records discoverable from both filters without duplicating tiles.

| Citizen-facing category | National Portal category | Primary tiles |
|---|---|---:|
| Citizenship & Identity | Citizenship, Visa & Passports | 12 |
| Certificates & Family | Welfare of Families | 26 |
| Transport & RTO | Driving & Transport | 18 |
| Taxes & Finance | Money & Taxes | 22 |
| Land & Housing | Housing & Local services | 16 |
| Utilities & Infrastructure | Infrastructure & Industries | 16 |
| Health & Wellness | Health & Wellness | 11 |
| Employment & Labour | Jobs | 13 |
| Pensions & Welfare | Benefits & Social development | 21 |
| Education & Scholarships | Education & Learning | 14 |
| Agriculture & Rural Services | Agriculture, Rural & Environment | 15 |
| Business & Self-employment | Business & Self-employed | 16 |
| Legal & Grievances | Justice, Law & Grievances | 18 |
| Travel & Tourism | Travel & Tourism | 4 |
| Sports & Culture | Youth sports & Culture | 4 |
| Digital & Communications | Science, IT & Communication | 8 |
| Defence & Overseas Welfare | Defence & Foreign affairs | 7 |
| Governance & Citizen Services | Governance & Planning | 15 |

## Research and normalization

Official references consulted on 17 October 2026; no whole-directory scraping was performed. Titles describe service families without asserting eligibility, fees, deadlines or uniform online availability. Some official homepages resisted direct extraction; official indexed pages were used for terminology. The National Portal directory is dynamic; its extracted shell's zero-count placeholders were not treated as directory totals.

- [National Portal categories](https://www.india.gov.in/category): all 18 broad categories and mapping above.
- [National Government Services Portal](https://services.india.gov.in/feed/index?ln=en) and [full category directory](https://www.india.gov.in/services/services-by-category): official discovery and central/state categorisation; the former redirects to the current National Portal services page.
- [ServicePlus service directory](https://serviceonline.gov.in/viewAllServiceList.html) and [service introduction](https://www.serviceonline.gov.in/login.do): certificate and state/local service terminology. Direct root retrieval timed out; indexed official results were consulted.
- [Parivahan](https://parivahan.gov.in/) and [official service overview](https://parivahan.gov.in/contactus): learner/driving licence and vehicle service families. Root retrieval failed; indexed overview and [MoRTH annual report](https://morth.gov.in/backend/documents/uploaded/1755600919_Annual-Report-English-with-Cover.pdf) supported DL/RC terminology.
- [Income Tax e-filing portal](https://www.incometax.gov.in/iec/foportal/): tax, PAN and filing terminology.
- [PM-KISAN](https://pmkisan.gov.in/) and [Know Your Status](https://www.pmkisan.gov.in/BeneficiaryStatus_New.aspx): farmer registration, beneficiary status and eKYC; indexed official content used where direct root extraction failed.
- [UIDAI](https://www.uidai.gov.in/) and [My Aadhaar](https://uidai.gov.in/en/my-aadhaar): enrolment, update, download, PVC and status service families.
- [ECI registration FAQ](https://www.eci.gov.in/faq/en/how-to-register) and [Voter forms](https://voters.eci.gov.in/home/forms): correction/shifting/replacement, overseas registration and deletion/objection. No old Form 8A instructions added.
- [EPFO member portal](https://unifiedportal-mem.epfindia.gov.in/) and [passbook/claim status](https://www.passbook.epfindia.gov.in/MemberPassBook/login): UAN/member terminology. Activation uses current EPFO channels; no obsolete activation instructions are embedded.
- [Maharashtra land records](https://mahabhumi.gov.in/eodbdashboard/): 7/12 and 8A named as Maharashtra-specific extracts.
- [e-Jagriti](https://e-jagriti.gov.in/): consumer commission filing uses the current platform name; e-Daakhil retained as a search alias.
- [UMANG](https://www.umang.gov.in/landing/) and [public LPG service overview](https://web.umang.gov.in/landing/department/ministry-of-petroleum-and-natural-gas.html): channel label and LPG family.
- [MNRE rooftop solar portal](https://www.solarrooftop.pmsuryaghar.gov.in/): PM Surya Ghar rooftop solar family.

Only the verified government directory is linked in the page footer, clearly marked “external government website” and isolated from cards. No individual official URL is invented.

### Groupings, additions and scope

- Municipal Trade Licence and Trade Licence share one record with Utilities and Business filter assignments and both seed aliases.
- Shop and Establishment Registration appears in seed G and M; one record is available in both filters.
- Passport fresh/reissue/correction remain inside the existing guided journey, without duplicate Coming Soon cards.
- Aadhaar Update and Correction includes demographic/biometric changes; the explicitly requested address-update task remains separately discoverable. Registration, certificate issuance and correction remain separate citizen tasks as requested. Property registration and sale deed registration likewise remain distinct general/document-specific tasks.
- Visa extension and FRRO/FRO remain distinct general/specialist entry points from the seed, with searchable shared terminology. No authority-specific workflow is implied.
- National Career Service, NSP, academic repositories, DigiLocker, UMANG, CSC and state portals are described as platforms/channels or directories; no Maadhyam API integration is implied.
- Seven additions: UMANG (platform); LPG Connection and Subsidy Services; PM Surya Ghar Rooftop Solar Assistance; Overseas Voter Registration; Electoral Roll Deletion / Objection; Aadhaar Enrolment / Update Status; EPF Claim Status.
- Local civil certificates, land/property, municipal utilities, RTO processes and state taxes are explicitly state-specific. Scheme/provider/institution-dependent records say “Availability varies”; central labels identify the service family, not a guarantee of universal eligibility. Maharashtra extracts explicitly name Maharashtra. Generic seed descriptions remain descriptive where no exact nationwide service exists. No seed concept was omitted.

## Interaction and preservation

Search normalizes case, punctuation and whitespace, and matches title, description, all category labels and keywords. Short aliases match words, avoiding incidental DL/RC substring matches. PM-KISAN and PM Kisan behave equivalently. Query links from Dashboard (`/services?q=...`) are preserved. Search and category filtering scan the complete in-memory registry; category changes and query edits reset to 12 cards. Load More adds 12, with accurate visible/matched/overall counts. Empty results retain Reset Filters. All 18 groups are selectable through a compact native select. No catalogue rendering/search/filter/pagination API request is made; the existing backend service endpoint is untouched.

The original PageHero, dark blue banner, typography, sidebar, floating assistant, card colors/radii/padding and 3/2/1-column responsive grid remain. Category-appropriate icons use the existing lucide dependency. Unsupported card content now includes a short scope/category line; Passport keeps its original description and content height; rows stretch consistently and unsupported footers have only their badge. Only Services.tsx and its new data module change application code. No route, detail page, Passport journey, readiness helper, backend application source/config, dependency or cloud schema changed. Two historical browser test scripts under the API tests directory gained hydration/upload-readiness waits; they change no backend implementation.

## Validation

The complete release gate was executed locally with isolated API/preview servers, mocked Firebase authentication, cloud providers disabled, and owned-server cleanup. The full gate rebuilt the final catalogue labels and included the all-256-card mobile overflow assertion. The final run includes the visual refinement retaining the original Passport description and omitting its extra category line to preserve its original card height. All 789 checks, including the 37 new catalogue cases and both corrected historical waits, passed together on this final source state.

| Check | Result |
|---|---:|
| Backend pytest | 463 passed |
| Browser/helper pytest | 263 passed (226 existing + 37 new catalogue cases) |
| HTTP contracts | 18 passed |
| Historical functional | 24 passed |
| Historical reasoning | 5 passed |
| Historical M9 browser | 5 passed |
| Historical Vault | 4 passed |
| Historical smoke | 7 passed |
| Total, without double counting targeted reruns | **789 passed** |
| ESLint `--max-warnings 0` | Passed; zero warnings/errors |
| TypeScript + Vite production build | Passed |
| `git diff --check` | Passed |

Command: `MAADHYAM_FINAL_QA_OUTPUT=qa/evidence/m12-1-catalogue Maadhyam/apps/api/.venv/bin/python qa/run_final.py` from repository root. Portable [execution receipt](evidence/m12-1-catalogue/execution.json), [backend XML](evidence/m12-1-catalogue/backend.xml), [browser XML](evidence/m12-1-catalogue/browser.xml), [HTTP XML](evidence/m12-1-catalogue/http.xml), lint/build logs and historical logs/JSON are committed alongside public UI comparisons. Portable lint/build logs normalize trailing whitespace only; test output and outcomes are retained. All suite exit codes are zero; the receipt records `serversOwnedAndStopped: true` and `liveProviders: false`.

The 37 new cases cover independent seed coverage, unique IDs/normalized titles, capability statuses, every title/description/keyword/category search, all 18 filters, requested synonyms, combination/empty/reset behavior, full-catalogue pagination, route-baseline preservation, card semantics, query links, keyboard access, 390/834/1440 layouts, existing style values, external-link labeling and absence of catalogue API calls. Existing full-suite cases continue to exercise Passport navigation/readiness, persistence, timestamps/ownership, What-If, discrepancy analysis, optimizer, rule changes, investigation findings, connected progress and the current capability contract.

Initial discovery found a category-selector accessible-name issue; an explicit Category label fixed it. A test initially included the existing asynchronous startup Vault request in its interaction window; it now waits for that response before measuring catalogue activity. An initial Passport assertion was corrected to use the existing action's actual accessible name. The final historical Vault run exposed a pre-existing hard-navigation hydration race: its first valid planner response could contain zero documents before IndexedDB restored the saved files. Its browser test now waits for the visible “2 uploaded · 2 reviewed self-held” assessment before retaining all original payload, printed-name, DOB, review-state and conflict assertions. The smoke upload case also now waits for the uploaded filename to render before its existing filename/review assertions; its immediate `count()` check had raced asynchronous file reading. No test was deleted or skipped, and no API response was stubbed to pass either case. Final review additionally clarified seven local/state scopes and extended mobile overflow verification to all cards; the complete gate was rerun afterwards.

Existing non-blocking advisories remain: Vite's bundle-size warning (final bundle about 741 kB minified / 206 kB gzip) and Starlette's test-client deprecation warning. No dependency changes were made. Live government workflows, paid Gemini accuracy and production acceptance are outside this catalogue release and were not claimed.

## Screenshot comparison

Reviewed pre-expansion screenshots from the prior M12.1 run against the catalogue acceptance screenshots. The banner/background, typography, sidebar, assistant, white rounded cards, teal Passport action and grid styling remain consistent. Added controls and scope text move the grid down; a larger catalogue intentionally adds rows through Load More. No horizontal overflow at 390, 834 or 1440 pixels. Automated style checks verify white card background, 16px radius, 28px padding, dark blue banner and 1/2/3 grid columns.

- Desktop: [before](evidence/m12-1-catalogue/comparison/services-before-1440.png), [after](evidence/m12-1-catalogue/comparison/services-after-1440.png).
- Mobile: [before](evidence/m12-1-catalogue/comparison/services-before-390.png), [after](evidence/m12-1-catalogue/comparison/services-after-390.png).
- [Tablet after](evidence/m12-1-catalogue/comparison/services-after-834.png).
- [Full desktop catalogue page](evidence/m12-1-catalogue/comparison/services-after-desktop-full.png), showing the initial 12 tiles and Passport action.

These intentionally committed comparisons show public catalogue content only. Detailed per-test screenshots/network diagnostics remain local under `qa/evidence/m12-1-catalogue/screenshots/`.

## Changed files

- `Maadhyam/apps/web/src/pages/Services.tsx`: catalogue rendering, local discovery controls and truthful status.
- `Maadhyam/apps/web/src/data/governmentServices.ts`: typed registry, official category mapping, aliases and search helper.
- `qa/test_service_catalogue.py`: registry and Chromium acceptance checks.
- `Maadhyam/apps/api/tests/run_vault_e2e.py`: historical browser-test hydration wait.
- `Maadhyam/apps/api/tests/run_frontend_tests.py`: historical browser-test asynchronous upload wait. Backend application source and configuration untouched.
- `qa/fixtures/service_catalogue_seed.json`: independent literal seed inventory from this request, including repeated references.
- `qa/fixtures/service_catalogue_routes.json`: pre-change route paths used to detect additions/removals.
- This report; `qa/M12_1_MANUAL_CLOUD_DEPLOYMENT_HANDOFF.md`; `.gitignore` and portable QA receipts.

## Git and deployment

The reviewed catalogue, tests, portable receipts and report are delivered on `origin/release/m10-m12-recovery` with a normal fast-forward push. The immutable release identity is the commit containing this report and the registry; resolve it with `git log -1 --format=%H -- qa/M12_1_SERVICE_CATALOGUE_EXPANSION_REPORT.md`. The exact SHA and post-push remote/local equality are recorded in the final delivery message (a commit cannot embed its own SHA).

Verification: compare `git rev-parse HEAD` with `git ls-remote origin refs/heads/release/m10-m12-recovery`. The target remote was verified at baseline `986984198366c8ffab222eb160558217f7d016d5` before committing; no force push or main-branch merge is used. Final intended-source review includes `git diff --check`, a credential-pattern scan of added sources, all 256 report inventory records against the registry, and unchanged backend/routes/configuration/dependency paths.

**No Google Cloud, Cloud Build, Cloud Run or Firebase deployment was executed.** Backend application source/config is unchanged since `9869841`; only historical browser test timing was corrected. The owner still needs to build/deploy the consolidated M12.1 backend and build Firebase Hosting from the latest combined release commit. The catalogue adds no infrastructure, backend endpoint, Firestore schema, Storage operation or cloud configuration. Unrelated `.DS_Store` and `Maadhyam_M12_source.zip` were preserved and excluded.

## All 256 service names


### Citizenship & Identity

- Passport Seva — Guided preview; central
- Aadhaar Services — Coming Soon; central
- Aadhaar Enrolment — Coming Soon; central
- Aadhaar Update and Correction — Coming Soon; central
- Aadhaar Download / e-Aadhaar — Coming Soon; central
- Aadhaar PVC Card — Coming Soon; central
- Aadhaar Address Update — Coming Soon; central
- Overseas Citizen of India (OCI) Services — Coming Soon; central
- Indian Citizenship Application / Registration — Coming Soon; central
- Visa Extension and Registration Services — Coming Soon; central
- FRRO / FRO Services — Coming Soon; central
- Aadhaar Enrolment / Update Status — Coming Soon; central

### Certificates & Family

- Birth Registration — Coming Soon; state-specific
- Birth Certificate — Coming Soon; state-specific
- Birth Certificate Correction — Coming Soon; state-specific
- Death Registration — Coming Soon; state-specific
- Death Certificate — Coming Soon; state-specific
- Marriage Registration — Coming Soon; state-specific
- Marriage Certificate — Coming Soon; state-specific
- Caste Certificate — Coming Soon; state-specific
- Income Certificate — Coming Soon; state-specific
- Domicile / Residence Certificate — Coming Soon; state-specific
- Economically Weaker Section (EWS) Certificate — Coming Soon; state-specific
- Non-Creamy Layer Certificate — Coming Soon; state-specific
- Legal Heir / Surviving Family Member Certificate — Coming Soon; state-specific
- Name Change / Gazette Publication — Coming Soon; state-specific
- Ration Card Application — Coming Soon; state-specific
- Ration Card Correction — Coming Soon; state-specific
- Ration Card Member Addition / Removal — Coming Soon; state-specific
- Ration Card Portability / One Nation One Ration Card — Coming Soon; state-specific
- Ration Card Status — Coming Soon; state-specific
- Food Subsidy Grievance — Coming Soon; state-specific
- Anganwadi Services — Coming Soon; state-specific
- Maternity Benefit Scheme Application — Coming Soon; state-specific
- Child Welfare Scheme Assistance — Coming Soon; state-specific
- Women Welfare Scheme Assistance — Coming Soon; state-specific
- Senior Citizen Welfare Scheme Assistance — Coming Soon; state-specific
- Social Assistance Scheme Application — Coming Soon; state-specific

### Transport & RTO

- Learner's Driving Licence — Coming Soon; state-specific
- Permanent Driving Licence — Coming Soon; state-specific
- Driving Licence Renewal — Coming Soon; state-specific
- Duplicate Driving Licence — Coming Soon; state-specific
- Driving Licence Address Change — Coming Soon; state-specific
- International Driving Permit — Coming Soon; state-specific
- Vehicle Registration Certificate (RC) — Coming Soon; state-specific
- Transfer of Vehicle Ownership — Coming Soon; state-specific
- Duplicate Vehicle RC — Coming Soon; state-specific
- Vehicle Fitness Certificate — Coming Soon; state-specific
- Vehicle Permit Services — Coming Soon; state-specific
- Vehicle Road Tax — Coming Soon; state-specific
- Vehicle Registration Address Change — Coming Soon; state-specific
- Vehicle Hypothecation Addition/Termination — Coming Soon; state-specific
- Vehicle NOC — Coming Soon; state-specific
- Fancy Registration Number — Coming Soon; state-specific
- Traffic Challan Services — Coming Soon; state-specific
- Vehicle Registration Status — Coming Soon; state-specific

### Taxes & Finance

- PAN Card Application — Coming Soon; central
- PAN Card Correction — Coming Soon; central
- PAN–Aadhaar Linking — Coming Soon; central
- Income Tax Return Filing — Coming Soon; central
- Income Tax e-Verification — Coming Soon; central
- Income Tax Refund Status — Coming Soon; central
- Income Tax Rectification Request — Coming Soon; central
- Income Tax Refund Reissue — Coming Soon; central
- Form 26AS / Tax Credit Statement — Coming Soon; central
- Annual Information Statement (AIS) — Coming Soon; central
- Income Tax Demand Response — Coming Soon; central
- Advance Tax / Self-Assessment Tax Payment — Coming Soon; central
- PAN Verification — Coming Soon; central
- TAN Application and Correction — Coming Soon; central
- GST Registration — Coming Soon; central
- GST Return Filing — Coming Soon; central
- GST Payment — Coming Soon; central
- GST Registration Amendment — Coming Soon; central
- GST Refund Services — Coming Soon; central
- GST Registration Cancellation — Coming Soon; central
- Professional Tax Registration / Payment — Coming Soon; state-specific
- Property Tax Payment — Coming Soon; state-specific

### Land & Housing

- Land Record / Record of Rights Extract — Coming Soon; state-specific
- 7/12 Extract (Maharashtra) — Coming Soon; state-specific
- 8A Extract (Maharashtra) — Coming Soon; state-specific
- Property Registration — Coming Soon; state-specific
- Sale Deed Registration — Coming Soon; state-specific
- Encumbrance Certificate — Coming Soon; state-specific
- Property Mutation — Coming Soon; state-specific
- Land Survey Records — Coming Soon; state-specific
- Land Measurement / Demarcation — Coming Soon; state-specific
- Property Ownership Records — Coming Soon; state-specific
- Building Plan Approval — Coming Soon; state-specific
- Construction Permit — Coming Soon; state-specific
- Occupancy Certificate — Coming Soon; state-specific
- Housing Scheme Application — Coming Soon; state-specific
- PMAY Housing Assistance — Coming Soon; state-specific
- Property Tax Assessment — Coming Soon; state-specific

### Utilities & Infrastructure

- New Electricity Connection — Coming Soon; state-specific
- Electricity Bill Payment — Coming Soon; state-specific
- Electricity Meter Name Change — Coming Soon; state-specific
- Electricity Billing Complaint — Coming Soon; state-specific
- New Water Connection — Coming Soon; state-specific
- Water Bill Payment — Coming Soon; state-specific
- Sewerage Connection — Coming Soon; state-specific
- Municipal Trade Licence — Coming Soon; state-specific
- Shop and Establishment Registration — Coming Soon; state-specific
- Waste Collection Complaint — Coming Soon; state-specific
- Streetlight Complaint — Coming Soon; state-specific
- Municipal Grievance Services — Coming Soon; state-specific
- Fire Safety NOC — Coming Soon; state-specific
- Public Utility Connection Transfer — Coming Soon; state-specific
- LPG Connection and Subsidy Services — Coming Soon; varies
- PM Surya Ghar Rooftop Solar Assistance — Coming Soon; varies

### Health & Wellness

- Ayushman Bharat PM-JAY Eligibility/Card Services — Coming Soon; varies
- ABHA Health Account — Coming Soon; central
- Government Hospital Appointment — Coming Soon; varies
- eSanjeevani Telemedicine — Coming Soon; central
- Immunisation Record Services — Coming Soon; varies
- Disability Certificate / UDID — Coming Soon; varies
- Medical Board Certificate — Coming Soon; varies
- Organ Donation Registration — Coming Soon; varies
- Health Facility Registration — Coming Soon; varies
- Health Scheme Beneficiary Services — Coming Soon; varies
- Government Health Insurance Assistance — Coming Soon; varies

### Employment & Labour

- Employment Exchange Registration — Coming Soon; state-specific
- Employment Exchange Renewal — Coming Soon; state-specific
- National Career Service Registration — Coming Soon; central
- e-Shram Registration — Coming Soon; central
- e-Shram Profile Update — Coming Soon; central
- Labour Welfare Scheme Application — Coming Soon; state-specific
- Construction Worker Registration — Coming Soon; state-specific
- Building and Other Construction Workers Benefits — Coming Soon; state-specific
- Apprenticeship Registration — Coming Soon; varies
- Skill Development Programme Registration — Coming Soon; varies
- Government Job Application Services — Coming Soon; varies
- Employment Certificate Services — Coming Soon; state-specific
- Worker Grievance Services — Coming Soon; varies

### Pensions & Welfare

- EPFO Services — Coming Soon; central
- UAN Activation (EPFO) — Coming Soon; central
- EPF Passbook — Coming Soon; central
- EPF Withdrawal / Online Claim — Coming Soon; central
- EPF Transfer — Coming Soon; central
- EPF KYC Update — Coming Soon; central
- EPF Nomination — Coming Soon; central
- EPS Pension Services — Coming Soon; central
- ESIC Insured Person Services — Coming Soon; central
- ESIC Sickness Benefit Services — Coming Soon; central
- ESIC Medical Benefit Services — Coming Soon; central
- ESIC Claim and Benefit Guidance — Coming Soon; central
- Jeevan Pramaan / Digital Life Certificate — Coming Soon; central
- Atal Pension Yojana Services — Coming Soon; central
- National Pension System Services — Coming Soon; central
- Old Age Pension Application — Coming Soon; state-specific
- Widow Pension Application — Coming Soon; state-specific
- Disability Pension Application — Coming Soon; state-specific
- Government Pension Grievances — Coming Soon; varies
- Government Employee Pension Assistance — Coming Soon; varies
- EPF Claim Status — Coming Soon; central

### Education & Scholarships

- National Scholarship Portal (platform) — Coming Soon; varies
- State Scholarship Applications — Coming Soon; state-specific
- Scholarship Renewal — Coming Soon; varies
- School Admission Services — Coming Soon; varies
- Higher Education Admission Services — Coming Soon; varies
- Student Certificate Verification — Coming Soon; varies
- Academic Transcript Requests — Coming Soon; varies
- Migration Certificate — Coming Soon; varies
- Transfer Certificate — Coming Soon; varies
- Examination Result Services — Coming Soon; varies
- Apprenticeship Opportunities — Coming Soon; varies
- Student Loan Assistance — Coming Soon; varies
- Skill Certification Services — Coming Soon; varies
- National Academic Depository / Academic Records (platform) — Coming Soon; varies

### Agriculture & Rural Services

- PM-KISAN Farmer Registration — Coming Soon; central
- PM-KISAN Beneficiary Status — Coming Soon; central
- PM-KISAN eKYC — Coming Soon; central
- Farmer Registration / Farmer ID Services — Coming Soon; state-specific
- Soil Health Card — Coming Soon; varies
- Crop Insurance / PMFBY — Coming Soon; varies
- Agriculture Subsidy Application — Coming Soon; varies
- Agricultural Equipment Subsidy — Coming Soon; varies
- Irrigation Assistance — Coming Soon; varies
- Agricultural Market Information Services — Coming Soon; varies
- Farmer Producer Organisation Services — Coming Soon; varies
- Rural Employment Guarantee / MGNREGA Services — Coming Soon; varies
- Rural Housing Assistance — Coming Soon; varies
- Fisheries and Livestock Scheme Assistance — Coming Soon; varies
- Environmental Clearance Services — Coming Soon; varies

### Business & Self-employment

- Udyam MSME Registration — Coming Soon; central
- MSME Certificate / Registration Update — Coming Soon; central
- Startup India Recognition — Coming Soon; central
- Company Incorporation — Coming Soon; central
- LLP Incorporation — Coming Soon; central
- Director Identification Number Services — Coming Soon; central
- MCA Annual Filing — Coming Soon; central
- FSSAI Food Business Registration / Licence — Coming Soon; central
- Importer Exporter Code — Coming Soon; central
- Business Tax Registration — Coming Soon; varies
- Factory Licence — Coming Soon; state-specific
- Labour Establishment Registration — Coming Soon; state-specific
- Business Compliance Filing — Coming Soon; varies
- Government e-Marketplace Seller Registration — Coming Soon; central
- Trademark Registration — Coming Soon; central
- Patent Filing Services — Coming Soon; central

### Legal & Grievances

- Character Certificate — Coming Soon; state-specific
- Police Clearance Certificate — Coming Soon; state-specific
- CPGRAMS Public Grievance Submission — Coming Soon; central
- RTI Application — Coming Soon; varies
- RTI First Appeal — Coming Soon; varies
- Police Complaint Services — Coming Soon; state-specific
- Cybercrime Complaint — Coming Soon; central
- Lost Document Report — Coming Soon; state-specific
- eCourts Case Status — Coming Soon; central
- Court Order and Judgment Search — Coming Soon; central
- Legal Aid Application — Coming Soon; varies
- Consumer Grievance / Consumer Helpline — Coming Soon; central
- Consumer Commission Filing / e-Jagriti — Coming Soon; central
- Lok Adalat Information / Services — Coming Soon; varies
- Police Verification Services — Coming Soon; state-specific
- Citizen Service Request Status — Coming Soon; varies
- Event / Public Gathering Permission — Coming Soon; state-specific
- Government Department Grievance Redressal — Coming Soon; varies

### Travel & Tourism

- Tourism Registration / Permit Services — Coming Soon; varies
- Tourist Guide Registration — Coming Soon; varies
- Pilgrimage Registration — Coming Soon; varies
- Hotel / Tourism Establishment Registration — Coming Soon; varies

### Sports & Culture

- Heritage Site Permission Services — Coming Soon; varies
- Sports Scholarship Services — Coming Soon; varies
- Sports Facility Registration — Coming Soon; varies
- Cultural Grant Applications — Coming Soon; varies

### Digital & Communications

- DigiLocker Document Services (platform) — Coming Soon; varies
- Digital Signature Certificate Services — Coming Soon; varies
- Telecommunications Complaint Services — Coming Soon; varies
- Telecom Consumer Grievance Services — Coming Soon; varies
- Digital Service Centre / CSC Services (channel) — Coming Soon; varies
- Government Digital Certificate Verification — Coming Soon; varies
- Broadband / Digital Connectivity Scheme Assistance — Coming Soon; varies
- UMANG (platform) — Coming Soon; varies

### Defence & Overseas Welfare

- Emigration Clearance Services — Coming Soon; central
- Overseas Indian Consular Services — Coming Soon; central
- Attestation / Apostille Services — Coming Soon; central
- Ex-Servicemen Welfare Services — Coming Soon; varies
- Defence Pension Services — Coming Soon; varies
- CSD Entitlement / Canteen Services — Coming Soon; varies
- Ex-Servicemen Identity / Benefit Services — Coming Soon; varies

### Governance & Citizen Services

- New Voter Registration — Coming Soon; central
- Voter Details Correction — Coming Soon; central
- Voter Address Shifting — Coming Soon; central
- Voter ID / EPIC Replacement — Coming Soon; central
- e-EPIC Download — Coming Soon; central
- Electoral Roll Search — Coming Soon; central
- Voter Registration Status — Coming Soon; central
- Government Employee Service Certificate — Coming Soon; varies
- Public Information and Citizen Charter Services — Coming Soon; varies
- State Government Citizen Service Portals (platforms) — Coming Soon; state-specific
- Disaster Relief Assistance — Coming Soon; varies
- Disaster Damage Compensation Scheme — Coming Soon; varies
- Government Scheme Eligibility Information — Coming Soon; varies
- Overseas Voter Registration — Coming Soon; central
- Electoral Roll Deletion / Objection — Coming Soon; central
