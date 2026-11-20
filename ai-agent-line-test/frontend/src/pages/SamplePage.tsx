import { useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';
import { initLiff, readLiffStatus } from '../services/liff';

const pages = {
  one: {
    eyebrow: 'Sample 1',
    title: 'Order sample',
    lede: 'This is a test page opened from the first menu icon.',
    rows: [
      ['Order', 'A-1001'],
      ['Item', 'Green tea'],
      ['Status', 'Ready for pickup'],
    ],
  },
  two: {
    eyebrow: 'Sample 2',
    title: 'Visit sample',
    lede: 'This is a test page opened from the second menu icon.',
    rows: [
      ['Store', 'Main branch'],
      ['Date', '20 Nov 2026'],
      ['Status', 'Checked in'],
    ],
  },
} as const;

export function SamplePage({ page }: { page: keyof typeof pages }) {
  const content = pages[page];
  const [insideLine, setInsideLine] = useState('Checking…');

  useEffect(() => {
    void initLiff()
      .then(() => {
        const status = readLiffStatus();
        setInsideLine(status.inClient ? 'Yes' : 'No, this is a browser');
      })
      .catch((error: unknown) => {
        setInsideLine(getErrorMessage(error));
      });
  }, []);

  return (
    <section className="card">
      <p className="eyebrow">{content.eyebrow}</p>
      <h1>{content.title}</h1>
      <p className="lede">{content.lede}</p>
      <dl className="facts">
        {content.rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
        <div>
          <dt>Opened inside LINE</dt>
          <dd>{insideLine}</dd>
        </div>
      </dl>
      <p className="hint">This page was opened from a LINE chat menu icon.</p>
    </section>
  );
}
