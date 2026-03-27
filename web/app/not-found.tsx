import Link from 'next/link';
import { Home, Search } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[var(--color-background)] px-6 text-center">
      <div className="max-w-sm w-full">
        {/* Large 404 */}
        <p className="text-[96px] font-bold leading-none text-emerald-500/15 mb-4 select-none tabular-nums">
          404
        </p>

        <h1 className="text-[22px] font-semibold text-[var(--color-text-primary)] mb-2 tracking-tight">
          Page not found
        </h1>
        <p className="text-[14px] text-[var(--color-text-muted)] mb-8 leading-relaxed">
          This page doesn&apos;t exist or has been moved.
          Check the URL or explore from the homepage.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-[13px] font-semibold text-white hover:bg-emerald-700 transition-colors"
          >
            <Home className="h-3.5 w-3.5" />
            Go home
          </Link>
          <Link
            href="/explore"
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] px-5 py-2.5 text-[13px] font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
          >
            <Search className="h-3.5 w-3.5" />
            Explore
          </Link>
        </div>
      </div>
    </div>
  );
}
