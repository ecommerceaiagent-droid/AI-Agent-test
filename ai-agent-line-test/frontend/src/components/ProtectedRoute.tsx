import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { loadSession } from '../services/session';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const session = loadSession();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
