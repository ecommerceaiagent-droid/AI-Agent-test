import axios from 'axios';
import type { VerifyResponse } from '../types';

const baseURL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 20000,
});

export async function verifyLineToken(idToken: string): Promise<VerifyResponse> {
  const { data } = await api.post<VerifyResponse>('/api/auth/verify/', { id_token: idToken });
  return data;
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (data && typeof data === 'object' && 'message' in data && typeof data.message === 'string') {
      return data.message;
    }
    if (error.code === 'ECONNABORTED') {
      return 'The backend took too long to respond. On the Render free plan the first request can be slow while the service wakes up.';
    }
    if (!error.response) {
      return 'Could not reach the backend. Check that Django is running and VITE_API_BASE_URL is correct.';
    }
    return `Request failed (${error.response.status}).`;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return 'Something went wrong.';
}
