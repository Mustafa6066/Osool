'use client';

import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, Shield, ShieldAlert, Sparkles } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { checkAdmin } from '@/lib/api';

interface AdminShellProps {
  eyebrow?: string;
  title: string;
  subtitle: string;
  actions?: ReactNode;
  children: ReactNode;
}

export default function AdminShell({
  eyebrow = 'Admin workspace',
  title,
  subtitle,
  actions,
  children,
}: AdminShellProps) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const [checkingAdmin, setCheckingAdmin] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isAuthenticated) {
      router.replace('/login?next=/admin');
      return;
    }

    let active = true;

    checkAdmin()
      .then(() => {
        if (active) {
          setIsAdmin(true);
        }
      })
      .catch(() => {
        if (active) {
          setIsAdmin(false);
        }
      })
      .finally(() => {
        if (active) {
          setCheckingAdmin(false);
        }
      });

    return () => {
      active = false;
    };
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || checkingAdmin) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      </AppShell>
    );
  }

  if (!isAdmin) {
    return (
      <AppShell>
        <main className="flex h-full items-center justify-center bg-[var(--color-background)] px-4">
          <div className="w-full max-w-xl rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center shadow-[0_30px_90px_rgba(0,0,0,0.04)]">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-red-500">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <h1 className="mt-5 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Admin access required</h1>
            <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
              This workspace is restricted to authorized administrators. Return to the main workspace if you do not have admin permissions.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to workspace
              </button>
            </div>
          </div>
        </main>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] pb-20 md:pb-0">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-start">
            <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                <Shield className="h-3.5 w-3.5" />
                {eyebrow}
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">{title}</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">{subtitle}</p>
            </div>

            <div className="flex flex-wrap items-center gap-3 lg:justify-end">
              {actions}
              <button
                onClick={() => router.push('/admin')}
                className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
              >
                <Sparkles className="h-4 w-4" />
                Admin home
              </button>
            </div>
          </section>

          {children}
        </div>
      </main>
    </AppShell>
  );
}