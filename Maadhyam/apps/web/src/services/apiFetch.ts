/** Public deployment URL only. Provider secrets never belong in VITE_* variables. */
export const apiOrigin = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  if (!path.startsWith('/api/')) throw new Error('Invalid API path');
  if (apiOrigin && !apiOrigin.startsWith('https://') && !import.meta.env.DEV) {
    throw new Error('The hosted API must use HTTPS');
  }
  return fetch(apiOrigin + path, init);
}
