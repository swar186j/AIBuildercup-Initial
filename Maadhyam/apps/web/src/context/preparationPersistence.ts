/** External browser-storage failure state, consumed through useSyncExternalStore. */
let failure = '';
const listeners = new Set<() => void>();
export function subscribePersistence(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function persistenceFailure() { return failure; }
export function clearPersistenceFailure() {
  if (!failure) return;
  failure = '';
  listeners.forEach(listener => listener());
}
export function persistPreparations(key: string, value: string) {
  try { localStorage.setItem(key, value); }
  catch {
    failure = 'Browser-local preparation saving failed. Your records remain in this session.';
    listeners.forEach(listener => listener());
  }
}
