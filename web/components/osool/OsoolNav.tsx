'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

import OsoolAvatar from './OsoolAvatar';
import { IconUp } from './Icons';

interface OsoolNavProps {
  /** Optional active link key for highlighting (not yet used; reserved for future). */
  active?: string;
}

/**
 * Editorial nav from the claude.ai/design handoff. Sticky, blurs the
 * background on scroll, and gains a hairline border once you've scrolled
 * past 8px. Brand uses the animated OsoolAvatar mascot.
 */
export default function OsoolNav({ active: _active }: OsoolNavProps = {}) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header className={'osool-nav' + (scrolled ? ' scrolled' : '')}>
      <div className="osool-container osool-nav-inner">
        <Link href="/" className="osool-nav-brand">
          <span className="osool-nav-mark">
            <OsoolAvatar size={26} animated />
          </span>
          Osool
        </Link>
        <nav className="osool-nav-links">
          <Link href="#product">Product</Link>
          <Link href="#trust">Trust</Link>
          <Link href="#how">How it works</Link>
          <Link href="#developers">Developers</Link>
        </nav>
        <Link href="/login" className="osool-btn osool-btn-sm">
          Sign in
        </Link>
        <Link href="/chat" className="osool-btn osool-btn-primary osool-btn-sm">
          Open Osool <IconUp size={13} style={{ transform: 'rotate(45deg)' }} />
        </Link>
      </div>
    </header>
  );
}
