import type { LocalDocument } from '../context/DocumentContext';
import { validatePassportAssessment } from './responseValidation';
import { documentPayload } from './citizenIntelligence';

export type PassportCheck = {
  id: string; title: string;
  status: 'available-for-review' | 'needs-attention' | 'needs-confirmation';
  reason: string; next_action: string; matching_document_ids: string[];
  alternatives: string[]; source_url: string; source_id: string;
};
export type PreparationReadiness={percentage:number;completed_checks:number;total_checks:number;formula:string;official_acceptance_verified:false;items:{id:string;title:string;state:'complete'|'missing'|'needs-review'|'difference'|'official-check';reason:string;next_action:string;document_ids:string[]}[]};
export type PassportAssessment = {
  readiness?:PreparationReadiness;
  ruleset_version: string; official_requirements_verified: boolean;
  source_health: string; checks: PassportCheck[]; disclaimer: string;
};
const API = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export async function assessPassport(answers: Record<string, unknown>, documents: LocalDocument[], applicantDateOfBirth: string, signal?: AbortSignal, applicantName = '', applicantHouseholdMemberId?:string): Promise<PassportAssessment> {
  const response = await fetch(`${API}/api/passport/assess`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ ...answers, applicantName, applicantHouseholdMemberId, applicantDateOfBirth, documents: documentPayload(documents) }),
  });
  if (!response.ok) throw new Error(`Passport assessment unavailable (${response.status}).`);
  const data:unknown=await response.json();
  validatePassportAssessment(data);
  const assessment=data as PassportAssessment;
  if(assessment.readiness!==undefined&&assessment.readiness!==null){
    const r=assessment.readiness;
    if(!Number.isInteger(r.percentage)||r.percentage<0||r.percentage>100||!Number.isInteger(r.completed_checks)||!Number.isInteger(r.total_checks)||r.total_checks<1||r.completed_checks<0||r.completed_checks>r.total_checks||r.percentage!==Math.round(100*r.completed_checks/r.total_checks)||typeof r.formula!=='string'||r.official_acceptance_verified!==false||!Array.isArray(r.items)||r.items.length!==r.total_checks||!r.items.every(i=>i&&typeof i.id==='string'&&typeof i.title==='string'&&['complete','missing','needs-review','difference','official-check'].includes(i.state)&&typeof i.reason==='string'&&typeof i.next_action==='string'&&Array.isArray(i.document_ids)&&i.document_ids.every(id=>typeof id==='string'))||r.items.filter(i=>i.state==='complete').length!==r.completed_checks)throw new Error('Unexpected preparation readiness response.');
  }
  return assessment;
}
