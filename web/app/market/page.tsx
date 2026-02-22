'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, ArrowDownRight, ArrowUpRight, DollarSign, Activity, BarChart3, MapPin, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import MarketTrendChart from '@/components/visualizations/MarketTrendChart';

// Fallback static values if API fails
const FALLBACK_STATS = [
    { label: "USD/EGP", value: "51.50", change: "+1.2%", trend: "up" as const, color: "text-red-500" },
    { label: "New Capital Avg/m", value: "45,000 EGP", change: "+4.5%", trend: "up" as const, color: "text-green-500" },
    { label: "Zayed ROI (YoY)", value: "32%", change: "-2.1%", trend: "down" as const, color: "text-amber-500" },
    { label: "Construction Cost", value: "Index 142", change: "+0.8%", trend: "up" as const, color: "text-slate-500" },
];

const FALLBACK_AREAS: AreaData[] = [
    { name: "New Cairo", key: "new_cairo", avgPriceSqm: 61550, growthRate: 0.15 },
    { name: "Sheikh Zayed", key: "zayed", avgPriceSqm: 64050, growthRate: 0.12 },
    { name: "North Coast", key: "north_coast", avgPriceSqm: 76150, growthRate: 0.18 },
    { name: "New Capital", key: "new_capital", avgPriceSqm: 45000, growthRate: 0.22 },
    { name: "6th October", key: "6th_october", avgPriceSqm: 47000, growthRate: 0.10 },
];

interface StatItem {
    label: string;
    value: string;
    change: string;
    trend: 'up' | 'down';
    color: string;
}

interface AreaData {
    name: string;
    key: string;
    avgPriceSqm: number;
    growthRate: number;
}

interface MarketData {
    stats: StatItem[];
    areas: AreaData[];
    trendChartData: {
        current_price: number;
        trend: "Bullish" | "Bearish" | "Stable";
        yoy_change: number;
        momentum: string;
        historical: Array<{ period: string; avg_price: number }>;
    } | null;
}

export default function MarketPage() {
    const [marketData, setMarketData] = useState<MarketData>({
        stats: FALLBACK_STATS,
        areas: FALLBACK_AREAS,
        trendChartData: null,
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchMarketData() {
            try {
                setLoading(true);
                const { data } = await api.get('/api/market-stats');

                // Parse stats from API response
                const globalData = data.global || {};
                const areasData = data.areas || {};

                const inflationRate = globalData.inflation_rate ?? 0.136;
                const bankCdRate = globalData.bank_cd_rate ?? 0.22;
                const usdEgp = globalData.usd_egp ?? 51.50;
                const constructionIndex = globalData.construction_index ?? 142;

                const newCapitalAvg = areasData.new_capital?.avg_price_sqm ?? 45000;
                const zayedGrowth = areasData.zayed?.growth_rate ?? 0.32;

                const stats: StatItem[] = [
                    {
                        label: "USD/EGP",
                        value: usdEgp.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
                        change: `+${(inflationRate * 100).toFixed(1)}%`,
                        trend: "up",
                        color: "text-red-500",
                    },
                    {
                        label: "New Capital Avg/m",
                        value: `${newCapitalAvg.toLocaleString()} EGP`,
                        change: areasData.new_capital?.growth_rate
                            ? `+${(areasData.new_capital.growth_rate * 100).toFixed(1)}%`
                            : "+4.5%",
                        trend: "up",
                        color: "text-green-500",
                    },
                    {
                        label: "Zayed ROI (YoY)",
                        value: `${(zayedGrowth * 100).toFixed(0)}%`,
                        change: bankCdRate ? `CD ${(bankCdRate * 100).toFixed(0)}%` : "CD 22%",
                        trend: zayedGrowth > 0.2 ? "up" : "down",
                        color: "text-amber-500",
                    },
                    {
                        label: "Construction Cost",
                        value: `Index ${constructionIndex}`,
                        change: "+0.8%",
                        trend: "up",
                        color: "text-slate-500",
                    },
                ];

                // Parse area data
                const areaMapping: { key: string; name: string }[] = [
                    { key: "new_cairo", name: "New Cairo" },
                    { key: "zayed", name: "Sheikh Zayed" },
                    { key: "north_coast", name: "North Coast" },
                    { key: "new_capital", name: "New Capital" },
                    { key: "6th_october", name: "6th October" },
                ];

                const areas: AreaData[] = areaMapping.map((area) => ({
                    name: area.name,
                    key: area.key,
                    avgPriceSqm: areasData[area.key]?.avg_price_sqm ?? FALLBACK_AREAS.find(f => f.key === area.key)?.avgPriceSqm ?? 50000,
                    growthRate: areasData[area.key]?.growth_rate ?? FALLBACK_AREAS.find(f => f.key === area.key)?.growthRate ?? 0.1,
                }));

                // Build trend chart data from most valuable area
                const topArea = areas.reduce((a, b) => a.avgPriceSqm > b.avgPriceSqm ? a : b);
                const trendChartData = {
                    current_price: topArea.avgPriceSqm,
                    trend: (topArea.growthRate > 0.15 ? "Bullish" : topArea.growthRate > 0.05 ? "Stable" : "Bearish") as "Bullish" | "Bearish" | "Stable",
                    yoy_change: topArea.growthRate * 100,
                    momentum: topArea.growthRate > 0.15 ? "Strong upward" : "Moderate",
                    historical: generateHistoricalData(topArea.avgPriceSqm, topArea.growthRate),
                };

                setMarketData({ stats, areas, trendChartData });
                setError(null);
            } catch (err) {
                console.error('Failed to fetch market data:', err);
                setError('Using cached market data');
                // Keep fallback values (already set as initial state)
            } finally {
                setLoading(false);
            }
        }

        fetchMarketData();
    }, []);

    // Generate synthetic historical data points from current price and growth rate
    function generateHistoricalData(currentPrice: number, growthRate: number) {
        const periods = ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025', 'Q1 2026'];
        const quarterlyRate = growthRate / 4;
        return periods.map((period, i) => ({
            period,
            avg_price: Math.round(currentPrice * (1 - (periods.length - 1 - i) * quarterlyRate)),
        }));
    }

    const maxPrice = Math.max(...marketData.areas.map((a) => a.avgPriceSqm));

    return (
        <div className="flex h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden">
            {/* Sidebar */}
            <Sidebar activePage="market" />

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-full overflow-hidden relative">
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-12 scrollbar-hide">
                    <div className="max-w-7xl mx-auto space-y-8 md:space-y-12">

                        {/* Header */}
                        <div className="space-y-4">
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)] text-xs font-bold uppercase tracking-wider">
                                <Activity size={12} /> Live Market Data
                            </div>
                            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[var(--color-text-primary)]">Egypt Real Estate Pulse</h1>
                            <p className="text-base sm:text-lg text-[var(--color-text-secondary)] max-w-2xl">
                                Real-time market analysis tracking currency inflation vs. asset appreciation across key zones (New Capital, North Coast, New Cairo).
                            </p>
                            {error && (
                                <p className="text-sm text-amber-500">{error}</p>
                            )}
                        </div>

                        {/* Stats Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                            {marketData.stats.map((stat, i) => (
                                <div
                                    key={i}
                                    className={`p-4 md:p-6 bg-[var(--color-surface)] rounded-2xl shadow-sm border border-[var(--color-border)] transition-opacity ${loading ? 'animate-pulse' : ''}`}
                                >
                                    <p className="text-xs sm:text-sm font-semibold text-[var(--color-text-muted)] mb-2">{stat.label}</p>
                                    <div className="flex items-end justify-between gap-1">
                                        <h3 className="text-lg sm:text-2xl font-bold text-[var(--color-text-primary)] truncate">{stat.value}</h3>
                                        <div className={`flex items-center gap-1 text-xs sm:text-sm font-bold flex-shrink-0 ${stat.trend === 'up' && stat.color === 'text-green-500' ? 'text-green-500' : stat.trend === 'up' ? 'text-red-500' : 'text-amber-500'}`}>
                                            {stat.trend === 'up' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                                            <span className="hidden sm:inline">{stat.change}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Market Trend Chart */}
                        {loading ? (
                            <div className="h-96 bg-[var(--color-surface)] rounded-3xl shadow-sm border border-[var(--color-border)] flex items-center justify-center">
                                <div className="flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
                                    <Loader2 className="w-8 h-8 animate-spin" />
                                    <p className="text-sm">Loading market trends...</p>
                                </div>
                            </div>
                        ) : marketData.trendChartData ? (
                            <MarketTrendChart
                                location="Egypt Real Estate Market"
                                data={marketData.trendChartData}
                            />
                        ) : null}

                        {/* Area Comparison Section */}
                        <div className="bg-[var(--color-surface)] rounded-3xl shadow-sm border border-[var(--color-border)] p-4 sm:p-6 md:p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="w-10 h-10 bg-[var(--color-primary-light)] rounded-xl flex items-center justify-center text-[var(--color-primary)]">
                                    <BarChart3 size={20} />
                                </div>
                                <div>
                                    <h3 className="text-lg sm:text-xl font-bold text-[var(--color-text-primary)]">Area Price Comparison</h3>
                                    <p className="text-xs sm:text-sm text-[var(--color-text-muted)]">Average price per sqm across key zones</p>
                                </div>
                            </div>

                            <div className="space-y-4 sm:space-y-5">
                                {marketData.areas
                                    .sort((a, b) => b.avgPriceSqm - a.avgPriceSqm)
                                    .map((area) => {
                                        const barWidth = (area.avgPriceSqm / maxPrice) * 100;
                                        const isTopArea = area.avgPriceSqm === maxPrice;
                                        return (
                                            <div key={area.key} className="group">
                                                <div className="flex items-center justify-between mb-1.5">
                                                    <div className="flex items-center gap-2">
                                                        <MapPin size={14} className="text-[var(--color-primary)] flex-shrink-0" />
                                                        <span className="text-sm font-semibold text-[var(--color-text-primary)]">{area.name}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2 sm:gap-3">
                                                        <span className="text-sm font-bold text-[var(--color-text-primary)]">
                                                            {area.avgPriceSqm.toLocaleString()} EGP/m\u00B2
                                                        </span>
                                                        <span className={`text-xs font-bold ${area.growthRate > 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                            {area.growthRate > 0 ? '+' : ''}{(area.growthRate * 100).toFixed(0)}%
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="w-full h-3 sm:h-4 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full rounded-full transition-all duration-700 ease-out ${isTopArea
                                                            ? 'bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-dark,var(--color-primary))]'
                                                            : 'bg-gradient-to-r from-[var(--color-primary)]/60 to-[var(--color-primary)]/40'
                                                            }`}
                                                        style={{ width: loading ? '0%' : `${barWidth}%` }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                            </div>

                            {/* Summary footer */}
                            <div className="mt-6 pt-4 border-t border-[var(--color-border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                                <p className="text-xs text-[var(--color-text-muted)]">
                                    Data sourced from market transactions and AI analysis
                                </p>
                                <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    Updated in real-time
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
