import { Button, ButtonAnchor, ButtonLink } from '../components/Button';
import { getLiffUrl } from '../services/liff';

export function Home() {
  const lineUrl = getLiffUrl();

  return (
    <section className="card">
      <p className="eyebrow">Prototype</p>
      <h1>AI Agent LINE Test</h1>
      <p className="lede">
        Sign in with LINE to verify an ID token, then message your Official Account to confirm the
        webhook replies from Django.
      </p>
      <div className="actions">
        <ButtonLink to="/signup">Signup</ButtonLink>
        <ButtonLink to="/login" variant="secondary">
          Login
        </ButtonLink>
        {lineUrl ? (
          <ButtonAnchor href={lineUrl}>Open in LINE</ButtonAnchor>
        ) : (
          <Button variant="secondary" disabled>
            Open in LINE
          </Button>
        )}
      </div>
      {!lineUrl && <p className="hint">Set VITE_LIFF_ID to enable Open in LINE.</p>}
    </section>
  );
}
