import type { AuthSession, SignupDraft } from '../types';

const SESSION_KEY = 'ai-agent-line-session';
const DRAFT_KEY = 'ai-agent-line-signup-draft';

function isSession(value: unknown): value is AuthSession {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const session = value as Partial<AuthSession>;
  return session.verified === true && typeof session.userId === 'string' && session.userId.length > 0;
}

export function saveSession(session: AuthSession): void {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function loadSession(): AuthSession | null {
  const raw = sessionStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isSession(parsed)) {
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    if (typeof parsed.expiresAt === 'number' && parsed.expiresAt * 1000 <= Date.now()) {
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    return parsed;
  } catch {
    sessionStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
}

export function saveSignupDraft(draft: SignupDraft): void {
  sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
}

export function loadSignupDraft(): SignupDraft | null {
  const raw = sessionStorage.getItem(DRAFT_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }
    const draft = parsed as Partial<SignupDraft>;
    if (typeof draft.fullName !== 'string' || typeof draft.email !== 'string') {
      return null;
    }
    return { fullName: draft.fullName, email: draft.email };
  } catch {
    return null;
  }
}
