"use client";

import { motion } from "framer-motion";
import { TrendingUp, MapPin, Building2, BarChart3 } from "lucide-react";

interface MarketBenchmarkChartProps {
    market_segment?: {
        name?: string;
        name_ar?: string;
        found?: boolean;
        avg_price_sqm?: number;
        growth_rate?: number;
        tier?: string;
        developers?: string[];
    };
    area_context?: {
        found?: boolean;
        avg_price_sqm?: number;
        growth_rate?: number;
        rental_yield?: number;
        tier1_developers?: string[];
        property_minimums?: Record<string, number>;
        inventory_count?: number;
    };
    avg_price_sqm?: number;
    rental_yield?: number;
    growth_rate?: number;
    isRTL?: boolean;
}

export default function MarketBenchmarkChart({
    market_segment,
    area_context,
    avg_price_sqm = 0,
    rental_yield = 0,
    growth_rate = 0,
    isRTL = false,
}: MarketBenchmarkChartProps) {
    const areaName = market_segment?.name || market_segment?.name_ar || "Area";
    const avgPrice = avg_price_sqm || area_context?.avg_price_sqm || market_segment?.avg_price_sqm || 0;
    const yield_pct = (rental_yield || area_context?.rental_yield || 0.065) * 100;
    const growth_pct = (growth_rate || area_context?.growth_rate || market_segment?.growth_rate || 0.12) * 100;
    const inventory = area_context?.inventory_count || 0;
    const tier1 = area_context?.tier1_developers || market_segment?.developers || [];

    if (avgPrice === 0) return null;

    // Price comparison bars (relative to max)
    const comparisons = [
        { name: "New Cairo", price: 61550 },
        { name: "Sheikh Zayed", price: 64050 },
        { name: "North Coast", price: 76150 },
        { name: "New Capital", price: 45000 },
        { name: "6th October", price: 47000 },
    ];

    // Find if current area is in comparisons, otherwise add it
    const areaLower = areaName.toLowerCase();
    const isInComparisons = comparisons.some(c => areaLower.includes(c.name.toLowerCase().split(" ")[0]));
    if (!isInComparisons && avgPrice > 0) {
        comparisons.push({ name: areaName, price: avgPrice });
    }

    // Mark current area
    const maxPrice = Math.max(...comparisons.map(c => c.price));

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden"
        >
            {/* Header */}
            <div className="px-5 pt-5 pb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                        <BarChart3 className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
                            Market Benchmark
                        </h3>
                        <p className="text-[10px] text-[var(--color-text-muted)]">
                            Price per m² comparison across zones
                        </p>
                    </div>
                </div>
                {inventory > 0 && (
                    <span className="text-[10px] px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-medium">
                        {inventory} listings
                    </span>
                )}
            </div>

            {/* Main metrics */}
            <div className="px-5 pb-4 grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-[var(--color-surface-elevated)]">
                    <div className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Avg Price/m²</div>
                    <div className="text-lg font-bold text-[var(--color-text-primary)]">
                        {avgPrice.toLocaleString()}
                    </div>
                    <div className="text-[9px] text-[var(--color-text-muted)]">EGP</div>
                </div>
                <div className="p-3 rounded-xl bg-[var(--color-surface-elevated)]">
                    <div className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Growth</div>
                    <div className="text-lg font-bold text-emerald-400">
                        +{growth_pct.toFixed(0)}%
                    </div>
                    <div className="text-[9px] text-[var(--color-text-muted)]">YoY</div>
                </div>
                <div className="p-3 rounded-xl bg-[var(--color-surface-elevated)]">
                    <div className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Rental Yield</div>
                    <div className="text-lg font-bold text-cyan-400">
                        {yield_pct.toFixed(1)}%
                    </div>
                    <div className="text-[9px] text-[var(--color-text-muted)]">Annual</div>
                </div>
            </div>

            {/* Horizontal bar chart */}
            <div className="px-5 pb-4">
                <div className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mb-3 font-medium">
                    Area Comparison (EGP/m²)
                </div>
                <div className="space-y-2">
                    {comparisons
                        .sort((a, b) => b.price - a.price)
                        .map((comp, idx) => {
                            const isCurrent = areaLower.includes(comp.name.toLowerCase().split(" ")[0]);
                            const widthPct = (comp.price / maxPrice) * 100;
                            return (
                                <div key={comp.name} className="flex items-center gap-3">
                                    <div className="w-24 text-[11px] text-[var(--color-text-secondary)] truncate text-right">
                                        {comp.name}
                                    </div>
                                    <div className="flex-1 h-5 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ scaleX: 0 }}
                                            animate={{ scaleX: widthPct / 100 }}
                                            transition={{ duration: 0.8, delay: idx * 0.1, ease: "easeOut" }}
                                            style={{ transformOrigin: 'left' }}
                                            className={`h-full rounded-full ${isCurrent
                                                ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
                                                : "bg-gradient-to-r from-gray-600 to-gray-500"
                                                }`}
                                        />
                                    </div>
                                    <div className={`w-16 text-[11px] font-medium ${isCurrent ? "text-emerald-400" : "text-[var(--color-text-secondary)]"}`}>
                                        {(comp.price / 1000).toFixed(1)}k
                                    </div>
                                </div>
                            );
                        })}
                </div>
            </div>

            {/* Developer tier */}
            {tier1.length > 0 && (
                <div className="px-5 pb-5 border-t border-[var(--color-border)]">
                    <div className="text-[9px] uppercase tracking-wider text-[var(--color-text-muted)] mt-3 mb-2 font-medium flex items-center gap-1">
                        <Building2 className="w-3 h-3" /> Top Developers
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                        {tier1.slice(0, 5).map((dev, i) => (
                            <span key={i} className="text-[10px] px-2 py-1 rounded-md bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)] border border-[var(--color-border)]">
                                {dev}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
}
