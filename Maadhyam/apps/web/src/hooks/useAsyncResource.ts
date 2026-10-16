import { useEffect, useState } from 'react';

/** Loading is derived from the request identity; old results never describe new inputs. */
export function useAsyncResource<T>(load: (signal: AbortSignal) => Promise<T>, revision = 0) {
  const [settled, setSettled] = useState<{
    load: typeof load; revision: number; data: T | null; error: unknown;
  } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(
      data => { if (!controller.signal.aborted) setSettled({ load, revision, data, error: null }); },
      error => { if (!controller.signal.aborted) setSettled({ load, revision, data: null, error }); },
    );
    return () => controller.abort();
  }, [load, revision]);
  const current = settled?.load === load && settled.revision === revision ? settled : null;
  return { data: current?.data ?? null, error: current?.error ?? null, loading: current === null };
}

export function requestDelay(milliseconds: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, milliseconds);
    if (signal.aborted) abort();
    else signal.addEventListener('abort', abort, { once: true });
  });
}
