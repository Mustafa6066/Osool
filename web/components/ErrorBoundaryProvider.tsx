'use client';

/**
 * Client-Side Error Boundary Provider
 * -------------------------------------
 * Wraps the app with ErrorBoundary since Next.js App Router
 * doesn't support error boundaries in Server Components.
 */

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ReactNode } from 'react';

export function ErrorBoundaryProvider({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log to console in development
        console.error('App Error:', error, errorInfo);
        
        // Send to Sentry in production if configured
        if (process.env.NODE_ENV === 'production' && process.env.NEXT_PUBLIC_SENTRY_DSN) {
          import('@sentry/nextjs')
            .then((Sentry) => {
              Sentry.captureException(error, {
                contexts: { react: { componentStack: errorInfo?.componentStack } },
              });
            })
            .catch(() => {
              // Sentry not installed — silent fallback
            });
        }
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
