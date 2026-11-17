import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getErrorMessage } from '../services/api';
import { completeLineAuthentication } from '../services/lineAuth';
import { clearPendingLogin, hasPendingLogin, initLiff, isLoggedIn, loginWithLine } from '../services/liff';

export function useLiffLogin() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [liffReady, setLiffReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const finish = useCallback(async () => {
    setWorking(true);
    setError(null);
    try {
      await completeLineAuthentication();
      clearPendingLogin();
      navigate('/profile', { replace: true });
    } catch (err) {
      clearPendingLogin();
      setError(getErrorMessage(err));
      setWorking(false);
    }
  }, [navigate]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await initLiff();
        if (cancelled) {
          return;
        }
        const signedIn = isLoggedIn();
        setLiffReady(true);
        setLoggedIn(signedIn);
        setReady(true);
        if (!hasPendingLogin()) {
          return;
        }
        if (signedIn) {
          await finish();
          return;
        }
        clearPendingLogin();
        setError('LINE login was not completed.');
      } catch (err) {
        if (cancelled) {
          return;
        }
        setLiffReady(false);
        setReady(true);
        setError(getErrorMessage(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [finish]);

  const startLogin = useCallback(async () => {
    setWorking(true);
    setError(null);
    try {
      await initLiff();
      setLiffReady(true);
      if (!isLoggedIn()) {
        loginWithLine(window.location.href);
        return;
      }
      setLoggedIn(true);
      await finish();
    } catch (err) {
      setError(getErrorMessage(err));
      setWorking(false);
    }
  }, [finish]);

  return { ready, liffReady, loggedIn, working, error, startLogin };
}
