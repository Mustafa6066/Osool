"use client";

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  ArrowRight,
  CheckCircle2,
  Loader2,
  Mail,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import api from '@/lib/api';

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

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const { language } = useLanguage();
  const token = searchParams.get('token');
  const verifiedRef = useRef(false);

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const missingTokenMessage =
    language === 'ar'
      ? 'Ø±Ø§Ø¨Ø· Ø§Ù„ØªØ­Ù‚Ù‚ ØºÙŠØ± ØµØ§Ù„Ø­ Ø£Ùˆ Ù†Ø§Ù‚Øµ. Ø§Ø³ØªØ®Ø¯Ù… Ø§Ù„Ø±Ø§Ø¨Ø· Ø§Ù„Ø£ØµÙ„ÙŠ Ù…Ù† Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ.'
      : 'The verification link is missing or invalid. Use the original link from your email.';

  useEffect(() => {
    if (!token) {
      return;
    }

    if (verifiedRef.current) {
      return;
    }
    verifiedRef.current = true;

    const verify = async () => {
      try {
        const response = await api.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`);
        if (response.data.status === 'verified') {
          setStatus('success');
          setMessage(
            language === 'ar'
              ? 'ØªÙ… ØªØ£ÙƒÙŠØ¯ Ø¨Ø±ÙŠØ¯Ùƒ Ø¨Ù†Ø¬Ø§Ø­. ÙŠÙ…ÙƒÙ†Ùƒ Ø§Ù„Ø¢Ù† Ø§Ù„Ù…ØªØ§Ø¨Ø¹Ø© Ø¯Ø§Ø®Ù„ Ù…Ø³Ø§Ø­Ø© Ø§Ù„Ø¹Ù…Ù„ Ø£Ùˆ Ø§Ù„Ø¹ÙˆØ¯Ø© Ù„Ù„Ø§Ø³ØªÙƒØ´Ø§Ù.'
              : 'Your email is verified. You can continue into the workspace or go back to exploration.'
          );
          return;
        }

        setStatus('error');
        setMessage(response.data.message || (language === 'ar' ? 'ØªØ¹Ø°Ø± Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø¨Ø±ÙŠØ¯.' : 'Email verification could not be completed.'));
      } catch (error: unknown) {
        setStatus('error');
        setMessage(
          getApiDetail(error,
            (language === 'ar'
              ? 'Ø§Ù†ØªÙ‡Øª ØµÙ„Ø§Ø­ÙŠØ© Ø±Ø§Ø¨Ø· Ø§Ù„ØªØ­Ù‚Ù‚ Ø£Ùˆ Ù„Ù… ÙŠØ¹Ø¯ ØµØ§Ù„Ø­Ù‹Ø§. Ø§Ø·Ù„Ø¨ Ø±Ø§Ø¨Ø·Ù‹Ø§ Ø¬Ø¯ÙŠØ¯Ù‹Ø§ Ù…Ù† Ø¥Ø¹Ø¯Ø§Ø¯Ø§Øª Ø§Ù„Ø­Ø³Ø§Ø¨.'
              : 'The verification link expired or is no longer valid. Request a new link from account settings.')
          )
        );
      }
    };

    void verify();
  }, [language, token]);

  const effectiveStatus = token ? status : 'no-token';
  const displayMessage = effectiveStatus === 'no-token' ? missingTokenMessage : message;

  const title = useMemo(() => {
    if (language === 'ar') {
      switch (effectiveStatus) {
        case 'loading':
          return 'Ø¬Ø§Ø±Ù Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø¨Ø±ÙŠØ¯';
        case 'success':
          return 'ØªÙ… Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø¨Ø±ÙŠØ¯';
        case 'error':
          return 'ØªØ¹Ø°Ø± Ø§Ù„ØªØ­Ù‚Ù‚';
        default:
          return 'Ø§Ù„Ø±Ø§Ø¨Ø· ØºÙŠØ± ØµØ§Ù„Ø­';
      }
    }

    switch (effectiveStatus) {
      case 'loading':
        return 'Verifying your email';
      case 'success':
        return 'Email verified';
      case 'error':
        return 'Verification failed';
      default:
        return 'Invalid link';
    }
  }, [effectiveStatus, language]);

  const tone = useMemo(() => {
    switch (effectiveStatus) {
      case 'success':
        return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300';
      case 'error':
        return 'border-red-500/20 bg-red-500/10 text-red-500';
      case 'no-token':
        return 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300';
      default:
        return 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)]';
    }
  }, [effectiveStatus]);

  const icon = useMemo(() => {
    switch (effectiveStatus) {
      case 'success':
        return <CheckCircle2 className="h-10 w-10" />;
      case 'error':
      case 'no-token':
        return <ShieldAlert className="h-10 w-10" />;
      default:
        return <Loader2 className="h-10 w-10 animate-spin" />;
    }
  }, [effectiveStatus]);

  return (
    <AppShell>
      <main className="bg-[var(--color-background)]">
        <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-7xl flex-col justify-center gap-8 px-4 py-10 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-300">
                <Mail className="h-3.5 w-3.5" />
                Account continuity
              </div>
              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Stay inside the same journey after verification.</h1>
              <p className="max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                Verification should feel like a checkpoint, not a dead end. This page confirms the result and gives you the next best move back into Osool.
              </p>
              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                  <Sparkles className="h-4 w-4" />
                  What happens next
                </div>
                <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  <p>If verification succeeds, move into your workspace and continue where you left off.</p>
                  <p>If the link fails, return to sign-in and request a fresh email from the account flow.</p>
                  <p>If you were still comparing projects or units, you can also jump back into Explore immediately.</p>
                </div>
              </div>
            </div>

            <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
              <div className={`inline-flex items-center gap-3 rounded-full border px-4 py-2 text-sm font-semibold ${tone}`}>
                {icon}
                {title}
              </div>

              <p className="mt-6 text-base leading-7 text-[var(--color-text-secondary)]">{displayMessage}</p>

              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                {effectiveStatus === 'success' ? (
                  <>
                    <Link
                      href="/dashboard"
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                    >
                      Go to workspace
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/explore"
                      className="inline-flex items-center justify-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                    >
                      Continue exploring
                    </Link>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                    >
                      Return to sign in
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/explore"
                      className="inline-flex items-center justify-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                    >
                      Browse public market views
                    </Link>
                  </>
                )}
              </div>

              <div className="mt-8 rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Recovery note</div>
                <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  {language === 'ar'
                    ? 'Ø¥Ø°Ø§ ÙØ´Ù„ Ø§Ù„Ø±Ø§Ø¨Ø·ØŒ Ø§Ø·Ù„Ø¨ Ø±Ø³Ø§Ù„Ø© Ø¬Ø¯ÙŠØ¯Ø© Ù…Ù† Ø±Ø­Ù„Ø© ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„ Ø£Ùˆ Ù…Ù† Ø¥Ø¹Ø¯Ø§Ø¯Ø§Øª Ø§Ù„Ø­Ø³Ø§Ø¨ Ø¨Ø¹Ø¯ ØªØ³Ø¬ÙŠÙ„ Ø§Ù„Ø¯Ø®ÙˆÙ„.'
                    : 'If the link fails, request a fresh email from the sign-in flow or from account settings after login.'}
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-[var(--color-background)]">
            <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
          </main>
        </AppShell>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
