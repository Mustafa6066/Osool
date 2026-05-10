/**
 * Frontend Monitoring Utility
 * --------------------------
 * Lightweight alternative to Sentry SDK for capturing and reporting
 * frontend errors to the backend relay and orchestrator.
 */

import { trackError } from '@/lib/orchestrator';
import { getAnonymousId } from '@/lib/session';
import { getCurrentUserFromToken } from '@/lib/api';

interface ErrorContext {
  contexts?: {
    react?: {
      componentStack?: string;
    };
  };
  tags?: Record<string, string>;
  extra?: Record<string, any>;
}

export const Sentry = {
  /**
   * Captures an exception and reports it to the monitoring system.
   * Matches the Sentry SDK API for easy future migration.
   */
  captureException: (error: Error, context?: ErrorContext) => {
    // 1. Log to console for development
    if (process.env.NODE_ENV !== 'production') {
      console.error('Monitoring captured exception:', error, context);
    }

    const anonymousId = getAnonymousId();
    const user = getCurrentUserFromToken();
    const url = typeof window !== 'undefined' ? window.location.href : '';
    const componentStack = context?.contexts?.react?.componentStack;

    // 2. Track via Orchestrator (Analytic & Pipeline)
    trackError({
      anonymousId,
      userId: user?.id,
      errorMessage: error.message,
      errorStack: error.stack,
      componentStack,
      url,
    });

    // 3. Relay to Sentry via Backend (Error Tracking)
    // Using fire-and-forget fetch to avoid blocking the UI
    const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

    fetch(`${API_URL}/api/monitor/frontend-error`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error_message: error.message,
        error_stack: error.stack,
        component_stack: componentStack,
        user_id: user?.id ? String(user.id) : undefined,
        url,
      }),
      keepalive: true,
    }).catch(() => {
      // Silently fail to avoid cascading errors
    });
  }
};
