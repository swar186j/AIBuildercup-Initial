import type { LocalDocument } from '../context/DocumentContext';
import { getDocumentCategories } from '../context/DocumentContext';

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
const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export async function assessPassport(answers: Record<string, unknown>, documents: LocalDocument[], applicantDateOfBirth: string, signal?: AbortSignal): Promise<PassportAssessment> {
  const response = await fetch(`${API}/api/passport/assess`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ ...answers, applicantDateOfBirth, documents: documents.map(d => ({
      id: d.id, categories: getDocumentCategories(d.metadata), holder: d.metadata.holder,
      reviewed: d.status === 'reviewed', documentType: d.metadata.documentType,
      printedName: d.metadata.printedName || '', dateOfBirth: d.metadata.dateOfBirth || '',
      residentialAddress: d.metadata.residentialAddress || '',
    })) }),
  });
  if (!response.ok) throw new Error(`Passport assessment unavailable (${response.status}).`);
  return response.json() as Promise<PassportAssessment>;
}
