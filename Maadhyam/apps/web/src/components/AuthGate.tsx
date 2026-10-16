import { useState, type FormEvent, type ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';

export default function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading, error: setupError, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (loading) return <main className="min-h-screen grid place-items-center bg-slate-50 text-slate-700" role="status">Checking your session…</main>;
  if (user) return <>{children}</>;
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(''); setBusy(true);
    try { await login(email, password); }
    catch { setError('Sign-in failed. Check your email, password and Firebase Authentication setup.'); }
    finally { setBusy(false); }
  }
  return <main className="min-h-screen grid place-items-center bg-slate-50 px-4 dark:bg-slate-950">
    <form onSubmit={e => { void submit(e); }} className="w-full max-w-sm space-y-4 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-900" aria-label="Sign in to Maadhyam">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Maadhyam</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">Sign in to access your workspace.</p>
      <label className="block text-sm text-slate-700 dark:text-white">Email
        <input required type="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} className="mt-1 w-full rounded-lg border p-2 text-slate-900" />
      </label>
      <label className="block text-sm text-slate-700 dark:text-white">Password
        <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1 w-full rounded-lg border p-2 text-slate-900" />
      </label>
      {(setupError || error) && <p role="alert" className="text-sm text-red-700">{setupError || error}</p>}
      <button disabled={busy || Boolean(setupError)} type="submit" className="w-full rounded-lg bg-teal-700 p-3 font-semibold text-white disabled:opacity-50">{busy ? 'Signing in…' : 'Sign in'}</button>
    </form>
  </main>;
}
