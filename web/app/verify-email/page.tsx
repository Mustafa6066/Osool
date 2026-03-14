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
import PublicPageNav from '@/components/PublicPageNav';
import { useLanguage } from '@/contexts/LanguageContext';
import api from '@/lib/api';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const { language } = useLanguage();
  const token = searchParams.get('token');
  const verifiedRef = useRef(false);

  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'no-token'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('no-token');
      setMessage(
        language === 'ar'
          ? 'رابط التحقق غير صالح أو ناقص. استخدم الرابط الأصلي من البريد الإلكتروني.'
          : 'The verification link is missing or invalid. Use the original link from your email.'
      );
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
              ? 'تم تأكيد بريدك بنجاح. يمكنك الآن المتابعة داخل مساحة العمل أو العودة للاستكشاف.'
              : 'Your email is verified. You can continue into the workspace or go back to exploration.'
          );
          return;
        }

        setStatus('error');
        setMessage(response.data.message || (language === 'ar' ? 'تعذر التحقق من البريد.' : 'Email verification could not be completed.'));
      } catch (error: any) {
        setStatus('error');
        const detail = error?.response?.data?.detail;
        setMessage(
          detail ||
            (language === 'ar'
              ? 'انتهت صلاحية رابط التحقق أو لم يعد صالحًا. اطلب رابطًا جديدًا من إعدادات الحساب.'
              : 'The verification link expired or is no longer valid. Request a new link from account settings.')
        );
      }
    };

    void verify();
  }, [language, token]);

  const title = useMemo(() => {
    if (language === 'ar') {
      switch (status) {
        case 'loading':
          return 'جارٍ التحقق من البريد';
        case 'success':
          return 'تم التحقق من البريد';
        case 'error':
          return 'تعذر التحقق';
        default:
          return 'الرابط غير صالح';
      }
    }

    switch (status) {
      case 'loading':
        return 'Verifying your email';
      case 'success':
        return 'Email verified';
      case 'error':
        return 'Verification failed';
      default:
        return 'Invalid link';
    }
  }, [language, status]);

  const tone = useMemo(() => {
    switch (status) {
      case 'success':
        return 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300';
      case 'error':
        return 'border-red-500/20 bg-red-500/10 text-red-500';
      case 'no-token':
        return 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300';
      default:
        return 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)]';
    }
  }, [status]);

  const icon = useMemo(() => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-10 w-10" />;
      case 'error':
      case 'no-token':
        return <ShieldAlert className="h-10 w-10" />;
      default:
        return <Loader2 className="h-10 w-10 animate-spin" />;
    }
  }, [status]);

  return (
    <PublicPageNav>
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

              <p className="mt-6 text-base leading-7 text-[var(--color-text-secondary)]">{message}</p>

              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                {status === 'success' ? (
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
                    ? 'إذا فشل الرابط، اطلب رسالة جديدة من رحلة تسجيل الدخول أو من إعدادات الحساب بعد تسجيل الدخول.'
                    : 'If the link fails, request a fresh email from the sign-in flow or from account settings after login.'}
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </PublicPageNav>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <PublicPageNav>
          <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-[var(--color-background)]">
            <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
          </main>
        </PublicPageNav>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
