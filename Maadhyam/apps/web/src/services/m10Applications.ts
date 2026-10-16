import { authenticatedFetch } from './authenticatedApi';
import type { JourneyData } from '../context/preparationStorage';

export type CloudApplication = {
  id: string;
  owner_user_id: string;
  service_type: string;
  application_type: string;
  status: 'draft' | 'in-progress' | 'completed';
  applicant_details: { name?: string; date_of_birth?: string };
  questionnaire_answers: JourneyData['answers'];
  current_step: number;
  selected_document_ids: string[];
  rule_pack_version: string;
  revision: number;
  updated_at: string;
};
export type DraftPayload = {
  client_id?: string;
  service_type: 'passport';
  application_type: JourneyData['assistanceType'];
  status: CloudApplication['status'];
  applicant_details: { name: string; date_of_birth: string };
  questionnaire_answers: JourneyData['answers'];
  current_step: number;
  selected_document_ids: string[];
  rule_pack_version: string;
};

async function json<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set('Content-Type', 'application/json');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  const connectionError = () => new Error('Account connection unavailable or timed out. Check that the API is running and Firebase/Firestore is configured. Any pending change has not been confirmed.');
  const request = async (): Promise<T> => {
    let res: Response;
    try { res = await authenticatedFetch(path, { ...init, headers, signal: controller.signal }); }
    catch { throw connectionError(); }
    if (!res.ok) {
      let message = `Cloud request failed (${res.status})`;
      try {
        const body = await res.json() as { error?: { message?: string }; detail?: string };
        message = body.error?.message || body.detail || message;
      } catch { /* use status */ }
      const error = new Error(message) as Error & { status?: number };
      error.status = res.status;
      throw error;
    }
    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  };
  try {
    // Bound token acquisition, response headers AND response-body parsing.
    return await Promise.race([request(), new Promise<never>((_, reject) => {
      controller.signal.addEventListener('abort', () => reject(connectionError()), { once: true });
    })]);
  } finally { clearTimeout(timeout); }
}
export const listCloudApplications = () => json<CloudApplication[]>('/api/applications');
export const createCloudApplication = (payload: DraftPayload) => json<CloudApplication>('/api/applications', { method: 'POST', body: JSON.stringify(payload) });
export const updateCloudApplication = (id: string, revision: number, payload: DraftPayload) =>
  json<CloudApplication>(`/api/applications/${encodeURIComponent(id)}`, {
    method: 'PATCH', body: JSON.stringify({ revision, ...payload, client_id: undefined, service_type: undefined }),
  });
export const deleteCloudApplication = (id: string, revision: number) =>
  json<void>(`/api/applications/${encodeURIComponent(id)}?revision=${revision}`, { method: 'DELETE' });
export const migrateCloudApplications = (records: DraftPayload[], migrationId: string) =>
  json<{ application_ids: string[]; local_data_deleted: false }>('/api/applications/migrate', {
    method: 'POST', body: JSON.stringify({ confirmed: true, migration_id: migrationId, records }),
  });
export type CloudPlanner = { completed: string[]; revision: number };
export const getCloudPlanner = () => json<CloudPlanner>('/api/applications/workspace/planner');
export const putCloudPlanner = (revision: number, task_id: string, completed: boolean) =>
  json<CloudPlanner>('/api/applications/workspace/planner', { method: 'PUT', body: JSON.stringify({ revision, task_id, completed }) });
export const resetCloudPlanner = (revision: number) =>
  json<CloudPlanner>(`/api/applications/workspace/planner?revision=${revision}`, { method: 'DELETE' });
