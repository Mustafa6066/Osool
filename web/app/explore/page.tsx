'use client';

import Link from 'next/link';
import AppShell from '@/components/nav/AppShell';
import { ArrowRight, BarChart3, Building2, Compass, MapPin, ShieldCheck, Sparkles } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

export default function ExplorePage() {
  const { t, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const PATHS = [
    { title: t('explore.pathInvestment'), description: t('explore.pathInvestmentDesc'), href: '/chat', icon: Sparkles },
    { title: t('explore.pathCorridors'), description: t('explore.pathCorridorsDesc'), href: '/areas', icon: MapPin },
    { title: t('explore.pathAudit'), description: t('explore.pathAuditDesc'), href: '/developers', icon: ShieldCheck },
    { title: t('explore.pathBrowse'), description: t('explore.pathBrowseDesc'), href: '/projects', icon: Building2 },
  ];

  const INSIGHTS = [
    { label: t('explore.bestYield'), value: t('explore.bestYieldValue'), detail: t('explore.bestYieldDetail') },
    { label: t('explore.bestAppreciation'), value: t('explore.bestAppreciationValue'), detail: t('explore.bestAppreciationDetail') },
    { label: t('explore.trustResearch'), value: t('explore.trustResearchValue'), detail: t('explore.trustResearchDetail') },
  ];

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={isRTL ? 'rtl' : 'ltr'}>
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 sm:py-14">
        <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.04)] sm:p-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
              <Compass className="h-3.5 w-3.5" />
              {t('explore.badge')}
            </div>
            <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
              {t('explore.heroTitle')}
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
              {t('explore.heroDesc')}
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              {PATHS.map((path) => {
                const Icon = path.icon;
                return (
                  <Link key={path.href} href={path.href}
                    className="group rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-[0_20px_40px_rgba(0,0,0,0.04)]">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                        <Icon className="h-5 w-5" />
                      </div>
                      <ArrowRight className={`h-4 w-4 text-[var(--color-text-muted)] transition-transform ${isRTL ? 'rotate-180 group-hover:-translate-x-1' : 'group-hover:translate-x-1'}`} />
                    </div>
                    <h2 className="mt-4 text-lg font-semibold">{path.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{path.description}</p>
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                <BarChart3 className="h-4 w-4 text-emerald-500" />
                {t('explore.pulseTitle')}
              </div>
              <div className="mt-4 space-y-4">
                {INSIGHTS.map((item) => (
                  <div key={item.label} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--color-text-muted)]">{item.label}</div>
                    <div className="mt-1 text-lg font-semibold">{item.value}</div>
                    <div className="mt-1 text-sm text-[var(--color-text-secondary)]">{item.detail}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[32px] border border-[var(--color-border)] bg-gradient-to-br from-emerald-500/12 via-transparent to-transparent p-7">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                {t('explore.fastPath')}
              </div>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight">{t('explore.fastPathTitle')}</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                {t('explore.fastPathDesc')}
              </p>
              <Link href="/chat"
                className="mt-6 inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]">
                <Sparkles className="h-4 w-4" />
                {t('explore.startAdvisor')}
              </Link>
            </div>
          </div>
        </section>
      </div>
      </div>
    </AppShell>
  );
}

