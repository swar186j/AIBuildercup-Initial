import { useEffect, useState, type ReactNode } from 'react';
import { apiFetch, apiOrigin } from '../services/apiFetch';

/** Wait for a free host to wake before starting revisioned workspace requests. */
export default function BackendGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(!apiOrigin);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!apiOrigin) return;
    const controller = new AbortController();
    const deadline = setTimeout(() => controller.abort(), 90000);
    let active = true;
    apiFetch('/api/health', { signal: controller.signal })
      .then(async response => {
        if (!response.ok || (await response.json()).status !== 'healthy') throw new Error('Unavailable');
        if (active) setReady(true);
      })
      .catch(() => { if (active) setError(true); })
      .finally(() => clearTimeout(deadline));
    return () => { active = false; clearTimeout(deadline); controller.abort(); };
  }, [attempt]);
  if (ready) return <>{children}</>;
  return <main className="min-h-screen grid place-items-center bg-slate-50 px-4 text-slate-700 dark:bg-slate-950 dark:text-slate-200">
    <div className="max-w-md space-y-4 text-center">
      {error ? <><p role="alert">The workspace could not start. Check your connection and retry.</p>
        <button className="rounded-lg bg-teal-700 px-5 py-2 text-white" onClick={() => { setError(false); setAttempt(value => value + 1); }}>Retry workspace connection</button></>
        : <p role="status">Starting your secure workspace. The free server may take a minute to wake up.</p>}
    </div>
  </main>;
}
