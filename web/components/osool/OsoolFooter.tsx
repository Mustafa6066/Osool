import Link from 'next/link';

import OsoolAvatar from './OsoolAvatar';

/**
 * Editorial footer from the claude.ai/design handoff. Three link columns
 * + brand block + bilingual tag + legal strip.
 */
export default function OsoolFooter() {
  return (
    <footer className="osool-footer">
      <div className="osool-container">
        <div className="osool-footer-grid">
          <div>
            <div className="osool-footer-brand">
              <span style={{ color: 'var(--osool-text)' }}>
                <OsoolAvatar size={22} />
              </span>
              <b>Osool</b>
            </div>
            <p className="osool-footer-tag">
              أصول — the verified registry and AI valuation for
              Egyptian real estate. Made in Cairo.
            </p>
          </div>
          <div>
            <h5>Product</h5>
            <div className="osool-footer-links">
              <Link href="/chat">Chat</Link>
              <Link href="/market">Market Pulse</Link>
              <Link href="/explore">AI Valuation</Link>
              <Link href="/properties">Contract Check</Link>
            </div>
          </div>
          <div>
            <h5>Company</h5>
            <div className="osool-footer-links">
              <Link href="/contact">About</Link>
              <Link href="/privacy">Trust &amp; safety</Link>
              <Link href="/contact">Press</Link>
              <Link href="/contact">Careers</Link>
            </div>
          </div>
          <div>
            <h5>Resources</h5>
            <div className="osool-footer-links">
              {/* /buying-guide is dynamic-only (/buying-guide/[slug]); point at /areas
                  which serves the same intent — a buyer-facing area overview. */}
              <Link href="/areas">Buyer&apos;s guide</Link>
              <Link href="/market">Market reports</Link>
              <Link href="/contact">API for developers</Link>
              <Link href="/contact">Contact</Link>
            </div>
          </div>
        </div>
        <div className="osool-footer-bottom">
          <span>© {new Date().getFullYear()} Osool Technologies · Cairo, Egypt</span>
          <div className="legal">
            <Link href="/privacy">CBE Law 194</Link>
            <Link href="/privacy">FRA 125</Link>
            <Link href="/privacy">Privacy</Link>
            <Link href="/privacy">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
