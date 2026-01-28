"use client";

import { motion } from "framer-motion";
import { 
    MapPinIcon, 
    TrendingUpIcon, 
    HomeIcon,
    UsersIcon,
    ChartBarIcon,
    CheckCircleIcon,
    XCircleIcon
} from "lucide-react";

interface AreaAnalysisProps {
    area: {
        name: string;
        avg_price_per_sqm: number;
        price_growth_ytd: number;
        demand_level: string;
        supply_level: string;
        market_trend: string;
        best_for: string[];
        top_developers: string[];
        pros: string[];
        cons: string[];
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
    // Defensive check for required props
    if (!area || !area.name) {
        console.warn('AreaAnalysis: Missing required area data');
        return null;
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            maximumFractionDigits: 0
        }).format(value);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-blue-950/30 to-indigo-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600/20 to-indigo-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                        <MapPinIcon className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">تحليل المنطقة 📍</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">{area.name}</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">متوسط سعر المتر</p>
                        <p className="text-lg font-bold text-blue-400">{formatCurrency(area.avg_price_per_sqm)}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">نمو السعر</p>
                        <p className="text-lg font-bold text-green-400">+{area.price_growth_ytd}%</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">مستوى الطلب</p>
                        <p className="text-lg font-bold text-amber-400">{area.demand_level}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">المعروض</p>
                        <p className="text-lg font-bold text-purple-400">{area.supply_level}</p>
                    </div>
                </div>

                {/* Best For */}
                <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <UsersIcon className="w-4 h-4 text-blue-400" />
                        <p className="text-sm font-medium text-white">المنطقة مناسبة لـ</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {(area.best_for || []).map((item, i) => (
                            <span key={i} className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm rounded-full">
                                {item}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Top Developers */}
                <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <HomeIcon className="w-4 h-4 text-indigo-400" />
                        <p className="text-sm font-medium text-white">أبرز المطورين</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {(area.top_developers || []).map((dev, i) => (
                            <span key={i} className="px-3 py-1 bg-indigo-500/20 text-indigo-300 text-sm rounded-full">
                                {dev}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Pros & Cons */}
                <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-green-950/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                            <CheckCircleIcon className="w-4 h-4 text-green-400" />
                            <p className="text-sm font-medium text-green-400">مميزات</p>
                        </div>
                        <ul className="space-y-2">
                            {(area.pros || []).map((pro, i) => (
                                <li key={i} className="text-sm text-[var(--color-text-secondary)] flex items-start gap-2">
                                    <span className="text-green-400">•</span> {pro}
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="bg-red-950/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                            <XCircleIcon className="w-4 h-4 text-red-400" />
                            <p className="text-sm font-medium text-red-400">تحديات</p>
                        </div>
                        <ul className="space-y-2">
                            {(area.cons || []).map((con, i) => (
                                <li key={i} className="text-sm text-[var(--color-text-secondary)] flex items-start gap-2">
                                    <span className="text-red-400">•</span> {con}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Comparison Quick Stats */}
                {comparison && (
                    <div className="bg-gradient-to-r from-amber-950/30 to-orange-950/30 rounded-xl p-4 border border-amber-500/20">
                        <div className="flex items-center gap-2 mb-3">
                            <ChartBarIcon className="w-4 h-4 text-amber-400" />
                            <p className="text-sm font-medium text-amber-400">مقارنة سريعة</p>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center text-sm">
                            <div>
                                <p className="text-[var(--color-text-secondary)]">أعلى نمو</p>
                                <p className="text-amber-300 font-medium">{comparison.highest_growth}</p>
                            </div>
                            <div>
                                <p className="text-[var(--color-text-secondary)]">للعائلات</p>
                                <p className="text-amber-300 font-medium">{comparison.best_family}</p>
                            </div>
                            <div>
                                <p className="text-[var(--color-text-secondary)]">للاستثمار</p>
                                <p className="text-amber-300 font-medium">{comparison.best_investment}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Price Heatmap */}
                {heatmap && heatmap.length > 0 && (
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                            <TrendingUpIcon className="w-4 h-4 text-cyan-400" />
                            <p className="text-sm font-medium text-white">خريطة الأسعار</p>
                        </div>
                        <div className="space-y-2">
                            {heatmap.map((loc, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <span className="text-sm text-[var(--color-text-secondary)] w-32 truncate">{loc.location}</span>
                                    <div className="flex-1 h-4 bg-[var(--color-surface)] rounded-full overflow-hidden">
                                        <div 
                                            className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 rounded-full"
                                            style={{ width: `${Math.min(loc.intensity, 100)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-[var(--color-text-secondary)] w-24 text-right">
                                        {formatCurrency(loc.avg_price_per_sqm)}/م²
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
