'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Activity, BarChart3, MapPin, Building2, Home, Users, Layers,
    TrendingUp, TrendingDown,
    DollarSign, Ruler, BedDouble, CreditCard,
    Trophy, Target, AlertCircle, Sparkles, ChevronDown,
    PieChart
} from 'lucide-react';
import SmartNav from '@/components/SmartNav';
import { useLanguage } from '@/contexts/LanguageContext';
import {
    computeDetailedStats,
    type DetailedStats,
} from '@/lib/marketStats';

/* ---- animation variants ---- */
const containerV = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } },
};
const itemV = {
    hidden: { opacity: 0, y: 20, scale: 0.97 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] as const } },
};
const slideUp = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } },
};

/* ---- utilities ---- */
const fmt = (n: number) => Math.round(n).toLocaleString();
const fmtM = (n: number) => (n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : fmt(n));

function AnimatedNumber({ value }: { value: number }) {
    const [display, setDisplay] = useState(0);
    useEffect(() => {
        let s = 0;
        const end = Math.round(value);
        if (end === 0) { setDisplay(0); return; }
        const dur = 1200;
        const st = Math.max(Math.floor(dur / Math.min(end, 60)), 16);
        const step = Math.max(Math.ceil(end / (dur / st)), 1);
        const t = setInterval(() => { s += step; if (s >= end) { setDisplay(end); clearInterval(t); } else setDisplay(s); }, st);
        return () => clearInterval(t);
    }, [value]);
    return <>{fmt(display)}</>;
}

/* ---- sub-components ---- */
function SectionHeader({ icon: Icon, title, subtitle, kpiRange }: { icon: any; title: string; subtitle: string; kpiRange: string }) {
    return (
        <motion.div variants={slideUp} className="flex items-start gap-3 mb-6 flex-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/5">
                <Icon className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-lg font-bold text-[var(--color-text-primary)]">{title}</h2>
                    <span className="text-[10px] font-mono text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">{kpiRange}</span>
                </div>
                <p className="text-sm text-[var(--color-text-muted)] mt-0.5">{subtitle}</p>
            </div>
        </motion.div>
    );
}

function HeroCard({ label, value, unit, icon: Icon, accent = false }: { label: string; value: number; unit?: string; icon: any; accent?: boolean }) {
    return (
        <motion.div variants={itemV} whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`relative overflow-hidden p-5 rounded-2xl border transition-all group cursor-default ${accent ? 'bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent border-emerald-500/20' : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-emerald-500/20'}`}>
            {accent && <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-emerald-500/10 blur-2xl" />}
            <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${accent ? 'bg-emerald-500/15 text-emerald-500' : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] group-hover:text-emerald-500'}`}>
                        <Icon className="w-4 h-4" />
                    </div>
                </div>
                <div className="flex items-baseline gap-1.5">
                    <span className={`text-2xl font-bold ${accent ? 'text-emerald-500' : 'text-[var(--color-text-primary)]'}`}><AnimatedNumber value={value} /></span>
                    {unit && <span className="text-sm text-[var(--color-text-muted)]">{unit}</span>}
                </div>
            </div>
        </motion.div>
    );
}

function InsightCard({ label, value, sublabel, icon: Icon, color = 'emerald' }: { label: string; value: string; sublabel?: string; icon: any; color?: string }) {
    const cm: Record<string, string> = { emerald: 'bg-emerald-500/10 text-emerald-500', amber: 'bg-amber-500/10 text-amber-500', blue: 'bg-blue-500/10 text-blue-500', violet: 'bg-violet-500/10 text-violet-500' };
    return (
        <motion.div variants={itemV} whileHover={{ scale: 1.02 }} className="p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] hover:border-emerald-500/20 transition-all">
            <div className="flex items-center gap-2 mb-2">
                <div className={`w-6 h-6 rounded-md flex items-center justify-center ${cm[color] || cm.emerald}`}><Icon className="w-3.5 h-3.5" /></div>
                <span className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
            </div>
            <div className="text-lg font-bold text-[var(--color-text-primary)]">{value}</div>
            {sublabel && <div className="text-xs text-[var(--color-text-muted)] mt-0.5">{sublabel}</div>}
        </motion.div>
    );
}

function AnimatedBar({ pct, delay = 0, color = 'emerald' }: { pct: number; delay?: number; color?: string }) {
    const g: Record<string, string> = { emerald: 'from-emerald-600 to-emerald-400', amber: 'from-amber-600 to-amber-400', blue: 'from-blue-600 to-blue-400', violet: 'from-violet-600 to-violet-400', rose: 'from-rose-600 to-rose-400' };
    return (
        <div className="h-2 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
            <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(pct, 100)}%` }} transition={{ duration: 1, delay, ease: 'easeOut' as const }}
                className={`h-full bg-gradient-to-r ${g[color] || g.emerald} rounded-full`} />
        </div>
    );
}

function SkeletonGrid() {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[0, 1, 2, 3].map(i => <div key={i} className="h-28 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] animate-pulse" />)}
        </div>
    );
}

function MiniSparkline({ min, avg, max, gMax }: { min: number; avg: number; max: number; gMax: number }) {
    const h = 32, w = 80;
    const s = (v: number) => h - (v / gMax) * h * 0.85;
    return (
        <svg width={w} height={h} className="opacity-40">
            <polyline fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                points={`0,${s(min)} ${w * 0.5},${s(avg)} ${w},${s(max)}`} className="text-emerald-500" />
            <circle cx={w * 0.5} cy={s(avg)} r="3" className="fill-emerald-500" />
        </svg>
    );
}

/* ---- MAIN PAGE ---- */
export default function MarketStatisticsPage() {
    const { t, language } = useLanguage();
    const [data, setData] = useState<DetailedStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [exp, setExp] = useState<Record<string, boolean>>({ area: true, developer: true, type: true, rooms: true, intel: true });
    const toggle = (k: string) => setExp(p => ({ ...p, [k]: !p[k] }));

    useEffect(() => {
        (async () => {
            try {
                setLoading(true);
                const res = await fetch('/assets/js/data.js');
                const txt = await res.text();
                // Fast parse: find the JSON object start/end without heavy regex
                const start = txt.indexOf('{');
                const end = txt.lastIndexOf('}');
                if (start === -1 || end === -1) throw new Error('parse');
                const raw = JSON.parse(txt.substring(start, end + 1));
                const props = raw.properties || [];
                if (!props.length) throw new Error('empty');
                setData(computeDetailedStats(props));
            } catch (e) {
                console.error(e);
                setError('Unable to load statistics. Retrying...');
                setTimeout(async () => {
                    try {
                        const res = await fetch('/assets/js/data.js');
                        const txt = await res.text();
                        const start = txt.indexOf('{');
                        const end = txt.lastIndexOf('}');
                        if (start !== -1 && end !== -1) {
                            const raw = JSON.parse(txt.substring(start, end + 1));
                            setData(computeDetailedStats(raw.properties || []));
                            setError(null);
                        }
                    } catch { /* noop */ }
                }, 2000);
            } finally { setLoading(false); }
        })();
    }, []);

    const areas = data?.meter_price_by_area ? Object.entries(data.meter_price_by_area) : [];
    const developers = data?.meter_price_by_developer ? Object.entries(data.meter_price_by_developer) : [];
    const types = data?.meter_price_by_type ? Object.entries(data.meter_price_by_type) : [];
    const rooms = data?.room_statistics ? Object.entries(data.room_statistics).sort(([a], [b]) => +a - +b) : [];
    const devLocs = data?.developer_by_location ? Object.values(data.developer_by_location) : [];
    const compounds = data?.top_compounds || [];
    const sizeBrackets = data?.size_bracket_statistics ? Object.entries(data.size_bracket_statistics) : [];
    const priceBrackets = data?.price_bracket_distribution ? Object.entries(data.price_bracket_distribution) : [];
    const bestDeals = data?.best_price_per_area ? Object.entries(data.best_price_per_area) : [];
    const payment = data?.payment_statistics;

    const sortedAreas = [...areas].sort((a, b) => b[1].avg_meter - a[1].avg_meter);
    const topArea = sortedAreas[0];
    const bottomArea = sortedAreas[sortedAreas.length - 1];
    const sortedDevs = [...developers].sort((a, b) => b[1].avg_meter - a[1].avg_meter);
    const topDev = sortedDevs[0];
    const bottomDev = sortedDevs[sortedDevs.length - 1];
    const topDevLocs = [...devLocs].sort((a, b) => b.count - a.count).slice(0, 5);
    const sortedTypes = [...types].sort((a, b) => b[1].count - a[1].count);
    const orderedPB = useMemo(() => {
        const o = ['Under 2M EGP', '2M \u2013 5M EGP', '5M \u2013 10M EGP', '10M \u2013 20M EGP', '20M \u2013 50M EGP', 'Over 50M EGP'];
        return [...priceBrackets].sort((a, b) => o.indexOf(a[0]) - o.indexOf(b[0]));
    }, [priceBrackets]);

    return (
        <SmartNav>
            <div className="h-full overflow-y-auto">
                <div className="p-4 sm:p-6 md:p-12 pb-24 md:pb-12">
                    <motion.div className="max-w-7xl mx-auto space-y-8 md:space-y-12" initial="hidden" animate="visible" variants={containerV}>

                        {/* HEADER */}
                        <motion.div variants={slideUp} className="space-y-4">
                            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}
                                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-emerald-500/15 to-teal-500/10 text-emerald-500 text-xs font-bold uppercase tracking-wider border border-emerald-500/20">
                                <Activity size={12} className="animate-pulse" />
                                30+ KPIs &middot; {data?.summary?.total_properties?.toLocaleString() || '...'} Properties &middot; Live
                            </motion.div>
                            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                {t('market.title')} <span className="bg-gradient-to-r from-emerald-500 to-teal-400 bg-clip-text text-transparent">{t('market.intelligence')}</span>
                            </h1>
                            <p className="text-base sm:text-lg text-[var(--color-text-muted)] max-w-2xl">
                                {t('market.subtitle')} &mdash; {t('market.computedFrom')} {data?.summary?.total_properties?.toLocaleString() || '...'} {t('market.properties')}.
                            </p>
                            {error && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2 text-sm text-amber-500"><AlertCircle size={14} />{error}</motion.div>}
                        </motion.div>

                        {/* HERO KPIs */}
                        {loading ? <SkeletonGrid /> : data?.summary && (
                            <motion.div variants={containerV} className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <HeroCard label={t('market.totalProperties')} value={data.summary.total_properties} unit={t('market.units')} icon={Building2} />
                                <HeroCard label={t('market.avgPriceSqm')} value={data.summary.avg_meter} unit="EGP" icon={BarChart3} accent />
                                <HeroCard label={t('market.marketFloor')} value={data.summary.min_meter} unit="EGP" icon={TrendingDown} />
                                <HeroCard label={t('market.marketCeiling')} value={data.summary.max_meter} unit="EGP" icon={TrendingUp} />
                            </motion.div>
                        )}

                        {/* Quick Stats */}
                        {!loading && data?.summary && (
                            <motion.div variants={slideUp} className="grid grid-cols-3 gap-3">
                                {[
                                    { icon: MapPin, color: 'blue', val: String(data.summary.areas_count), lbl: t('market.areas') },
                                    { icon: Home, color: 'violet', val: String(data.summary.types_count), lbl: t('market.types') },
                                    { icon: DollarSign, color: 'amber', val: fmtM(data.summary.avg_price), lbl: t('market.avgPrice') },
                                ].map(({ icon: Ic, color, val, lbl }) => (
                                    <div key={lbl} className="p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center gap-3">
                                        <div className={`w-8 h-8 rounded-lg bg-${color}-500/10 flex items-center justify-center`}><Ic className={`w-4 h-4 text-${color}-500`} /></div>
                                        <div><div className="text-lg font-bold text-[var(--color-text-primary)]">{val}</div><div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{lbl}</div></div>
                                    </div>
                                ))}
                            </motion.div>
                        )}

                        {/* S2: BY AREA */}
                        {!loading && areas.length > 0 && (
                            <motion.div variants={slideUp}>
                                <button onClick={() => toggle('area')} className="w-full flex items-center justify-between">
                                    <SectionHeader icon={MapPin} title={t('market.byArea')} subtitle={t('market.byAreaSub')} kpiRange="KPIs 5-10" />
                                    <motion.div animate={{ rotate: exp.area ? 180 : 0 }} className="text-[var(--color-text-muted)]"><ChevronDown className="w-5 h-5" /></motion.div>
                                </button>
                                <AnimatePresence>{exp.area && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                                        <motion.div variants={containerV} className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                                            <InsightCard label={t('market.mostExpensive')} value={topArea?.[0] || '\u2014'} sublabel={topArea ? `${fmt(topArea[1].avg_meter)} EGP/m\u00B2` : undefined} icon={TrendingUp} color="amber" />
                                            <InsightCard label={t('market.mostAffordable')} value={bottomArea?.[0] || '\u2014'} sublabel={bottomArea ? `${fmt(bottomArea[1].avg_meter)} EGP/m\u00B2` : undefined} icon={TrendingDown} color="emerald" />
                                            <InsightCard label={t('market.activeAreas')} value={`${data?.summary?.areas_count || areas.length}`} sublabel={t('market.locationsTracked')} icon={MapPin} color="blue" />
                                        </motion.div>
                                        <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead><tr className="bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
                                                        {['Area', 'Min /m\u00B2', 'Avg /m\u00B2', 'Max /m\u00B2', 'Units'].map(h => (
                                                            <th key={h} className={`${h === 'Area' ? 'text-left' : 'text-right'} px-4 py-3 font-semibold text-xs uppercase tracking-wider`}>{h}</th>
                                                        ))}
                                                        <th className="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider hidden lg:table-cell">Best Deal</th>
                                                    </tr></thead>
                                                    <tbody className="divide-y divide-[var(--color-border)]">
                                                        {sortedAreas.map(([name, stats], i) => {
                                                            const deal = data?.best_price_per_area?.[name];
                                                            return (
                                                                <motion.tr key={name} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                                    <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]"><div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500" />{name}</div></td>
                                                                    <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.min_meter)}</td>
                                                                    <td className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400 font-mono text-xs">{fmt(stats.avg_meter)}</td>
                                                                    <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.max_meter)}</td>
                                                                    <td className="px-4 py-3 text-right text-[var(--color-text-primary)] font-mono text-xs">{stats.count}</td>
                                                                    <td className="px-4 py-3 text-left hidden lg:table-cell">{deal ? <span className="text-xs text-[var(--color-text-muted)]">{fmt(deal.price_per_sqm)}/m&sup2; &mdash; <span className="text-emerald-500 font-medium">{deal.compound || deal.developer}</span></span> : <span className="text-xs text-[var(--color-text-muted)]">&mdash;</span>}</td>
                                                                </motion.tr>
                                                            );
                                                        })}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}</AnimatePresence>
                            </motion.div>
                        )}

                        {/* S3: BY DEVELOPER */}
                        {!loading && developers.length > 0 && (
                            <motion.div variants={slideUp}>
                                <button onClick={() => toggle('developer')} className="w-full flex items-center justify-between">
                                    <SectionHeader icon={Building2} title={t('market.byDeveloper')} subtitle={t('market.byDeveloperSub')} kpiRange="KPIs 11-16" />
                                    <motion.div animate={{ rotate: exp.developer ? 180 : 0 }} className="text-[var(--color-text-muted)]"><ChevronDown className="w-5 h-5" /></motion.div>
                                </button>
                                <AnimatePresence>{exp.developer && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                                        <motion.div variants={containerV} className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
                                            <InsightCard label={t('market.mostPremium')} value={topDev?.[0] || '\u2014'} sublabel={topDev ? `${fmt(topDev[1].avg_meter)} EGP/m\u00B2` : undefined} icon={Trophy} color="amber" />
                                            <InsightCard label={t('market.mostAffordable')} value={bottomDev?.[0] || '\u2014'} sublabel={bottomDev ? `${fmt(bottomDev[1].avg_meter)} EGP/m\u00B2` : undefined} icon={Target} color="emerald" />
                                            <InsightCard label={t('market.activeDevelopers')} value={`${data?.summary?.developers_count || developers.length}`} sublabel={t('market.inTheMarket')} icon={Users} color="violet" />
                                        </motion.div>
                                        <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead><tr className="bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
                                                        {['Developer', 'Min /m\u00B2', 'Avg /m\u00B2', 'Max /m\u00B2', 'Units'].map(h => (
                                                            <th key={h} className={`${h === 'Developer' ? 'text-left' : 'text-right'} px-4 py-3 font-semibold text-xs uppercase tracking-wider`}>{h}</th>
                                                        ))}
                                                    </tr></thead>
                                                    <tbody className="divide-y divide-[var(--color-border)]">
                                                        {sortedDevs.map(([name, stats], i) => (
                                                            <motion.tr key={name} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                                <td className="px-4 py-3 font-medium text-[var(--color-text-primary)]"><div className="flex items-center gap-2"><Building2 className="w-3.5 h-3.5 text-[var(--color-text-muted)]" /><span className="truncate max-w-[200px]">{name}</span></div></td>
                                                                <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.min_meter)}</td>
                                                                <td className="px-4 py-3 text-right font-bold text-emerald-600 dark:text-emerald-400 font-mono text-xs">{fmt(stats.avg_meter)}</td>
                                                                <td className="px-4 py-3 text-right text-[var(--color-text-muted)] font-mono text-xs">{fmt(stats.max_meter)}</td>
                                                                <td className="px-4 py-3 text-right text-[var(--color-text-primary)] font-mono text-xs">{stats.count}</td>
                                                            </motion.tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}</AnimatePresence>
                            </motion.div>
                        )}

                        {/* S4: BY TYPE */}
                        {!loading && types.length > 0 && (
                            <motion.div variants={slideUp}>
                                <button onClick={() => toggle('type')} className="w-full flex items-center justify-between">
                                    <SectionHeader icon={Home} title={t('market.byCategory')} subtitle={t('market.byCategorySub')} kpiRange="KPIs 17-20" />
                                    <motion.div animate={{ rotate: exp.type ? 180 : 0 }} className="text-[var(--color-text-muted)]"><ChevronDown className="w-5 h-5" /></motion.div>
                                </button>
                                <AnimatePresence>{exp.type && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                            {sortedTypes.map(([type, stats], i) => (
                                                <motion.div key={type} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} whileHover={{ y: -3 }}
                                                    className="p-5 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] hover:border-emerald-500/20 transition-all">
                                                    <div className="flex items-center justify-between mb-4">
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{type}</span>
                                                        <span className="text-[11px] font-mono text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">{stats.count} units</span>
                                                    </div>
                                                    <div className="flex items-end justify-between">
                                                        <div className="grid grid-cols-3 gap-3 flex-1">
                                                            <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">Min</div><div className="text-sm font-bold text-[var(--color-text-primary)] font-mono">{fmt(stats.min_meter)}</div></div>
                                                            <div><div className="text-[10px] text-emerald-500 uppercase mb-1">Avg</div><div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 font-mono">{fmt(stats.avg_meter)}</div></div>
                                                            <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">Max</div><div className="text-sm font-bold text-[var(--color-text-primary)] font-mono">{fmt(stats.max_meter)}</div></div>
                                                        </div>
                                                        <MiniSparkline min={stats.min_meter} avg={stats.avg_meter} max={stats.max_meter} gMax={data?.summary?.max_meter || stats.max_meter} />
                                                    </div>
                                                    <div className="mt-3"><AnimatedBar pct={(stats.avg_meter / (data?.summary?.max_meter || stats.max_meter)) * 100} delay={i * 0.1} /></div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}</AnimatePresence>
                            </motion.div>
                        )}

                        {/* S5: ROOMS */}
                        {!loading && rooms.length > 0 && (
                            <motion.div variants={slideUp}>
                                <button onClick={() => toggle('rooms')} className="w-full flex items-center justify-between">
                                    <SectionHeader icon={BedDouble} title={t('market.roomStats')} subtitle={t('market.roomStatsSub')} kpiRange="KPIs 21-24" />
                                    <motion.div animate={{ rotate: exp.rooms ? 180 : 0 }} className="text-[var(--color-text-muted)]"><ChevronDown className="w-5 h-5" /></motion.div>
                                </button>
                                <AnimatePresence>{exp.rooms && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
                                            {rooms.filter(([b]) => +b <= 7).map(([bedrooms, stats], i) => (
                                                <motion.div key={bedrooms} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.06 }} whileHover={{ y: -3, scale: 1.02 }}
                                                    className="p-4 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] text-center hover:border-emerald-500/20 transition-all">
                                                    <div className="text-2xl font-bold text-[var(--color-text-primary)] mb-1">{bedrooms === '0' ? 'Studio' : `${bedrooms} BR`}</div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] mb-3">{stats.count} units</div>
                                                    <div className="space-y-2">
                                                        <div><div className="text-[9px] text-[var(--color-text-muted)] uppercase">Avg Price</div><div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmtM(stats.avg_price)}</div></div>
                                                        {stats.avg_size_sqm > 0 && <div><div className="text-[9px] text-[var(--color-text-muted)] uppercase">Avg Size</div><div className="text-xs font-medium text-[var(--color-text-primary)]">{Math.round(stats.avg_size_sqm)} m&sup2;</div></div>}
                                                        <div><div className="text-[9px] text-[var(--color-text-muted)] uppercase">Avg /m&sup2;</div><div className="text-xs font-medium text-[var(--color-text-muted)]">{fmt(stats.avg_meter)}</div></div>
                                                    </div>
                                                    <div className="mt-3"><AnimatedBar pct={(stats.count / Math.max(...rooms.map(([, s]) => s.count))) * 100} delay={i * 0.1} color={bedrooms === '0' ? 'violet' : 'emerald'} /></div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}</AnimatePresence>
                            </motion.div>
                        )}

                        {/* S6: MARKET INTELLIGENCE */}
                        {!loading && data && (
                            <motion.div variants={slideUp}>
                                <button onClick={() => toggle('intel')} className="w-full flex items-center justify-between">
                                    <SectionHeader icon={Sparkles} title={t('market.marketIntel')} subtitle={t('market.marketIntelSub')} kpiRange="KPIs 25-30" />
                                    <motion.div animate={{ rotate: exp.intel ? 180 : 0 }} className="text-[var(--color-text-muted)]"><ChevronDown className="w-5 h-5" /></motion.div>
                                </button>
                                <AnimatePresence>{exp.intel && (
                                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }}>
                                        {/* Payment + Price Distribution */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                            {payment && payment.properties_with_plans > 0 && (
                                                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] hover:border-emerald-500/20 transition-all">
                                                    <div className="flex items-center gap-2 mb-5">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/10 flex items-center justify-center"><CreditCard className="w-4 h-4 text-emerald-500" /></div>
                                                        <div><span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.paymentOverview')}</span><div className="text-[10px] text-[var(--color-text-muted)]">{payment.properties_with_plans.toLocaleString()} {t('market.withPlans')}</div></div>
                                                    </div>
                                                    <div className="grid grid-cols-3 gap-4">
                                                        <div className="text-center p-3 rounded-xl bg-[var(--color-background)]">
                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{t('market.avgDown')}</div>
                                                            <div className="text-xl font-bold text-[var(--color-text-primary)]">{payment.avg_down_payment}%</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">{payment.min_down_payment}% &ndash; {payment.max_down_payment}%</div>
                                                        </div>
                                                        <div className="text-center p-3 rounded-xl bg-[var(--color-background)]">
                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{t('market.installments')}</div>
                                                            <div className="text-xl font-bold text-[var(--color-text-primary)]">{payment.avg_installment_years} yrs</div>
                                                        </div>
                                                        <div className="text-center p-3 rounded-xl bg-[var(--color-background)]">
                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{t('market.monthly')}</div>
                                                            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{fmt(payment.avg_monthly_installment)}</div>
                                                            <div className="text-[10px] text-[var(--color-text-muted)]">EGP/mo</div>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}
                                            {orderedPB.length > 0 && (
                                                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] hover:border-emerald-500/20 transition-all">
                                                    <div className="flex items-center gap-2 mb-5">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-indigo-500/10 flex items-center justify-center"><PieChart className="w-4 h-4 text-blue-500" /></div>
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.priceDistribution')}</span>
                                                    </div>
                                                    <div className="space-y-3">
                                                        {orderedPB.map(([label, bracket], idx) => {
                                                            const total = orderedPB.reduce((s, [, b]) => s + b.count, 0);
                                                            const p = total > 0 ? (bracket.count / total * 100) : 0;
                                                            const cls = ['emerald', 'blue', 'violet', 'amber', 'rose', 'emerald'];
                                                            return (<div key={label}><div className="flex items-center justify-between mb-1"><span className="text-xs font-medium text-[var(--color-text-primary)]">{label}</span><span className="text-xs text-[var(--color-text-muted)]">{bracket.count} ({p.toFixed(0)}%)</span></div><AnimatedBar pct={p} delay={idx * 0.1} color={cls[idx % cls.length]} /></div>);
                                                        })}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>

                                        {/* Size + Compounds */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                            {sizeBrackets.length > 0 && (
                                                <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                                    <div className="flex items-center gap-2 mb-4">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-purple-500/10 flex items-center justify-center"><Ruler className="w-4 h-4 text-violet-500" /></div>
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.sizeBracket')}</span>
                                                    </div>
                                                    <div className="space-y-3">
                                                        {sizeBrackets.map(([label, bracket]) => (
                                                            <div key={label} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                                <div><span className="text-sm font-medium text-[var(--color-text-primary)]">{label}</span><span className="text-xs text-[var(--color-text-muted)] ml-2">({bracket.count})</span></div>
                                                                <div className="text-right"><div className="text-sm font-bold text-[var(--color-text-primary)]">{fmtM(bracket.avg_price)} EGP</div><div className="text-[10px] text-[var(--color-text-muted)]">{fmt(bracket.avg_meter)} /m&sup2;</div></div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                            {compounds.length > 0 && (
                                                <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                                    <div className="flex items-center gap-2 mb-4">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500/20 to-orange-500/10 flex items-center justify-center"><Layers className="w-4 h-4 text-amber-500" /></div>
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.topCompounds')}</span>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {compounds.slice(0, 7).map((comp, i) => (
                                                            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 + i * 0.05 }}
                                                                className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                                <div className="min-w-0 flex-1">
                                                                    <div className="flex items-center gap-2">
                                                                        <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0">{i + 1}</span>
                                                                        <div className="text-sm font-medium text-[var(--color-text-primary)] truncate">{comp.compound}</div>
                                                                    </div>
                                                                    <div className="text-[10px] text-[var(--color-text-muted)] ml-7">{comp.location}</div>
                                                                </div>
                                                                <div className="text-right flex-shrink-0 ml-3">
                                                                    <div className="text-sm font-bold text-[var(--color-text-primary)]">{comp.count} units</div>
                                                                    <div className="text-[10px] text-emerald-500">{fmt(comp.avg_meter)} /m&sup2;</div>
                                                                </div>
                                                            </motion.div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>

                                        {/* Dev-Loc + Best Deals */}
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                            {topDevLocs.length > 0 && (
                                                <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)]">
                                                    <div className="flex items-center gap-2 mb-4">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/10 flex items-center justify-center"><BarChart3 className="w-4 h-4 text-blue-500" /></div>
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.developerArea')}</span>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {topDevLocs.map((entry, i) => (
                                                            <div key={i} className="flex items-center justify-between py-2 border-b border-[var(--color-border)] last:border-0">
                                                                <div className="min-w-0 flex-1"><div className="text-sm font-medium text-[var(--color-text-primary)] truncate">{entry.developer}</div><div className="text-[10px] text-[var(--color-text-muted)] flex items-center gap-1"><MapPin className="w-2.5 h-2.5" />{entry.location}</div></div>
                                                                <div className="text-right flex-shrink-0 ml-3"><div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmt(entry.avg_meter)} /m&sup2;</div><div className="text-[10px] text-[var(--color-text-muted)]">{entry.count} units</div></div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                            {bestDeals.length > 0 && (
                                                <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}
                                                    className="p-6 bg-[var(--color-surface)] rounded-2xl border border-emerald-500/20">
                                                    <div className="flex items-center gap-2 mb-4">
                                                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-500/10 flex items-center justify-center"><Target className="w-4 h-4 text-emerald-500" /></div>
                                                        <div><span className="text-sm font-bold text-[var(--color-text-primary)]">{t('market.bestDeals')}</span><div className="text-[10px] text-[var(--color-text-muted)]">{t('market.bestDealsSubtitle')}</div></div>
                                                    </div>
                                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                        {bestDeals.slice(0, 6).map(([area, deal], i) => (
                                                            <motion.div key={area} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.6 + i * 0.08 }}
                                                                className="p-3 bg-[var(--color-background)] rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                                <div className="text-xs font-semibold text-[var(--color-text-muted)] mb-1">{area}</div>
                                                                <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">{fmt(deal.price_per_sqm)} EGP/m&sup2;</div>
                                                                <div className="text-[10px] text-[var(--color-text-muted)] mt-0.5 truncate">{deal.compound || deal.developer} &middot; {fmtM(deal.price)} EGP</div>
                                                            </motion.div>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </div>
                                    </motion.div>
                                )}</AnimatePresence>
                            </motion.div>
                        )}

                        {/* Footer */}
                        <motion.div variants={slideUp} className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-6 border-t border-[var(--color-border)]">
                            <p className="text-xs text-[var(--color-text-muted)]">{t('market.dataSourced')} &middot; {data?.summary?.total_properties?.toLocaleString() || 0} {t('market.propertiesAnalyzed')}</p>
                            <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                                <motion.div animate={{ scale: [1, 1.3, 1] }} transition={{ repeat: Infinity, duration: 2 }} className="w-2 h-2 rounded-full bg-emerald-500" />
                                {t('market.liveStats')}
                            </div>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </SmartNav>
    );
}
