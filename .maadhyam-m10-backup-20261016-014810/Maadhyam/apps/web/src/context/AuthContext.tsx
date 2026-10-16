import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { onAuthStateChanged, signInWithEmailAndPassword, signOut, type User } from 'firebase/auth';
import { auth, firebaseConfigurationError } from '../services/firebase';

type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
  token(): Promise<string>;
};
const Context = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
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
    async logout() { if (auth) await signOut(auth); },
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
