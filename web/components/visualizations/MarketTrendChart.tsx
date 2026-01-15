"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Activity, AlertCircle } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import ClientOnly from "../ClientOnly";


interface MarketTrendChartProps {
    location: string;
    data: {
        historical?: Array<{
            period: string;
            avg_price: number;
            volume?: number;
        }>;
        forecast?: Array<{
            period: string;
            predicted_price: number;
        }>;
        current_price: number;
        trend: "Bullish" | "Bearish" | "Stable";
        yoy_change?: number;
        momentum?: string;
    };
}

export default function MarketTrendChart({ location, data }: MarketTrendChartProps) {
    const { historical = [], forecast = [], current_price, trend, yoy_change = 0, momentum = "" } = data;

    // Combine historical and forecast data
    const combinedData = [
        ...historical.map(d => ({
            period: d.period,
            price: d.avg_price,
            volume: d.volume,
            type: "historical"
        })),
        ...forecast.map(d => ({
            period: d.period,
            price: d.predicted_price,
            type: "forecast"
        }))
    ];

    // Trend colors and icons
    const trendConfig = {
        Bullish: {
            color: "#10b981",
            gradient: ["#10b981", "#059669"],
            icon: <TrendingUp className="w-5 h-5" />,
            bg: "bg-green-500/10",
            border: "border-green-500/20",
            text: "text-green-400"
        },
        Bearish: {
            color: "#ef4444",
            gradient: ["#ef4444", "#dc2626"],
            icon: <TrendingDown className="w-5 h-5" />,
            bg: "bg-red-500/10",
            border: "border-red-500/20",
            text: "text-red-400"
        },
        Stable: {
            color: "#3b82f6",
            gradient: ["#3b82f6", "#2563eb"],
            icon: <Activity className="w-5 h-5" />,
            bg: "bg-blue-500/10",
            border: "border-blue-500/20",
            text: "text-blue-400"
        }
    };

    const config = trendConfig[trend];

    return (
        <ClientOnly>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] rounded-2xl p-6 border border-white/10 shadow-2xl"
            >
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <Activity className="w-5 h-5 text-blue-400" />
                            Market Trends
                        </h3>
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.2, type: "spring" }}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bg} border ${config.border}`}
                        >
                            {config.icon}
                            <span className={`font-semibold text-sm ${config.text}`}>{trend}</span>
                        </motion.div>
                    </div>
                    <p className="text-gray-400 text-sm">{location}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                    {/* Current Price */}
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white/5 rounded-xl p-4 border border-white/10"
                    >
                        <div className="text-xs text-gray-400 mb-1">Current Avg Price</div>
                        <div className="text-2xl font-bold text-white">
                            {(current_price / 1000).toFixed(0)}K
                        </div>
                        <div className="text-xs text-gray-500 mt-1">EGP/sqm</div>
                    </motion.div>

                    {/* YoY Change */}
                    {yoy_change !== 0 && (
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className={`rounded-xl p-4 border ${config.bg} ${config.border}`}
                        >
                            <div className="text-xs text-gray-400 mb-1">YoY Change</div>
                            <div className={`text-2xl font-bold ${config.text} flex items-center gap-1`}>
                                {yoy_change > 0 ? "+" : ""}{yoy_change.toFixed(1)}%
                                {yoy_change > 0 ? (
                                    <TrendingUp className="w-4 h-4" />
                                ) : (
                                    <TrendingDown className="w-4 h-4" />
                                )}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">vs last year</div>
                        </motion.div>
                    )}

                    {/* Momentum */}
                    {momentum && (
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-white/5 rounded-xl p-4 border border-white/10"
                        >
                            <div className="text-xs text-gray-400 mb-1">Momentum</div>
                            <div className="text-sm font-semibold text-white">
                                {momentum}
                            </div>
                        </motion.div>
                    )}
                </div>

                {/* Chart */}
                {combinedData.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.4 }}
                        className="bg-white/5 rounded-xl p-4 border border-white/10 mb-6"
                    >
                        <h4 className="text-sm font-semibold text-gray-300 mb-4">Price Movement</h4>
                        <ResponsiveContainer width="100%" height={250}>
                            <AreaChart data={combinedData}>
                                <defs>
                                    <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={config.color} stopOpacity={0.3} />
                                        <stop offset="95%" stopColor={config.color} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis
                                    dataKey="period"
                                    stroke="#94a3b8"
                                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                                />
                                <YAxis
                                    stroke="#94a3b8"
                                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                                    tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "#1a1c2e",
                                        border: "1px solid rgba(255,255,255,0.1)",
                                        borderRadius: "8px",
                                        color: "#fff"
                                    }}
                                    formatter={(value: number, name: string) => [
                                        `${(value / 1000).toFixed(1)}K EGP/sqm`,
                                        name === "price" ? "Price" : name
                                    ]}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="price"
                                    stroke={config.color}
                                    strokeWidth={3}
                                    fill="url(#priceGradient)"
                                    dot={{ fill: config.color, r: 4 }}
                                />
                            </AreaChart>
                        </ResponsiveContainer>

                        {/* Legend */}
                        <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-400">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: config.color }} />
                                <span>Historical</span>
                            </div>
                            {forecast.length > 0 && (
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: config.color }} />
                                    <span>Forecast</span>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Insights */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className={`p-4 rounded-xl ${config.bg} border ${config.border}`}
                >
                    <div className="flex items-start gap-3">
                        <AlertCircle className={`w-5 h-5 ${config.text} flex-shrink-0 mt-0.5`} />
                        <div>
                            <h5 className={`text-sm font-semibold ${config.text} mb-2`}>Market Insights</h5>
                            <div className="space-y-2 text-xs text-gray-400">
                                {trend === "Bullish" && (
                                    <>
                                        <p>• {location} is experiencing strong price growth ({yoy_change > 0 ? `+${yoy_change.toFixed(1)}%` : ""} YoY)</p>
                                        <p>• High demand and limited supply driving prices up</p>
                                        <p>• Consider buying now before further appreciation</p>
                                        <p>• Expected to continue upward trend in next 12-24 months</p>
                                    </>
                                )}
                                {trend === "Bearish" && (
                                    <>
                                        <p>• {location} showing declining prices ({yoy_change < 0 ? `${yoy_change.toFixed(1)}%` : ""} YoY)</p>
                                        <p>• Potential buying opportunity if fundamentals are strong</p>
                                        <p>• Consider negotiating for better prices</p>
                                        <p>• Monitor market for stabilization signals</p>
                                    </>
                                )}
                                {trend === "Stable" && (
                                    <>
                                        <p>• {location} market is stable with steady prices</p>
                                        <p>• Good time for long-term investment</p>
                                        <p>• Predictable returns with lower volatility</p>
                                        <p>• Focus on rental yield and location quality</p>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Data Source */}
                <div className="mt-6 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                        <span>Analysis powered by AMR using 3,000+ transactions</span>
                    </div>
                </div>
            </motion.div>
        </ClientOnly>
    );
}
