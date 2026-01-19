'use client';

import { TrendingUp, ArrowDownRight, ArrowUpRight, DollarSign, Activity } from 'lucide-react';

export default function MarketPage() {
    return (
        <div className="min-h-screen bg-[var(--color-background)] p-6 md:p-12">
            <div className="max-w-7xl mx-auto space-y-12">

                {/* Header */}
                <div className="space-y-4">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)] text-xs font-bold uppercase tracking-wider">
                        <Activity size={12} /> Live Market Data
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-[var(--color-text-primary)]">Egypt Real Estate Pulse</h1>
                    <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl">
                        Real-time market analysis tracking currency inflation vs. asset appreciation across key zones (New Capital, North Coast, New Cairo).
                    </p>
                </div>

                {/* Stats Grid */}
                <div className="grid md:grid-cols-4 gap-6">
                    {[
                        { label: "USD/EGP Parallel", value: "54.10", change: "+1.2%", trend: "up", color: "text-red-500" },
                        { label: "New Capital Avg/m", value: "48,500 EGP", change: "+4.5%", trend: "up", color: "text-green-500" },
                        { label: "Zayed ROI (YoY)", value: "32%", change: "-2.1%", trend: "down", color: "text-amber-500" },
                        { label: "Construction Cost", value: "Index 142", change: "+0.8%", trend: "up", color: "text-slate-500" },
                    ].map((stat, i) => (
                        <div key={i} className="p-6 bg-[var(--color-surface)] rounded-2xl shadow-sm border border-[var(--color-border)]">
                            <p className="text-sm font-semibold text-[var(--color-text-muted)] mb-2">{stat.label}</p>
                            <div className="flex items-end justify-between">
                                <h3 className="text-2xl font-bold text-[var(--color-text-primary)]">{stat.value}</h3>
                                <div className={`flex items-center gap-1 text-sm font-bold ${stat.trend === 'up' && stat.color === 'text-green-500' ? 'text-green-500' : stat.trend === 'up' ? 'text-red-500' : 'text-amber-500'}`}>
                                    {stat.trend === 'up' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                                    {stat.change}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Placeholder Chart Section */}
                <div className="h-96 bg-[var(--color-surface)] rounded-3xl shadow-sm border border-[var(--color-border)] flex items-center justify-center p-8 text-center">
                    <div className="space-y-4 max-w-md">
                        <div className="w-16 h-16 bg-[var(--color-surface-elevated)] rounded-full flex items-center justify-center mx-auto text-[var(--color-text-muted)]">
                            <TrendingUp size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-[var(--color-text-primary)]">Detailed Charts Coming Soon</h3>
                        <p className="text-[var(--color-text-muted)]">
                            We are currently aggregating 5 years of historical data to build the most accurate predictive market engine in Egypt.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
