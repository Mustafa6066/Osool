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
import SmartNav from '@/components/SmartNav';
import { useAuth } from '@/contexts/AuthContext';
import { createTicket } from '@/lib/api';

const CATEGORIES = [
  {
    value: 'general',
    label: 'General inquiry',
    description: 'Use this when you need a human follow-up but the issue is not tied to billing, property data, or access.',
  },
  {
    value: 'payment',
    label: 'Payment issue',
    description: 'Use this for failed payments, billing confusion, reservation money, or receipt mismatches.',
  },
  {
    value: 'property',
    label: 'Property issue',
    description: 'Use this for incorrect listing information, missing unit data, or project-level discrepancies.',
  },
  {
    value: 'technical',
    label: 'Technical problem',
    description: 'Use this for broken pages, failed actions, missing states, or recurring product bugs.',
  },
  {
    value: 'account',
    label: 'Account and profile',
    description: 'Use this for login, profile, permissions, or verification continuity issues.',
  },
] as const;

const PRIORITIES = [
  {
    value: 'low',
    label: 'Low',
    description: 'Question or non-blocking issue.',
  },
  {
    value: 'medium',
    label: 'Medium',
    description: 'Important but not stopping progress right now.',
  },
  {
    value: 'high',
    label: 'High',
    description: 'Blocking a workflow or creating a serious mismatch.',
  },
  {
    value: 'urgent',
    label: 'Urgent',
    description: 'Critical and time-sensitive.',
  },
] as const;

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
      setError('Subject must be at least 3 characters.');
      return;
    }

    if (description.trim().length < 10) {
      setError('Description must be at least 10 characters.');
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
    } catch (submitError: any) {
      setError(submitError?.response?.data?.detail || 'Failed to create ticket. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <SmartNav>
        <div className="flex h-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      </SmartNav>
    );
  }

  return (
    <SmartNav>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] pb-20 md:pb-0">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[0.94fr_1.06fr]">
            <div className="space-y-6">
              <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
                <Link href="/tickets" className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors hover:text-[var(--color-text-primary)]">
                  <ArrowLeft className="h-4 w-4" />
                  Back to support inbox
                </Link>
                <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Structured intake
                </div>
                <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">Open a ticket with enough context to get a useful first reply.</h1>
                <p className="mt-4 text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                  This form is for tracked issues that need support ownership. Keep the subject crisp, the description factual, and the issue scoped to one thread.
                </p>
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Before you submit</div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>Include the exact page, property, developer, project, or payment step involved.</p>
                  <p>Write what you expected to happen and what actually happened.</p>
                  <p>If there is a transaction or timing issue, include the relevant timestamp or reference.</p>
                </div>
                <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                  <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                    <Sparkles className="h-4 w-4 text-emerald-500" />
                    Current routing
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                    Category: {selectedCategory.label}. Priority: {selectedPriority.label}. You can adjust both before submitting.
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
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">Subject</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Write the blocker in one line.</p>
                  <input
                    type="text"
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                    maxLength={200}
                    placeholder="Example: Payment confirmation failed after reservation step"
                    className="mt-3 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none transition-colors focus:border-emerald-500/40"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-primary)]">Category</label>
                      <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Choose the lane that best matches the issue.</p>
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
                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">{item.label}</div>
                        <div className="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">{item.description}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">Priority</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Set urgency based on real impact, not preference.</p>
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
                        <div className="text-sm font-semibold">{item.label}</div>
                        <div className="mt-2 text-xs leading-5 opacity-90">{item.description}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--color-text-primary)]">Description</label>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">Add the facts support needs to move the issue forward.</p>
                  <textarea
                    value={description}
                    onChange={(event) => setDescription(event.target.value)}
                    rows={10}
                    maxLength={5000}
                    placeholder="Describe the issue, where it happened, what you expected, what happened instead, and any IDs or timing details that matter."
                    className="mt-3 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none transition-colors focus:border-emerald-500/40"
                  />
                  <div className="mt-2 text-right text-xs text-[var(--color-text-muted)]">{description.length}/5000</div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-border)] pt-6">
                  <Link
                    href="/tickets"
                    className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                  >
                    Cancel
                  </Link>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    Submit ticket
                    {!submitting && <ArrowRight className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </form>
          </section>
        </div>
      </main>
    </SmartNav>
  );
}
