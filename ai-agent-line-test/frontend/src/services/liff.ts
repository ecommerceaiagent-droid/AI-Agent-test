import liff from '@line/liff';

const PENDING_KEY = 'ai-agent-line-login-pending';

let initPromise: Promise<void> | null = null;

export function getLiffId(): string {
  return import.meta.env.VITE_LIFF_ID?.trim() ?? '';
}

export function getLiffUrl(): string {
  const liffId = getLiffId();
  return liffId ? `https://liff.line.me/${liffId}` : '';
}

export function initLiff(): Promise<void> {
  const liffId = getLiffId();
  if (!liffId) {
    return Promise.reject(new Error('VITE_LIFF_ID is not set. Add it to frontend/.env and restart Vite.'));
  }
  if (!initPromise) {
    initPromise = liff.init({ liffId }).catch((error: unknown) => {
      initPromise = null;
      throw error;
    });
  }
  return initPromise;
}

export function isLoggedIn(): boolean {
  return liff.isLoggedIn();
}

export function isInLineClient(): boolean {
  return liff.isInClient();
}

export function loginWithLine(redirectUri: string): void {
  sessionStorage.setItem(PENDING_KEY, '1');
  liff.login({ redirectUri });
}

export function hasPendingLogin(): boolean {
  return sessionStorage.getItem(PENDING_KEY) === '1';
}

export function clearPendingLogin(): void {
  sessionStorage.removeItem(PENDING_KEY);
}

export function logout(): void {
  if (liff.isLoggedIn()) {
    liff.logout();
  }
}

export async function getProfile() {
  return liff.getProfile();
}

export function getIDToken(): string | null {
  return liff.getIDToken();
}
