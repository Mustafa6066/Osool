'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Send,
  Sparkles,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { createTicket } from '@/lib/api';

const CATEGORIES = [
  {
    value: 'general',
    labelKey: 'ticketNew.categoryGeneral',
    descKey: 'ticketNew.categoryGeneralDesc',
  },
  {
    value: 'payment',
    labelKey: 'ticketNew.categoryPayment',
    descKey: 'ticketNew.categoryPaymentDesc',
  },
  {
    value: 'property',
    labelKey: 'ticketNew.categoryProperty',
    descKey: 'ticketNew.categoryPropertyDesc',
  },
  {
    value: 'technical',
    labelKey: 'ticketNew.categoryTechnical',
    descKey: 'ticketNew.categoryTechnicalDesc',
  },
  {
    value: 'account',
    labelKey: 'ticketNew.categoryAccount',
    descKey: 'ticketNew.categoryAccountDesc',
  },
] as const;

const PRIORITIES = [
  {
    value: 'low',
    labelKey: 'ticketNew.priorityLow',
    descKey: 'ticketNew.priorityLowDesc',
  },
  {
    value: 'medium',
    labelKey: 'ticketNew.priorityMedium',
    descKey: 'ticketNew.priorityMediumDesc',
  },
  {
    value: 'high',
    labelKey: 'ticketNew.priorityHigh',
    descKey: 'ticketNew.priorityHighDesc',
  },
  {
    value: 'urgent',
    labelKey: 'ticketNew.priorityUrgent',
    descKey: 'ticketNew.priorityUrgentDesc',
  },
] as const;

function getApiDetail(error: unknown, fallback: string): string {
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof error.response === 'object' &&
    error.response !== null &&
    'data' in error.response &&
    typeof error.response.data === 'object' &&
    error.response.data !== null &&
    'detail' in error.response.data &&
    typeof error.response.data.detail === 'string'
  ) {
    return error.response.data.detail;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

function getPriorityTone(priority: string): string {
  switch (priority) {
    case 'urgent':
      return 'border-red-500/30 bg-red-500/10 text-red-500';
    case 'high':
      return 'border-orange-500/30 bg-orange-500/10 text-orange-500';
    case 'medium':
      return 'border-blue-500/30 bg-blue-500/10 text-blue-500';
    default:
      return 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)]';
  }
}

export default function NewTicketPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { t } = useLanguage();
  const router = useRouter();

  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('general');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  const selectedCategory = CATEGORIES.find((item) => item.value === category) || CATEGORIES[0];
  const selectedPriority = PRIORITIES.find((item) => item.value === priority) || PRIORITIES[1];

  const handleSubmit = async (event: { preventDefault: () => void }) => {
    event.preventDefault();
    setError(null);

    if (subject.trim().length < 3) {
      setError(t('ticketNew.errorSubjectShort'));
      return;
    }

    if (description.trim().length < 10) {
      setError(t('ticketNew.errorDescriptionShort'));
      return;
    }

    setSubmitting(true);
    try {
      const ticket = await createTicket({
        subject: subject.trim(),
        description: description.trim(),
        category,
        priority,
      });
      router.push(`/tickets/${ticket.id}`);
    } catch (submitError: unknown) {
      setError(getApiDetail(submitError, t('ticketNew.errorCreateFailed')));
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] pb-20 md:pb-0">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[0.94fr_1.06fr]">
            <div className="space-y-6">
              <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
                <Link href="/tickets" className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">
                  <ArrowLeft className="h-4 w-4" />
                  {t('ticketNew.back')}
                </Link>
                <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {t('ticketNew.badge')}
                </div>
                <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">{t('ticketNew.title')}</h1>
                <p className="mt-4 text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                  {t('ticketNew.subtitle')}
                </p>
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('ticketNew.checklistLabel')}</div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>{t('ticketNew.checklistItem1')}</p>
                  <p>{t('ticketNew.checklistItem2')}</p>
                  <p>{t('ticketNew.checklistItem3')}</p>
                </div>
                <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                    <Sparkles className="h-4 w-4 text-emerald-500" />
                    {t('ticketNew.routingLabel')}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                    {t('ticketNew.formCategory')}: {t(selectedCategory.labelKey)}. {t('ticketNew.formPriority')}: {t(selectedPriority.labelKey)}.
                  </p>
                </div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:p-8">
              <div className="flex flex-col gap-6">
                {error && (
                  <div className="flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-500">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">{t('ticketNew.formSubject')}</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{t('ticketNew.formSubjectHint')}</p>
                  <input
                    type="text"
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                    maxLength={200}
                    placeholder={t('ticketNew.formSubjectPlaceholder')}
                    className="mt-3 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none transition-colors focus:border-emerald-500/40"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-primary)]">{t('ticketNew.formCategory')}</label>
                      <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{t('ticketNew.formCategoryHint')}</p>
                    </div>
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    {CATEGORIES.map((item) => (
                      <button
                        key={item.value}
                        type="button"
                        onClick={() => setCategory(item.value)}
                        className={`rounded-2xl border p-4 text-left transition-colors ${
                          category === item.value
                            ? 'border-emerald-500/30 bg-emerald-500/10'
                            : 'border-[var(--color-border)] bg-[var(--color-background)] hover:border-emerald-500/20'
                        }`}
                      >
                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">{t(item.labelKey)}</div>
                        <div className="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">{t(item.descKey)}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">{t('ticketNew.formPriority')}</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{t('ticketNew.formPriorityHint')}</p>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    {PRIORITIES.map((item) => (
                      <button
                        key={item.value}
                        type="button"
                        onClick={() => setPriority(item.value)}
                        className={`rounded-2xl border p-4 text-left transition-colors ${
                          priority === item.value
                            ? getPriorityTone(item.value)
                            : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:border-emerald-500/20'
                        }`}
                      >
                        <div className="text-sm font-semibold">{t(item.labelKey)}</div>
                        <div className="mt-2 text-xs leading-5 opacity-90">{t(item.descKey)}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">{t('ticketNew.formDescription')}</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">{t('ticketNew.formDescriptionHint')}</p>
                  <textarea
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    rows={10}
                    maxLength={5000}
                    placeholder={t('ticketNew.formDescriptionPlaceholder')}
                    className="mt-3 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none transition-colors focus:border-emerald-500/40"
                  />
                  <div className="mt-2 text-right text-xs text-[var(--color-text-muted)]">{description.length}/5000</div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-border)] pt-6">
                  <Link
                    href="/tickets"
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                  >
                    {t('ticketNew.formCancel')}
                  </Link>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    {t('ticketNew.formSubmit')}
                    {!submitting && <ArrowRight className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </form>
          </section>
        </div>
      </main>
    </AppShell>
  );
}
