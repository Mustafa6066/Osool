'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Compass, LayoutDashboard, Menu, Sparkles, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/components/ThemeToggle';
import LanguageToggle from '@/components/LanguageToggle';
import ProfileDropdown from '@/components/ProfileDropdown';

const PUBLIC_LINKS = [
  { label: 'Home', href: '/' },
  { label: 'Explore', href: '/explore' },
  { label: 'Developers', href: '/developers' },
  { label: 'Areas', href: '/areas' },
  { label: 'Projects', href: '/projects' },
];

export default function PublicPageNav({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-background)]/88 backdrop-blur-2xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--color-text-primary)] text-[var(--color-background)] shadow-sm">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-tight">Osool.ai</div>
              <div className="text-[11px] text-[var(--color-text-muted)]">Egypt real estate intelligence</div>
            </div>
          </Link>

          <nav className="hidden items-center gap-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] p-1 md:flex">
            {PUBLIC_LINKS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'bg-[var(--color-text-primary)] text-[var(--color-background)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden items-center gap-2 md:flex">
            <LanguageToggle />
            <ThemeToggle />
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] transition-colors hover:border-emerald-500/40"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  Workspace
                </Link>
                <ProfileDropdown onGenerateInvitation={() => undefined} />
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-full px-4 py-2 text-sm font-medium text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text-primary)]"
                >
                  Sign in
                </Link>
                <Link
                  href="/chat"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-4 py-2 text-sm font-semibold text-[var(--color-background)] transition-transform hover:scale-[1.02]"
                >
                  <Sparkles className="h-4 w-4" />
                  Start with Osool
                </Link>
              </>
            )}
          </div>

          <button
            onClick={() => setMobileOpen((open) => !open)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] md:hidden"
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="border-t border-[var(--color-border)] bg-[var(--color-background)] px-4 py-4 md:hidden">
            <div className="space-y-2">
              {PUBLIC_LINKS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`block rounded-2xl px-4 py-3 text-sm font-medium ${
                    isActive(item.href)
                      ? 'bg-[var(--color-text-primary)] text-[var(--color-background)]'
                      : 'bg-[var(--color-surface)] text-[var(--color-text-primary)]'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2">
              <LanguageToggle />
              <ThemeToggle />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <Link
                href={isAuthenticated ? '/dashboard' : '/login'}
                onClick={() => setMobileOpen(false)}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm font-medium"
              >
                <LayoutDashboard className="h-4 w-4" />
                {isAuthenticated ? 'Workspace' : 'Sign in'}
              </Link>
              <Link
                href="/explore"
                onClick={() => setMobileOpen(false)}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[var(--color-text-primary)] px-4 py-3 text-sm font-semibold text-[var(--color-background)]"
              >
                <Compass className="h-4 w-4" />
                Explore
              </Link>
            </div>
          </div>
        )}
      </header>

      <div className="pt-16">{children}</div>
    </div>
  );
}
