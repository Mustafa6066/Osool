'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  BarChart3,
  Building2,
  Clock3,
  Compass,
  CreditCard,
  Loader2,
  MapPin,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import SmartNav from '@/components/SmartNav';
import { formatCompactPrice } from '@/lib/decision-support';
import { computeDetailedStats, type DetailedStats, type MeterStats, type PriceBracket } from '@/lib/marketStats';

function formatSqmPrice(value: number): string {
  return `${Math.round(value).toLocaleString('en-EG')} EGP/m²`;
}

function typedEntries<TValue>(record: Record<string, TValue>): Array<[string, TValue]> {
  return Object.entries(record) as Array<[string, TValue]>;
}

export default function MarketStatisticsPage() {
  const [stats, setStats] = useState<DetailedStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/assets/js/data.js');
        const text = await response.text();
        const start = text.indexOf('{');
        const end = text.lastIndexOf('}');

        if (start === -1 || end === -1) {
          throw new Error('Could not parse market data');
        }

        const raw = JSON.parse(text.slice(start, end + 1));
        const properties = raw.properties || [];
        if (!properties.length) {
          throw new Error('No market data available');
        }

        setStats(computeDetailedStats(properties));
      } catch (loadError) {
        console.error(loadError);
        setError('Market intelligence is unavailable right now.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const areaLeaders = useMemo(() => {
    if (!stats) {
      return [] as Array<{ name: string; avg: number; count: number }>;
    }

    return typedEntries<MeterStats>(stats.meter_price_by_area)
      .map(([name, value]) => ({ name, avg: value.avg_meter, count: value.count }))
      .sort((left, right) => right.avg - left.avg)
      .slice(0, 5);
  }, [stats]);

  const developerLeaders = useMemo(() => {
    if (!stats) {
      return [] as Array<{ name: string; avg: number; count: number }>;
    }

    return typedEntries<MeterStats>(stats.meter_price_by_developer)
      .map(([name, value]) => ({ name, avg: value.avg_meter, count: value.count }))
      .sort((left, right) => right.avg - left.avg)
      .slice(0, 4);
  }, [stats]);

  const priceBrackets = useMemo(() => {
    if (!stats) {
      return [] as Array<{ label: string; count: number; avg: number }>;
    }

    const order = ['Under 2M EGP', '2M – 5M EGP', '5M – 10M EGP', '10M – 20M EGP', '20M – 50M EGP', 'Over 50M EGP'];
    return typedEntries<PriceBracket>(stats.price_bracket_distribution)
      .map(([label, value]) => ({ label, count: value.count, avg: value.avg_meter }))
      .sort((left, right) => order.indexOf(left.label) - order.indexOf(right.label));
  }, [stats]);

  const supplySignal = useMemo(() => {
    if (!stats) {
      return null;
    }

    return (
      typedEntries<MeterStats>(stats.meter_price_by_area)
        .map(([name, value]) => ({ name, count: value.count }))
        .sort((left, right) => right.count - left.count)[0] || null
    );
  }, [stats]);

  return (
    <SmartNav>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] pb-20 md:pb-0">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
            <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                <BarChart3 className="h-3.5 w-3.5" />
                Market intelligence board
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">Read the market before you read individual listings.</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                This route now acts as a quick intelligence layer across pricing, corridor strength, developer positioning, and payment conditions before you move back into Explore or Advisor.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/explore"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
                >
                  <Compass className="h-4 w-4" />
                  Back to Explore
                </Link>
                <Link
                  href="/chat?prompt=Summarize the current Egyptian property market for my budget, risk profile, and preferred timeline.&autostart=1"
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
                >
                  <Sparkles className="h-4 w-4" />
                  Ask Osool for a market brief
                </Link>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Tracked properties</div>
                  <Building2 className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">
                  {loading ? '…' : stats?.summary.total_properties.toLocaleString('en-EG') || '—'}
                </div>
                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Live inventory count coming from the current embedded market data set.</div>
              </div>
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Average ticket</div>
                  <Wallet className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">
                  {loading ? '…' : stats ? formatCompactPrice(stats.summary.avg_price) : '—'}
                </div>
                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Typical asking-price level across the current market snapshot.</div>
              </div>
              <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Supply leader</div>
                  <MapPin className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="mt-2 text-lg font-semibold text-[var(--color-text-primary)]">
                  {loading ? '…' : supplySignal?.name || '—'}
                </div>
                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">
                  {loading
                    ? 'Loading supply signal…'
                    : supplySignal
                      ? `${supplySignal.count} active units in the current data set.`
                      : 'No supply signal available.'}
                </div>
              </div>
            </div>
          </section>

          {loading ? (
            <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-24">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            </div>
          ) : error || !stats ? (
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-10 text-center">
              <div className="text-xl font-semibold text-[var(--color-text-primary)]">{error || 'Market data is unavailable right now.'}</div>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                You can still continue through Explore or ask Osool Advisor for a guided market read.
              </p>
            </div>
          ) : (
            <>
              <section className="grid gap-6 lg:grid-cols-[1fr_0.95fr]">
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Area leaders</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">Which corridors are currently commanding the highest pricing?</h2>
                    </div>
                    <TrendingUp className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 space-y-3">
                    {areaLeaders.map((area, index) => (
                      <div key={area.name} className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                        <div>
                          <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                            {index + 1}. {area.name}
                          </div>
                          <div className="mt-1 text-xs text-[var(--color-text-muted)]">{area.count} tracked units</div>
                        </div>
                        <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{formatSqmPrice(area.avg)}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Market floor</div>
                      <TrendingDown className="h-4 w-4 text-emerald-500" />
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{formatSqmPrice(stats.summary.min_meter)}</div>
                    <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Lowest price-per-meter point in the current embedded inventory.</div>
                  </div>
                  <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Market ceiling</div>
                      <TrendingUp className="h-4 w-4 text-emerald-500" />
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{formatSqmPrice(stats.summary.max_meter)}</div>
                    <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Highest pricing edge currently visible in the same data snapshot.</div>
                  </div>
                  <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sm:col-span-2">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Read this correctly</div>
                    <div className="mt-2 text-base font-semibold text-[var(--color-text-primary)]">
                      Use this page for orientation, then move into areas, developers, projects, and units for an actual decision.
                    </div>
                  </div>
                </div>
              </section>

              <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Developer pulse</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">Premium positioning by developer</h2>
                    </div>
                    <Building2 className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 grid gap-3">
                    {developerLeaders.map((developer) => (
                      <div key={developer.name} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <div className="text-sm font-semibold text-[var(--color-text-primary)]">{developer.name}</div>
                            <div className="mt-1 text-xs text-[var(--color-text-muted)]">{developer.count} tracked units</div>
                          </div>
                          <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">{formatSqmPrice(developer.avg)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Affordability ladder</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">Where supply sits across price brackets</h2>
                    </div>
                    <Wallet className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 space-y-4">
                    {priceBrackets.map((bracket) => (
                      <div key={bracket.label}>
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-[var(--color-text-primary)]">{bracket.label}</div>
                          <div className="text-xs text-[var(--color-text-muted)]">{bracket.count} units</div>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-[var(--color-background)]">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400"
                            style={{
                              width: `${Math.min(
                                100,
                                (bracket.count / Math.max(...priceBrackets.map((item) => item.count), 1)) * 100
                              )}%`,
                            }}
                          />
                        </div>
                        <div className="mt-2 text-xs text-[var(--color-text-muted)]">Average pricing inside bracket: {formatSqmPrice(bracket.avg)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Payment pulse</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">How flexible are current payment structures?</h2>
                    </div>
                    <CreditCard className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-3">
                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Avg down payment</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{Math.round(stats.payment_statistics.avg_down_payment)}%</div>
                    </div>
                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Avg installment length</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{stats.payment_statistics.avg_installment_years.toFixed(1)} yrs</div>
                    </div>
                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Plans tracked</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{stats.payment_statistics.properties_with_plans}</div>
                    </div>
                  </div>
                </div>

                <div className="rounded-[32px] border border-[var(--color-border)] bg-emerald-500/10 p-6">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                    <Clock3 className="h-4 w-4" />
                    Next move
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Turn this market context into a narrower shortlist.</h2>
                  <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                    The market route should inform your next question, not replace it. Move into areas and developers for directional confidence, then use property detail and Advisor to judge actual entry quality.
                  </p>
                  <div className="mt-6 space-y-3">
                    <Link
                      href="/areas"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)]"
                    >
                      Compare corridors
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/developers"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)]"
                    >
                      Audit developers
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/properties"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)]"
                    >
                      Review live units
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </section>
            </>
          )}
        </div>
      </main>
    </SmartNav>
  );
}
