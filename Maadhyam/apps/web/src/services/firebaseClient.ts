
import { getApp, getApps, initializeApp } from "firebase/app";
import {
  getAuth,
  onAuthStateChanged,
  signInAnonymously,
  type User,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

function firebaseAuth() {
  if (
    !firebaseConfig.apiKey ||
    !firebaseConfig.authDomain ||
    !firebaseConfig.projectId ||
    !firebaseConfig.appId
  ) {
    throw new Error(
      "Firebase web configuration is missing.",
    );
  }

  const app =
    getApps().length > 0
      ? getApp()
      : initializeApp(firebaseConfig);

  return getAuth(app);
}

let pendingSignIn: Promise<User> | null = null;

export async function ensureDemoUser(): Promise<User> {
  const auth = firebaseAuth();

  await auth.authStateReady();

  if (auth.currentUser) {
    return auth.currentUser;
  }

  if (!pendingSignIn) {
    pendingSignIn = signInAnonymously(auth)
      .then(({ user }) => user)
      .finally(() => {
        pendingSignIn = null;
      });
  }

  return pendingSignIn;
}

export async function getFirebaseToken(): Promise<string> {
  const user = await ensureDemoUser();
  return user.getIdToken();
}

export function subscribeFirebaseUser(callback:(user:User|null)=>void){
  return onAuthStateChanged(firebaseAuth(),callback);
}
