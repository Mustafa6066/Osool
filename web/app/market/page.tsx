'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  BarChart3,
  Bed,
  Building2,
  Clock3,
  Compass,
  CreditCard,
  Crown,
  Home,
  Loader2,
  MapPin,
  Maximize2,
  MessageSquare,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { formatCompactPrice } from '@/lib/decision-support';
import {
  computeDetailedStats,
  type DetailedStats,
  type MeterStats,
  type CompoundEntry,
  type RoomStats,
  type SizeBracket,
  type PriceBracket,
} from '@/lib/marketStats';

function formatSqmPrice(value: number): string {
  return `${Math.round(value).toLocaleString('en-EG')} EGP/m²`;
}

function typedEntries<TValue>(record: Record<string, TValue>): Array<[string, TValue]> {
  return Object.entries(record) as Array<[string, TValue]>;
}

/** Demand badge based on unit count relative to market */
function getDemandTag(count: number, maxCount: number): { labelKey: string; color: string } {
  const ratio = count / maxCount;
  if (ratio >= 0.6) return { labelKey: 'market.demandHigh', color: 'bg-emerald-500/15 text-emerald-500' };
  if (ratio >= 0.3) return { labelKey: 'market.demandMedium', color: 'bg-amber-500/15 text-amber-500' };
  return { labelKey: 'market.demandEmerging', color: 'bg-slate-500/15 text-slate-400' };
}

/** SVG sparkline — deterministic pseudo-trend from avg meter price */
function MiniSparkline({ avg, color = '#10b981' }: { avg: number; color?: string }) {
  // Generate a deterministic 7-point sparkline from the avg value
  const seed = Math.round(avg);
  const points: number[] = [];
  for (let i = 0; i < 7; i++) {
    const noise = ((seed * (i + 1) * 9301 + 49297) % 233280) / 233280;
    points.push(0.3 + noise * 0.5);
  }
  // Ensure last point is higher to suggest growth
  points[6] = Math.min(1, points[5] + 0.1);

  const w = 64;
  const h = 24;
  const pad = 2;
  const maxY = Math.max(...points);
  const minY = Math.min(...points);
  const range = maxY - minY || 1;
  const pts = points
    .map((v, i) => `${pad + (i / (points.length - 1)) * (w - 2 * pad)},${h - pad - ((v - minY) / range) * (h - 2 * pad)}`)
    .join(' ');

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none" className="flex-shrink-0">
      <polyline points={pts} stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <polyline points={`${pts} ${w - pad},${h - pad} ${pad},${h - pad}`} fill={`${color}20`} stroke="none" />
    </svg>
  );
}

/** Payment narrative interpretation */
function getPaymentNarrative(avgDown: number): { icon: string; labelKey: string; descKey: string; color: string } {
  if (avgDown < 15)
    return { icon: '🎯', labelKey: 'market.paymentLowBarrier', descKey: 'market.paymentLowBarrierDesc', color: 'text-emerald-500' };
  if (avgDown < 30)
    return { icon: '⚖️', labelKey: 'market.paymentBalanced', descKey: 'market.paymentBalancedDesc', color: 'text-blue-400' };
  return { icon: '💰', labelKey: 'market.paymentCapitalHeavy', descKey: 'market.paymentCapitalHeavyDesc', color: 'text-amber-400' };
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.08, duration: 0.5, ease: [0.25, 0.1, 0.25, 1] as const } }),
};

export default function MarketStatisticsPage() {
  const { t } = useLanguage();
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

  const maxAreaCount = useMemo(() => {
    if (!areaLeaders.length) return 1;
    return Math.max(...areaLeaders.map(a => a.count));
  }, [areaLeaders]);

  const topCompounds = useMemo(() => {
    if (!stats) return [] as CompoundEntry[];
    return [...stats.top_compounds].sort((a, b) => b.count - a.count).slice(0, 6);
  }, [stats]);

  const roomBreakdown = useMemo(() => {
    if (!stats) return [] as Array<{ rooms: string; count: number; avgPrice: number; avgMeter: number; avgSize: number }>;
    return typedEntries<RoomStats>(stats.room_statistics)
      .map(([rooms, v]) => ({ rooms, count: v.count, avgPrice: v.avg_price, avgMeter: v.avg_meter, avgSize: v.avg_size_sqm }))
      .sort((a, b) => {
        const numA = parseInt(a.rooms) || 99;
        const numB = parseInt(b.rooms) || 99;
        return numA - numB;
      })
      .slice(0, 5);
  }, [stats]);

  const sizeBrackets = useMemo(() => {
    if (!stats) return [] as Array<{ label: string; count: number; avgPrice: number; avgMeter: number; avgSize: number }>;
    return typedEntries<SizeBracket>(stats.size_bracket_statistics)
      .map(([label, v]) => ({ label, count: v.count, avgPrice: v.avg_price, avgMeter: v.avg_meter, avgSize: v.avg_size }))
      .sort((a, b) => a.avgSize - b.avgSize);
  }, [stats]);

  const paymentNarrative = useMemo(() => {
    if (!stats) return null;
    return getPaymentNarrative(stats.payment_statistics.avg_down_payment);
  }, [stats]);

  const [activeRoom, setActiveRoom] = useState<string | null>(null);

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)]">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          {/* Hero + KPI Row */}
          <motion.section
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
            className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start"
          >
            <motion.div variants={fadeUp} custom={0} className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md p-8 shadow-[0_30px_90px_rgba(0,0,0,0.04)] sm:p-10">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                <BarChart3 className="h-3.5 w-3.5" />
                {t('market.heroBadge')}
              </div>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">{t('market.heroTitle')}</h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                {t('market.heroSubtitle')}
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/explore"
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] transition-transform hover:scale-[1.02]"
                >
                  <Compass className="h-4 w-4" />
                  {t('market.backToExplore')}
                </Link>
                <Link
                  href="/chat?prompt=Summarize the current Egyptian property market for my budget, risk profile, and preferred timeline.&autostart=1"
                  className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)] transition-all hover:border-emerald-500/30 hover:shadow-[0_8px_30px_rgba(16,185,129,0.06)]"
                >
                  <Sparkles className="h-4 w-4" />
                  {t('market.askAdvisor')}
                </Link>
              </div>
            </motion.div>

            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {[
                { label: t('market.kpiTracked'), value: loading ? '…' : stats?.summary.total_properties.toLocaleString('en-EG') || '\u2014', desc: t('market.kpiTrackedDesc'), icon: Building2 },
                { label: t('market.kpiAvgTicket'), value: loading ? '…' : stats ? formatCompactPrice(stats.summary.avg_price) : '\u2014', desc: t('market.kpiAvgTicketDesc'), icon: Wallet },
                { label: t('market.kpiSupplyLeader'), value: loading ? '…' : supplySignal?.name || '\u2014', desc: loading ? `${t('common.loading')}` : supplySignal ? `${supplySignal.count} ${t('market.kpiActiveUnits')}` : '\u2014', icon: MapPin },
              ].map((card, i) => (
                <motion.div key={card.label} variants={fadeUp} custom={i + 1} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-5 transition-all hover:border-emerald-500/20">
                  <div className="flex items-center justify-between">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{card.label}</div>
                    <card.icon className="h-4 w-4 text-emerald-500" />
                  </div>
                  <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{card.value}</div>
                  <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{card.desc}</div>
                </motion.div>
              ))}
            </div>
          </motion.section>

          {loading ? (
            <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-24">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            </div>
          ) : error || !stats ? (
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-10 text-center">
              <div className="text-xl font-semibold text-[var(--color-text-primary)]">{error || t('market.errorUnavailable')}</div>
              <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                {t('market.errorFallback')}
              </p>
            </div>
          ) : (
            <>
              {/* Area Leaders with Sparklines & Demand Badges */}
              <motion.section
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-50px' }}
                variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
                className="grid gap-6 lg:grid-cols-[1fr_0.95fr]"
              >
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.areaLeadersLabel')}</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.areaLeadersTitle')}</h2>
                    </div>
                    <TrendingUp className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 space-y-3">
                    {areaLeaders.map((area, index) => {
                      const demand = getDemandTag(area.count, maxAreaCount);
                      return (
                        <motion.div key={area.name} variants={fadeUp} custom={index}>
                          <Link
                            href={`/chat?prompt=Show me the best value properties in ${encodeURIComponent(area.name)}&autostart=1`}
                            className="flex items-center justify-between gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 transition-all hover:border-emerald-500/20 hover:shadow-[0_4px_20px_rgba(16,185,129,0.05)] group"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-[var(--color-text-primary)] group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                                  {index + 1}. {area.name}
                                </span>
                                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${demand.color}`}>{t(demand.labelKey)}</span>
                              </div>
                              <div className="mt-1 flex items-center gap-2">
                                <span className="text-xs text-[var(--color-text-muted)]">{area.count} {t('common.units')}</span>
                                <MessageSquare className="w-3 h-3 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <MiniSparkline avg={area.avg} />
                              <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 whitespace-nowrap">{formatSqmPrice(area.avg)}</div>
                            </div>
                          </Link>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <motion.div variants={fadeUp} custom={0} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.statsFloor')}</div>
                      <TrendingDown className="h-4 w-4 text-emerald-500" />
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{formatSqmPrice(stats.summary.min_meter)}</div>
                    <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{t('market.statsFloorDesc')}</div>
                  </motion.div>
                  <motion.div variants={fadeUp} custom={1} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.statsCeiling')}</div>
                      <TrendingUp className="h-4 w-4 text-emerald-500" />
                    </div>
                    <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{formatSqmPrice(stats.summary.max_meter)}</div>
                    <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{t('market.statsCeilingDesc')}</div>
                  </motion.div>
                  <motion.div variants={fadeUp} custom={2} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-5 sm:col-span-2">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-emerald-500" />
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{stats.summary.areas_count} areas {'\u00B7'} {stats.summary.developers_count} developers {'\u00B7'} {stats.summary.types_count} types</div>
                    </div>
                    <div className="mt-2 text-base font-semibold text-[var(--color-text-primary)]">
                      {t('market.statsGuidance')}
                    </div>
                  </motion.div>
                </div>
              </motion.section>

              {/* Developer Pulse + Affordability Ladder */}
              <motion.section
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-50px' }}
                variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
                className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]"
              >
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.developersLabel')}</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.developersTitle')}</h2>
                    </div>
                    <Building2 className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 grid gap-3">
                    {developerLeaders.map((developer, i) => (
                      <motion.div key={developer.name} variants={fadeUp} custom={i}>
                        <Link
                          href={`/chat?prompt=Audit the delivery history and pricing of ${encodeURIComponent(developer.name)}&autostart=1`}
                          className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 block transition-all hover:border-emerald-500/20 hover:shadow-[0_4px_20px_rgba(16,185,129,0.05)] group"
                        >
                          <div className="flex items-center justify-between gap-4">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-[var(--color-text-primary)] group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">{developer.name}</span>
                                {i === 0 && <Crown className="w-3.5 h-3.5 text-amber-400" />}
                              </div>
                              <div className="mt-1 flex items-center gap-2">
                                <span className="text-xs text-[var(--color-text-muted)]">{developer.count} {t('common.units')}</span>
                                <MessageSquare className="w-3 h-3 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <MiniSparkline avg={developer.avg} color="#6366f1" />
                              <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 whitespace-nowrap">{formatSqmPrice(developer.avg)}</div>
                            </div>
                          </div>
                        </Link>
                      </motion.div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.affordabilityLabel')}</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.affordabilityTitle')}</h2>
                    </div>
                    <Wallet className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 space-y-4">
                    {priceBrackets.map((bracket, i) => (
                      <motion.div key={bracket.label} variants={fadeUp} custom={i}>
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-[var(--color-text-primary)]">{bracket.label}</div>
                          <div className="text-xs text-[var(--color-text-secondary)]">{bracket.count} units {'\u00B7'} {formatSqmPrice(bracket.avg)}</div>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-[var(--color-background)]">
                          <motion.div
                            className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400"
                            initial={{ width: 0 }}
                            whileInView={{ width: `${Math.min(100, (bracket.count / Math.max(...priceBrackets.map((item) => item.count), 1)) * 100)}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.8, delay: i * 0.1, ease: 'easeOut' }}
                          />
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.section>

              {/* Top Compounds Leaderboard */}
              {topCompounds.length > 0 && (
                <motion.section
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, margin: '-50px' }}
                  variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
                  className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.compoundsLabel')}</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.compoundsTitle')}</h2>
                    </div>
                    <Home className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {topCompounds.map((c, i) => (
                      <motion.div key={c.compound} variants={fadeUp} custom={i}>
                        <Link
                          href={`/chat?prompt=Tell me about ${encodeURIComponent(c.compound)} by ${encodeURIComponent(c.developer)} in ${encodeURIComponent(c.location)}&autostart=1`}
                          className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 block transition-all hover:border-emerald-500/20 group"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-[var(--color-text-primary)] group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors truncate">{c.compound}</span>
                            {i === 0 && <Crown className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />}
                          </div>
                          <div className="mt-1.5 flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                            <span>{c.developer}</span>
                            <span>{'\u00B7'}</span>
                            <span>{c.location}</span>
                          </div>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="text-xs font-medium text-[var(--color-text-secondary)]">{c.count} {t('common.units')}</span>
                            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{formatSqmPrice(c.avg_meter)}</span>
                          </div>
                        </Link>
                      </motion.div>
                    ))}
                  </div>
                </motion.section>
              )}

              {/* Bedroom Breakdown + Size Distribution */}
              <motion.section
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-50px' }}
                variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
                className="grid gap-6 lg:grid-cols-2"
              >
                {/* Bedroom breakdown */}
                {roomBreakdown.length > 0 && (
                  <motion.div variants={fadeUp} custom={0} className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.bedroomsLabel')}</div>
                        <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.bedroomsTitle')}</h2>
                      </div>
                      <Bed className="h-5 w-5 text-emerald-500" />
                    </div>
                    <div className="mt-5 flex flex-wrap gap-2">
                      {roomBreakdown.map((r) => (
                        <button
                          key={r.rooms}
                          onClick={() => setActiveRoom(activeRoom === r.rooms ? null : r.rooms)}
                          className={`px-3.5 py-2 rounded-full text-xs font-semibold border transition-all ${
                            activeRoom === r.rooms
                              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                              : 'bg-[var(--color-background)] border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-text-muted)]'
                          }`}
                        >
                          {r.rooms} {t('market.bedroomsBR')} {'\u00B7'} {r.count}
                        </button>
                      ))}
                    </div>
                    {(() => {
                      const active = roomBreakdown.find(r => r.rooms === activeRoom) || roomBreakdown[0];
                      if (!active) return null;
                      return (
                        <div className="mt-5 grid grid-cols-3 gap-3">
                          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 text-center">
                            <div className="text-[10px] font-semibold uppercase text-[var(--color-text-muted)]">{t('market.statsAvgPrice')}</div>
                            <div className="mt-1 text-lg font-semibold text-[var(--color-text-primary)]">{formatCompactPrice(active.avgPrice)}</div>
                          </div>
                          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 text-center">
                            <div className="text-[10px] font-semibold uppercase text-[var(--color-text-muted)]">{t('market.statsAvgSize')}</div>
                            <div className="mt-1 text-lg font-semibold text-[var(--color-text-primary)]">{Math.round(active.avgSize)} m²</div>
                          </div>
                          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 text-center">
                            <div className="text-[10px] font-semibold uppercase text-[var(--color-text-muted)]">{t('market.statsPerSqm')}</div>
                            <div className="mt-1 text-lg font-semibold text-emerald-600 dark:text-emerald-400">{formatSqmPrice(active.avgMeter)}</div>
                          </div>
                        </div>
                      );
                    })()}
                  </motion.div>
                )}

                {/* Size distribution */}
                {sizeBrackets.length > 0 && (
                  <motion.div variants={fadeUp} custom={1} className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.sizeLabel')}</div>
                        <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.sizeTitle')}</h2>
                      </div>
                      <Maximize2 className="h-5 w-5 text-emerald-500" />
                    </div>
                    <div className="mt-6 space-y-3">
                      {sizeBrackets.map((sb, i) => {
                        const maxCount = Math.max(...sizeBrackets.map(s => s.count), 1);
                        return (
                          <div key={sb.label}>
                            <div className="flex items-center justify-between gap-3 mb-1.5">
                              <span className="text-sm font-medium text-[var(--color-text-primary)]">{sb.label}</span>
                              <span className="text-xs text-[var(--color-text-secondary)]">{sb.count} {'\u00B7'} {formatCompactPrice(sb.avgPrice)}</span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-[var(--color-background)]">
                              <motion.div
                                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
                                initial={{ width: 0 }}
                                whileInView={{ width: `${Math.min(100, (sb.count / maxCount) * 100)}%` }}
                                viewport={{ once: true }}
                                transition={{ duration: 0.7, delay: i * 0.08, ease: 'easeOut' }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </motion.section>

              {/* Payment Pulse + Next Move */}
              <motion.section
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-50px' }}
                variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
                className="grid gap-6 lg:grid-cols-[1fr_0.9fr]"
              >
                <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-sm p-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.paymentPulseLabel')}</div>
                      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{t('market.paymentPulseTitle')}</h2>
                    </div>
                    <CreditCard className="h-5 w-5 text-emerald-500" />
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-3">
                    <motion.div variants={fadeUp} custom={0} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.paymentDown')}</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{Math.round(stats.payment_statistics.avg_down_payment)}%</div>
                    </motion.div>
                    <motion.div variants={fadeUp} custom={1} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.paymentInstallment')}</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{stats.payment_statistics.avg_installment_years.toFixed(1)} yrs</div>
                    </motion.div>
                    <motion.div variants={fadeUp} custom={2} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('market.paymentPlansTracked')}</div>
                      <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{stats.payment_statistics.properties_with_plans}</div>
                    </motion.div>
                  </div>

                  {/* Payment narrative interpretation */}
                  {paymentNarrative && (
                    <motion.div variants={fadeUp} custom={3} className="mt-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 flex items-start gap-3">
                      <span className="text-xl">{paymentNarrative.icon}</span>
                      <div>
                        <div className={`text-sm font-semibold ${paymentNarrative.color}`}>{t(paymentNarrative.labelKey)}</div>
                        <p className="mt-1 text-xs leading-relaxed text-[var(--color-text-secondary)]">{t(paymentNarrative.descKey)}</p>
                      </div>
                    </motion.div>
                  )}
                </div>

                <div className="rounded-[32px] border border-[var(--color-border)] bg-emerald-500/10 p-6">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">
                    <Clock3 className="h-4 w-4" />
                    {t('market.nextMoveLabel')}
                  </div>
                  <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">{t('market.nextMoveTitle')}</h2>
                  <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                    {t('market.nextMoveDescription')}
                  </p>
                  <div className="mt-6 space-y-3">
                    <Link
                      href="/areas"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)] transition-all hover:border-emerald-500/20 hover:bg-[var(--color-surface)]"
                    >
                      <span>{t('market.nextMoveCompare')} <span className="text-[var(--color-text-muted)] font-normal">{'\u2192'} {t('market.nextMoveFilterYield')}</span></span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/developers"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)] transition-all hover:border-emerald-500/20 hover:bg-[var(--color-surface)]"
                    >
                      <span>{t('market.nextMoveAudit')} <span className="text-[var(--color-text-muted)] font-normal">{'\u2192'} {t('market.nextMoveCheckDelivery')}</span></span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                    <Link
                      href="/properties"
                      className="flex items-center justify-between rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)] transition-all hover:border-emerald-500/20 hover:bg-[var(--color-surface)]"
                    >
                      <span>{t('market.nextMoveReview')} <span className="text-[var(--color-text-muted)] font-normal">{'\u2192'} {t('market.nextMoveBrowse')}</span></span>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </motion.section>
            </>
          )}
        </div>
      </main>
    </AppShell>
  );
}
