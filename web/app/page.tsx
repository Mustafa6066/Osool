'use client';

import Link from 'next/link';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  ArrowRight, MessageSquare, Sparkles, TrendingUp,
  ShieldCheck, Building2, MapPin, BarChart3,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { useRef } from 'react';

/* ─── spring presets ─────────────────────────── */
const SPRING_UP = { type: 'spring' as const, damping: 28, stiffness: 200 };

/* ─── feature data ────────────────────────────── */
const FEATURES = [
  { key: 'advisor', icon: MessageSquare, titleKey: 'landing.featureAdvisor', descKey: 'landing.featureAdvisorDesc' },
  { key: 'data', icon: TrendingUp, titleKey: 'landing.featureData', descKey: 'landing.featureDataDesc' },
  { key: 'trust', icon: ShieldCheck, titleKey: 'landing.featureTrust', descKey: 'landing.featureTrustDesc' },
];

/* ─── stats data ──────────────────────────────── */
const STATS = [
  { value: '12,000+', key: 'landing.statsProperties', icon: Building2 },
  { value: '150+', key: 'landing.statsDevelopers', icon: BarChart3 },
  { value: '40+', key: 'landing.statsAreas', icon: MapPin },
  { value: '94%', key: 'landing.statsAccuracy', icon: Sparkles },
];

/* ═══════════════════════════════════════════════
   LANDING PAGE — Ultra-minimal, Liquid Glass
   ═══════════════════════════════════════════════ */
export default function Home() {
  const { t } = useLanguage();
  const heroRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

  return (
    <AppShell>
      <div className="overflow-y-auto">

        {/* ════════════════════════════════════
           HERO
           ════════════════════════════════════ */}
        <motion.section
          ref={heroRef}
          style={{ opacity: heroOpacity, scale: heroScale }}
          className="relative flex min-h-[90vh] items-center justify-center px-4 overflow-hidden"
        >
          {/* Ambient orbs */}
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute left-1/2 top-1/3 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-500/[0.06] blur-[140px]" />
            <div className="absolute bottom-1/4 start-1/4 h-[400px] w-[400px] rounded-full bg-teal-500/[0.04] blur-[120px]" />
            <div className="absolute top-1/4 end-1/4 h-[300px] w-[300px] rounded-full bg-emerald-400/[0.03] blur-[100px]" />
          </div>

          <div className="relative z-10 mx-auto max-w-3xl text-center">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20, filter: 'blur(8px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ ...SPRING_UP, delay: 0.1 }}
              className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/8 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {t('landing.heroBadge')}
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 30, filter: 'blur(8px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ ...SPRING_UP, delay: 0.2 }}
              className="mt-8 text-4xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-5xl lg:text-6xl xl:text-7xl leading-[1.1]"
            >
              {t('landing.heroTitle')}
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...SPRING_UP, delay: 0.3 }}
              className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-[var(--color-text-secondary)] sm:text-lg"
            >
              {t('landing.heroSubtitle')}
            </motion.p>

            {/* CTA buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...SPRING_UP, delay: 0.4 }}
              className="mt-10 flex flex-wrap items-center justify-center gap-4"
            >
              <Link
                href="/chat"
                className="group inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-7 py-3.5 text-sm font-semibold text-[var(--color-background)] transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-emerald-500/10 active:scale-[0.98]"
              >
                <Sparkles className="h-4 w-4 transition-transform group-hover:rotate-12" />
                {t('landing.ctaStart')}
              </Link>
              <Link
                href="/explore"
                className="group inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm px-7 py-3.5 text-sm font-semibold text-[var(--color-text-primary)] transition-all hover:border-emerald-500/30 hover:scale-[1.02] active:scale-[0.98]"
              >
                {t('landing.ctaExplore')}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </motion.div>

            {/* Social proof line */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.8 }}
              className="mt-8 text-xs text-[var(--color-text-muted)]"
            >
              {t('landing.socialProof')}
            </motion.p>
          </div>
        </motion.section>

        {/* ════════════════════════════════════
           STATS BAR
           ════════════════════════════════════ */}
        <section className="mx-auto max-w-4xl px-4 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={SPRING_UP}
            className="grid grid-cols-2 gap-4 sm:grid-cols-4"
          >
            {STATS.map((stat) => {
              const Icon = stat.icon;
              return (
                <div
                  key={stat.key}
                  className="flex flex-col items-center gap-2 rounded-2xl glass-card p-5 text-center"
                >
                  <Icon className="h-5 w-5 text-emerald-500" strokeWidth={1.6} />
                  <div className="text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">
                    {stat.value}
                  </div>
                  <div className="text-xs text-[var(--color-text-muted)]">
                    {t(stat.key)}
                  </div>
                </div>
              );
            })}
          </motion.div>
        </section>

        {/* ════════════════════════════════════
           FEATURES
           ════════════════════════════════════ */}
        <section className="mx-auto max-w-4xl px-4 pb-16">
          <div className="grid gap-4 sm:grid-cols-3">
            {FEATURES.map((f, i) => {
              const Icon = f.icon;
              return (
                <motion.div
                  key={f.key}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-5%' }}
                  transition={{ ...SPRING_UP, delay: i * 0.1 }}
                  className="group rounded-[24px] glass-card p-6 transition-all hover:border-emerald-500/25 hover:shadow-lg hover:shadow-emerald-500/5"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 transition-transform group-hover:scale-105">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="mt-4 text-lg font-semibold text-[var(--color-text-primary)]">
                    {t(f.titleKey)}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">
                    {t(f.descKey)}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </section>

        {/* ════════════════════════════════════
           VISUAL SHOWCASE — Interactive placeholder
           ════════════════════════════════════ */}
        <section className="mx-auto max-w-5xl px-4 pb-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-10%' }}
            transition={SPRING_UP}
            className="relative overflow-hidden rounded-[28px] border border-[var(--color-border)] bg-gradient-to-b from-[var(--color-surface)] to-[var(--color-background)] p-px"
          >
            <div className="rounded-[27px] bg-[var(--color-surface)] p-8 sm:p-12">
              {/* Mock UI: chat conversation preview */}
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                {/* User message */}
                <div className="flex justify-end">
                  <div className="rounded-2xl rounded-br-md bg-[var(--user-surface)] px-4 py-3 max-w-[80%]">
                    <p className="text-sm text-[var(--color-text-primary)]">
                      {t('landing.askCoInvestorDescription').replace(/"/g, '')}
                    </p>
                  </div>
                </div>
                {/* AI response skeleton */}
                <div className="flex gap-3">
                  <div className="mt-1 flex-shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div className="flex-1 space-y-2.5">
                    <div className="h-3 w-4/5 rounded-full bg-emerald-500/10 animate-pulse" />
                    <div className="h-3 w-3/5 rounded-full bg-emerald-500/8 animate-pulse" style={{ animationDelay: '150ms' }} />
                    <div className="h-3 w-2/3 rounded-full bg-emerald-500/6 animate-pulse" style={{ animationDelay: '300ms' }} />
                    {/* Inline metric card skeleton */}
                    <div className="mt-3 grid grid-cols-2 gap-3">
                      <div className="rounded-xl border border-[var(--color-border)] p-3 space-y-2">
                        <div className="h-2 w-1/2 rounded-full bg-[var(--color-border)]" />
                        <div className="h-5 w-3/4 rounded-full bg-emerald-500/15" />
                      </div>
                      <div className="rounded-xl border border-[var(--color-border)] p-3 space-y-2">
                        <div className="h-2 w-1/2 rounded-full bg-[var(--color-border)]" />
                        <div className="h-5 w-3/4 rounded-full bg-emerald-500/15" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Gradient fade at bottom */}
              <div className="absolute bottom-0 inset-x-0 h-20 bg-gradient-to-t from-[var(--color-surface)] to-transparent pointer-events-none rounded-b-[27px]" />
            </div>
          </motion.div>
        </section>

        {/* ════════════════════════════════════
           BOTTOM CTA
           ════════════════════════════════════ */}
        <section className="mx-auto max-w-3xl px-4 pb-20 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={SPRING_UP}
          >
            <h2 className="text-3xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
              {t('landing.ctaTitle')}
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-base text-[var(--color-text-secondary)]">
              {t('landing.ctaDesc')}
            </p>
            <Link
              href="/chat"
              className="mt-8 inline-flex items-center gap-2 rounded-full bg-emerald-500 px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-emerald-600 hover:scale-[1.02] hover:shadow-lg hover:shadow-emerald-500/20 active:scale-[0.98]"
            >
              <Sparkles className="h-4 w-4" />
              {t('landing.ctaButton')}
            </Link>
          </motion.div>
        </section>

        {/* ════════════════════════════════════
           FOOTER
           ════════════════════════════════════ */}
        <footer className="border-t border-[var(--color-border)]">
          <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-8 text-sm text-[var(--color-text-muted)] sm:px-6 md:flex-row md:items-center md:justify-between">
            <span>{t('landing.footerTagline')}</span>
            <div className="flex gap-5">
              <Link href="/developers" className="hover:text-[var(--color-text-primary)] transition-colors">
                {t('landing.footerDevelopers')}
              </Link>
              <Link href="/areas" className="hover:text-[var(--color-text-primary)] transition-colors">
                {t('landing.footerAreas')}
              </Link>
              <Link href="/projects" className="hover:text-[var(--color-text-primary)] transition-colors">
                {t('landing.footerProjects')}
              </Link>
            </div>
          </div>
        </footer>
      </div>
    </AppShell>
  );
}
