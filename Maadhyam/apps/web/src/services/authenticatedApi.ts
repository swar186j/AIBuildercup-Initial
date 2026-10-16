import { apiFetch } from './apiFetch';
import { auth } from './firebase';

/** Use for M10 protected endpoints. Existing public /api requests are unchanged. */
export async function authenticatedFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const user = auth?.currentUser;
  if (!user) throw new Error('Sign in required');
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${await user.getIdToken()}`);
  return apiFetch(path, { ...init, headers });
}
