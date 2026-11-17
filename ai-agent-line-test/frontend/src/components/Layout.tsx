import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          AI Agent LINE Test
        </Link>
      </header>
      <main className="content">{children}</main>
    </div>
  );
}
