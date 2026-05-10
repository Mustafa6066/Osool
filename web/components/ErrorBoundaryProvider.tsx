'use client';

/**
 * Client-Side Error Boundary Provider
 * -------------------------------------
 * Wraps the app with ErrorBoundary since Next.js App Router
 * doesn't support error boundaries in Server Components.
 */

import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ReactNode } from 'react';
import { Sentry } from '@/lib/monitoring';

export function ErrorBoundaryProvider({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Log to console in development
        console.error('App Error:', error, errorInfo);
        
        // Send to monitoring service in production (Relayed via backend)
        if (process.env.NODE_ENV === 'production') {
          Sentry.captureException(error, {
            contexts: {
              react: {
                componentStack: errorInfo.componentStack || undefined
              }
            }
          });
        }
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
