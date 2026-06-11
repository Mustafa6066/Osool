'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Crown, Download, FileText, Loader2, Sparkles } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { BillingStatus, getBillingStatus } from '@/lib/api';

const REPORT_STATUS_COPY: Record<string, { en: string; ar: string }> = {
  pending: { en: 'Awaiting payment', ar: 'في انتظار الدفع' },
  paid: { en: 'Queued', ar: 'في قائمة الانتظار' },
  generating: { en: 'Generating…', ar: 'جارٍ الإنشاء…' },
  delivered: { en: 'Ready', ar: 'جاهز' },
  failed: { en: 'Failed — contact support', ar: 'فشل — تواصل مع الدعم' },
};

// Dashboard card: current plan, renewal date, and purchased reports.
export default function SubscriptionCard() {
  const router = useRouter();
  const { language, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getBillingStatus()
      .then((s) => !cancelled && setStatus(s))
      .catch(() => undefined)
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-500" />
      </div>
    );
  }
  if (!status) return null;

  const isPro = status.tier === 'premium' || status.tier === 'admin';
  const periodEnd = status.subscription?.current_period_end
    ? new Date(status.subscription.current_period_end).toLocaleDateString(
        isRTL ? 'ar-EG' : 'en-US',
        { year: 'numeric', month: 'long', day: 'numeric' },
      )
    : null;

  return (
    <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6" dir={direction}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl ${
              isPro ? 'bg-emerald-500 text-white' : 'bg-[var(--color-background)] text-emerald-500'
            }`}
          >
            {isPro ? <Crown className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
          </div>
          <div>
            <h3 className="font-semibold text-[var(--color-text-primary)]">
              {isPro
                ? isRTL ? 'أصول برو' : 'Osool Pro'
                : isRTL ? 'الباقة المجانية' : 'Free plan'}
            </h3>
            <p className="text-xs text-[var(--color-text-secondary)]">
              {isPro && periodEnd
                ? isRTL
                  ? `صالح حتى ${periodEnd}`
                  : `Active until ${periodEnd}`
                : isRTL
                  ? '٣ فحوصات يوميًا'
                  : '3 Reality Checks per day'}
            </p>
          </div>
        </div>
        {!isPro && (
          <button
            onClick={() => router.push('/pricing?source=dashboard')}
            className="shrink-0 rounded-2xl bg-emerald-500 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-emerald-600"
          >
            {isRTL ? 'ترقية' : 'Upgrade'}
          </button>
        )}
      </div>

      {status.reports.length > 0 && (
        <div className="mt-5 border-t border-[var(--color-border)] pt-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            {isRTL ? 'تقاريرك' : 'Your reports'}
          </h4>
          <ul className="mt-3 space-y-2">
            {status.reports.map((report) => {
              const copy = REPORT_STATUS_COPY[report.status] ?? REPORT_STATUS_COPY.pending;
              return (
                <li
                  key={report.id}
                  className="flex items-center justify-between gap-3 rounded-2xl bg-[var(--color-background)] px-4 py-3"
                >
                  <div className="flex min-w-0 items-center gap-2.5">
                    <FileText className="h-4 w-4 shrink-0 text-emerald-500" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-[var(--color-text-primary)]">
                        {isRTL ? 'تقرير التقييم الذكي' : 'AI Valuation Report'}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">{copy[language]}</p>
                    </div>
                  </div>
                  {report.status === 'delivered' && (
                    <button
                      onClick={() => router.push(`/reports/${report.id}`)}
                      className="inline-flex shrink-0 items-center gap-1.5 rounded-xl border border-emerald-500/40 px-3 py-1.5 text-xs font-semibold text-emerald-600 transition hover:bg-emerald-500/10"
                    >
                      <Download className="h-3.5 w-3.5" />
                      {isRTL ? 'عرض' : 'View'}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
