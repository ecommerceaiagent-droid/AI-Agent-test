import { useEffect, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { Alert } from '../components/Alert';
import { Button } from '../components/Button';
import { getErrorMessage } from '../services/api';
import { completeLineAuthentication } from '../services/lineAuth';
import { initLiff, isInLineClient, logout } from '../services/liff';
import { clearSession, loadSession } from '../services/session';
import type { AuthSession } from '../types';

export function Profile() {
  const navigate = useNavigate();
  const [session, setSession] = useState<AuthSession | null>(() => loadSession());
  const [inLine, setInLine] = useState<boolean | null>(null);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    initLiff()
      .then(() => {
        if (!cancelled) {
          setInLine(isInLineClient());
        }
      })
      .catch(() => {
        if (!cancelled) {
          setInLine(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshProfile() {
    setWorking(true);
    setError(null);
    try {
      const next = await completeLineAuthentication();
      setSession(next);
      setInLine(isInLineClient());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setWorking(false);
    }
  }

  function handleLogout() {
    clearSession();
    try {
      logout();
    } catch {
      // Local session is already cleared when LIFF was not initialized.
    }
    navigate('/', { replace: true });
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  const clientLabel =
    inLine === null ? 'Verified' : inLine ? 'Verified · Inside LINE' : 'Verified · Browser';
  const initial = (session.displayName || '?').slice(0, 1).toUpperCase();

  return (
    <section className="card">
      <p className="eyebrow">Profile</p>
      <h1>LINE profile</h1>
      <div className="profile">
        {session.pictureUrl ? (
          <img
            className="avatar"
            src={session.pictureUrl}
            alt=""
            width={96}
            height={96}
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="avatar avatar-fallback" aria-hidden="true">
            {initial}
          </div>
        )}
        <dl className="facts">
          <div>
            <dt>LINE Display Name</dt>
            <dd>{session.displayName || 'Not provided'}</dd>
          </div>
          <div>
            <dt>LINE User ID</dt>
            <dd className="mono">{session.userId}</dd>
          </div>
          <div>
            <dt>Profile Picture</dt>
            <dd>{session.pictureUrl ? 'Shown above from the verified token' : 'Not provided'}</dd>
          </div>
          <div>
            <dt>Status Message</dt>
            <dd>{session.statusMessage || 'None'}</dd>
          </div>
          <div>
            <dt>Authentication Status</dt>
            <dd>{clientLabel}</dd>
          </div>
        </dl>
      </div>
      {session.email && <p className="hint">Email from the verified token: {session.email}</p>}
      {error && <Alert tone="error">{error}</Alert>}
      <div className="actions">
        <Button onClick={() => void refreshProfile()} disabled={working}>
          {working ? 'Refreshing…' : 'Refresh Profile'}
        </Button>
        <Button variant="secondary" onClick={handleLogout}>
          Logout
        </Button>
      </div>
    </section>
  );
}
