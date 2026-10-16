import { authenticatedFetch } from './authenticatedApi';
import type { DocumentMetadata, LocalDocument } from '../context/DocumentContext';
import type { HouseholdMember } from '../context/HouseholdContext';

export type CloudDocument = { id: string; filename: string; mime: string; added_at: string; metadata: DocumentMetadata; status: LocalDocument['status']; revision: number; deleting?: boolean };
export type CloudHousehold = { members: HouseholdMember[]; revision: number };

async function request<T>(path: string, init: RequestInit = {}, binary = false): Promise<T> {
  const controller = new AbortController();
  let timeout: ReturnType<typeof setTimeout>;
  const deadline = new Promise<never>((_, reject) => {
    timeout = setTimeout(() => { controller.abort(); reject(new Error('Cloud request timed out. Retry before leaving this page.')); }, 60000);
  });
  const operation = async () => {
    const response = await authenticatedFetch('/api/workspace' + path, { ...init, signal: controller.signal });
    if (!response.ok) {
      let message = `Cloud request failed (${response.status})`;
      try { const body = await response.json(); message = body.error?.message || body.detail || message; } catch { /* use status */ }
      throw new Error(message);
    }
    if (response.status === 204) return undefined as T;
    return (binary ? response.blob() : response.json()) as Promise<T>;
  };
  try { return await Promise.race([operation(), deadline]); }
  finally { clearTimeout(timeout!); }
}
export const listDocuments = () => request<CloudDocument[]>('/documents');
export async function restoreDocument(record: CloudDocument): Promise<LocalDocument> {
  const blob = record.deleting ? new Blob([], { type: record.mime }) : await request<Blob>(`/documents/${record.id}/content`, {}, true);
  const file = new File([blob], record.filename, { type: record.mime });
  return { id: record.id, file, url: URL.createObjectURL(file), metadata: record.metadata, status: record.status, addedAt: new Date(record.added_at), pendingDeletion: record.deleting };
}
export function uploadDocument(document: LocalDocument) {
  const body = new FormData();
  body.set('file', document.file);
  body.set('metadata', JSON.stringify(document.metadata));
  return request<CloudDocument>(`/documents/${document.id}`, { method: 'PUT', body });
}
export const patchDocument = (document: LocalDocument, revision: number) => request<CloudDocument>(`/documents/${document.id}`, {
  method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision, metadata: document.metadata, status: document.status }),
});
export const deleteDocument = (id: string, revision: number) => request<void>(`/documents/${id}?revision=${revision}`, { method: 'DELETE' });
export const loadHousehold = () => request<CloudHousehold>('/household');
export const saveHousehold = (members: HouseholdMember[], revision: number) => request<CloudHousehold>('/household', {
  method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ members, revision }),
});
