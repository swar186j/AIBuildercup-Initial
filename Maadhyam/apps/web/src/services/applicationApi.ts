/** Demo-only persistence client. Do not send real personal information. */
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
export type ApplicationStatus = 'draft' | 'in-progress' | 'completed';
export type SavedApplication = {
  id: string; service: string; kind: string; status: ApplicationStatus;
  payload: Record<string, unknown>; created_at: string; updated_at: string; revision: number;
};
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}/api/applications${path}`, {
    ...init, headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!response.ok) throw new Error(`Application API error: ${response.status}`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const applicationApi = {
  list: () => request<SavedApplication[]>(''),
  get: (id: string) => request<SavedApplication>(`/${encodeURIComponent(id)}`),
  create: (kind = 'fresh') => request<SavedApplication>('', {
    method: 'POST', body: JSON.stringify({ service: 'passport', kind, payload: {} }),
  }),
  save: (app: SavedApplication) => request<SavedApplication>(`/${encodeURIComponent(app.id)}`, {
    method: 'PUT', body: JSON.stringify({ status: app.status, payload: app.payload, revision: app.revision }),
  }),
  history: (id: string) => request<{event: string; timestamp: string}[]>(`/${encodeURIComponent(id)}/history`),
  remove: (id: string) => request<void>(`/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};
