'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    TrendingUp, TrendingDown, Sparkles, X, Activity,
    Shield, Building2, Eye, ChevronRight, Star, StarOff,
    Zap, BarChart3, ArrowUpRight, ArrowDownRight, Minus,
} from 'lucide-react';

/* ── Types ── */
interface MarketTrend {
    id: string;
    area: string;
    areaAr: string;
    type: string;
    change: number;
    avgPriceSqm: number;
    demand: 'High' | 'Medium' | 'Low';
    trend7d: number[];
}

interface AIInsight {
    id: string;
    title: string;
    titleAr: string;
    body: string;
    bodyAr: string;
    prompt: string;
    promptAr: string;
    tag: string;
}

interface VerificationEvent {
    id: string;
    text: string;
    textAr: string;
    timestamp: string;
}

interface MarketPulseSidebarProps {
    language: string;
    onPrompt: (prompt: string) => void;
}

/* ── Sparkline Component ── */
const Sparkline = ({ data, positive }: { data: number[], positive: boolean }) => {
    if (!data || data.length < 2) return null;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    const h = 24;
    const w = 56;
    const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`).join(' ');
    return (
        <svg width={w} height={h} className="flex-shrink-0">
            <polyline
                points={points}
                fill="none"
                stroke={positive ? '#10b981' : '#ef4444'}
                strokeWidth={1.5}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
};

/* ── Static Market Data (replaced with API when available) ── */
const MARKET_TRENDS: MarketTrend[] = [
    { id: '1', area: 'New Cairo', areaAr: 'القاهرة الجديدة', type: 'Residential', change: 2.4, avgPriceSqm: 62842, demand: 'High', trend7d: [60200, 60800, 61100, 61550, 62100, 62500, 62842] },
    { id: '2', area: 'Sheikh Zayed', areaAr: 'الشيخ زايد', type: 'Residential', change: -0.3, avgPriceSqm: 46859, demand: 'Medium', trend7d: [47200, 47100, 47050, 47000, 46950, 46900, 46859] },
    { id: '3', area: 'North Coast', areaAr: 'الساحل الشمالي', type: 'Resort', change: 5.1, avgPriceSqm: 38500, demand: 'High', trend7d: [35800, 36200, 36900, 37400, 37800, 38100, 38500] },
    { id: '4', area: '6th October', areaAr: '٦ أكتوبر', type: 'Mixed', change: 1.2, avgPriceSqm: 41200, demand: 'Medium', trend7d: [40500, 40600, 40800, 40900, 41000, 41100, 41200] },
    { id: '5', area: 'New Capital', areaAr: 'العاصمة الإدارية', type: 'Residential', change: 3.8, avgPriceSqm: 29500, demand: 'High', trend7d: [27800, 28100, 28500, 28900, 29100, 29300, 29500] },
];

const AI_INSIGHTS: AIInsight[] = [
    {
        id: '1',
        title: 'North Coast ROI Spike',
        titleAr: 'ارتفاع عوائد الساحل الشمالي',
        body: '3 new developer launches in the North Coast are showing unusually high projected ROIs vs. the 12-month average.',
        bodyAr: '٣ مشاريع جديدة في الساحل الشمالي تظهر عوائد استثمارية أعلى من المتوسط بنسبة ملحوظة.',
        prompt: 'Give me a deep dive into the recent ROI changes in the North Coast and which new launches are driving them',
        promptAr: 'أعطيني تحليل معمق عن التغيرات الأخيرة في عوائد الاستثمار في الساحل الشمالي وأي المشاريع الجديدة اللي بتحركها',
        tag: 'Opportunity',
    },
    {
        id: '2',
        title: 'New Capital Price Momentum',
        titleAr: 'زخم أسعار العاصمة الإدارية',
        body: 'Residential prices in the New Administrative Capital have risen 3.8% this week — fastest weekly gain in 6 months.',
        bodyAr: 'أسعار السكني في العاصمة الإدارية ارتفعت ٣.٨٪ هذا الأسبوع — أسرع ارتفاع أسبوعي في ٦ أشهر.',
        prompt: 'Analyze the New Administrative Capital price momentum and whether this growth rate is sustainable',
        promptAr: 'حلل زخم الأسعار في العاصمة الإدارية وهل معدل النمو ده مستدام',
        tag: 'Alert',
    },
];

const VERIFICATION_EVENTS: VerificationEvent[] = [
    { id: '1', text: 'Smart Contract Verified: 12 Units at Palm Hills', textAr: 'عقد ذكي موثق: ١٢ وحدة في بالم هيلز', timestamp: '2m ago' },
    { id: '2', text: 'Ownership Tokenized: 3 Fractional Shares at Sodic', textAr: 'ملكية مُرمّزة: ٣ حصص في سوديك', timestamp: '8m ago' },
    { id: '3', text: 'Contract Verified: Mountain View iCity', textAr: 'عقد موثق: ماونتن فيو آي سيتي', timestamp: '15m ago' },
];

/* ── Main Component ── */
export default function MarketPulseSidebar({ language, onPrompt }: MarketPulseSidebarProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [watchlist, setWatchlist] = useState<Set<string>>(() => {
        if (typeof window === 'undefined') return new Set<string>();
        try {
            const saved = localStorage.getItem('osool_watchlist');
            return saved ? new Set(JSON.parse(saved)) : new Set<string>();
        } catch { return new Set<string>(); }
    });

    const isAr = language === 'ar';

    useEffect(() => {
        try { localStorage.setItem('osool_watchlist', JSON.stringify([...watchlist])); } catch {}
    }, [watchlist]);

    const toggleWatchlist = useCallback((id: string) => {
        setWatchlist(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id); else next.add(id);
            return next;
        });
    }, []);

    const handleTrendClick = useCallback((trend: MarketTrend) => {
        const prompt = isAr
            ? `أعطيني تحليل معمق عن التغيرات الأخيرة في أسعار ${trend.areaAr} (${trend.type})`
            : `Give me a deep dive into the recent price changes in ${trend.area} (${trend.type})`;
        onPrompt(prompt);
        setIsOpen(false);
    }, [isAr, onPrompt]);

    const handleInsightClick = useCallback((insight: AIInsight) => {
        onPrompt(isAr ? insight.promptAr : insight.prompt);
        setIsOpen(false);
    }, [isAr, onPrompt]);

    const demandColor = (d: string) => {
        switch (d) {
            case 'High': return 'text-emerald-500 bg-emerald-500/10';
            case 'Medium': return 'text-amber-500 bg-amber-500/10';
            default: return 'text-slate-400 bg-slate-400/10';
        }
    };

    // Sort: watchlisted first, then by absolute change
    const sortedTrends = [...MARKET_TRENDS].sort((a, b) => {
        const aW = watchlist.has(a.id) ? 1 : 0;
        const bW = watchlist.has(b.id) ? 1 : 0;
        if (bW !== aW) return bW - aW;
        return Math.abs(b.change) - Math.abs(a.change);
    });

    return (
        <>
            {/* ── Collapsed pill trigger ── */}
            <AnimatePresence>
                {!isOpen && (
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        onClick={() => setIsOpen(true)}
                        className="fixed right-0 top-1/2 -translate-y-1/2 z-40 hidden lg:flex items-center gap-2 pl-3 pr-2 py-2.5 rounded-l-2xl border border-r-0 border-[var(--color-border)]/60 bg-[var(--color-surface)]/80 backdrop-blur-xl hover:bg-[var(--color-surface)] shadow-lg transition-all group"
                        title={isAr ? 'نبض السوق' : 'Market Pulse'}
                    >
                        <Activity className="w-4 h-4 text-emerald-500 group-hover:animate-pulse" />
                        <span className="text-[11px] font-semibold text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)] transition-colors writing-mode-vertical hidden xl:block"
                            style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
                        >
                            {isAr ? 'نبض السوق' : 'PULSE'}
                        </span>
                    </motion.button>
                )}
            </AnimatePresence>

            {/* ── Panel ── */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop (mobile) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
                            onClick={() => setIsOpen(false)}
                        />

                        <motion.aside
                            initial={{ x: 380, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            exit={{ x: 380, opacity: 0 }}
                            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
                            className="fixed right-0 top-0 bottom-0 w-[340px] lg:w-[360px] bg-[var(--color-surface)]/95 backdrop-blur-2xl border-l border-[var(--color-border)]/50 z-50 flex flex-col shadow-[-10px_0_40px_rgba(0,0,0,0.08)]"
                            dir={isAr ? 'rtl' : 'ltr'}
                        >
                            {/* ── Header ── */}
                            <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]/50">
                                <div className="flex items-center gap-2.5">
                                    <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                                        <Activity className="w-4 h-4 text-emerald-500" />
                                    </div>
                                    <div>
                                        <span className="text-[14px] font-semibold text-[var(--color-text-primary)]">
                                            {isAr ? 'نبض السوق' : 'Market Pulse'}
                                        </span>
                                        <div className="flex items-center gap-1.5">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                            <span className="text-[10px] text-[var(--color-text-muted)]">{isAr ? 'مباشر' : 'Live'}</span>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-1.5 hover:bg-[var(--color-surface-elevated)] rounded-lg transition-colors"
                                >
                                    <X className="w-4 h-4 text-[var(--color-text-muted)]" />
                                </button>
                            </div>

                            {/* ── Scrollable Content ── */}
                            <div className="flex-1 overflow-y-auto p-4 space-y-5">

                                {/* ── AI Opportunity ── */}
                                <section>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                                        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
                                            {isAr ? 'تنبيهات الذكاء الاصطناعي' : 'AI Alerts'}
                                        </span>
                                    </div>
                                    <div className="space-y-2.5">
                                        {AI_INSIGHTS.map(insight => (
                                            <button
                                                key={insight.id}
                                                onClick={() => handleInsightClick(insight)}
                                                className="w-full text-left rounded-xl border border-amber-500/20 bg-amber-500/5 hover:bg-amber-500/10 p-3.5 transition-all group"
                                            >
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1 min-w-0">
                                                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-1.5">
                                                            <Zap className="w-3 h-3" />
                                                            {insight.tag}
                                                        </span>
                                                        <p className="text-[13px] font-semibold text-[var(--color-text-primary)] leading-snug mb-1">
                                                            {isAr ? insight.titleAr : insight.title}
                                                        </p>
                                                        <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                                                            {isAr ? insight.bodyAr : insight.body}
                                                        </p>
                                                    </div>
                                                    <ChevronRight className="w-4 h-4 text-amber-500/50 group-hover:text-amber-500 group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-4" />
                                                </div>
                                                <span className="inline-flex items-center gap-1 mt-2.5 text-[10px] font-medium text-amber-600/80 dark:text-amber-400/80 group-hover:text-amber-600 dark:group-hover:text-amber-400">
                                                    {isAr ? 'اضغط للتحليل' : 'Click to Analyze'} <ArrowUpRight className="w-3 h-3" />
                                                </span>
                                            </button>
                                        ))}
                                    </div>
                                </section>

                                {/* ── Live Trend Ticker ── */}
                                <section>
                                    <div className="flex items-center gap-2 mb-3">
                                        <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                                        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
                                            {isAr ? 'اتجاهات أسبوعية' : 'Weekly Trends'}
                                        </span>
                                    </div>
                                    <div className="space-y-1.5">
                                        {sortedTrends.map(trend => (
                                            <div
                                                key={trend.id}
                                                className="flex items-center gap-3 rounded-xl border border-[var(--color-border)]/50 bg-[var(--color-background)]/60 hover:bg-[var(--color-background)] p-3 transition-all group cursor-pointer"
                                                onClick={() => handleTrendClick(trend)}
                                            >
                                                {/* Star / Watchlist */}
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); toggleWatchlist(trend.id); }}
                                                    className="p-0.5 flex-shrink-0"
                                                    title={watchlist.has(trend.id) ? 'Remove from watchlist' : 'Add to watchlist'}
                                                >
                                                    {watchlist.has(trend.id)
                                                        ? <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                                                        : <Star className="w-3.5 h-3.5 text-[var(--color-text-muted)]/40 hover:text-amber-500 transition-colors" />
                                                    }
                                                </button>

                                                {/* Info */}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-[12px] font-semibold text-[var(--color-text-primary)] truncate">
                                                            {isAr ? trend.areaAr : trend.area}
                                                        </span>
                                                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${demandColor(trend.demand)}`}>
                                                            {isAr ? (trend.demand === 'High' ? 'عالي' : trend.demand === 'Medium' ? 'متوسط' : 'منخفض') : trend.demand}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-2 mt-0.5">
                                                        <span className="text-[11px] text-[var(--color-text-muted)]">
                                                            {trend.avgPriceSqm.toLocaleString()} {isAr ? 'ج.م/م²' : 'EGP/m²'}
                                                        </span>
                                                        <span className={`text-[11px] font-semibold flex items-center gap-0.5 ${trend.change >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                                            {trend.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                                                            {trend.change >= 0 ? '+' : ''}{trend.change}%
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Sparkline */}
                                                <Sparkline data={trend.trend7d} positive={trend.change >= 0} />
                                            </div>
                                        ))}
                                    </div>
                                </section>

                                {/* ── Blockchain Verification ── */}
                                <section>
                                    <div className="flex items-center gap-2 mb-3">
                                        <Shield className="w-3.5 h-3.5 text-blue-500" />
                                        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-[var(--color-text-muted)]">
                                            {isAr ? 'التحقق والتوثيق' : 'Verification Feed'}
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {VERIFICATION_EVENTS.map(ev => (
                                            <div key={ev.id} className="flex items-start gap-2.5 rounded-lg border border-[var(--color-border)]/30 bg-[var(--color-background)]/40 p-2.5">
                                                <div className="w-6 h-6 rounded-md bg-blue-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                                                    <Shield className="w-3 h-3 text-blue-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-[11px] text-[var(--color-text-secondary)] leading-snug">
                                                        {isAr ? ev.textAr : ev.text}
                                                    </p>
                                                    <span className="text-[10px] text-[var(--color-text-muted)] mt-0.5 block">{ev.timestamp}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            </div>

                            {/* ── Footer CTA ── */}
                            <div className="p-4 border-t border-[var(--color-border)]/50">
                                <button
                                    onClick={() => { onPrompt(isAr ? 'أعطيني ملخص كامل عن وضع السوق العقاري النهاردة' : 'Give me a full market summary for today'); setIsOpen(false); }}
                                    className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-[12px] font-semibold transition-colors flex items-center justify-center gap-2"
                                >
                                    <BarChart3 className="w-3.5 h-3.5" />
                                    {isAr ? 'ملخص السوق الكامل' : 'Full Market Summary'}
                                </button>
                            </div>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
