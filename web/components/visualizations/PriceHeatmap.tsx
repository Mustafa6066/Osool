"use client";

import { motion } from "framer-motion";
import { MapIcon } from "@heroicons/react/24/outline";

interface PriceHeatmapProps {
    locations: Array<{
        location: string;
        avg_price_per_sqm: number;
        intensity: number;
    }>;
    title?: string;
}

export default function PriceHeatmap({ locations = [], title = "خريطة الأسعار" }: PriceHeatmapProps) {
    if (!locations || locations.length === 0) return null;
    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            maximumFractionDigits: 0
        }).format(value);
    };

    const getHeatColor = (intensity: number) => {
        if (intensity >= 80) return 'from-red-500 to-red-400';
        if (intensity >= 60) return 'from-orange-500 to-orange-400';
        if (intensity >= 40) return 'from-yellow-500 to-yellow-400';
        if (intensity >= 20) return 'from-green-500 to-green-400';
        return 'from-blue-500 to-blue-400';
    };

    const getTextColor = (intensity: number) => {
        if (intensity >= 80) return 'text-red-400';
        if (intensity >= 60) return 'text-orange-400';
        if (intensity >= 40) return 'text-yellow-400';
        if (intensity >= 20) return 'text-green-400';
        return 'text-blue-400';
    };

    // Sort by price descending
    const sortedLocations = [...locations].sort((a, b) => b.avg_price_per_sqm - a.avg_price_per_sqm);
    const maxPrice = Math.max(...locations.map(l => l.avg_price_per_sqm));

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-rose-950/30 to-pink-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-rose-600/20 to-pink-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center">
                        <MapIcon className="w-5 h-5 text-rose-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">{title} 🗺️</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">مقارنة أسعار المناطق</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-4">
                {/* Legend */}
                <div className="flex items-center justify-center gap-4 text-xs text-[var(--color-text-secondary)]">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-gradient-to-r from-blue-500 to-blue-400"></div>
                        <span>منخفض</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-gradient-to-r from-green-500 to-green-400"></div>
                        <span>متوسط</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-gradient-to-r from-yellow-500 to-yellow-400"></div>
                        <span>فوق المتوسط</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-gradient-to-r from-orange-500 to-orange-400"></div>
                        <span>مرتفع</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-gradient-to-r from-red-500 to-red-400"></div>
                        <span>مرتفع جداً</span>
                    </div>
                </div>

                {/* Heatmap Bars */}
                <div className="space-y-3">
                    {sortedLocations.map((loc, i) => {
                        const relativeIntensity = (loc.avg_price_per_sqm / maxPrice) * 100;
                        return (
                            <motion.div 
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="flex items-center gap-4"
                            >
                                <span className="text-sm text-white w-32 truncate font-medium">{loc.location}</span>
                                <div className="flex-1 h-6 bg-[var(--color-surface)] rounded-full overflow-hidden relative">
                                    <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${relativeIntensity}%` }}
                                        transition={{ duration: 0.5, delay: i * 0.1 }}
                                        className={`h-full bg-gradient-to-r ${getHeatColor(loc.intensity)} rounded-full`}
                                    />
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <span className="text-xs text-white font-medium drop-shadow-lg">
                                            {formatCurrency(loc.avg_price_per_sqm)}/م²
                                        </span>
                                    </div>
                                </div>
                                <span className={`text-sm font-bold w-16 text-right ${getTextColor(loc.intensity)}`}>
                                    #{i + 1}
                                </span>
                            </motion.div>
                        );
                    })}
                </div>

                {/* Summary */}
                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-[var(--color-border)]">
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-3 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">أغلى منطقة</p>
                        <p className="text-sm font-bold text-red-400">{sortedLocations[0]?.location}</p>
                        <p className="text-xs text-[var(--color-text-secondary)]">
                            {formatCurrency(sortedLocations[0]?.avg_price_per_sqm || 0)}/م²
                        </p>
                    </div>
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-3 text-center">
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">أرخص منطقة</p>
                        <p className="text-sm font-bold text-green-400">{sortedLocations[sortedLocations.length - 1]?.location}</p>
                        <p className="text-xs text-[var(--color-text-secondary)]">
                            {formatCurrency(sortedLocations[sortedLocations.length - 1]?.avg_price_per_sqm || 0)}/م²
                        </p>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
