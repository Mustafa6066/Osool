"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Banknote, Coins, Home, Info } from "lucide-react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";

interface DataPoint {
    year: number;
    label: string;
    cash: number;
    gold: number;
    property: number;
    property_value_only?: number;
    cumulative_rent?: number;
}

interface InflationKillerChartProps {
    initial_investment: number;
    years: number;
    data_points: DataPoint[];
    summary: {
        cash_final: number;
        cash_loss_percent: number;
        gold_final: number;
        gold_gain_percent: number;
        property_final: number;
        property_gain_percent: number;
        property_vs_cash_advantage: number;
        property_vs_gold_advantage: number;
        total_rent_earned?: number;
    };
    assumptions?: {
        inflation_rate: number;
        gold_appreciation: number;
        property_appreciation: number;
        rental_yield: number;
        source?: string;
    };
    verdict: {
        winner: string;
        message_ar: string;
        message_en: string;
    };
}

// Format large numbers to millions
const formatMillions = (value: number): string => {
    return `${(value / 1_000_000).toFixed(1)}M`;
};

// Format currency
const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("en-EG", {
        style: "decimal",
        maximumFractionDigits: 0,
    }).format(value);
};

export default function InflationKillerChart({
    initial_investment,
    years,
    data_points,
    summary,
    assumptions,
    verdict,
}: InflationKillerChartProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] rounded-2xl p-6 border border-white/10 overflow-hidden"
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <span className="text-3xl">🔥</span>
                    <div>
                        <h3 className="text-xl font-bold text-white">Inflation Killer</h3>
                        <p className="text-gray-400 text-sm">
                            {formatMillions(initial_investment)} EGP over {years} years
                        </p>
                    </div>
                </div>
                {assumptions?.source && (
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Info className="w-3 h-3" />
                        <span>{assumptions.source}</span>
                    </div>
                )}
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-3 mb-6">
                {/* Cash Card */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="bg-red-500/10 border border-red-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <Banknote className="w-5 h-5 text-red-400" />
                        <span className="text-sm text-gray-400">Cash</span>
                    </div>
                    <div className="text-2xl font-bold text-red-400">
                        -{summary.cash_loss_percent}%
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                        <TrendingDown className="w-3 h-3" />
                        Inflation eats it
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                        → {formatMillions(summary.cash_final)} EGP
                    </div>
                </motion.div>

                {/* Gold Card */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <Coins className="w-5 h-5 text-yellow-400" />
                        <span className="text-sm text-gray-400">Gold</span>
                    </div>
                    <div className="text-2xl font-bold text-yellow-400">
                        +{summary.gold_gain_percent}%
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                        <TrendingUp className="w-3 h-3" />
                        Volatile gains
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                        → {formatMillions(summary.gold_final)} EGP
                    </div>
                </motion.div>

                {/* Property Card */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="bg-green-500/10 border border-green-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <Home className="w-5 h-5 text-green-400" />
                        <span className="text-sm text-gray-400">Property</span>
                    </div>
                    <div className="text-2xl font-bold text-green-400">
                        +{summary.property_gain_percent}%
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                        <TrendingUp className="w-3 h-3" />
                        + Rental Income
                    </div>
                    <div className="text-xs text-gray-600 mt-2">
                        → {formatMillions(summary.property_final)} EGP
                    </div>
                </motion.div>
            </div>

            {/* Chart */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white/5 rounded-xl p-4 border border-white/10 mb-4"
            >
                <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={data_points} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorProperty" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorGold" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#eab308" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorCash" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                        <XAxis
                            dataKey="label"
                            stroke="#94a3b8"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="#94a3b8"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            tickFormatter={formatMillions}
                            width={50}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#1a1c2e",
                                border: "1px solid #ffffff20",
                                borderRadius: "8px",
                                padding: "12px",
                            }}
                            labelStyle={{ color: "#fff", fontWeight: "bold", marginBottom: "8px" }}
                            formatter={(value: number, name: string) => [
                                `${formatCurrency(value)} EGP`,
                                name.charAt(0).toUpperCase() + name.slice(1),
                            ]}
                        />
                        <Legend
                            wrapperStyle={{ paddingTop: "20px" }}
                            formatter={(value) => (
                                <span className="text-gray-400 text-sm">
                                    {value.charAt(0).toUpperCase() + value.slice(1)}
                                </span>
                            )}
                        />
                        <Area
                            type="monotone"
                            dataKey="property"
                            stroke="#10b981"
                            strokeWidth={2}
                            fill="url(#colorProperty)"
                            name="property"
                        />
                        <Area
                            type="monotone"
                            dataKey="gold"
                            stroke="#eab308"
                            strokeWidth={2}
                            fill="url(#colorGold)"
                            name="gold"
                        />
                        <Area
                            type="monotone"
                            dataKey="cash"
                            stroke="#ef4444"
                            strokeWidth={2}
                            fill="url(#colorCash)"
                            name="cash"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </motion.div>

            {/* Verdict */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="bg-green-500/10 border border-green-500/20 rounded-xl p-4"
            >
                <div className="text-center">
                    <div className="flex items-center justify-center gap-2 mb-2">
                        <span className="text-2xl">🏆</span>
                        <span className="text-3xl font-bold text-green-400">
                            +{formatMillions(summary.property_vs_cash_advantage)} EGP
                        </span>
                    </div>
                    <p className="text-sm text-gray-300" dir="rtl">
                        {verdict.message_ar}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">{verdict.message_en}</p>
                </div>
            </motion.div>

            {/* Rental Income Callout */}
            {summary.total_rent_earned && summary.total_rent_earned > 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.6 }}
                    className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-400"
                >
                    <span>💰</span>
                    <span>
                        Total rental income: {formatCurrency(summary.total_rent_earned)} EGP over {years} years
                    </span>
                </motion.div>
            )}
        </motion.div>
    );
}
