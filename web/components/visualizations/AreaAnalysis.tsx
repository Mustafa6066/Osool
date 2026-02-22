"use client";

import { motion } from "framer-motion";
import {
    MapPinIcon,
    TrendingUpIcon,
    HomeIcon,
    UsersIcon,
    CheckCircleIcon,
    XCircleIcon,
    BuildingIcon,
    BarChart3Icon
} from "lucide-react";

interface AreaAnalysisProps {
    area: {
        name: string;
        avg_price_per_sqm?: number;
        avg_price_sqm?: number;
        price_growth_ytd?: number;
        growth_rate?: number;
        rental_yield?: number;
        demand_level?: string;
        supply_level?: string;
        market_trend?: string;
        best_for?: string[];
        top_developers?: string[];
        tier1_developers?: string[];
        pros?: string[];
        cons?: string[];
        property_minimums?: Record<string, number>;
    };
    comparison?: {
        highest_growth: string;
        best_family: string;
        best_investment: string;
    };
    heatmap?: Array<{
        location: string;
        avg_price_per_sqm: number;
        intensity: number;
    }>;
}

export default function AreaAnalysis({ area, comparison, heatmap }: AreaAnalysisProps) {
    if (!area || !area.name) return null;

    // Normalize data
    const avgPrice = area.avg_price_per_sqm || area.avg_price_sqm || 0;
    const rawGrowth = area.price_growth_ytd || (area.growth_rate ? (area.growth_rate < 5 ? area.growth_rate * 100 : area.growth_rate) : 0);
    const growthPct = rawGrowth < 1 && rawGrowth > 0 ? rawGrowth * 100 : rawGrowth;
    const rentalYield = area.rental_yield ? (area.rental_yield < 1 ? area.rental_yield * 100 : area.rental_yield) : 0;
    const developers = area.top_developers || area.tier1_developers || [];
    const pros = area.pros || [];
    const cons = area.cons || [];
    const bestFor = area.best_for || [];
    const minimums = area.property_minimums || {};

    // Skip if truly empty
    if (avgPrice === 0 && growthPct === 0 && developers.length === 0) return null;

    const fmt = (v: number) => {
        if (!v || isNaN(v)) return 'N/A';
        return v.toLocaleString('en-EG');
    };

    const fmtPrice = (v: number) => {
        if (!v || isNaN(v)) return 'N/A';
        if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M EGP`;
        return `${(v / 1_000).toFixed(0)}K EGP`;
    };

    // Build comparison bar data for mini chart
    const areaComparisons = [
        { name: "القاهرة الجديدة", price: 61550 },
        { name: "الشيخ زايد", price: 64050 },
        { name: "الساحل", price: 76150 },
        { name: "العاصمة", price: 45000 },
        { name: "أكتوبر", price: 47000 },
    ];
    const maxBarPrice = Math.max(...areaComparisons.map(a => a.price), avgPrice);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden"
        >
            {/* Header — compact */}
            <div className="flex items-center gap-3 px-5 py-3.5 border-b border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
                <MapPinIcon className="w-4 h-4 text-blue-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-[var(--color-text-primary)]" dir="rtl">
                        تحليل {area.name}
                    </h3>
                </div>
                {area.market_trend && (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        area.market_trend === 'صاعد' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'
                    }`}>
                        {area.market_trend}
                    </span>
                )}
            </div>

            <div className="px-5 py-4 space-y-4" dir="rtl">
                {/* Key Numbers — inline text, not cards */}
                <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                    {avgPrice > 0 && (
                        <div>
                            <span className="text-[var(--color-text-muted)]">متوسط المتر: </span>
                            <span className="font-bold text-[var(--color-text-primary)]">{fmt(avgPrice)} ج.م</span>
                        </div>
                    )}
                    {growthPct > 0 && (
                        <div>
                            <span className="text-[var(--color-text-muted)]">النمو: </span>
                            <span className="font-bold text-emerald-500">+{growthPct.toFixed(0)}%</span>
                        </div>
                    )}
                    {rentalYield > 0 && (
                        <div>
                            <span className="text-[var(--color-text-muted)]">العائد الإيجاري: </span>
                            <span className="font-bold text-blue-500">{rentalYield.toFixed(1)}%</span>
                        </div>
                    )}
                    {area.demand_level && (
                        <div>
                            <span className="text-[var(--color-text-muted)]">الطلب: </span>
                            <span className="font-bold text-amber-500">{area.demand_level}</span>
                        </div>
                    )}
                </div>

                {/* Mini Comparison Bars — slim horizontal chart */}
                {avgPrice > 0 && (
                    <div className="space-y-1.5">
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)] flex items-center gap-1.5">
                            <BarChart3Icon className="w-3 h-3" />
                            مقارنة سعر المتر بالمناطق
                        </p>
                        <div className="space-y-1">
                            {areaComparisons.map((comp) => {
                                const isCurrentArea = area.name.includes(comp.name) || comp.name.includes(area.name.split(' ')[0]);
                                const barW = (comp.price / maxBarPrice) * 100;
                                return (
                                    <div key={comp.name} className="flex items-center gap-2 text-[11px]">
                                        <span className={`w-24 text-left truncate ${isCurrentArea ? 'font-bold text-blue-500' : 'text-[var(--color-text-muted)]'}`}>
                                            {comp.name}
                                        </span>
                                        <div className="flex-1 h-2 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                                            <motion.div
                                                initial={{ width: 0 }}
                                                animate={{ width: `${barW}%` }}
                                                transition={{ duration: 0.8, delay: 0.2 }}
                                                className={`h-full rounded-full ${isCurrentArea ? 'bg-blue-500' : 'bg-[var(--color-text-muted)]/30'}`}
                                            />
                                        </div>
                                        <span className={`w-14 text-left tabular-nums ${isCurrentArea ? 'font-bold text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}`}>
                                            {fmt(comp.price)}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Property Entry Prices */}
                {Object.keys(minimums).length > 0 && (
                    <div>
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)] mb-1.5 flex items-center gap-1.5">
                            <HomeIcon className="w-3 h-3" />
                            الحد الأدنى للأسعار
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(minimums).map(([type, price]) => (
                                <span key={type} className="text-[11px] px-2.5 py-1 rounded-lg bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)]">
                                    {type === 'apartment' ? 'شقة' : type === 'villa' ? 'فيلا' : type === 'townhouse' ? 'تاون هاوس' : type === 'duplex' ? 'دوبلكس' : type === 'chalet' ? 'شاليه' : type}: <span className="font-semibold text-[var(--color-text-primary)]">{fmtPrice(price as number)}</span>
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Developers */}
                {developers.length > 0 && (
                    <div>
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)] mb-1.5 flex items-center gap-1.5">
                            <UsersIcon className="w-3 h-3" />
                            أبرز المطورين
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                            {developers.map((dev, i) => (
                                <span key={i} className="text-[11px] px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 font-medium">
                                    {dev}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Best For */}
                {bestFor.length > 0 && (
                    <div>
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)] mb-1.5">مناسبة لـ</p>
                        <div className="flex flex-wrap gap-1.5">
                            {bestFor.map((item, i) => (
                                <span key={i} className="text-[11px] px-2 py-0.5 rounded-md bg-teal-500/10 text-teal-400 font-medium">
                                    {item}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Pros & Cons — inline text */}
                {(pros.length > 0 || cons.length > 0) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {pros.length > 0 && (
                            <div>
                                <p className="text-[11px] font-semibold text-emerald-500 mb-1 flex items-center gap-1">
                                    <CheckCircleIcon className="w-3 h-3" /> مميزات
                                </p>
                                <ul className="space-y-0.5">
                                    {pros.map((p, i) => (
                                        <li key={i} className="text-[11px] text-[var(--color-text-secondary)] pr-3">• {p}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {cons.length > 0 && (
                            <div>
                                <p className="text-[11px] font-semibold text-red-400 mb-1 flex items-center gap-1">
                                    <XCircleIcon className="w-3 h-3" /> تحديات
                                </p>
                                <ul className="space-y-0.5">
                                    {cons.map((c, i) => (
                                        <li key={i} className="text-[11px] text-[var(--color-text-secondary)] pr-3">• {c}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                )}

                {/* Comparison Quick Stats */}
                {comparison && (
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-[11px] pt-2 border-t border-[var(--color-border)]">
                        {comparison.highest_growth && (
                            <div>
                                <span className="text-[var(--color-text-muted)]">أعلى نمو: </span>
                                <span className="font-semibold text-amber-400">{comparison.highest_growth}</span>
                            </div>
                        )}
                        {comparison.best_investment && (
                            <div>
                                <span className="text-[var(--color-text-muted)]">للاستثمار: </span>
                                <span className="font-semibold text-amber-400">{comparison.best_investment}</span>
                            </div>
                        )}
                        {comparison.best_family && (
                            <div>
                                <span className="text-[var(--color-text-muted)]">للعائلات: </span>
                                <span className="font-semibold text-amber-400">{comparison.best_family}</span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </motion.div>
    );
}
