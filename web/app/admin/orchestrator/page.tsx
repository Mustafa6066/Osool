'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AlertTriangle,
  ArrowLeft,
  ExternalLink,
  Loader2,
  RefreshCw,
  Workflow,
} from 'lucide-react';
import { checkAdmin } from '@/lib/api';

const ORCHESTRATOR_ADMIN_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL ||
  process.env.NEXT_PUBLIC_ADMIN_URL ||
  ''
).replace(/\/$/, '');

export default function OrchestratorConsolePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [iframeKey, setIframeKey] = useState(0);

  useEffect(() => {
    let mounted = true;

    checkAdmin()
      .then(() => {
        if (mounted) setIsAdmin(true);
      })
      .catch(() => {
        if (mounted) setIsAdmin(false);
      })
      .finally(() => {
        if (mounted) setChecking(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] flex items-center justify-center px-4">
        <div className="max-w-lg w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center">
          <AlertTriangle className="w-10 h-10 mx-auto text-amber-500 mb-4" />
          <h1 className="text-xl font-semibold mb-2">Admin access required</h1>
          <p className="text-sm text-[var(--color-text-muted)] mb-5">
            This route is restricted to authorized administrators.
          </p>
          <button
            onClick={() => router.push('/admin')}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-text-primary)] text-[var(--color-background)] text-sm font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to admin
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-6">
          <div className="flex items-start gap-3">
            <button
              onClick={() => router.push('/admin')}
              className="mt-1 p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-400 mb-3">
                <Workflow className="w-3.5 h-3.5" />
                Orchestrator bridge
              </div>
              <h1 className="text-2xl font-bold">Orchestrator Console</h1>
              <p className="text-sm text-[var(--color-text-muted)] mt-1 max-w-2xl">
                Open the orchestrator admin from inside the main Osool frontend. If the embedded view is blocked by browser or server policy, use the direct link.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIframeKey((current) => current + 1)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-emerald-500/40 transition-colors text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh embed
            </button>
            {ORCHESTRATOR_ADMIN_URL && (
              <a
                href={ORCHESTRATOR_ADMIN_URL}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-colors text-sm font-medium"
              >
                <ExternalLink className="w-4 h-4" />
                Open direct
              </a>
            )}
          </div>
        </div>

        {!ORCHESTRATOR_ADMIN_URL ? (
          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
              <div>
                <h2 className="text-lg font-semibold mb-2">Missing orchestrator admin URL</h2>
                <p className="text-sm text-[var(--color-text-muted)] mb-3">
                  Set NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL, or reuse NEXT_PUBLIC_ADMIN_URL, in the frontend deployment to your orchestrator admin app URL.
                </p>
                <code className="block rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] px-4 py-3 text-sm overflow-x-auto">
                  NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL=https://your-orchestrator-admin-domain
                </code>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)]">
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
              <div>
                <p className="text-sm font-medium">Embedded console</p>
                <p className="text-xs text-[var(--color-text-muted)]">Sign in with your orchestrator admin credentials if prompted.</p>
              </div>
              <span className="text-xs text-[var(--color-text-muted)]">{ORCHESTRATOR_ADMIN_URL}</span>
            </div>

            <iframe
              key={iframeKey}
              src={ORCHESTRATOR_ADMIN_URL}
              title="Osool Orchestrator Console"
              className="w-full h-[calc(100vh-240px)] min-h-[720px] bg-white"
            />
          </div>
        )}
      </div>
    </div>
  );
}