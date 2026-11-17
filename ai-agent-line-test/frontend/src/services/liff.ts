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

function stayOnEndpoint(): void {
  const params = new URLSearchParams(window.location.search);
  if (!params.has('liff.state')) {
    return;
  }
  params.delete('liff.state');
  const search = params.toString();
  const next = `${window.location.pathname}${search ? `?${search}` : ''}${window.location.hash}`;
  window.history.replaceState(window.history.state, '', next);
}

export interface LiffStatus {
  inClient: boolean;
  os: string;
  language: string;
  lineVersion: string;
  liffVersion: string;
  contextType: string;
  viewType: string;
  loggedIn: boolean;
}

export function readLiffStatus(): LiffStatus {
  const context = liff.getContext();
  return {
    inClient: liff.isInClient(),
    os: liff.getOS() || 'Unavailable',
    language: liff.getLanguage() || 'Unavailable',
    lineVersion: liff.getLineVersion() || 'Unavailable',
    liffVersion: liff.getVersion() || 'Unavailable',
    contextType: context?.type || 'Unavailable',
    viewType: context?.viewType || 'Unavailable',
    loggedIn: liff.isLoggedIn(),
  };
}

export function initLiff(): Promise<void> {
  const liffId = getLiffId();
  if (!liffId) {
    return Promise.reject(new Error('VITE_LIFF_ID is not set. Add it to frontend/.env and restart Vite.'));
  }
  if (!initPromise) {
    stayOnEndpoint();
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
