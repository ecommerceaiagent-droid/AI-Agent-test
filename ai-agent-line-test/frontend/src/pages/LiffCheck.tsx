import { useCallback, useEffect, useState } from 'react';
import { Alert } from '../components/Alert';
import { Button } from '../components/Button';
import { getErrorMessage } from '../services/api';
import { completeLineAuthentication } from '../services/lineAuth';
import {
  clearPendingLogin,
  getLiffId,
  hasPendingLogin,
  initLiff,
  loginWithLine,
  readLiffStatus,
  type LiffStatus,
} from '../services/liff';
import type { AuthSession } from '../types';

export function LiffCheck() {
  const [working, setWorking] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [status, setStatus] = useState<LiffStatus | null>(null);
  const [profile, setProfile] = useState<AuthSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runCheck = useCallback(async () => {
    setWorking(true);
    setError(null);
    setProfile(null);
    try {
      await initLiff();
      const nextStatus = readLiffStatus();
      setInitialized(true);
      setStatus(nextStatus);
      if (hasPendingLogin() && !nextStatus.loggedIn) {
        clearPendingLogin();
        setError('LINE did not grant access to the profile. The checks above do not need that permission.');
      } else if (nextStatus.loggedIn) {
        clearPendingLogin();
        const session = await completeLineAuthentication();
        setProfile(session);
      }
    } catch (err) {
      setInitialized(false);
      setStatus(null);
      setError(getErrorMessage(err));
    } finally {
      setWorking(false);
    }
  }, []);

  useEffect(() => {
    void runCheck();
  }, [runCheck]);

  function requestProfile() {
    setError(null);
    loginWithLine(window.location.origin);
  }

  const liffId = getLiffId();

  return (
    <section className="card">
      <p className="eyebrow">LIFF check</p>
      <h1>Is the LIFF app running?</h1>
      <p className="lede">
        This page starts LIFF and shows what LINE reports. It does not ask for a name, email, or password.
      </p>
      <dl className="facts">
        <div>
          <dt>LIFF initialized</dt>
          <dd>{working ? 'Checking…' : initialized ? 'Yes' : 'No'}</dd>
        </div>
        <div>
          <dt>LIFF ID</dt>
          <dd className="mono">{liffId || 'Not set'}</dd>
        </div>
        <div>
          <dt>Opened inside LINE</dt>
          <dd>{status ? (status.inClient ? 'Yes' : 'No, this is a browser') : 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Operating system</dt>
          <dd>{status?.os || 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Language</dt>
          <dd>{status?.language || 'Unavailable'}</dd>
        </div>
        <div>
          <dt>LINE version</dt>
          <dd>{status?.lineVersion || 'Unavailable'}</dd>
        </div>
        <div>
          <dt>LIFF version</dt>
          <dd>{status?.liffVersion || 'Unavailable'}</dd>
        </div>
        <div>
          <dt>Screen</dt>
          <dd>{status ? `${status.contextType} / ${status.viewType}` : 'Unavailable'}</dd>
        </div>
        <div>
          <dt>LINE profile permission</dt>
          <dd>{status ? (status.loggedIn ? 'Granted' : 'Not granted') : 'Unavailable'}</dd>
        </div>
      </dl>
      {profile && (
        <dl className="facts">
          <div>
            <dt>LINE display name</dt>
            <dd>{profile.displayName}</dd>
          </div>
          <div>
            <dt>LINE user ID</dt>
            <dd className="mono">{profile.userId}</dd>
          </div>
          <div>
            <dt>ID token</dt>
            <dd>Verified by Django</dd>
          </div>
        </dl>
      )}
      {error && <Alert tone="error">{error}</Alert>}
      <div className="actions">
        <Button onClick={() => void runCheck()} disabled={working}>
          {working ? 'Checking…' : 'Run check again'}
        </Button>
        {initialized && status && !status.loggedIn && (
          <Button variant="secondary" onClick={requestProfile} disabled={working}>
            Request LINE profile
          </Button>
        )}
      </div>
      <p className="hint">
        Open this page from the LINE app. Initialized and Opened inside LINE should both say Yes.
      </p>
    </section>
  );
}
