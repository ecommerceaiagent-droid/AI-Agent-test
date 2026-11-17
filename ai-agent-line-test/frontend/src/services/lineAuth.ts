import { getIDToken, getProfile, initLiff, isLoggedIn } from './liff';
import { verifyLineToken } from './api';
import { saveSession } from './session';
import type { AuthSession } from '../types';

let inFlight: Promise<AuthSession> | null = null;

async function verifyCurrentLogin(): Promise<AuthSession> {
  await initLiff();
  if (!isLoggedIn()) {
    throw new Error('LINE login is not complete.');
  }

  const idToken = getIDToken();
  if (!idToken) {
    throw new Error('LINE did not return an ID token. Add the openid scope to the LIFF app.');
  }

  const profile = await getProfile();
  const verified = await verifyLineToken(idToken);
  const user = verified.user;
  if (!user?.userId) {
    throw new Error('Backend verification did not return a LINE user ID.');
  }

  const session: AuthSession = {
    userId: user.userId,
    displayName: user.displayName || 'LINE user',
    pictureUrl: user.pictureUrl,
    statusMessage: profile.statusMessage?.trim() || null,
    email: user.email,
    expiresAt: user.expiresAt,
    verified: true,
    verifiedAt: new Date().toISOString(),
  };
  saveSession(session);
  return session;
}

export function completeLineAuthentication(): Promise<AuthSession> {
  if (!inFlight) {
    inFlight = verifyCurrentLogin().finally(() => {
      inFlight = null;
    });
  }
  return inFlight;
}
