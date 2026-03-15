import Link from 'next/link';
import { ArrowRight, BarChart3, Building2, FileSearch, GitCompare, MapPin, ShieldCheck, Sparkles } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';

const PATHS = [
    {
        title: 'Find my best investment',
        description: 'Budget-aware guidance for yield, appreciation, and risk appetite.',
        href: '/chat',
        icon: Sparkles,
    },
    {
        title: 'Check fair price',
        description: 'Move from asking price to explainable fair-value reasoning.',
        href: '/properties',
        icon: BarChart3,
    },
    {
        title: 'Audit a developer',
        description: 'Delivery confidence, quality consistency, and resale resilience.',
        href: '/developers',
        icon: ShieldCheck,
    },
    {
        title: 'Stress-test a shortlist',
        description: 'Surface tradeoffs, entry risks, and the smartest next move before you commit.',
        href: '/chat',
        icon: FileSearch,
    },
];

const TRUST = [
    { label: 'Decision layer', value: 'AI + data + trust checks' },
    { label: 'Egypt coverage', value: 'Areas, developers, projects, pricing' },
    { label: 'User experience', value: 'From confusion to a clear next move' },
];

const EXPLORE = [
    {
        title: 'High-conviction areas',
        description: 'Compare corridors by yield, appreciation, and stability.',
        href: '/areas',
        icon: MapPin,
    },
    {
        title: 'Developer trust board',
        description: 'Rank delivery history, finish quality, and resale strength.',
        href: '/developers',
        icon: GitCompare,
    },
    {
        title: 'Verified projects',
        description: 'Review project pricing, payment plans, and delivery timing.',
        href: '/projects',
        icon: Building2,
    },
];

export default function Home() {
    return (
        <AppShell>
            <section className="mx-auto max-w-7xl px-4 pb-14 pt-8 sm:px-6 sm:pt-12">
                <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
                    <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_32px_100px_rgba(0,0,0,0.05)] sm:p-10 lg:p-12">
                        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400">
                            <Sparkles className="h-3.5 w-3.5" />
                            Calm, trusted intelligence
                        </div>

                        <h1 className="mt-6 max-w-4xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
                            The smartest way to move from browsing Egypt&apos;s property market to making a confident decision.
                        </h1>

                        <p className="mt-5 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                            Osool reduces the cognitive load of real-estate decisions with one system for area research,
                            developer trust, pricing clarity, and advisor-guided next steps.
                        </p>

                        <div className="mt-8 grid gap-4 sm:grid-cols-2">
                            {PATHS.map((path) => {
                                const Icon = path.icon;
                                return (
                                    <Link
                                        key={path.title}
                                        href={path.href}
                                        className="group rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40 hover:shadow-[0_20px_40px_rgba(0,0,0,0.04)]"
                                    >
                                        <div className="flex items-center justify-between gap-3">
                                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                                <Icon className="h-5 w-5" />
                                            </div>
                                            <ArrowRight className="h-4 w-4 text-[var(--color-text-muted)] transition-transform group-hover:translate-x-1" />
                                        </div>
                                        <div className="mt-4 text-lg font-semibold">{path.title}</div>
                                        <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{path.description}</div>
                                    </Link>
                                );
                            })}
                        </div>

                        <div className="mt-8 flex flex-wrap gap-3">
                            <Link
                                href="/chat"
                                className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] transition-transform hover:scale-[1.02]"
                            >
                                <Sparkles className="h-4 w-4" />
                                Start with Osool Advisor
                            </Link>
                            <Link
                                href="/explore"
                                className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                            >
                                Explore the market
                            </Link>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7">
                            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                                Smart decision brief
                            </div>
                            <div className="mt-4 rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5">
                                <div className="flex items-center justify-between gap-3">
                                    <div>
                                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">Best match: income-oriented investor</div>
                                        <div className="mt-1 text-sm text-[var(--color-text-secondary)]">Shortlist optimized for yield under 5M EGP.</div>
                                    </div>
                                    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                                        Confidence 91%
                                    </span>
                                </div>

                                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                                        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Best corridor</div>
                                        <div className="mt-1 text-base font-semibold">Sheikh Zayed rentals</div>
                                        <div className="mt-1 text-sm text-[var(--color-text-secondary)]">Resilient demand and stable occupancy.</div>
                                    </div>
                                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                                        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Watch-out</div>
                                        <div className="mt-1 text-base font-semibold">New Capital pricing drift</div>
                                        <div className="mt-1 text-sm text-[var(--color-text-secondary)]">Strong upside, but entry pricing needs tighter selection.</div>
                                    </div>
                                </div>

                                <div className="mt-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-[var(--color-text-primary)]">
                                    Next best action: compare two shortlisted corridors and ask Osool to recommend the lower-risk entry point.
                                </div>
                            </div>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                            {TRUST.map((item) => (
                                <div key={item.label} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{item.label}</div>
                                    <div className="mt-2 text-sm font-semibold text-[var(--color-text-primary)]">{item.value}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            <section className="border-y border-[var(--color-border)] bg-[var(--color-surface)]/40">
                <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 md:grid-cols-3">
                    {EXPLORE.map((item) => {
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.title}
                                href={item.href}
                                className="group rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:border-emerald-500/40"
                            >
                                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                    <Icon className="h-5 w-5" />
                                </div>
                                <h2 className="mt-4 text-lg font-semibold">{item.title}</h2>
                                <p className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{item.description}</p>
                            </Link>
                        );
                    })}
                </div>
            </section>

            <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6">
                <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
                    <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                            What changes here
                        </div>
                        <h2 className="mt-3 text-3xl font-semibold tracking-tight">Osool should feel like a decision layer, not a noisy listings site.</h2>
                        <p className="mt-4 text-sm leading-7 text-[var(--color-text-secondary)]">
                            Every major flow now points toward the same product promise: a calmer, smarter path from discovery to confidence,
                            with AI and evidence reducing work instead of creating more of it.
                        </p>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Trust</div>
                            <div className="mt-2 text-lg font-semibold">Developer audits, pricing clarity, and cleaner next steps.</div>
                        </div>
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Smartness</div>
                            <div className="mt-2 text-lg font-semibold">Intent-driven routing across advisor, explore, and saved work.</div>
                        </div>
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Compatibility</div>
                            <div className="mt-2 text-lg font-semibold">Built on top of your current routes, SEO pages, and API surface.</div>
                        </div>
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Next move</div>
                            <div className="mt-2 text-lg font-semibold">Use Explore for breadth, then move into Advisor for depth.</div>
                        </div>
                    </div>
                </div>
            </section>

            <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)]/40">
                <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-[var(--color-text-muted)] sm:px-6 md:flex-row md:items-center md:justify-between">
                    <div>Osool.ai is evolving into a calmer decision workspace for Egyptian real estate.</div>
                    <div className="flex gap-5">
                        <Link href="/developers" className="hover:text-[var(--color-text-primary)]">Developers</Link>
                        <Link href="/areas" className="hover:text-[var(--color-text-primary)]">Areas</Link>
                        <Link href="/projects" className="hover:text-[var(--color-text-primary)]">Projects</Link>
                    </div>
                </div>
            </footer>
        </AppShell>
    );
}
