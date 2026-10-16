import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

const required = ['VITE_FIREBASE_API_KEY', 'VITE_FIREBASE_AUTH_DOMAIN', 'VITE_FIREBASE_PROJECT_ID', 'VITE_FIREBASE_APP_ID'] as const;
const env = import.meta.env;
const missing = required.filter(key => !env[key]);
export const firebaseConfigured = missing.length === 0;
export const firebaseConfigurationError = missing.length ? `Missing Firebase settings: ${missing.join(', ')}` : null;

const app = firebaseConfigured ? (getApps().length ? getApp() : initializeApp({
  apiKey: env.VITE_FIREBASE_API_KEY,
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: env.VITE_FIREBASE_PROJECT_ID,
  appId: env.VITE_FIREBASE_APP_ID,
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET,
})) : null;

export const auth = app ? getAuth(app) : null;
if (auth && import.meta.env.DEV && env.VITE_USE_FIREBASE_AUTH_EMULATOR === 'true') {
  connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
}
