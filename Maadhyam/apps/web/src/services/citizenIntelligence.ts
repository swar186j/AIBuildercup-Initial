import { getProductGuidance } from "../data/assistantGuidance";
import { getFirebaseToken } from "./firebaseClient";
import { validateChat, validatePassportPlan, validateReasoning } from './responseValidation';
import type { LocalDocument } from '../context/DocumentContext';

export type IntelligenceTask = { id: string; title: string; reason: string; dependsOn: string[]; priority: number; status: string };
export type IntelligenceFinding = { id: string; field: string; message: string; severity: string; evidence: { value: string; documentIds: string[] }[] };
export type IntelligenceAssessment = {
  mode: string; sourceUrl: string; documentCount: number; reviewedSelfDocuments: number;
  findings: IntelligenceFinding[]; tasks: IntelligenceTask[]; minimumReviewSet: string[];
  readyForOfficialSubmission: boolean; readinessNote: string;
  familyHolders: string[]; whatIf: { allConflictsResolved: { remainingReviewTasks: number } };
};
export function documentPayload(documents: LocalDocument[]) {
  return documents.map(d => ({
    id: d.id, documentType: d.metadata.documentType || '', holder: d.metadata.householdMemberId && d.metadata.householdMemberId !== 'applicant' && d.metadata.holder === 'self' ? 'other' : d.metadata.holder,
    householdMemberId: d.metadata.householdMemberId, associationConsent: d.metadata.associationConsent===true,
    reviewed: d.status === 'reviewed', extractionSource:d.metadata.extractionSource??'manual',
    categories: d.metadata.categories?.length ? d.metadata.categories : [d.metadata.category],
    printedName: d.metadata.printedName || '', dateOfBirth: d.metadata.dateOfBirth || '',
    residentialAddress: d.metadata.residentialAddress || '', expiryDate: d.metadata.expiryDate || '',
  }));
}
async function post<T>(url: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = {'Content-Type':'application/json'};
  if (url.endsWith('/chat') && (body as {useGemini?: boolean}).useGemini) {
    headers.Authorization = `Bearer ${await getFirebaseToken()}`;
  }
  const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body), signal: AbortSignal.timeout(40000) });
  if (!response.ok) throw new Error(`Intelligence service returned ${response.status}`);
  const result: unknown = await response.json();
  if (url.endsWith('/passport-plan')) validatePassportPlan(result);
  if (url.endsWith('/reasoning')) validateReasoning(result);
  if (url.endsWith('/chat')) validateChat(result);
  return result as T;
}
export function analyzeCitizen(documents: LocalDocument[], assistanceType = 'fresh') {
  return post<IntelligenceAssessment>('/api/intelligence/analyze', {documents:documentPayload(documents), assistanceType});
}
export function askCitizen(documents: LocalDocument[], question: string, useGemini = false, fictionalDataConfirmed = false) {
  const guidance = !useGemini ? getProductGuidance(question) : undefined;
  if (guidance) return Promise.resolve(guidance);
  return post<{answer:string;mode:string;sourceUrl:string;link?:{path:string;label:string}}>('/api/intelligence/chat', {
    documents:documentPayload(documents),question,useGemini,fictionalDataConfirmed,
  });
}

export type PassportChecklistItem = {
  id: string; label: string; status: string; candidateDocumentIds: string[];
  officialAcceptanceVerified: boolean; note: string;
};
export type PassportResolutionOption = {
  findingId: string; field: string; strategy: string;
  alternatives: {id: string; label: string; automaticallyApproved: boolean}[];
  chosenCorrection: null; reason: string;
};
export type PassportPlan = {
  scenario: string; scenarioTitle: string; checklist: PassportChecklistItem[];
  resolutionOptions: PassportResolutionOption[]; preparationBlockers: string[];
  orderedTaskIds: string[]; nextAction: string | null;
  officialEligibilityDetermined: boolean; officialAcceptanceDetermined: boolean;
  sourceUrl: string; disclaimer: string;
};
export type PassportPlanResponse = {assessment: IntelligenceAssessment; passportPlan: PassportPlan};
export function preparePassport(
  documents: LocalDocument[], assistanceType = 'fresh', applicantAgeGroup = '', scopedPayload?: ReturnType<typeof documentPayload>,
): Promise<PassportPlanResponse> {
  return post<PassportPlanResponse>('/api/intelligence/passport-plan', {
    documents: scopedPayload??documentPayload(documents), assistanceType, applicantAgeGroup,
  });
}

// M7/M8: deterministic hypothetical scenarios and unverified family evidence claims.
export type FamilyEvidenceLink = {
  documentId: string; relation: 'parent' | 'guardian' | 'spouse' | 'child' | 'sibling' | 'other';
  claimedByApplicant: boolean; relationshipEvidenceDocumentIds: string[];
};
export type ReasoningSimulation = {
  id: string; label: string; removeDocumentIds?: string[]; markReviewedIds?: string[];
  replaceFields?: Record<string, Partial<Record<'printedName' | 'dateOfBirth' | 'residentialAddress', string>>>;
};
export type ReasoningResponse = {
  mode: string;
  baseline: { reviewFindings: string[]; blockers: string[]; assessment: IntelligenceAssessment };
  dependencyGraph: { nodes: {id:string;title:string;priority:number}[]; edges: {before:string;after:string}[]; executionOrder:string[]; cyclesDetected:boolean; optimizationScope:string };
  familyEvidence: { links: {documentId:string;relation:string;holder:string;relationshipEvidenceIds:string[];reviewedRelationshipEvidenceIds:string[];requiresVerification:boolean;officialRelationshipVerified:boolean;warning:string}[];unlinkedFamilyDocumentIds:string[];officialRelationshipVerified:boolean;note:string };
  simulations: {id:string;label:string;before:{reviewFindings:string[];blockers:string[]};after:{reviewFindings:string[];blockers:string[]};resolvedFindingIds:string[];newFindingIds:string[];remainingTaskIds:string[];officialAcceptanceVerified:boolean;caution:string}[];
  officialEligibilityDetermined:boolean;disclaimer:string;
};
export function reasonCitizen(documents: LocalDocument[], familyLinks: FamilyEvidenceLink[], simulations: ReasoningSimulation[], assistanceType = 'fresh', applicantAgeGroup = ''): Promise<ReasoningResponse> {
  return post<ReasoningResponse>('/api/intelligence/reasoning', {
    documents: documentPayload(documents), familyLinks, simulations, assistanceType, applicantAgeGroup,
  });
}
