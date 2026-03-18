'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X, MapPin, Sparkles, ChevronRight, BarChart2, Home, Bed, Ruler, Tag,
    TrendingUp, DollarSign, ExternalLink, ChevronDown
} from 'lucide-react';

/* ─── types mirroring AgentInterface's Property type ─── */
export interface InsightsProperty {
    id: string;
    title: string;
    location: string;
    price: number;
    currency: string;
    metrics: {
        size: number;
        bedrooms: number;
        bathrooms: number;
        wolf_score: number;
        roi: number;
        price_per_sqm: number;
        liquidity_rating: string;
    };
    image: string;
    developer: string;
    tags: string[];
    status: string;
}

interface ChatInsightsShellProps {
    property: InsightsProperty | null;
    isOpen: boolean;
    onClose: () => void;
    language: string;
    onPrompt?: (prompt: string) => void;
}

/* ─── Animated counter ─── */
function AnimatedNum({ target, suffix = '', decimals = 0 }: { target: number; suffix?: string; decimals?: number }) {
    const [val, setVal] = useState(0);
    const raf = useRef<number | null>(null);

    useEffect(() => {
        const start = performance.now();
        const duration = 900;

        function tick(now: number) {
            const t = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - t, 4); // easeOutQuart
            setVal(target * ease);
            if (t < 1) raf.current = requestAnimationFrame(tick);
        }

        raf.current = requestAnimationFrame(tick);
        return () => { if (raf.current) cancelAnimationFrame(raf.current); };
    }, [target]);

    const display = decimals > 0 ? val.toFixed(decimals) : Math.round(val).toString();
    return <span>{display}{suffix}</span>;
}

/* ─── Score ring ─── */
function ScoreRing({ score }: { score: number }) {
    const r = 26;
    const circum = 2 * Math.PI * r;
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const t = setTimeout(() => setProgress(score / 100), 80);
        return () => clearTimeout(t);
    }, [score]);

    const color = score >= 70 ? '#10b981' : score >= 45 ? '#f59e0b' : '#ef4444';

    return (
        <div className="relative w-16 h-16 flex-shrink-0">
            <svg width="64" height="64" className="rotate-[-90deg]" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="5" className="text-gray-100 dark:text-gray-800" />
                <circle
                    cx="32" cy="32" r={r} fill="none"
                    stroke={color} strokeWidth="5"
                    strokeDasharray={circum}
                    strokeDashoffset={circum * (1 - progress)}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)' }}
                />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-[13px] font-bold" style={{ color }}>{score}</span>
            </div>
        </div>
    );
}

/* ─── Spec tile ─── */
function SpecTile({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
    return (
        <div className={`p-3.5 rounded-2xl border ${highlight
            ? 'bg-emerald-50/60 dark:bg-emerald-500/5 border-emerald-500/20'
            : 'bg-gray-50/60 dark:bg-gray-800/40 border-[var(--color-border)]/50'}`}>
            <div className={`text-[10px] font-semibold uppercase tracking-wider mb-1 ${highlight ? 'text-emerald-600/80 dark:text-emerald-400/80' : 'text-[var(--color-text-muted)]'}`}>{label}</div>
            <div className={`text-[14px] font-bold ${highlight ? 'text-emerald-600 dark:text-emerald-400' : 'text-[var(--color-text-primary)]'}`}>{value}</div>
        </div>
    );
}

export default function ChatInsightsShell({ property, isOpen, onClose, language, onPrompt }: ChatInsightsShellProps) {
    const isRTL = language === 'ar';

    const askAbout = (tpl: string) => {
        if (!property || !onPrompt) return;
        const prompt = tpl.replace('{title}', property.title).replace('{location}', property.location);
        onPrompt(prompt);
    };

    const quickActions = isRTL
        ? [
            { label: 'خطة السداد', prompt: 'خطة السداد لـ "{title}"؟' },
            { label: 'حساب ROI', prompt: 'احسب العائد الاستثماري لـ "{title}"' },
            { label: 'وحدات مشابهة', prompt: 'وحدات مشابهة لـ "{title}" في {location}' },
        ]
        : [
            { label: 'Payment plans', prompt: 'What are the payment plans for "{title}"?' },
            { label: 'Calculate ROI', prompt: 'Calculate 10-year ROI for "{title}" in {location}' },
            { label: 'Similar units', prompt: 'Show me similar units to "{title}" in {location}' },
        ];

    /* shared content */
    const content = property ? (
        <div className="flex-1 overflow-y-auto custom-scrollbar">
            {/* Hero image with layoutId to animate from the chat card */}
            <motion.div layoutId={`property-img-${property.id}`} className="relative aspect-[16/9] overflow-hidden bg-[var(--color-surface-elevated)]">
                <img
                    src={property.image}
                    className="w-full h-full object-cover"
                    alt={property.title}
                />
                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                {/* Status pill */}
                <div className="absolute top-3 end-3 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md text-[var(--color-text-primary)] px-3 py-1 rounded-full text-[11px] font-semibold shadow-sm border border-black/5 dark:border-white/10">
                    {property.status}
                </div>
                {/* Price overlay at bottom */}
                <div className="absolute bottom-0 start-0 end-0 px-5 pb-4 pt-8">
                    <p className="text-white text-[22px] font-bold tracking-tight drop-shadow">
                        <AnimatedNum target={property.price / 1_000_000} decimals={2} suffix="M EGP" />
                    </p>
                </div>
            </motion.div>

            <div className="p-5 space-y-6">
                {/* Title + location */}
                <div>
                    <h2 className="text-[18px] font-semibold text-[var(--color-text-primary)] leading-tight tracking-tight" dir="auto">
                        {property.title}
                    </h2>
                    {property.developer && (
                        <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5 font-medium">{property.developer}</p>
                    )}
                    <p className="text-[13px] text-[var(--color-text-secondary)] flex items-center gap-1.5 mt-1.5 font-medium" dir="auto">
                        <MapPin className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" strokeWidth={2} />
                        {property.location}
                    </p>
                </div>

                {/* Osool Intelligence Score */}
                {property.metrics.wolf_score > 0 && (
                    <div className="bg-gradient-to-br from-emerald-500/8 to-transparent rounded-[18px] p-4 border border-emerald-500/15 relative overflow-hidden">
                        <div className="absolute top-0 end-0 w-28 h-28 bg-emerald-500/12 blur-[36px] rounded-full pointer-events-none" />
                        <div className="flex items-center gap-2 mb-3.5 relative z-10">
                            <Sparkles className="w-4 h-4 text-emerald-500" strokeWidth={2} />
                            <span className="text-[12px] font-bold text-[var(--color-text-primary)] uppercase tracking-wider">
                                {isRTL ? 'مؤشر أصول' : 'Osool Score'}
                            </span>
                        </div>
                        <div className="flex items-center gap-4 relative z-10">
                            <ScoreRing score={property.metrics.wolf_score} />
                            <div className="flex-1 space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <span className="text-[11px] text-[var(--color-text-muted)] font-medium">{isRTL ? 'السيولة' : 'Liquidity'}</span>
                                    <span className="text-[13px] font-bold text-[var(--color-text-primary)]">{property.metrics.liquidity_rating}</span>
                                </div>
                                {property.metrics.roi > 0 && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-[11px] text-[var(--color-text-muted)] font-medium">{isRTL ? 'العائد' : 'ROI Est.'}</span>
                                        <span className="text-[13px] font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3" />
                                            +{property.metrics.roi}%
                                        </span>
                                    </div>
                                )}
                                {/* ROI bar */}
                                {property.metrics.roi > 0 && (
                                    <div className="h-1 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden mt-0.5">
                                        <motion.div
                                            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${Math.min(property.metrics.roi * 5, 100)}%` }}
                                            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
                                        />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Specs grid — 2-col */}
                <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] mb-3 uppercase tracking-widest ps-0.5">
                        {isRTL ? 'المواصفات' : 'Specifications'}
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                        {property.metrics.size > 0 && (
                            <SpecTile label={isRTL ? 'المساحة' : 'Built Area'} value={`${property.metrics.size} m²`} />
                        )}
                        {property.metrics.bedrooms > 0 && (
                            <SpecTile label={isRTL ? 'غرف النوم' : 'Bedrooms'} value={String(property.metrics.bedrooms)} />
                        )}
                        {property.metrics.price_per_sqm > 0 && (
                            <SpecTile
                                label={isRTL ? 'السعر/م²' : 'Price/m²'}
                                value={property.metrics.price_per_sqm > 999
                                    ? `${(property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                    : String(property.metrics.price_per_sqm)}
                            />
                        )}
                        <SpecTile
                            label={isRTL ? 'الإجمالي' : 'Valuation'}
                            value={`${(property.price / 1_000_000).toFixed(2)}M`}
                            highlight
                        />
                    </div>
                </div>

                {/* Tags */}
                {property.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                        {property.tags.map((tag, i) => (
                            <span key={i} className="text-[11px] font-medium bg-gray-100 dark:bg-gray-800 text-[var(--color-text-secondary)] px-3 py-1 rounded-full border border-gray-200/70 dark:border-gray-700/70">
                                {tag}
                            </span>
                        ))}
                    </div>
                )}

                {/* Quick-action chips */}
                {onPrompt && (
                    <div>
                        <h3 className="text-[10px] font-bold text-[var(--color-text-muted)] mb-2.5 uppercase tracking-widest ps-0.5">
                            {isRTL ? 'اسأل عن' : 'Ask about'}
                        </h3>
                        <div className="flex flex-col gap-2">
                            {quickActions.map((qa, i) => (
                                <button
                                    key={i}
                                    onClick={() => askAbout(qa.prompt)}
                                    className="text-start w-full text-[12px] font-medium text-[var(--color-text-secondary)] px-3.5 py-2.5 rounded-xl bg-[var(--color-surface-elevated)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text-primary)] border border-[var(--color-border)]/50 hover:border-emerald-500/30 transition-all flex items-center justify-between group"
                                >
                                    {qa.label}
                                    <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-emerald-500" />
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* CTA */}
                <div className="pb-2">
                    <button className="w-full py-3.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-[14px] font-semibold text-[14px] transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-black/10 dark:shadow-white/10 flex items-center justify-center gap-2">
                        {isRTL ? 'طلب معاينة خاصة' : 'Request Private Viewing'}
                        <ChevronRight className="w-4 h-4 opacity-70" strokeWidth={2.5} />
                    </button>
                </div>
            </div>
        </div>
    ) : null;

    /* ─── header ─── */
    const header = (
        <div className="h-14 border-b border-[var(--color-border)]/50 flex items-center justify-between px-5 flex-shrink-0 bg-white/60 dark:bg-gray-900/60 backdrop-blur-sm">
            <div className="flex items-center gap-2.5">
                <span className="text-[14px] font-semibold text-[var(--color-text-primary)]">
                    {isRTL ? 'تفاصيل العقار' : 'Property Details'}
                </span>
                <span className="text-[9px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-widest">
                    Live
                </span>
            </div>
            <button
                onClick={onClose}
                aria-label={isRTL ? 'إغلاق التفاصيل' : 'Close details'}
                className="w-8 h-8 flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] bg-gray-100/60 dark:bg-gray-800/60 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-all"
            >
                <X className="w-4 h-4" strokeWidth={2} />
            </button>
        </div>
    );

    return (
        <AnimatePresence>
            {isOpen && property && (
                <>
                    {/* Mobile: full-screen overlay */}
                    <motion.div
                        key="mobile-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden"
                        onClick={onClose}
                    />

                    {/* Pane — full-screen on mobile, side panel on desktop */}
                    <motion.aside
                        key="insights-pane"
                        initial={{ x: isRTL ? -380 : 380, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        exit={{ x: isRTL ? -380 : 380, opacity: 0 }}
                        transition={{ type: 'spring', damping: 30, stiffness: 320 }}
                        className="
                            fixed inset-0 z-50 flex flex-col
                            bg-[var(--color-surface)]/98 backdrop-blur-2xl
                            lg:static lg:inset-auto lg:z-auto
                            lg:w-[380px] lg:flex-shrink-0
                            lg:border-s border-[var(--color-border)]/50
                            lg:shadow-[-12px_0_48px_rgba(0,0,0,0.05)]
                            lg:m-4 lg:ms-0 lg:rounded-[20px]
                            overflow-hidden
                        "
                    >
                        {header}
                        {content}
                    </motion.aside>
                </>
            )}
        </AnimatePresence>
    );
}
