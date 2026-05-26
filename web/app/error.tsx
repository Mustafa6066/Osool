'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Link from 'next/link';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[Osool Error]', error);
  }, [error]);

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[var(--color-background)] px-6 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="max-w-sm w-full"
      >
        {/* Icon */}
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="h-7 w-7 text-red-500" strokeWidth={1.8} />
        </div>

        {/* Heading */}
        <h1 className="text-[22px] font-semibold text-[var(--color-text-primary)] mb-2 tracking-tight">
          Something went wrong
        </h1>
        <p className="text-[14px] text-[var(--color-text-muted)] mb-8 leading-relaxed">
          An unexpected error occurred. Please try again or return home.
          {error.digest && (
            <span className="block mt-2 text-[11px] font-mono text-[var(--color-text-muted)]/60">
              Error ID: {error.digest}
            </span>
          )}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-full bg-emerald-600 px-5 py-2.5 text-[13px] font-semibold text-white hover:bg-emerald-700 active:scale-95 transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] px-5 py-2.5 text-[13px] font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
          >
            <Home className="h-3.5 w-3.5" />
            Go home
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
