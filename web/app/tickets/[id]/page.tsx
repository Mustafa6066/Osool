'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  Loader2,
  Lock,
  MessageSquare,
  Send,
  Shield,
  User,
  XCircle,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { addTicketReply, getTicketDetail, type TicketDetail } from '@/lib/api';

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

export default function TicketDetailPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();
  const params = useParams();
  const rawId = params.id;
  const ticketId = Number(Array.isArray(rawId) ? rawId[0] : rawId);

  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  useEffect(() => {
    const loadTicket = async () => {
      if (!isAuthenticated || !ticketId) {
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const detail = await getTicketDetail(ticketId);
        setTicket(detail);
      } catch (loadError) {
        console.error(loadError);
        setError(t('ticketDetail.loadFailed'));
      } finally {
        setLoading(false);
      }
    };

    void loadTicket();
  }, [isAuthenticated, ticketId]);

  const handleSendReply = async () => {
    if (!ticket || !replyContent.trim() || sending || ticket.status === 'closed') {
      return;
    }

    setSending(true);
    try {
      const reply = await addTicketReply(ticketId, replyContent.trim());
      setTicket({ ...ticket, replies: [...ticket.replies, reply] });
      setReplyContent('');
      setTimeout(() => threadEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 120);
    } catch (sendError) {
      console.error(sendError);
      setError(t('ticketDetail.sendFailed'));
    } finally {
      setSending(false);
    }
  };

  const timelineLabel = useMemo(() => {
    if (!ticket?.created_at) {
      return t('ticketDetail.noTimestamp');
    }
    return new Date(ticket.created_at).toLocaleString();
  }, [ticket?.created_at]);

  if (authLoading || loading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      </AppShell>
    );
  }

  if (!ticket) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center px-4">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
            <div className="text-xl font-semibold text-[var(--color-text-primary)]">{error || t('ticketDetail.notFound')}</div>
            <div className="mt-3">
              <Link href="/tickets" className="text-sm font-medium text-emerald-600 dark:text-emerald-300">
                {t('ticketDetail.returnLink')}
              </Link>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[0.94fr_1.06fr]">
            <div className="space-y-6">
              <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
                <Link href="/tickets" className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">
                  <ArrowLeft className="h-4 w-4" />
                  {t('ticketDetail.back')}
                </Link>
                <div className="mt-6 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${getStatusTone(ticket.status)}`}>
                    {STATUS_KEYS[ticket.status] ? t(STATUS_KEYS[ticket.status]) : ticket.status}
                  </span>
                  <span className={`text-sm font-semibold ${getPriorityTone(ticket.priority)}`}>
                    {PRIORITY_KEYS[ticket.priority] ? t(PRIORITY_KEYS[ticket.priority]) : ticket.priority} {t('ticketDetail.prioritySuffix')}
                  </span>
                </div>
                <h1 className="mt-5 text-3xl font-semibold tracking-tight sm:text-4xl">{ticket.subject}</h1>
                <p className="mt-4 text-base leading-7 text-[var(--color-text-secondary)]">
                  {t('ticketDetail.subtitle')}
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketDetail.statsCategory')}</div>
                  <div className="mt-2 text-lg font-semibold text-[var(--color-text-primary)]">{CATEGORY_KEYS[ticket.category] ? t(CATEGORY_KEYS[ticket.category]) : ticket.category}</div>
                </div>
                <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketDetail.statsOpened')}</div>
                  <div className="mt-2 text-lg font-semibold text-[var(--color-text-primary)]">{timelineLabel}</div>
                </div>
                <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketDetail.statsReplies')}</div>
                  <div className="mt-2 text-lg font-semibold text-[var(--color-text-primary)]">{ticket.replies.length}</div>
                </div>
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketDetail.rulesLabel')}</div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>{t('ticketDetail.rule1')}</p>
                  <p>{t('ticketDetail.rule2')}</p>
                  <p>{t('ticketDetail.rule3')}</p>
                </div>
              </div>
            </div>

            <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:p-8">
              {error && (
                <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-500">
                  {error}
                </div>
              )}

              <div className="border-b border-[var(--color-border)] pb-5">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketDetail.conversationLabel')}</div>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('ticketDetail.conversationTitle')}</h2>
              </div>

              <div className="mt-6 space-y-4">
                <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/10">
                      <User className="h-4 w-4 text-blue-500" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">{t('ticketDetail.authorYou')}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{timelineLabel}</div>
                    </div>
                  </div>
                  <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-[var(--color-text-secondary)]">{ticket.description}</p>
                </div>

                {ticket.replies.map((reply) => (
                  <div
                    key={reply.id}
                    className={`rounded-[28px] border p-5 ${reply.is_admin_reply ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-[var(--color-border)] bg-[var(--color-background)]'}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`flex h-9 w-9 items-center justify-center rounded-full ${reply.is_admin_reply ? 'bg-emerald-500/10' : 'bg-blue-500/10'}`}>
                        {reply.is_admin_reply ? <Shield className="h-4 w-4 text-emerald-500" /> : <User className="h-4 w-4 text-blue-500" />}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                          {reply.user_name}
                          {reply.is_admin_reply && <span className="ml-2 text-xs font-medium text-emerald-600 dark:text-emerald-300">{t('ticketDetail.authorSupport')}</span>}
                        </div>
                        <div className="text-xs text-[var(--color-text-muted)]">
                          {reply.created_at ? new Date(reply.created_at).toLocaleString() : t('ticketDetail.noTimestamp')}
                        </div>
                      </div>
                    </div>
                    <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-[var(--color-text-secondary)]">{reply.content}</p>
                  </div>
                ))}
                <div ref={threadEndRef} />
              </div>

              <div className="mt-8 border-t border-[var(--color-border)] pt-6">
                {ticket.status === 'closed' ? (
                  <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-5 text-sm text-[var(--color-text-secondary)]">
                    <div className="flex items-center gap-2 font-semibold text-[var(--color-text-primary)]">
                      <Lock className="h-4 w-4" />
                      {t('ticketDetail.closedLabel')}
                    </div>
                    <p className="mt-2 leading-6">{t('ticketDetail.closedDescription')}</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-primary)]">{t('ticketDetail.replyLabel')}</label>
                      <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{t('ticketDetail.replyHint')}</p>
                    </div>
                    <textarea
                      value={replyContent}
                      onChange={(event) => setReplyContent(event.target.value)}
                      rows={5}
                      placeholder={t('ticketDetail.replyPlaceholder')}
                      className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none transition-colors focus-visible:border-[var(--color-primary)]/40 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/20"
                    />
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="inline-flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                        <MessageSquare className="h-4 w-4" />
                        {t('ticketDetail.replyGuidance')}
                      </div>
                      <button
                        type="button"
                        onClick={handleSendReply}
                        disabled={!replyContent.trim() || sending}
                        className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        {t('ticketDetail.replySubmit')}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
