/**
 * Cloud persistence boundary for user-confirmed Passport preparations.
 * Document bytes, household member details, and raw extracted images are NOT sent.
 */
import { newJourney, readJourney, type JourneyData } from '../context/preparationStorage';
import type { PassportAssistanceType } from '../data/journeyData';
import type { CloudApplication, CreateCloudApplication } from './cloudApplications';

const passportTypes: PassportAssistanceType[] = [
  'fresh', 'reissue', 'correction', 'documents', 'police',
];

export function preparationToCloud(id: string, journey: JourneyData): CreateCloudApplication {
  return {
    client_id: id,
    service_type: 'passport',
    application_type: journey.assistanceType,
    status: journey.stepIndex === 3 ? 'completed' : journey.stepIndex === 0 ? 'draft' : 'in-progress',
    applicant_details: {
      name: journey.applicantName,
      date_of_birth: journey.applicantDob,
      ...(journey.applicantHouseholdMemberId ? {household_member_id:journey.applicantHouseholdMemberId} : {}),
    },
    questionnaire_answers: { ...journey.answers },
    current_step: journey.stepIndex,
    selected_document_ids: [...journey.documentIds],
    rule_pack_version: 'unverified',
  };
}

/** Ignore malformed/foreign cloud records instead of corrupting local preparations. */
export function cloudToPreparation(record: CloudApplication): JourneyData | null {
  if (record.service_type !== 'passport' || !passportTypes.includes(record.application_type as PassportAssistanceType)) {
    return null;
  }
  if (!/^LOCAL-[A-Za-z0-9-]{8,100}$/.test(record.id)) return null;
  const type = record.application_type as PassportAssistanceType;
  const details = record.applicant_details;
  const answers = record.questionnaire_answers;
  if (!details || typeof details !== 'object' || !answers || typeof answers !== 'object') return null;

  return readJourney({
    ...newJourney(type),
    assistanceType: type,
    createdAt:record.created_at,
    lastSavedAt:record.lastSavedAt??record.updated_at,
    applicantName: details.name,
    applicantHouseholdMemberId: details.household_member_id,
    applicantDob: details.date_of_birth,
    answers: { ...answers, assistanceType: type },
    stepIndex: record.current_step,
    documentIds: record.selected_document_ids,
  });
}

function sameValue(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right)) {
    return Array.isArray(left) && Array.isArray(right) &&
      left.length === right.length && left.every((v,i) => sameValue(v,right[i]));
  }
  if (left !== null && right !== null && typeof left === 'object' && typeof right === 'object') {
    const a = left as Record<string,unknown>;
    const b = right as Record<string,unknown>;
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length &&
      keys.every(k => Object.prototype.hasOwnProperty.call(b,k) && sameValue(a[k],b[k]));
  }
  return false;
}

/** Compare only persisted applicant fields; do not silently overwrite another session's edits. */
export function sameCloudPreparation(
  record: CloudApplication,
  expected: CreateCloudApplication,
): boolean {
  return record.service_type === expected.service_type &&
    record.application_type === expected.application_type &&
    record.status === expected.status &&
    record.current_step === expected.current_step &&
    sameValue(record.applicant_details,expected.applicant_details) &&
    sameValue(record.questionnaire_answers,expected.questionnaire_answers) &&
    sameValue(record.selected_document_ids,expected.selected_document_ids);
}
