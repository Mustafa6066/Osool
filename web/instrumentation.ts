/**
 * Next.js instrumentation — runs once when the server starts.
 * Registers Web Vitals reporting and performance monitoring.
 */

export async function register() {
  // Server-side only instrumentation
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    console.log('[Osool] Server instrumentation registered');
  }
}

/**
 * Report Web Vitals to analytics backend.
 * This function is called by Next.js for every web vital metric.
 */
export function onRequestError(
  error: { digest: string } & Error,
  request: {
    path: string;
    method: string;
    headers: Record<string, string>;
  },
  context: {
    routerKind: 'Pages Router' | 'App Router';
    routePath: string;
    routeType: 'render' | 'route' | 'action' | 'middleware';
    renderSource: 'react-server-components' | 'react-server-components-payload' | 'server-rendering';
    revalidateReason: 'on-demand' | 'stale' | undefined;
    renderType: 'dynamic' | 'dynamic-resume';
  }
) {
  // Log server errors with structured context
  console.error('[Osool] Request error:', {
    digest: error.digest,
    message: error.message,
    path: request.path,
    method: request.method,
    routePath: context.routePath,
    routeType: context.routeType,
    routerKind: context.routerKind,
  });

  // If Sentry is configured, report there
  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    // Dynamic import to avoid loading Sentry when not configured
    import('@sentry/nextjs').then((Sentry) => {
      Sentry.captureException(error, {
        extra: {
          path: request.path,
          routePath: context.routePath,
          routeType: context.routeType,
        },
      });
    }).catch(() => {
      // Sentry not installed — silently ignore
    });
  }
}
