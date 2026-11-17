import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert } from '../components/Alert';
import { Button } from '../components/Button';
import { useLiffLogin } from '../hooks/useLiffLogin';
import { loadSignupDraft, saveSignupDraft } from '../services/session';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function Signup() {
  const draft = loadSignupDraft();
  const [fullName, setFullName] = useState(draft?.fullName ?? '');
  const [email, setEmail] = useState(draft?.email ?? '');
  const [formError, setFormError] = useState<string | null>(null);
  const { ready, liffReady, loggedIn, working, error, startLogin } = useLiffLogin();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = fullName.trim();
    const address = email.trim();
    if (name.length < 2) {
      setFormError('Enter your full name.');
      return;
    }
    if (!EMAIL_PATTERN.test(address)) {
      setFormError('Enter a valid email address.');
      return;
    }
    setFormError(null);
    saveSignupDraft({ fullName: name, email: address });
    await startLogin();
  }

  const status = !ready
    ? 'Checking LINE login…'
    : !liffReady
      ? 'LIFF is not initialized.'
      : loggedIn
        ? 'LINE session found.'
        : 'Not logged in with LINE.';

  return (
    <section className="card">
      <p className="eyebrow">Signup</p>
      <h1>Create your test session</h1>
      <p className="lede">
        Name and email stay in this browser. There is no password and no database account. LINE Login
        is the authentication step.
      </p>
      <form className="form" onSubmit={onSubmit} noValidate>
        <label>
          Full Name
          <input
            name="fullName"
            autoComplete="name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            required
            maxLength={80}
          />
        </label>
        <label>
          Email Address
          <input
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            maxLength={254}
          />
        </label>
        <p className="status-line">{status}</p>
        {formError && <Alert tone="error">{formError}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        <Button type="submit" disabled={working}>
          {working ? 'Connecting to LINE…' : 'Login with LINE'}
        </Button>
      </form>
      <p className="hint">
        Already verified? <Link to="/login">Login</Link>
      </p>
    </section>
  );
}
