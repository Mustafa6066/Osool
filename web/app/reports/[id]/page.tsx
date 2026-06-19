'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Loader2, Printer } from 'lucide-react';
import { downloadBillingReport, ReportContentSection } from '@/lib/api';
import { useLanguage } from '@/contexts/LanguageContext';

// Purchased-report viewer: bilingual, print-optimized (browser print → PDF
// renders Arabic RTL natively, no server-side PDF pipeline needed).
export default function ReportViewerPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { language, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [content, setContent] = useState<{ en: ReportContentSection; ar: ReportContentSection } | null>(null);
  const [deliveredAt, setDeliveredAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    downloadBillingReport(Number(params.id))
      .then((data) => {
        if (cancelled) return;
        setContent(data.content);
        setDeliveredAt(data.delivered_at);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = err?.response?.status;
        setError(
          status === 409
            ? isRTL ? 'التقرير لسه بيتجهز — جرب بعد دقائق.' : 'Report is still being prepared — try again in a few minutes.'
            : isRTL ? 'تعذر تحميل التقرير.' : 'Could not load the report.',
        );
      });
    return () => {
      cancelled = true;
    };
  }, [params.id, isRTL]);

  const section = content ? content[language] ?? content.en : null;
  const BackIcon = isRTL ? ArrowRight : ArrowLeft;

  return (
    <div className="min-h-screen bg-[var(--color-background)]" dir={direction}>
      <header className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3 print:hidden sm:px-6">
        <button
          onClick={() => router.push('/dashboard')}
          className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:text-[var(--color-text-primary)]"
        >
          <BackIcon className="h-4 w-4" />
          {isRTL ? 'لوحة التحكم' : 'Dashboard'}
        </button>
        {section && (
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-2xl bg-[var(--osool-accent)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[var(--osool-accent-dark)]"
          >
            <Printer className="h-4 w-4" />
            {isRTL ? 'طباعة / PDF' : 'Print / PDF'}
          </button>
        )}
      </header>

      <main className="mx-auto max-w-3xl px-6 py-10 print:max-w-none print:px-0 print:py-0">
        {error && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-6 text-center text-sm text-amber-600">
            {error}
          </div>
        )}

        {!error && !section && (
          <div className="flex justify-center py-24">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--osool-accent)]" />
          </div>
        )}

        {section && (
          <article className="space-y-8 text-[var(--color-text-primary)] print:text-black">
            <div className="border-b border-[var(--color-border)] pb-6">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--osool-accent)]">
                {isRTL ? 'تقرير أصول الاستثماري' : 'Osool Investment Report'}
              </p>
              <h1 className="mt-2 text-3xl font-bold">{section.title}</h1>
              {deliveredAt && (
                <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                  {new Date(deliveredAt).toLocaleDateString(isRTL ? 'ar-EG' : 'en-US', {
                    year: 'numeric', month: 'long', day: 'numeric',
                  })}
                </p>
              )}
              <p className="mt-4 text-lg leading-relaxed text-[var(--color-text-secondary)] print:text-black">
                {section.summary}
              </p>
            </div>

            <section>
              <h2 className="text-xl font-semibold">
                {isRTL ? 'نظرة على السوق' : 'Market Overview'}
              </h2>
              <p className="mt-3 whitespace-pre-line leading-relaxed text-[var(--color-text-secondary)] print:text-black">
                {section.market_overview}
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold">
                {isRTL ? 'التوصيات' : 'Recommendations'}
              </h2>
              <div className="mt-4 space-y-4">
                {section.recommendations?.map((rec, i) => (
                  <div
                    key={`${rec.project}-${i}`}
                    className="rounded-2xl border border-[var(--color-border)] p-5 print:break-inside-avoid"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-semibold">{rec.project}</h3>
                      <div className="flex gap-2 text-xs">
                        <span className="rounded-full bg-[var(--osool-accent-soft)] px-2.5 py-1 font-semibold text-[var(--osool-accent)]">
                          ROI: {rec.roi_estimate}
                        </span>
                        <span className="rounded-full bg-[var(--color-background)] px-2.5 py-1 text-[var(--color-text-secondary)] print:border print:border-gray-300">
                          {isRTL ? 'المخاطرة' : 'Risk'}: {rec.risk_level}
                        </span>
                      </div>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--color-text-secondary)] print:text-black">
                      {rec.why}
                    </p>
                    <p className="mt-2 text-xs text-[var(--color-text-muted)]">
                      {isRTL ? 'الأنسب لـ' : 'Best for'}: {rec.best_for}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {section.area_insights?.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold">
                  {isRTL ? 'تحليلات المناطق' : 'Area Insights'}
                </h2>
                <div className="mt-4 space-y-3">
                  {section.area_insights.map((area, i) => (
                    <div key={`${area.area}-${i}`} className="rounded-2xl bg-[var(--color-surface)] p-4 print:border print:border-gray-300">
                      <h3 className="text-sm font-semibold">{area.area}</h3>
                      <p className="mt-1 text-sm text-[var(--color-text-secondary)] print:text-black">{area.trend}</p>
                      <p className="mt-1 text-xs text-[var(--color-text-muted)]">{area.outlook}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="rounded-2xl border border-[var(--osool-accent-mid)] bg-[var(--osool-accent-soft)] p-5 print:break-inside-avoid">
              <h2 className="text-xl font-semibold">
                {isRTL ? 'خطة العمل' : 'Action Plan'}
              </h2>
              <p className="mt-3 whitespace-pre-line leading-relaxed text-[var(--color-text-secondary)] print:text-black">
                {section.action_plan}
              </p>
            </section>

            <footer className="border-t border-[var(--color-border)] pt-4 text-center text-xs text-[var(--color-text-muted)]">
              {isRTL
                ? 'هذا التقرير إرشادي وليس نصيحة استثمارية ملزمة. أصول — منصة العقارات الذكية في مصر.'
                : 'This report is advisory and not binding investment advice. Osool — Egypt’s intelligent real estate platform.'}
            </footer>
          </article>
        )}
      </main>
    </div>
  );
}
