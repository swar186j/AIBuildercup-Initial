/* eslint react-refresh/only-export-components: ["error", { "allowExportNames": ["useAuth"] }] */
import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { onAuthStateChanged, signInWithEmailAndPassword, signOut, type User } from 'firebase/auth';
import { auth, firebaseConfigurationError } from '../services/firebase';

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
  token(): Promise<string>;
  registerLogoutGuard(guard: () => boolean): () => void;
};
const Context = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const logoutGuards = useRef(new Set<() => boolean>());
  const [loading, setLoading] = useState(Boolean(auth));
  const [error, setError] = useState<string | null>(firebaseConfigurationError);
  useEffect(() => {
    if (!auth) return;
    return onAuthStateChanged(auth, current => { setUser(current); setLoading(false); }, () => {
      setError('Unable to verify your sign-in session.'); setLoading(false);
    });
  }, []);
  const value = useMemo<AuthState>(() => ({
    user, loading, error,
    async login(email, password) {
      if (!auth) throw new Error(firebaseConfigurationError || 'Firebase is not configured');
      setError(null);
      await signInWithEmailAndPassword(auth, email.trim(), password);
    },
    registerLogoutGuard(guard) {
      logoutGuards.current.add(guard);
      return () => { logoutGuards.current.delete(guard); };
    },
    async logout() {
      if ([...logoutGuards.current].some(guard => !guard())) throw new Error('Some changes are not saved. Wait for confirmation or retry saving before signing out.');
      if (auth) await signOut(auth);
    },
    async token() {
      if (!auth?.currentUser) throw new Error('Sign in required');
      return auth.currentUser.getIdToken();
    },
  }), [user, loading, error]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
