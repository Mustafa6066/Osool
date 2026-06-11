'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, Clock, Crown, Loader2 } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { getBillingStatus } from '@/lib/api';

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 60000;

type Phase = 'confirming' | 'active' | 'pending_report' | 'timeout';

// Paymob redirects here after checkout. The redirect alone proves nothing —
// we poll the billing status until the webhook flips the tier (or a report
// purchase shows up as paid), then celebrate.
export default function BillingSuccessPage() {
  const router = useRouter();
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';
  const [phase, setPhase] = useState<Phase>('confirming');
  const startedAt = useRef(Date.now());

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const status = await getBillingStatus();
        if (cancelled) return;
        if (status.tier === 'premium' || status.tier === 'admin') {
          sessionStorage.removeItem('osool_checkout_iframe');
          setPhase('active');
          return;
        }
        const paidReport = status.reports.find((r) =>
          ['paid', 'generating', 'delivered'].includes(r.status),
        );
        if (paidReport) {
          sessionStorage.removeItem('osool_checkout_iframe');
          setPhase('pending_report');
          return;
        }
      } catch {
        // Keep polling — transient errors are expected right after redirect
      }
      if (Date.now() - startedAt.current > POLL_TIMEOUT_MS) {
        setPhase('timeout');
        return;
      }
      setTimeout(poll, POLL_INTERVAL_MS);
    };

    poll();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div
      className="flex h-screen items-center justify-center bg-[var(--color-background)] px-6"
      dir={direction}
    >
      <div className="w-full max-w-md rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
        {phase === 'confirming' && (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-emerald-500" />
            <h1 className="mt-6 text-xl font-semibold text-[var(--color-text-primary)]">
              {isRTL ? 'جارٍ تأكيد الدفع…' : 'Confirming your payment…'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL
                ? 'ثوانٍ معدودة — بنستنى تأكيد بوابة الدفع.'
                : 'Just a few seconds — waiting for the payment gateway confirmation.'}
            </p>
          </>
        )}

        {phase === 'active' && (
          <>
            <div className="mx-auto inline-flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/15">
              <Crown className="h-8 w-8 text-emerald-500" />
            </div>
            <h1 className="mt-6 text-2xl font-semibold text-[var(--color-text-primary)]">
              {isRTL ? '🎉 أهلاً بك في أصول برو!' : '🎉 Welcome to Osool Pro!'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL
                ? 'اشتراكك مُفعّل. بيانات الصفقات الكاملة والتنبيهات بقت متاحة ليك.'
                : 'Your subscription is active. Full deal data and alerts are now unlocked.'}
            </p>
            <button
              onClick={() => router.push('/chat')}
              className="mt-8 w-full rounded-2xl bg-emerald-500 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
            >
              {isRTL ? 'ابدأ الاستخدام' : 'Start exploring'}
            </button>
          </>
        )}

        {phase === 'pending_report' && (
          <>
            <div className="mx-auto inline-flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/15">
              <CheckCircle2 className="h-8 w-8 text-emerald-500" />
            </div>
            <h1 className="mt-6 text-2xl font-semibold text-[var(--color-text-primary)]">
              {isRTL ? 'تم الدفع — تقريرك بيتجهز' : 'Payment received — your report is being prepared'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL
                ? 'هيوصلك إيميل أول ما يجهز، وهتلاقيه في لوحة التحكم خلال دقائق.'
                : "We'll email you when it's ready — it will appear in your dashboard within minutes."}
            </p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-8 w-full rounded-2xl bg-emerald-500 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
            >
              {isRTL ? 'لوحة التحكم' : 'Go to dashboard'}
            </button>
          </>
        )}

        {phase === 'timeout' && (
          <>
            <div className="mx-auto inline-flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/15">
              <Clock className="h-8 w-8 text-amber-500" />
            </div>
            <h1 className="mt-6 text-xl font-semibold text-[var(--color-text-primary)]">
              {isRTL ? 'التأكيد بياخد وقت أطول من المعتاد' : 'Confirmation is taking longer than usual'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL
                ? 'لو خصم المبلغ، هيتفعل اشتراكك تلقائيًا خلال دقائق. تقدر تتابع من لوحة التحكم أو تتواصل معنا.'
                : 'If you were charged, your purchase will activate automatically within minutes. Check your dashboard or contact support.'}
            </p>
            <div className="mt-8 flex gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="flex-1 rounded-2xl bg-emerald-500 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
              >
                {isRTL ? 'لوحة التحكم' : 'Dashboard'}
              </button>
              <button
                onClick={() => router.push('/contact')}
                className="flex-1 rounded-2xl border border-[var(--color-border)] py-3 text-sm font-semibold text-[var(--color-text-primary)]"
              >
                {isRTL ? 'الدعم' : 'Support'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
