'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Filter,
  LifeBuoy,
  Loader2,
  MessageSquare,
  Plus,
  Sparkles,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getMyTickets, type Ticket } from '@/lib/api';

const STATUS_KEYS: Record<string, string> = {
  open: 'tickets.statusOpen',
  in_progress: 'tickets.statusInProgress',
  resolved: 'tickets.statusResolved',
  closed: 'tickets.statusClosed',
};

const CATEGORY_KEYS: Record<string, string> = {
  general: 'tickets.categoryGeneral',
  payment: 'tickets.categoryPayment',
  property: 'tickets.categoryProperty',
  technical: 'tickets.categoryTechnical',
  account: 'tickets.categoryAccount',
};

const PRIORITY_KEYS: Record<string, string> = {
  low: 'tickets.priorityLow',
  medium: 'tickets.priorityMedium',
  high: 'tickets.priorityHigh',
  urgent: 'tickets.priorityUrgent',
};

function getStatusTone(status: string): string {
  switch (status) {
    case 'open':
      return 'border-blue-500/20 bg-blue-500/10 text-blue-600 dark:text-blue-300';
    case 'in_progress':
      return 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300';
    case 'resolved':
      return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300';
    case 'closed':
      return 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-muted)]';
    default:
      return 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)]';
  }
}

function getPriorityTone(priority: string): string {
  switch (priority) {
    case 'urgent':
      return 'text-red-500';
    case 'high':
      return 'text-orange-500';
    case 'medium':
      return 'text-blue-500';
    default:
      return 'text-[var(--color-text-muted)]';
  }
}

export default function TicketsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();

  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  const loadTickets = useCallback(async () => {
    if (!isAuthenticated) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await getMyTickets(statusFilter);
      setTickets(result.tickets);
      setTotal(result.total);
    } catch (loadError) {
      console.error(loadError);
      setError('Support inbox is unavailable right now.');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, statusFilter]);

  useEffect(() => {
    void loadTickets();
  }, [loadTickets]);

  const counts = useMemo(() => {
    const base = { open: 0, in_progress: 0, resolved: 0, closed: 0 };
    for (const ticket of tickets) {
      if (ticket.status in base) {
        base[ticket.status as keyof typeof base] += 1;
      }
    }
    return base;
  }, [tickets]);

  if (authLoading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      </AppShell>
    );
  }

  const statusFilters = [
    { key: undefined, label: t('tickets.filterAll') },
    { key: 'open', label: t('tickets.statusOpen') },
    { key: 'in_progress', label: t('tickets.statusInProgress') },
    { key: 'resolved', label: t('tickets.statusResolved') },
    { key: 'closed', label: t('tickets.statusClosed') },
  ];

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[1fr_0.92fr]">
            <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                <LifeBuoy className="h-3.5 w-3.5" />
                {t('tickets.badge')}
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">{t('tickets.title')}</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                {t('tickets.subtitle')}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/tickets/new"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                >
                  <Plus className="h-4 w-4" />
                  {t('tickets.openNew')}
                </Link>
                <Link
                  href="/chat?prompt=I need help deciding whether this issue should go to support or be solved through advisor guidance.&autostart=1"
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                >
                  <Sparkles className="h-4 w-4" />
                  {t('tickets.askAdvisor')}
                </Link>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-2">
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statsView')}</div>
                <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : total.toLocaleString('en-EG')}</div>
                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{t('tickets.statsViewDesc')}</div>
              </div>
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statsAttention')}</div>
                <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : (counts.open + counts.in_progress).toLocaleString('en-EG')}</div>
                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{t('tickets.statsAttentionDesc')}</div>
              </div>
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sm:col-span-2">
                <div className="grid gap-3 sm:grid-cols-4">
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statusOpen')}</div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : counts.open}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statusInProgress')}</div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : counts.in_progress}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statusResolved')}</div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : counts.resolved}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.statusClosed')}</div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{loading ? 'â€¦' : counts.closed}</div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1fr_0.82fr]">
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="flex flex-col gap-4 border-b border-[var(--color-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('tickets.inboxTitle')}</div>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('tickets.inboxSubtitle')}</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {statusFilters.map((filter) => (
                    <button
                      key={filter.key || 'all'}
                      onClick={() => setStatusFilter(filter.key)}
                      className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${
                        statusFilter === filter.key
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                          : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                      }`}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {loading ? (
                  <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
                  </div>
                ) : error ? (
                  <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-5 text-sm text-red-500">
                    {error}
                  </div>
                ) : tickets.length === 0 ? (
                  <div className="rounded-[28px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] px-6 py-14 text-center">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10">
                      <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                    </div>
                    <h3 className="mt-5 text-xl font-semibold text-[var(--color-text-primary)]">
                      {statusFilter ? t('tickets.emptyFiltered') : t('tickets.emptyTitle')}
                    </h3>
                    <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-[var(--color-text-secondary)]">
                      {statusFilter
                        ? t('tickets.emptyFilteredSuggestion')
                        : t('tickets.emptyDescription')}
                    </p>
                    <div className="mt-6 flex flex-wrap justify-center gap-3">
                      <Link
                        href="/chat"
                        className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                      >
                        <Sparkles className="h-4 w-4" />
                        {t('tickets.askAdvisor')}
                      </Link>
                      <Link
                        href="/tickets/new"
                        className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                      >
                        <Plus className="h-4 w-4" />
                        {t('tickets.createTicket')}
                      </Link>
                    </div>
                  </div>
                ) : (
                  tickets.map((ticket) => (
                    <Link key={ticket.id} href={`/tickets/${ticket.id}`} className="block rounded-[24px] border border-[var(--color-border)] bg-[var(--color-background)] p-5 transition-colors hover:border-emerald-500/30 hover:bg-emerald-500/5">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${getStatusTone(ticket.status)}`}>
                              {t(STATUS_KEYS[ticket.status]) || ticket.status}
                            </span>
                            <span className={`text-xs font-semibold ${getPriorityTone(ticket.priority)}`}>
                              {t(PRIORITY_KEYS[ticket.priority]) || ticket.priority}
                            </span>
                            <span className="text-xs text-[var(--color-text-muted)]">
                              {t(CATEGORY_KEYS[ticket.category]) || ticket.category}
                            </span>
                          </div>
                          <h3 className="mt-3 text-lg font-semibold text-[var(--color-text-primary)]">{ticket.subject}</h3>
                          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
                            <span>#{ticket.id}</span>
                            <span>{ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : 'No date'}</span>
                            <span>{ticket.replies_count} {t('tickets.replies')}</span>
                            {ticket.updated_at && <span>Updated {new Date(ticket.updated_at).toLocaleDateString()}</span>}
                          </div>
                        </div>
                        <div className="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 dark:text-emerald-300">
                          Open thread
                          <ArrowRight className="h-4 w-4" />
                        </div>
                      </div>
                    </Link>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                  <Filter className="h-4 w-4" />
                  {t('tickets.routingLabel')}
                </div>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight">{t('tickets.routingTitle')}</h2>
                <div className="mt-5 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>{t('tickets.routingAdvisor')}</p>
                  <p>{t('tickets.routingSupport')}</p>
                  <p>{t('tickets.routingBestPractice')}</p>
                </div>
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-emerald-500/10 p-6">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                  <Clock3 className="h-4 w-4" />
                  {t('tickets.triageLabel')}
                </div>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">{t('tickets.triageTitle')}</h2>
                <div className="mt-5 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>{t('tickets.triageStep1')}</p>
                  <p>{t('tickets.triageStep2')}</p>
                  <p>{t('tickets.triageStep3')}</p>
                </div>
                <div className="mt-6">
                  <Link
                    href="/tickets/new"
                    className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                  >
                    {t('tickets.triageStart')}
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <AlertCircle className="h-5 w-5 text-blue-500" />
                    <div className="mt-3 text-sm font-semibold text-[var(--color-text-primary)]">{t('tickets.legendOpen')}</div>
                    <div className="mt-1 text-xs text-[var(--color-text-muted)]">{t('tickets.legendOpenDesc')}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <Clock3 className="h-5 w-5 text-amber-500" />
                    <div className="mt-3 text-sm font-semibold text-[var(--color-text-primary)]">{t('tickets.legendInProgress')}</div>
                    <div className="mt-1 text-xs text-[var(--color-text-muted)]">{t('tickets.legendInProgressDesc')}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-4">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                    <div className="mt-3 text-sm font-semibold text-[var(--color-text-primary)]">{t('tickets.legendResolved')}</div>
                    <div className="mt-1 text-xs text-[var(--color-text-muted)]">{t('tickets.legendResolvedDesc')}</div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
