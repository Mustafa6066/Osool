'use client';

import { useEffect, useState } from 'react';

type Capability = {
  mode: 'live' | 'fallback';
  message: string | null;
};

type ServiceStatus = {
  operating_mode: 'normal' | 'degraded';
  capabilities: Record<string, Capability>;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const POLL_INTERVAL_MS = 60_000;

export default function ServiceStatusBanner() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/health/service-status`, {
          cache: 'no-store',
        });
        if (!res.ok) return;
        const data: ServiceStatus = await res.json();
        if (!cancelled) setStatus(data);
      } catch {
        // Silent — the banner is best-effort. If status itself is unreachable,
        // a network-level error notification will surface elsewhere.
      }
    };

    fetchStatus();
    const id = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (!status || status.operating_mode === 'normal' || dismissed) return null;

  const messages = Object.values(status.capabilities)
    .filter((c) => c.mode === 'fallback' && c.message)
    .map((c) => c.message as string);

  if (messages.length === 0) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="sticky top-0 z-[150] w-full border-b border-amber-400/40 bg-amber-50 px-4 py-2 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
    >
      <div className="mx-auto flex max-w-6xl items-start justify-between gap-3">
        <div className="flex-1">
          <strong className="font-semibold">Reduced mode:</strong>{' '}
          <span>{messages.join(' ')}</span>
        </div>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss"
          className="shrink-0 rounded px-2 py-0.5 text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-900/40"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
