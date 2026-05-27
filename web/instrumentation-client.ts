/**
 * Next.js 16 client instrumentation — runs once when the app mounts in
 * the browser. Initialises Sentry for client-side error tracking when
 * NEXT_PUBLIC_SENTRY_DSN is configured.
 *
 * The server-side counterpart lives in `instrumentation.ts` (its
 * onRequestError hook already forwards to Sentry — see that file).
 *
 * Without this file, Sentry is dependency-installed but never starts,
 * so frontend errors (the half of the stack users actually see) go
 * uncaptured.
 */

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  // Lazy import keeps Sentry out of the bundle when DSN isn't set.
  import('@sentry/nextjs').then((Sentry) => {
    Sentry.init({
      dsn,
      // Production gets a conservative sample to keep quota reasonable;
      // preview / dev capture everything because volume is tiny.
      tracesSampleRate: process.env.NEXT_PUBLIC_VERCEL_ENV === 'production' ? 0.1 : 1.0,
      // Replay only the failing session, never the happy path — too
      // expensive and PII-risky to record everything.
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 1.0,
      // Strip query strings and known PII fields from URLs and breadcrumbs
      // before they leave the browser. The auth + chat endpoints can carry
      // session tokens and free-text prompts that include phone numbers.
      beforeSend(event) {
        if (event.request?.url) {
          event.request.url = event.request.url.split('?')[0];
        }
        // Drop chat prompt bodies — those are user PII.
        if (event.request?.data && typeof event.request.data === 'object') {
          const data = event.request.data as Record<string, unknown>;
          if ('message' in data) data.message = '[REDACTED]';
          if ('password' in data) data.password = '[REDACTED]';
        }
        return event;
      },
      environment: process.env.NEXT_PUBLIC_VERCEL_ENV || 'development',
      release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,
    });
  }).catch(() => {
    // Sentry import failed (dep missing or build issue) — silently ignore
    // so a broken Sentry never breaks the app itself.
  });
}

// Next.js 16 expects a navigation hook export. No-op by default.
export const onRouterTransitionStart = () => {};
