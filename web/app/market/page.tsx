'use client';

import { useState, useEffect } from 'react';
import {
    Activity, BarChart3, MapPin, Building2, Home, Users, Layers,
    TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight,
    DollarSign, Ruler, BedDouble, Paintbrush, CreditCard,
    Trophy, Target, Loader2, AlertCircle, Sparkles
} from 'lucide-react';
import api from '@/lib/api';
import SmartNav from '@/components/SmartNav';

/* ═══════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════ */
interface MeterStats {
    min_meter: number;
    avg_meter: number;
    max_meter: number;
    count: number;
}

interface RoomStats {
    count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    avg_size_sqm: number;
    avg_meter: number;
}

interface BestDeal {
    property_id: number;
    title: string;
    price: number;
    price_per_sqm: number;
    developer: string;
    compound: string;
}

interface DevLocEntry {
    developer: string;
    location: string;
    avg_meter: number;
    count: number;
}

interface CompoundEntry {
    compound: string;
    developer: string;
    location: string;
    count: number;
    avg_meter: number;
}

interface SizeBracket {
    count: number;
    avg_price: number;
    avg_meter: number;
    avg_size: number;
}

interface PaymentStats {
    avg_down_payment: number;
    avg_installment_years: number;
    avg_monthly_installment: number;
    min_down_payment: number;
    max_down_payment: number;
    properties_with_plans: number;
}

interface PriceBracket {
    count: number;
    avg_meter: number;
}

interface DetailedStats {
    meter_price_by_area: Record<string, MeterStats>;
    meter_price_by_developer: Record<string, MeterStats>;
    meter_price_by_type: Record<string, MeterStats>;
    room_statistics: Record<string, RoomStats>;
    developer_by_location: Record<string, DevLocEntry>;
    best_price_per_area: Record<string, BestDeal>;
    best_price_per_developer: Record<string, BestDeal>;
    best_price_per_type: Record<string, BestDeal>;
    finishing_statistics: Record<string, MeterStats>;
    size_bracket_statistics: Record<string, SizeBracket>;
    payment_statistics: PaymentStats;
    price_bracket_distribution: Record<string, PriceBracket>;
    top_compounds: CompoundEntry[];
    summary: {
        total_properties: number;
        avg_price: number;
        avg_meter: number;
        min_meter: number;
        max_meter: number;
        areas_count: number;
        developers_count: number;
        types_count: number;
    };
}

/* ═══════════════════════════════════════════════════════════════
   UTILITY COMPONENTS
   ═══════════════════════════════════════════════════════════════ */

/** Format number with commas */
const fmt = (n: number) => Math.round(n).toLocaleString();

/** Format as millions */
const fmtM = (n: number) => `${(n / 1_000_000).toFixed(1)}M`;

/** Section header with icon */
function SectionHeader({ icon: Icon, title, subtitle, kpiRange }: {
    icon: any; title: string; subtitle: string; kpiRange: string;
}) {
    return (
        <div className="flex items-start gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-[var(--color-text-primary)]">{title}</h2>
                    <span className="text-[10px] font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-1.5 py-0.5 rounded">
                        {kpiRange}
                    </span>
                </div>
                <p className="text-sm text-[var(--color-text-muted)] mt-0.5">{subtitle}</p>
            </div>
        </div>
    );
}

/** Hero KPI card */
function HeroCard({ label, value, unit, icon: Icon, accent = false }: {
    label: string; value: string; unit?: string; icon: any; accent?: boolean;
}) {
    return (
        <div className={`p-5 rounded-2xl border transition-all ${accent
            ? 'bg-emerald-500/5 border-emerald-500/20'
            : 'bg-[var(--color-surface)] border-[var(--color-border)]'
            }`}>
            <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${accent
                    ? 'bg-emerald-500/15 text-emerald-500'
                    : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                    }`}>
                    <Icon className="w-4 h-4" />
                </div>
            </div>
            <div className="flex items-baseline gap-1.5">
                <span className={`text-2xl font-bold ${accent ? 'text-emerald-500' : 'text-[var(--color-text-primary)]'}`}>
                    {value}
                </span>
                {unit && <span className="text-sm text-[var(--color-text-muted)]">{unit}</span>}
            </div>
        </div>
    );
}

/** Insight mini card */
function InsightCard({ label, value, sublabel, icon: Icon, color = 'emerald' }: {
    label: string; value: string; sublabel?: string; icon: any; color?: string;
}) {
    const colorMap: Record<string, string> = {
        emerald: 'bg-emerald-500/10 text-emerald-500',
        amber: 'bg-amber-500/10 text-amber-500',
        blue: 'bg-blue-500/10 text-blue-500',
        violet: 'bg-violet-500/10 text-violet-500',
    };
    return (
        <div className="p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)]">
            <div className="flex items-center gap-2 mb-2">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center ${colorMap[color] || colorMap.emerald}`}>
                    <Icon className="w-3.5 h-3.5" />
                </div>
                <span className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
            </div>
            <div className="text-lg font-bold text-[var(--color-text-primary)]">{value}</div>
            {sublabel && <div className="text-xs text-[var(--color-text-muted)] mt-0.5">{sublabel}</div>}
        </div>
    );
}

/** Loading skeleton grid */
function SkeletonGrid({ count = 4 }: { count?: number }) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-${count} gap-4`}>
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="h-28 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] animate-pulse" />
            ))}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════ */
export default function MarketStatisticsPage() {
    const [data, setData] = useState<DetailedStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchStats() {
            try {
                setLoading(true);
                const { data: stats } = await api.get('/api/market/detailed-stats');
                setData(stats);
                setError(null);
            } catch (err: any) {
                console.error('Failed to fetch market statistics:', err);
                setError('Unable to load market statistics. Please try again.');
            } finally {
                setLoading(false);
            }
        }
        fetchStats();
    }, []);

    // Derived KPIs
    const areas = data?.meter_price_by_area ? Object.entries(data.meter_price_by_area) : [];
    const developers = data?.meter_price_by_developer ? Object.entries(data.meter_price_by_developer) : [];
    const types = data?.meter_price_by_type ? Object.entries(data.meter_price_by_type) : [];
    const rooms = data?.room_statistics ? Object.entries(data.room_statistics).sort(([a], [b]) => parseInt(a) - parseInt(b)) : [];
    const devLocs = data?.developer_by_location ? Object.values(data.developer_by_location) : [];
    const compounds = data?.top_compounds || [];
    const finishing = data?.finishing_statistics ? Object.entries(data.finishing_statistics) : [];
    const sizeBrackets = data?.size_bracket_statistics ? Object.entries(data.size_bracket_statistics) : [];
    const priceBrackets = data?.price_bracket_distribution ? Object.entries(data.price_bracket_distribution) : [];
    const bestDeals = data?.best_price_per_area ? Object.entries(data.best_price_per_area) : [];
    const payment = data?.payment_statistics;

    // Top / bottom areas
    const sortedAreas = [...areas].sort((a, b) => b[1].avg_meter - a[1].avg_meter);
    const topArea = sortedAreas[0];
    const bottomArea = sortedAreas[sortedAreas.length - 1];

    // Top / bottom developers
    const sortedDevs = [...developers].sort((a, b) => b[1].avg_meter - a[1].avg_meter);
    const topDev = sortedDevs[0];
    const bottomDev = sortedDevs[sortedDevs.length - 1];

    // Top dev-loc combos
    const topDevLocs = [...devLocs].sort((a, b) => b.count - a.count).slice(0, 5);

    return (
        <SmartNav>
            <div className="h-full overflow-y-auto">
                <div className="p-4 sm:p-6 md:p-12 pb-24 md:pb-12">
                    <div className="max-w-7xl mx-auto space-y-8 md:space-y-12">

                        {/* ═══════════════════════════════════════════════════════
                            HEADER
                        ═══════════════════════════════════════════════════════ */}
                        <div className="space-y-4">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-xs font-bold uppercase tracking-wider">
                                <Activity size={12} /> 30 KPIs · Live Data
                            </div>
                            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                Market Statistics
                            </h1>
                            <p className="text-base sm:text-lg text-[var(--color-text-muted)] max-w-2xl">
                                Comprehensive price per meter analysis across areas, developers, and property categories.
                            </p>
                            {error && (
                                <div className="flex items-center gap-2 text-sm text-amber-500">
                                    <AlertCircle size={14} />
                                    {error}
                                </div>
                            )}
                        </div>

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 1: HERO SUMMARY (KPIs 1-4)
                        ═══════════════════════════════════════════════════════ */}
                        {loading ? <SkeletonGrid count={4} /> : data?.summary && (
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <HeroCard
                                    label="Total Properties"
                                    value={fmt(data.summary.total_properties)}
                                    unit="units"
                                    icon={Building2}
                                />
                                <HeroCard
                                    label="Avg Price/m²"
                                    value={fmt(data.summary.avg_meter)}
                                    unit="EGP"
                                    icon={BarChart3}
                                    accent
                                />
                                <HeroCard
                                    label="Market Floor /m²"
                                    value={fmt(data.summary.min_meter)}
                                    unit="EGP"
                                    icon={TrendingDown}
                                />
                                <HeroCard
                                    label="Market Ceiling /m²"
                                    value={fmt(data.summary.max_meter)}
                                    unit="EGP"
                                    icon={TrendingUp}
                                />
                            </div>
                        )}

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 2: PRICE/M² BY AREA (KPIs 5-10)
                        ═══════════════════════════════════════════════════════ */}
                        {!loading && areas.length > 0 && (
                            <div>
                                <SectionHeader
                                    icon={MapPin}
                                    title="Price per Meter — By Area"
                                    subtitle="Min, average, and max price/m² across locations"
                                    kpiRange="KPIs 5-10"
                                />

                                {/* Insight row */}
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                                    <InsightCard
                                        label="Most Expensive Area"
                                        value={topArea?.[0] || '—'}
                                        sublabel={topArea ? `${fmt(topArea[1].avg_meter)} EGP/m²` : undefined}
                                        icon={TrendingUp}
                                        color="amber"
                                    />
                                    <InsightCard
                                        label="Most Affordable Area"
                                        value={bottomArea?.[0] || '—'}
                                        sublabel={bottomArea ? `${fmt(bottomArea[1].avg_meter)} EGP/m²` : undefined}
                                        icon={TrendingDown}
                                        color="emerald"
                                    />
                                    <InsightCard
                                        label="Active Areas"
                                        value={`${data?.summary?.areas_count || areas.length}`}
                                        sublabel="locations tracked"
                                        icon={MapPin}
                                        color="blue"
                                    />
                                </div>

                                {/* Area table */}
                                <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
                                                    <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider">Area</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Min /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Avg /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Max /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Units</th>
                                                    <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider hidden lg:table-cell">Best Deal</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[var(--color-border)]">
                                                {sortedAreas.map(([name, stats], i) => {
                                                    const deal = data?.best_price_per_area?.[name];
                                                    return (
                                                        <tr key={name} className="hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                            <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">
                                                                <div className="flex items-center gap-2">
                                                                    <MapPin className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                                                                    {name}
                                                                </div>
                                                            </td>
                                                            <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.min_meter)}</td>
                                                            <td className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400 font-mono text-xs">{fmt(stats.avg_meter)}</td>
                                                            <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.max_meter)}</td>
                                                            <td className="px-4 py-3 text-right text-[var(--color-text-primary)] font-mono text-xs">{stats.count}</td>
                                                            <td className="px-4 py-3 text-left hidden lg:table-cell">
                                                                {deal ? (
                                                                    <span className="text-xs text-[var(--color-text-muted)]">
                                                                        {fmt(deal.price_per_sqm)}/m² — <span className="text-[var(--color-text-primary)]">{deal.compound || deal.developer}</span>
                                                                    </span>
                                                                ) : <span className="text-xs text-[var(--color-text-muted)]">—</span>}
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 3: PRICE/M² BY DEVELOPER (KPIs 11-16)
                        ═══════════════════════════════════════════════════════ */}
                        {!loading && developers.length > 0 && (
                            <div>
                                <SectionHeader
                                    icon={Building2}
                                    title="Price per Meter — By Developer"
                                    subtitle="Developer pricing breakdown with min/avg/max meter rates"
                                    kpiRange="KPIs 11-16"
                                />

                                {/* Insight row */}
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                                    <InsightCard
                                        label="Most Premium Developer"
                                        value={topDev?.[0] || '—'}
                                        sublabel={topDev ? `${fmt(topDev[1].avg_meter)} EGP/m²` : undefined}
                                        icon={Trophy}
                                        color="amber"
                                    />
                                    <InsightCard
                                        label="Most Affordable Developer"
                                        value={bottomDev?.[0] || '—'}
                                        sublabel={bottomDev ? `${fmt(bottomDev[1].avg_meter)} EGP/m²` : undefined}
                                        icon={Target}
                                        color="emerald"
                                    />
                                    <InsightCard
                                        label="Active Developers"
                                        value={`${data?.summary?.developers_count || developers.length}`}
                                        sublabel="in the market"
                                        icon={Users}
                                        color="violet"
                                    />
                                </div>

                                {/* Developer table */}
                                <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
                                                    <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider">Developer</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Min /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Avg /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Max /m²</th>
                                                    <th className="text-right px-4 py-3 font-semibold text-xs uppercase tracking-wider">Units</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[var(--color-border)]">
                                                {sortedDevs.map(([name, stats]) => (
                                                    <tr key={name} className="hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                        <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]">
                                                            <div className="flex items-center gap-2">
                                                                <Building2 className="w-3.5 h-3.5 text-[var(--color-text-muted)] flex-shrink-0" />
                                                                <span className="truncate max-w-[200px]">{name}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.min_meter)}</td>
                                                        <td className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400 font-mono text-xs">{fmt(stats.avg_meter)}</td>
                                                        <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.max_meter)}</td>
                                                        <td className="px-4 py-3 text-right text-[var(--color-text-primary)] font-mono text-xs">{stats.count}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 4: PRICE/M² BY PROPERTY TYPE (KPIs 17-20)
                        ═══════════════════════════════════════════════════════ */}
                        {!loading && types.length > 0 && (
                            <div>
                                <SectionHeader
                                    icon={Home}
                                    title="Price per Meter — By Category"
                                    subtitle="Property type pricing comparison"
                                    kpiRange="KPIs 17-20"
                                />
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {types.map(([type, stats]) => (
                                        <div key={type} className="p-5 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] hover:border-emerald-500/20 transition-colors">
                                            <div className="flex items-center justify-between mb-4">
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">{type}</span>
                                                <span className="text-[11px] font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-2 py-0.5 rounded-full">
                                                    {stats.count} units
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-3 gap-3">
                                                <div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Min</div>
                                                    <div className="text-sm font-bold text-[var(--color-text-primary)] font-mono">{fmt(stats.min_meter)}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-emerald-500 uppercase tracking-wider mb-1">Avg</div>
                                                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 font-mono">{fmt(stats.avg_meter)}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Max</div>
                                                    <div className="text-sm font-bold text-[var(--color-text-primary)] font-mono">{fmt(stats.max_meter)}</div>
                                                </div>
                                            </div>
                                            {/* Mini bar */}
                                            <div className="mt-3 h-1.5 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full"
                                                    style={{ width: `${Math.min((stats.avg_meter / (data?.summary?.max_meter || stats.max_meter)) * 100, 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 5: ROOM STATISTICS (KPIs 21-24)
                        ═══════════════════════════════════════════════════════ */}
                        {!loading && rooms.length > 0 && (
                            <div>
                                <SectionHeader
                                    icon={BedDouble}
                                    title="Room Statistics"
                                    subtitle="Price and size metrics by bedroom count"
                                    kpiRange="KPIs 21-24"
                                />
                                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                                    {rooms.map(([bedrooms, stats]) => (
                                        <div key={bedrooms} className="p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] text-center hover:border-emerald-500/20 transition-colors">
                                            <div className="text-2xl font-bold text-[var(--color-text-primary)] mb-1">
                                                {bedrooms === '0' ? 'Studio' : `${bedrooms} BR`}
                                            </div>
                                            <div className="space-y-2 mt-3">
                                                <div>
                                                    <div className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Units</div>
                                                    <div className="text-sm font-bold text-[var(--color-text-primary)]">{stats.count}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Avg Price</div>
                                                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmtM(stats.avg_price)}</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Avg Size</div>
                                                    <div className="text-xs font-medium text-[var(--color-text-primary)]">{Math.round(stats.avg_size_sqm)} m²</div>
                                                </div>
                                                <div>
                                                    <div className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Avg /m²</div>
                                                    <div className="text-xs font-medium text-[var(--color-text-muted)]">{fmt(stats.avg_meter)}</div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* ═══════════════════════════════════════════════════════
                            SECTION 6: MARKET INTELLIGENCE (KPIs 25-30)
                        ═══════════════════════════════════════════════════════ */}
                        {!loading && data && (
                            <div>
                                <SectionHeader
                                    icon={Sparkles}
                                    title="Market Intelligence"
                                    subtitle="Payment plans, finishing types, size brackets, and cross-analysis"
                                    kpiRange="KPIs 25-30"
                                />

                                {/* Row 1: Payment & Price Distribution */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

                                    {/* Payment Plan Stats */}
                                    {payment && payment.properties_with_plans > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <CreditCard className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Payment Plan Overview</span>
                                            </div>
                                            <div className="grid grid-cols-3 gap-4">
                                                <div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Avg Down Payment</div>
                                                    <div className="text-xl font-bold text-[var(--color-text-primary)]">{payment.avg_down_payment}%</div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)]">{payment.min_down_payment}% – {payment.max_down_payment}%</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Avg Installments</div>
                                                    <div className="text-xl font-bold text-[var(--color-text-primary)]">{payment.avg_installment_years} yrs</div>
                                                </div>
                                                <div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Avg Monthly</div>
                                                    <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{fmt(payment.avg_monthly_installment)}</div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)]">EGP/month</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Price Bracket Distribution */}
                                    {priceBrackets.length > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <DollarSign className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Price Distribution</span>
                                            </div>
                                            <div className="space-y-3">
                                                {priceBrackets.map(([label, bracket]) => {
                                                    const total = priceBrackets.reduce((sum, [, b]) => sum + b.count, 0);
                                                    const pct = total > 0 ? (bracket.count / total * 100) : 0;
                                                    return (
                                                        <div key={label}>
                                                            <div className="flex items-center justify-between mb-1">
                                                                <span className="text-xs font-medium text-[var(--color-text-primary)]">{label}</span>
                                                                <span className="text-xs text-[var(--color-text-muted)]">{bracket.count} units ({pct.toFixed(0)}%)</span>
                                                            </div>
                                                            <div className="h-2 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                                                                <div
                                                                    className="h-full bg-gradient-to-r from-emerald-600/60 to-emerald-400 rounded-full transition-all duration-700"
                                                                    style={{ width: `${pct}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Row 2: Finishing Types & Size Brackets */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

                                    {/* Finishing Type Stats */}
                                    {finishing.length > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <Paintbrush className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Finishing Type Analysis</span>
                                            </div>
                                            <div className="space-y-3">
                                                {finishing.map(([type, stats]) => (
                                                    <div key={type} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                        <div>
                                                            <span className="text-sm font-medium text-[var(--color-text-primary)]">{type}</span>
                                                            <span className="text-xs text-[var(--color-text-muted)] ml-2">({stats.count})</span>
                                                        </div>
                                                        <div className="flex items-center gap-4 font-mono text-xs">
                                                            <span className="text-[var(--color-text-muted)]">{fmt(stats.min_meter)}</span>
                                                            <span className="font-bold text-emerald-600 dark:text-emerald-400">{fmt(stats.avg_meter)}</span>
                                                            <span className="text-[var(--color-text-muted)]">{fmt(stats.max_meter)}</span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Size Bracket Stats */}
                                    {sizeBrackets.length > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <Ruler className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Size Bracket Analysis</span>
                                            </div>
                                            <div className="space-y-3">
                                                {sizeBrackets.map(([label, bracket]) => (
                                                    <div key={label} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                        <div>
                                                            <span className="text-sm font-medium text-[var(--color-text-primary)]">{label}</span>
                                                            <span className="text-xs text-[var(--color-text-muted)] ml-2">({bracket.count} units)</span>
                                                        </div>
                                                        <div className="text-right">
                                                            <div className="text-sm font-bold text-[var(--color-text-primary)]">{fmtM(bracket.avg_price)} EGP</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">{fmt(bracket.avg_meter)} /m²</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Row 3: Top Compounds & Developer-Location Cross */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                                    {/* Top Compounds */}
                                    {compounds.length > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <Layers className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Top Compounds by Volume</span>
                                            </div>
                                            <div className="space-y-2">
                                                {compounds.slice(0, 7).map((comp, i) => (
                                                    <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                        <div className="min-w-0 flex-1">
                                                            <div className="text-sm font-medium text-[var(--color-text-primary)] truncate">{comp.compound}</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">{comp.developer} · {comp.location}</div>
                                                        </div>
                                                        <div className="text-right flex-shrink-0 ml-3">
                                                            <div className="text-sm font-bold text-[var(--color-text-primary)]">{comp.count} units</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">{fmt(comp.avg_meter)} /m²</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Developer-Location Cross Analysis */}
                                    {topDevLocs.length > 0 && (
                                        <div className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                            <div className="flex items-center gap-2 mb-4">
                                                <BarChart3 className="w-4 h-4 text-emerald-500" />
                                                <span className="text-sm font-bold text-[var(--color-text-primary)]">Developer × Area Cross Analysis</span>
                                            </div>
                                            <div className="space-y-2">
                                                {topDevLocs.map((entry, i) => (
                                                    <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                        <div className="min-w-0 flex-1">
                                                            <div className="text-sm font-medium text-[var(--color-text-primary)] truncate">{entry.developer}</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)] flex items-center gap-1">
                                                                <MapPin className="w-2.5 h-2.5" /> {entry.location}
                                                            </div>
                                                        </div>
                                                        <div className="text-right flex-shrink-0 ml-3">
                                                            <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmt(entry.avg_meter)} /m²</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">{entry.count} units</div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Best Deals Row */}
                                {bestDeals.length > 0 && (
                                    <div className="mt-6 p-6 bg-[var(--color-surface)] rounded-2xl border border-emerald-500/20">
                                        <div className="flex items-center gap-2 mb-4">
                                            <Target className="w-4 h-4 text-emerald-500" />
                                            <span className="text-sm font-bold text-[var(--color-text-primary)]">Best Deals per Area</span>
                                            <span className="text-[10px] text-[var(--color-text-muted)]">Lowest price/m² property in each location</span>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                            {bestDeals.slice(0, 6).map(([area, deal]) => (
                                                <div key={area} className="p-3 bg-[var(--color-background)] rounded-xl">
                                                    <div className="text-xs font-semibold text-[var(--color-text-muted)] mb-1">{area}</div>
                                                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmt(deal.price_per_sqm)} EGP/m²</div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] mt-0.5 truncate">
                                                        {deal.compound || deal.developer} · {fmtM(deal.price)} EGP
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Footer */}
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-4 border-t border-[var(--color-border)]">
                            <p className="text-xs text-[var(--color-text-muted)]">
                                Data sourced from Osool property database · {data?.summary?.total_properties || 0} properties analyzed
                            </p>
                            <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                Live statistics
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </SmartNav>
    );
}
