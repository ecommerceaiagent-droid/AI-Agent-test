import { Link } from 'react-router-dom';
import { Alert } from '../components/Alert';
import { Button } from '../components/Button';
import { useLiffLogin } from '../hooks/useLiffLogin';

export function Login() {
  const { ready, liffReady, loggedIn, working, error, startLogin } = useLiffLogin();
  const status = !ready
    ? 'Initializing LIFF…'
    : !liffReady
      ? 'LIFF is not initialized.'
      : loggedIn
        ? 'Logged in with LINE. Verify the ID token to open your profile.'
        : 'Not logged in with LINE.';

  return (
    <section className="card">
      <p className="eyebrow">Login</p>
      <h1>Login with LINE</h1>
      <p className="lede">
        LIFF starts when this page opens. The ID token is sent to Django and checked with LINE before
        the profile is shown.
      </p>
      <p className="status-line" role="status">
        {status}
      </p>
      {error && <Alert tone="error">{error}</Alert>}
      <div className="actions">
        <Button onClick={() => void startLogin()} disabled={working || !ready}>
          {working ? 'Verifying…' : 'Login with LINE'}
        </Button>
      </div>
      <p className="hint">
        Need the name and email form? <Link to="/signup">Signup</Link>
      </p>
    </section>
  );
}
