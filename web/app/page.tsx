'use client';

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight, Sparkles, ShieldCheck, LineChart, BrainCircuit,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';

const SPRING_UP = { type: 'spring' as const, damping: 28, stiffness: 210 };

const CAPABILITIES = [
  {
    key: 'market-intel',
    icon: LineChart,
    enTitle: 'Market Intelligence',
    arTitle: 'ذكاء السوق',
    enDesc: 'Reads pricing shifts, rental yield movement, and local momentum signals in real-time.',
    arDesc: 'يرصد تغيرات الأسعار وعوائد الإيجار وإشارات الزخم المحلي في الوقت الحقيقي.',
  },
  {
    key: 'risk-audit',
    icon: ShieldCheck,
    enTitle: 'Risk Audit',
    arTitle: 'تدقيق المخاطر',
    enDesc: 'Highlights delivery risk, developer reliability, and downside exposure before commitment.',
    arDesc: 'يكشف مخاطر التسليم وموثوقية المطور والتعرض للهبوط قبل اتخاذ القرار.',
  },
  {
    key: 'decision-agent',
    icon: BrainCircuit,
    enTitle: 'Decision Agent',
    arTitle: 'وكيل القرار',
    enDesc: 'Turns natural language goals into ranked opportunities and next best actions.',
    arDesc: 'يحوّل أهدافك المكتوبة إلى فرص مرتبة وخطوات عملية تالية.',
  },
];

export default function Home() {
  const { language, t } = useLanguage();
  const isAr = language === 'ar';
  const prefersReducedMotion = useReducedMotion();

  return (
    <AppShell>
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-28 left-[20%] h-72 w-72 rounded-full bg-emerald-500/8 blur-[90px]" />
          <div className="absolute top-[30%] right-[12%] h-64 w-64 rounded-full bg-teal-500/8 blur-[90px]" />
        </div>

        {/* Hero */}
        <section className="relative mx-auto max-w-6xl px-4 pt-16 pb-12 sm:px-6 lg:px-10">
          <div className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 28 }}
              animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
              transition={prefersReducedMotion ? { duration: 0 } : SPRING_UP}
              dir={isAr ? 'rtl' : 'ltr'}
            >
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                <Sparkles className="h-3.5 w-3.5" />
                {isAr ? 'محرك قرار استثماري' : 'Investment Decision Engine'}
              </div>

              <h1 className="mt-6 text-4xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl leading-[1.05]">
                {isAr
                  ? (
                    <>
                      قرارات استثمار عقاري
                      <br />
                      أوضح وأهدأ
                    </>
                  )
                  : (
                    <>
                      Confident Real Estate Decisions
                      <br />
                      With Less Noise
                    </>
                  )}
              </h1>

              <p className="mt-5 max-w-xl text-base leading-relaxed text-[var(--color-text-secondary)] sm:text-lg">
                {isAr
                  ? 'أصول يحوّل بيانات السوق المعقدة إلى توصية عملية: ماذا تشتري، لماذا، وما مستوى المخاطرة.'
                  : 'Osool turns complex market data into an actionable recommendation: what to buy, why, and with which risk level.'}
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link
                  href="/chat"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-6 py-3 text-sm font-semibold text-[var(--color-background)] transition-transform hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/35"
                >
                  <Sparkles className="h-4 w-4" />
                  {t('landing.ctaStart')}
                </Link>
                <Link
                  href="/explore"
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3 text-sm font-semibold text-[var(--color-text-primary)] transition-colors hover:bg-[var(--color-surface-elevated)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/35"
                >
                  {t('landing.ctaExplore')}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </motion.div>

            {/* AI visual panel */}
            <motion.div
              initial={prefersReducedMotion ? false : { opacity: 0, y: 28 }}
              animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
              transition={prefersReducedMotion ? { duration: 0 } : { ...SPRING_UP, delay: 0.1 }}
              className="relative"
            >
              <div className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-[0_16px_40px_rgba(0,0,0,0.08)]">
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {isAr ? 'ملخص ثقة القرار' : 'Decision Confidence Summary'}
                  </div>
                  <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                </div>

                <div className="space-y-3">
                  <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--color-text-muted)]">
                      {isAr ? 'يعتمد التقييم على' : 'Assessment Inputs'}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                      <span className="rounded-full border border-[var(--color-border)] px-2.5 py-1 text-[var(--color-text-secondary)]">{isAr ? 'اتجاه السعر' : 'Price Trend'}</span>
                      <span className="rounded-full border border-[var(--color-border)] px-2.5 py-1 text-[var(--color-text-secondary)]">{isAr ? 'جودة التسليم' : 'Delivery Reliability'}</span>
                      <span className="rounded-full border border-[var(--color-border)] px-2.5 py-1 text-[var(--color-text-secondary)]">{isAr ? 'مرونة السداد' : 'Payment Flexibility'}</span>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="flex items-center justify-between text-[11px] text-[var(--color-text-muted)]">
                      <span>{isAr ? 'مستوى الثقة الحالي' : 'Current Confidence'}</span>
                      <span className="font-semibold text-emerald-600">94%</span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-emerald-500/15">
                      <motion.div
                        initial={prefersReducedMotion ? false : { scaleX: 0 }}
                        whileInView={prefersReducedMotion ? undefined : { scaleX: 1 }}
                        viewport={{ once: true }}
                        transition={prefersReducedMotion ? { duration: 0 } : { duration: 1.2, ease: 'easeOut' }}
                        className="h-full rounded-full bg-emerald-500 origin-left"
                        style={{ width: '94%' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Capabilities */}
        <section className="mx-auto max-w-6xl px-4 pb-14 sm:px-6 lg:px-10">
          <div className="mb-6" dir={isAr ? 'rtl' : 'ltr'}>
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-[var(--color-text-primary)]">
              {isAr ? 'قدرات الذكاء الاصطناعي في أصول' : 'What Osool AI Does Best'}
            </h2>
            <p className="mt-2 text-sm sm:text-base text-[var(--color-text-secondary)] max-w-2xl">
              {isAr
                ? 'تصميم بسيط، تحليلات عميقة، ومخرجات قابلة للتنفيذ فوراً.'
                : 'Minimal interface, deep analytics, and actionable outputs in seconds.'}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {CAPABILITIES.map((cap, i) => {
              const Icon = cap.icon;
              return (
                <motion.div
                  key={cap.key}
                  initial={prefersReducedMotion ? false : { opacity: 0, y: 22 }}
                  whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-5%' }}
                  transition={prefersReducedMotion ? { duration: 0 } : { ...SPRING_UP, delay: i * 0.08 }}
                  className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-600">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="h-2 w-2 rounded-full bg-emerald-500/70" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-[var(--color-text-primary)]" dir={isAr ? 'rtl' : 'ltr'}>
                    {isAr ? cap.arTitle : cap.enTitle}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]" dir={isAr ? 'rtl' : 'ltr'}>
                    {isAr ? cap.arDesc : cap.enDesc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* Final CTA */}
        <section className="mx-auto max-w-4xl px-4 pb-20 text-center sm:px-6 lg:px-10">
          <motion.div
            initial={prefersReducedMotion ? false : { opacity: 0, y: 22 }}
            whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={prefersReducedMotion ? { duration: 0 } : SPRING_UP}
            className="rounded-3xl border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-10"
          >
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-3xl" dir={isAr ? 'rtl' : 'ltr'}>
              {isAr ? 'ابدأ جلسة التحليل الآن' : 'Start Your Analysis Session'}
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm sm:text-base text-[var(--color-text-secondary)]" dir={isAr ? 'rtl' : 'ltr'}>
              {isAr
                ? 'اكتب هدفك الاستثماري، ودع أصول يقترح لك أفضل الفرص مع تحليل المخاطر والعائد.'
                : 'Describe your investment goal and let Osool return ranked opportunities with risk and return diagnostics.'}
            </p>
            <Link
              href="/chat"
              className="mt-7 inline-flex items-center gap-2 rounded-full bg-emerald-500 px-7 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/35"
            >
              <Sparkles className="h-4 w-4" />
              {t('landing.ctaButton')}
            </Link>
          </motion.div>
        </section>
      </div>
    </AppShell>
  );
}
