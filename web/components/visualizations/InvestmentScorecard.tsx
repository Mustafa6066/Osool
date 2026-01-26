"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle2, Activity } from "lucide-react";

interface InvestmentScorecardProps {
    property: {
        id: number;
        title: string;
        price: number;
        location: string;
    };
    analysis: {
        match_score?: number;
        roi_projection?: number;
        risk_level?: "Low" | "Medium" | "High";
        market_trend?: "Bullish" | "Bearish" | "Stable";
        price_verdict?: string;
        location_quality?: number;
        annual_return?: number;
        break_even_years?: number;
    };
}

export default function InvestmentScorecard({ property, analysis }: InvestmentScorecardProps) {
    // Defensive check for required props
    if (!property || !property.title) {
        console.warn('InvestmentScorecard: Missing required property data');
        return null;
    }

    const {
        match_score = 0,
        roi_projection = 0,
        risk_level = "Medium",
        market_trend = "Stable",
        price_verdict = "Fair market value",
        location_quality = 0,
        annual_return = 0,
        break_even_years = 0
    } = analysis;

    // Color coding
    const riskColors = {
        Low: "text-green-500 bg-green-500/10 border-green-500/20",
        Medium: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
        High: "text-red-500 bg-red-500/10 border-red-500/20"
    };

    const trendIcons = {
        Bullish: <TrendingUp className="w-4 h-4 text-green-500" />,
        Bearish: <TrendingDown className="w-4 h-4 text-red-500" />,
        Stable: <Minus className="w-4 h-4 text-blue-500" />
    };

    const trendColors = {
        Bullish: "text-green-500 bg-green-500/10",
        Bearish: "text-red-500 bg-red-500/10",
        Stable: "text-blue-500 bg-blue-500/10"
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] rounded-2xl p-6 border border-white/10 shadow-2xl"
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-1">{property.title}</h3>
                <p className="text-gray-400 text-sm">{property.location}</p>
                <div className="mt-2 flex items-center gap-2">
                    <span className="text-2xl font-bold text-blue-400">
                        {(property.price / 1000000).toFixed(1)}M EGP
                    </span>
                    <span className="text-xs text-gray-500 px-2 py-1 bg-white/5 rounded">
                        {price_verdict}
                    </span>
                </div>
            </div>

            {/* Main Metrics Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Match Score */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="bg-white/5 rounded-xl p-4 border border-white/10"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-xs">Match Score</span>
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="text-3xl font-bold text-white">{match_score}</span>
                        <span className="text-gray-500 text-sm mb-1">/100</span>
                    </div>
                    <div className="mt-2 w-full bg-white/10 rounded-full h-2">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${match_score}%` }}
                            transition={{ duration: 1, delay: 0.3 }}
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
                        />
                    </div>
                </motion.div>

                {/* ROI Projection */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white/5 rounded-xl p-4 border border-white/10"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-xs">ROI Projection</span>
                        <TrendingUp className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="text-3xl font-bold text-green-400">{roi_projection.toFixed(1)}</span>
                        <span className="text-gray-500 text-sm mb-1">% annual</span>
                    </div>
                    {annual_return > 0 && (
                        <p className="text-xs text-gray-400 mt-2">
                            ~{(annual_return / 1000).toFixed(0)}K EGP/year
                        </p>
                    )}
                </motion.div>

                {/* Risk Level */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3 }}
                    className={`rounded-xl p-4 border ${riskColors[risk_level]}`}
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-xs">Risk Level</span>
                        <AlertTriangle className={`w-4 h-4 ${risk_level === "Low" ? "text-green-400" : risk_level === "High" ? "text-red-400" : "text-yellow-400"}`} />
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{risk_level}</span>
                    </div>
                    {break_even_years > 0 && (
                        <p className="text-xs mt-2 opacity-80">
                            Break-even: {break_even_years} years
                        </p>
                    )}
                </motion.div>

                {/* Market Trend */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.4 }}
                    className={`rounded-xl p-4 border border-white/10 ${trendColors[market_trend]}`}
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-xs">Market Trend</span>
                        {trendIcons[market_trend]}
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{market_trend}</span>
                    </div>
                    <div className="flex items-center gap-1 mt-2">
                        {market_trend === "Bullish" && (
                            <>
                                <TrendingUp className="w-3 h-3 text-green-400" />
                                <span className="text-xs text-green-400">Strong growth</span>
                            </>
                        )}
                        {market_trend === "Bearish" && (
                            <>
                                <TrendingDown className="w-3 h-3 text-red-400" />
                                <span className="text-xs text-red-400">Declining</span>
                            </>
                        )}
                        {market_trend === "Stable" && (
                            <>
                                <Activity className="w-3 h-3 text-blue-400" />
                                <span className="text-xs text-blue-400">Steady market</span>
                            </>
                        )}
                    </div>
                </motion.div>
            </div>

            {/* Location Quality */}
            {location_quality > 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="bg-white/5 rounded-xl p-4 border border-white/10"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-gray-400 text-sm">Location Quality</span>
                        <span className="text-yellow-400 text-lg font-bold">{location_quality.toFixed(1)} ⭐</span>
                    </div>
                    <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <motion.div
                                key={star}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: 0.5 + star * 0.05 }}
                                className={`h-2 flex-1 rounded ${star <= location_quality ? "bg-yellow-400" : "bg-white/10"}`}
                            />
                        ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-2">
                        Based on infrastructure, schools, hospitals, and accessibility
                    </p>
                </motion.div>
            )}

            {/* AI Badge */}
            <div className="mt-6 pt-4 border-t border-white/10">
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span>AI-Powered Analysis by AMR</span>
                </div>
            </div>
        </motion.div>
    );
}
