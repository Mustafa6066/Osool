'use client';

import { motion } from 'framer-motion';
import { TrendingUp, BarChart2, MapPin, Heart, Scale, Sparkles } from 'lucide-react';

/* ─── mirror the types used in AgentInterface ─── */
interface PropertyMetrics {
    size: number;
    bedrooms: number;
    bathrooms: number;
    wolf_score: number;
    roi: number;
    price_per_sqm: number;
    liquidity_rating: string;
}

interface Property {
    id: string;
    title: string;
    location: string;
    price: number;
    currency: string;
    metrics: PropertyMetrics;
    image: string;
    developer: string;
    tags: string[];
    status: string;
}

interface AnalyticsContext {
    has_analytics?: boolean;
    avg_price_sqm?: number;
    growth_rate?: number;
    rental_yield?: number;
    [key: string]: unknown;
}

interface BentoResultGridProps {
    properties: Property[];
    analyticsContext?: AnalyticsContext | null;
    language: string;
    savedIds: Set<string>;
    onOpenDetails: (prop: Property) => void;
    onSave: (prop: Property, e: React.MouseEvent) => void;
    onValuation: (prop: Property, e: React.MouseEvent) => void;
    onCompare: (prop: Property, e: React.MouseEvent) => void;
}

/* ─── Stat tile used inside bento grid ─── */
function StatTile({
    label, value, sub, accent = false, delay = 0,
}: {
    label: string; value: string; sub?: string; accent?: boolean; delay?: number;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.94 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay }}
            className={`p-3.5 rounded-2xl border flex flex-col justify-between min-h-[80px] ${
                accent
                    ? 'bg-emerald-50/60 dark:bg-emerald-500/5 border-emerald-500/20'
                    : 'bg-[var(--color-surface-elevated)]/70 border-[var(--color-border)]/50'
            }`}
        >
            <span className={`text-[10px] font-bold uppercase tracking-wider ${accent ? 'text-emerald-600/70 dark:text-emerald-400/70' : 'text-[var(--color-text-muted)]'}`}>{label}</span>
            <div>
                <span className={`text-[18px] font-bold tracking-tight leading-none ${accent ? 'text-emerald-600 dark:text-emerald-400' : 'text-[var(--color-text-primary)]'}`}>{value}</span>
                {sub && <span className="text-[11px] font-medium text-[var(--color-text-muted)] ms-1">{sub}</span>}
            </div>
        </motion.div>
    );
}

/* ─── Hero card (first property, large) ─── */
function HeroCard({
    prop, language, isSaved, onOpen, onSave, onValuation, onCompare,
}: {
    prop: Property;
    language: string;
    isSaved: boolean;
    onOpen: () => void;
    onSave: (e: React.MouseEvent) => void;
    onValuation: (e: React.MouseEvent) => void;
    onCompare: (e: React.MouseEvent) => void;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
            onClick={onOpen}
            className="group relative flex flex-col cursor-pointer overflow-hidden rounded-[18px] border border-[var(--color-border)]/60 hover:border-emerald-500/40 bg-[var(--color-surface)]/60 backdrop-blur-sm transition-all duration-300 hover:shadow-[0_12px_40px_rgba(16,185,129,0.08)] hover:-translate-y-1"
        >
            {/* Image */}
            <motion.div
                layoutId={`property-img-${prop.id}`}
                className="relative aspect-[16/9] overflow-hidden bg-[var(--color-surface-elevated)]"
                style={{ borderRadius: 0 }}
            >
                <img
                    src={prop.image}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                    alt={prop.title}
                />
                {/* Status badge */}
                <div className="absolute top-3 end-3 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md text-[var(--color-text-primary)] px-2.5 py-1 rounded-full text-[10px] font-semibold shadow-sm border border-black/5 dark:border-white/10">
                    {prop.status}
                </div>
                {/* Price overlay */}
                <div className="absolute bottom-0 start-0 end-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent px-4 pb-3 pt-8">
                    <span className="text-white text-[20px] font-bold tracking-tight drop-shadow">
                        {(prop.price / 1_000_000).toFixed(1)}M <span className="text-[13px] font-normal opacity-80">EGP</span>
                    </span>
                </div>
            </motion.div>

            {/* Body */}
            <div className="p-4 flex flex-col gap-2.5">
                <div>
                    <h3 className="font-semibold text-[var(--color-text-primary)] text-[15px] leading-snug" dir="auto">{prop.title}</h3>
                    <p className="text-[13px] text-[var(--color-text-muted)] flex items-center gap-1 mt-0.5" dir="auto">
                        <MapPin className="w-3 h-3 text-emerald-500 flex-shrink-0" />
                        {prop.location}{prop.developer ? ` · ${prop.developer}` : ''}
                    </p>
                </div>

                {/* Score bar */}
                {prop.metrics.wolf_score > 0 && (
                    <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <motion.div
                                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]"
                                initial={{ width: 0 }}
                                animate={{ width: `${Math.min(prop.metrics.wolf_score, 100)}%` }}
                                transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
                            />
                        </div>
                        <span className="text-[11px] font-bold text-[var(--color-text-secondary)] flex-shrink-0">
                            <Sparkles className="w-3 h-3 text-emerald-500 inline me-0.5" />
                            {prop.metrics.wolf_score}/100
                        </span>
                    </div>
                )}

                {/* Badges row */}
                <div className="flex flex-wrap gap-1.5">
                    {prop.metrics.roi > 0 && (
                        <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-md flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" /> +{prop.metrics.roi}% ROI
                        </span>
                    )}
                    {prop.metrics.price_per_sqm > 0 && (
                        <span className="text-[11px] font-medium text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-2 py-0.5 rounded-md">
                            {prop.metrics.price_per_sqm.toLocaleString()}/m²
                        </span>
                    )}
                    {prop.metrics.bedrooms > 0 && (
                        <span className="text-[11px] font-medium text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-2 py-0.5 rounded-md">
                            {prop.metrics.bedrooms}BR
                        </span>
                    )}
                </div>

                {/* Action buttons */}
                <div className="flex gap-1 pt-0.5" dir="ltr">
                    <button
                        onClick={onSave}
                        className={`p-1.5 rounded-lg transition-colors ${isSaved ? 'text-red-500 bg-red-500/10' : 'text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10'}`}
                        title={isSaved ? 'Saved' : 'Save'}
                    >
                        <Heart className="w-3.5 h-3.5" fill={isSaved ? 'currentColor' : 'none'} />
                    </button>
                    <button
                        onClick={onValuation}
                        className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-emerald-500 hover:bg-emerald-500/10 transition-colors"
                        title="Run Valuation"
                    >
                        <BarChart2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                        onClick={onCompare}
                        className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-blue-500 hover:bg-blue-500/10 transition-colors"
                        title="Compare"
                    >
                        <Scale className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}

/* ─── Compact list row (remaining properties after hero) ─── */
function CompactCard({
    prop, delay, isSaved, onOpen, onSave,
}: {
    prop: Property;
    delay: number;
    isSaved: boolean;
    onOpen: () => void;
    onSave: (e: React.MouseEvent) => void;
}) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay }}
            onClick={onOpen}
            className="group flex gap-3 p-3 border border-[var(--color-border)]/50 hover:border-emerald-500/30 bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)] rounded-[14px] cursor-pointer transition-all duration-200 hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(0,0,0,0.04)]"
        >
            <motion.div
                layoutId={`property-img-${prop.id}`}
                className="w-14 h-14 rounded-xl flex-shrink-0 overflow-hidden bg-[var(--color-surface-elevated)]"
                style={{ borderRadius: 12 }}
            >
                <img src={prop.image} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" alt={prop.title} />
            </motion.div>
            <div className="flex-1 min-w-0 flex flex-col justify-center">
                <p className="text-[13px] font-semibold text-[var(--color-text-primary)] truncate leading-tight" dir="auto">{prop.title}</p>
                <p className="text-[11px] text-[var(--color-text-muted)] truncate mt-0.5" dir="auto">{prop.location}</p>
                <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-[13px] font-bold text-[var(--color-text-primary)] tracking-tight">{(prop.price / 1_000_000).toFixed(1)}M</span>
                    {prop.metrics.roi > 0 && (
                        <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">+{prop.metrics.roi}%</span>
                    )}
                </div>
            </div>
            <button
                onClick={onSave}
                className={`self-center p-1.5 rounded-lg flex-shrink-0 transition-colors ${isSaved ? 'text-red-500 bg-red-500/10' : 'text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10'}`}
                title={isSaved ? 'Saved' : 'Save'}
            >
                <Heart className="w-3 h-3" fill={isSaved ? 'currentColor' : 'none'} />
            </button>
        </motion.div>
    );
}

/* ─── Main export ─── */
export default function BentoResultGrid({
    properties,
    analyticsContext,
    language,
    savedIds,
    onOpenDetails,
    onSave,
    onValuation,
    onCompare,
}: BentoResultGridProps) {
    if (!properties.length) return null;

    const isRTL = language === 'ar';
    const [hero, ...rest] = properties;
    const hasAnalytics = analyticsContext?.has_analytics;
    const avgPrice = analyticsContext?.avg_price_sqm ?? 0;
    const growth = analyticsContext?.growth_rate ?? 0;
    const yield_ = analyticsContext?.rental_yield ?? 0;
    const showAnalyticsTiles = hasAnalytics && (avgPrice > 0 || growth > 0 || yield_ > 0);

    return (
        <div className="mt-5" dir="ltr">
            {/* ── Bento layout: hero + side tiles ── */}
            <div className="grid grid-cols-1 md:grid-cols-[1fr_180px] gap-3">
                {/* Hero property */}
                <HeroCard
                    prop={hero}
                    language={language}
                    isSaved={savedIds.has(String(hero.id))}
                    onOpen={() => onOpenDetails(hero)}
                    onSave={(e) => onSave(hero, e)}
                    onValuation={(e) => onValuation(hero, e)}
                    onCompare={(e) => onCompare(hero, e)}
                />

                {/* Right column: analytics tiles (desktop only), otherwise hidden */}
                {showAnalyticsTiles && (
                    <div className="hidden md:flex flex-col gap-2.5">
                        {avgPrice > 0 && (
                            <StatTile
                                label={isRTL ? 'متوسط السعر/م²' : 'Area avg/m²'}
                                value={avgPrice > 999 ? `${(avgPrice / 1000).toFixed(1)}k` : String(avgPrice)}
                                sub="EGP"
                                delay={0.05}
                            />
                        )}
                        {growth > 0 && (
                            <StatTile
                                label={isRTL ? 'نمو سنوي' : 'YoY growth'}
                                value={`+${(growth * 100).toFixed(0)}%`}
                                accent
                                delay={0.1}
                            />
                        )}
                        {yield_ > 0 && (
                            <StatTile
                                label={isRTL ? 'عائد إيجاري' : 'Rental yield'}
                                value={`${(yield_ * 100).toFixed(1)}%`}
                                delay={0.15}
                            />
                        )}
                        {/* Wolf Score tile if available */}
                        {hero.metrics.wolf_score > 0 && (
                            <StatTile
                                label={isRTL ? 'مؤشر أصول' : 'Osool Score'}
                                value={String(hero.metrics.wolf_score)}
                                sub="/100"
                                accent
                                delay={0.2}
                            />
                        )}
                    </div>
                )}
            </div>

            {/* Analytics tiles in a row on mobile (below hero) */}
            {showAnalyticsTiles && (
                <div className="md:hidden grid grid-cols-3 gap-2 mt-2.5">
                    {avgPrice > 0 && (
                        <StatTile label={isRTL ? 'متوسط/م²' : 'Avg/m²'} value={avgPrice > 999 ? `${(avgPrice / 1000).toFixed(1)}k` : String(avgPrice)} delay={0.05} />
                    )}
                    {growth > 0 && (
                        <StatTile label={isRTL ? 'نمو' : 'Growth'} value={`+${(growth * 100).toFixed(0)}%`} accent delay={0.1} />
                    )}
                    {yield_ > 0 && (
                        <StatTile label={isRTL ? 'عائد' : 'Yield'} value={`${(yield_ * 100).toFixed(1)}%`} delay={0.15} />
                    )}
                </div>
            )}

            {/* Additional properties as compact list */}
            {rest.length > 0 && (
                <div className="mt-3 space-y-2">
                    {rest.map((prop, idx) => (
                        <CompactCard
                            key={prop.id}
                            prop={prop}
                            delay={0.1 + idx * 0.07}
                            isSaved={savedIds.has(String(prop.id))}
                            onOpen={() => onOpenDetails(prop)}
                            onSave={(e) => onSave(prop, e)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
