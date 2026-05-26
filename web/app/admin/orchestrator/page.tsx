'use client';

import { useMemo, useState } from 'react';
import { AlertTriangle, ExternalLink, RefreshCw, Workflow } from 'lucide-react';
import AdminShell from '@/components/AdminShell';

const ORCHESTRATOR_ADMIN_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL ||
  process.env.NEXT_PUBLIC_ADMIN_URL ||
  ''
).replace(/\/$/, '');

export default function OrchestratorConsolePage() {
  const [iframeKey, setIframeKey] = useState(0);

  const actions = useMemo(() => {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => setIframeKey((current) => current + 1)}
          className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh embed
        </button>
        {ORCHESTRATOR_ADMIN_URL ? (
          <a
            href={ORCHESTRATOR_ADMIN_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
          >
            <ExternalLink className="h-4 w-4" />
            Open direct
          </a>
        ) : null}
      </div>
    );
  }, []);

  return (
    <AdminShell
      eyebrow="Admin orchestrator"
      title="Operate the orchestrator console without leaving the main admin workspace."
      subtitle="Use the embedded bridge when it loads cleanly, or jump directly into the standalone admin if browser or server framing rules block the iframe."
      actions={actions}
    >
      {!ORCHESTRATOR_ADMIN_URL ? (
        <div className="rounded-[32px] border border-amber-500/20 bg-amber-500/10 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-500" />
            <div>
              <h2 className="text-xl font-semibold text-[var(--color-text-primary)]">Missing orchestrator admin URL</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                Set NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL, or reuse NEXT_PUBLIC_ADMIN_URL, in the frontend deployment so this route knows where to load the orchestrator admin.
              </p>
              <code className="mt-4 block overflow-x-auto rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-sm text-[var(--color-text-primary)]">
                NEXT_PUBLIC_ORCHESTRATOR_ADMIN_URL=https://your-orchestrator-admin-domain
              </code>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <section className="grid gap-4 sm:grid-cols-3">
            <InfoCard title="Bridge mode" text="Use the iframe for quick checks when browser policy permits embedding." />
            <InfoCard title="Direct mode" text="Use the direct link for full-screen work, separate auth, or browser policy conflicts." />
            <InfoCard title="Refresh behavior" text="Use refresh embed after admin sign-in or when the console becomes stale." />
          </section>

          <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <div className="flex flex-col gap-3 border-b border-[var(--color-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                  <Workflow className="h-4 w-4" />
                  Embedded console
                </div>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Orchestrator admin iframe</h2>
              </div>
              <div className="text-sm text-[var(--color-text-secondary)]">{ORCHESTRATOR_ADMIN_URL}</div>
            </div>

            <div className="mt-6 overflow-hidden rounded-[28px] border border-[var(--color-border)] bg-white">
              <iframe
                key={iframeKey}
                src={ORCHESTRATOR_ADMIN_URL}
                title="Osool Orchestrator Console"
                className="h-[calc(100vh-320px)] min-h-[720px] w-full bg-white"
              />
            </div>
          </section>
        </div>
      )}
    </AdminShell>
  );
}

function InfoCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="text-sm font-semibold text-[var(--color-text-primary)]">{title}</div>
      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{text}</div>
    </div>
  );
}
