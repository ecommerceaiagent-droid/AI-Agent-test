export interface VerifiedLineUser {
  userId: string;
  displayName: string;
  pictureUrl: string | null;
  email: string | null;
  expiresAt: number | null;
}

export interface VerifyResponse {
  status: string;
  user: VerifiedLineUser;
}

export interface AuthSession {
  userId: string;
  displayName: string;
  pictureUrl: string | null;
  statusMessage: string | null;
  email: string | null;
  expiresAt: number | null;
  verified: true;
  verifiedAt: string;
}
