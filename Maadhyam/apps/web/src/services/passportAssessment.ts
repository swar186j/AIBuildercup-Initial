import { apiFetch } from './apiFetch';
import type { LocalDocument } from '../context/DocumentContext';
import { validatePassportAssessment } from './responseValidation';
import { documentPayload } from './citizenIntelligence';

export type PassportCheck = {
  id: string; title: string;
  status: 'available-for-review' | 'needs-attention' | 'needs-confirmation';
  reason: string; next_action: string; matching_document_ids: string[];
  alternatives: string[]; source_url: string; source_id: string;
};
export type PassportAssessment = {
  ruleset_version: string; official_requirements_verified: boolean;
  source_health: string; checks: PassportCheck[]; disclaimer: string;
};
export async function assessPassport(answers: Record<string, unknown>, documents: LocalDocument[], applicantDateOfBirth: string, signal?: AbortSignal): Promise<PassportAssessment> {
  const response = await apiFetch('/api/passport/assess', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ ...answers, applicantDateOfBirth, documents: documentPayload(documents) }),
  });
  if (!response.ok) throw new Error(`Passport assessment unavailable (${response.status}).`);
  const data:unknown=await response.json();
  validatePassportAssessment(data);
  return data as PassportAssessment;
}
