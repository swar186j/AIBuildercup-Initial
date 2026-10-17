/** Grounded product guidance; no citizen metadata or provider call is needed. */
export const assistantGuidance = {
  dashboard: {
    path: '/', destination: '/services', label: 'Explore services',
    prompts: ['What can Maadhyam help me prepare?', 'How do I get started?', 'Explore government services'],
    answer: 'Maadhyam helps you organize documents, review metadata and possible differences, and prepare a Passport checklist. Start in Document Vault with fictional sample documents, review their details, then explore Services. Passport is the available guided preview; other guided journeys are Coming Soon. Maadhyam does not submit government applications or decide eligibility.',
  },
  services: {
    path: '/services', destination: '/services', label: 'Explore services',
    prompts: ['Which services can I explore?', 'Which guided preparation journeys are available?', 'Help me find an Aadhaar-related service'],
    answer: 'Open Services to browse service families and expand their related actions. Search Aadhaar or PVC to find the Aadhaar family. Aadhaar and EPFO guided preparation are Coming Soon; listings provide discovery information. Passport Seva is the only guided preview. Use the official reference portal for government services; Maadhyam does not submit applications.',
  },
  household: {
    path: '/household', destination: '/household', label: 'Open Household Intelligence',
    prompts: ['How do I add a household member?', 'How do I assign document ownership?', 'How is household information saved?'],
    answer: 'In Household Intelligence, add a member label and relationship. Review documents in Document Vault, then use Confirm evidence ownership in Household Intelligence to select the document and member and confirm association permission. Household labels start in this browser session. Use Save household to cloud and explicitly consent to sign-in and cloud saving to retain the household workspace. Wait for the save acknowledgement. Relationships and document acceptance are not legally verified.',
  },
  workflows: {
    path: '/workflows', destination: '/workflows', label: 'Open Citizen Workflow Assistant',
    prompts: ['Help me choose a workflow', 'How can I prepare for an official helpdesk visit?', 'How do I identify the next action?'],
    answer: 'Open Citizen Workflow Assistant and choose the workflow that matches your preparation goal. Review the displayed tasks and evidence gaps, then identify the first unfinished action whose prerequisites are complete. For an official helpdesk visit, prepare your questions, review document differences and confirm requirements with the responsible authority. Workflow guidance does not submit an application or confirm official acceptance.',
  },
  documents: {
    path: '/documents', destination: '/documents', label: 'Open Document Vault',
    prompts: ['How do I upload and review a document?', 'What does reviewed metadata mean?', 'How does private cloud storage work?'],
    answer: 'In Document Vault, upload a fictional sample file, open its review form, check the entered or extracted fields, assign its owner and mark it reviewed. Reviewed metadata means you checked those fields; it is not official verification. Private cloud storage requires sign-in and explicit cloud consent. Confirm the cloud upload acknowledgement before relying on it. Session and local metadata saving are distinct from cloud file storage. Gemini is optional and restricted to explicitly confirmed fictional demo metadata.',
  },
  applications: {
    path: '/applications', destination: '/applications', label: 'Open My Preparations',
    prompts: ['How do I resume a saved preparation?', 'What does preparation completed mean?', 'How does saving work?'],
    answer: 'Open My Preparations and select a saved Passport preparation to resume it. Preparation completed describes Maadhyam preparation tasks, not a government approval or live application status. Session records last in the current session; optional local saving keeps preparation data in this browser. Cloud saving requires sign-in and consent. Check the saved timestamp and acknowledgement, and restore the intended record before continuing.',
  },
  planner: {
    path: '/planner', destination: '/planner', label: 'Open Resolution Planner',
    prompts: ['Help me understand my preparation checklist', 'How do I review document differences?', 'What should I do before the next step?'],
    answer: 'In Resolution Planner, review the checklist and complete prerequisites before dependent tasks. Review document differences in the Vault first: compare reviewed fields for the same person and correct or clarify your sample metadata. Revisit the checklist after changes, and confirm requirements with the official authority before your next step. Hypothetical scenarios and readiness scores are preparation guidance, not eligibility or document acceptance decisions.',
  },
  passport: {
    path: '/services/passport', destination: '/services/passport', label: 'Explore Passport Seva',
    prompts: ['Help me prepare for a passport application', 'What documents should I review?', 'How is readiness calculated?'],
    answer: 'Open Passport Seva and choose the existing guided preparation preview for a new passport, reissue or correction. Start by uploading fictional sample documents in Document Vault, review their metadata and ownership, then select your scenario in the Passport journey. Review its document checklist, evidence gaps and differences before saving your preparation. Readiness reflects reviewed evidence and preparation tasks; missing evidence needs review. It does not establish official eligibility or acceptance. Check current requirements and submit only through the official Passport portal.',
  },
} as const;
export function getAssistantPage(path: string): keyof typeof assistantGuidance {
  if (path.startsWith('/services/passport')) return 'passport';
  return (Object.keys(assistantGuidance) as (keyof typeof assistantGuidance)[]).find(key=>key!=='dashboard' && path.startsWith(assistantGuidance[key].path)) ?? 'dashboard';
}
export function getProductGuidance(question: string) {
  const normalized = question.toLowerCase().replace(/[?!.]/g, '').trim();
  const item = Object.values(assistantGuidance).find(entry=>entry.prompts.some(prompt=>prompt.toLowerCase().replace(/[?!.]/g, '').trim()===normalized)) ??
    (/passport/.test(normalized) && /help|prepar|start/.test(normalized) ? assistantGuidance.passport : undefined);
  return item ? {answer:item.answer, mode:'local-product-guidance', sourceUrl:'', link:{path:item.destination,label:item.label}} : undefined;
}
