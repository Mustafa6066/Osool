'use client';

import Link from 'next/link';
import { ArrowRight, MessageSquare, Sparkles, TrendingUp, ShieldCheck } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';

const FEATURES = [
    { key: 'advisor', icon: MessageSquare, titleKey: 'landing.featureAdvisor', descKey: 'landing.featureAdvisorDesc' },
    { key: 'data', icon: TrendingUp, titleKey: 'landing.featureData', descKey: 'landing.featureDataDesc' },
    { key: 'trust', icon: ShieldCheck, titleKey: 'landing.featureTrust', descKey: 'landing.featureTrustDesc' },
];

export default function Home() {
    const { t } = useLanguage();

    return (
        <AppShell>
            <div className="h-full overflow-y-auto">
                {/* Hero */}
                <section className="relative flex min-h-[82vh] items-center justify-center px-4">
                    {/* Background decoration */}
                    <div className="pointer-events-none absolute inset-0 overflow-hidden">
                        <div className="absolute left-1/2 top-1/3 h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-500/[0.07] blur-[120px]" />
                        <div className="absolute bottom-0 left-1/4 h-[300px] w-[300px] rounded-full bg-emerald-500/[0.04] blur-[100px]" />
                    </div>

                    <div className="relative z-10 mx-auto max-w-3xl text-center">
                        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
                            <Sparkles className="h-3.5 w-3.5" />
                            {t('landing.heroBadge')}
                        </div>

                        <h1 className="mt-8 text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl">
                            {t('landing.heroTitle')}
                        </h1>

                        <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-[var(--color-text-secondary)]">
                            {t('landing.heroSubtitle')}
                        </p>

                        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
                            <Link
                                href="/chat"
                                className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-6 py-3.5 text-sm font-semibold text-[var(--color-background)] transition-transform hover:scale-[1.02]"
                            >
                                <Sparkles className="h-4 w-4" />
                                {t('landing.ctaStart')}
                            </Link>
                            <Link
                                href="/explore"
                                className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3.5 text-sm font-semibold text-[var(--color-text-primary)] transition-colors hover:border-emerald-500/40"
                            >
                                {t('landing.ctaExplore')}
                                <ArrowRight className="h-4 w-4" />
                            </Link>
                        </div>
                    </div>
                </section>

                {/* Features */}
                <section className="mx-auto max-w-4xl px-4 pb-24">
                    <div className="grid gap-4 sm:grid-cols-3">
                        {FEATURES.map((f) => {
                            const Icon = f.icon;
                            return (
                                <div
                                    key={f.key}
                                    className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-colors hover:border-emerald-500/30"
                                >
                                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                        <Icon className="h-5 w-5" />
                                    </div>
                                    <div className="mt-4 text-lg font-semibold">{t(f.titleKey)}</div>
                                    <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{t(f.descKey)}</div>
                                </div>
                            );
                        })}
                    </div>
                </section>

                {/* Footer */}
                <footer className="border-t border-[var(--color-border)]">
                    <div className="mx-auto flex max-w-5xl flex-col gap-4 px-4 py-8 text-sm text-[var(--color-text-muted)] sm:px-6 md:flex-row md:items-center md:justify-between">
                        <span>{t('landing.footerTagline')}</span>
                        <div className="flex gap-5">
                            <Link href="/developers" className="hover:text-[var(--color-text-primary)]">{t('landing.footerDevelopers')}</Link>
                            <Link href="/areas" className="hover:text-[var(--color-text-primary)]">{t('landing.footerAreas')}</Link>
                            <Link href="/projects" className="hover:text-[var(--color-text-primary)]">{t('landing.footerProjects')}</Link>
                        </div>
                    </div>
                </footer>
            </div>
        </AppShell>
    );
}
