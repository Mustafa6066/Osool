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
    isRTL?: boolean;
}

export default function InvestmentScorecard({ property, analysis, isRTL = false }: InvestmentScorecardProps) {
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

    // i18n labels
    const labels = {
        matchScore: isRTL ? 'درجة التوافق' : 'Match Score',
        roiProjection: isRTL ? 'العائد على الاستثمار' : 'ROI Projection',
        annual: isRTL ? '% سنوياً' : '% annual',
        riskLevel: isRTL ? 'مستوى المخاطرة' : 'Risk Level',
        marketTrend: isRTL ? 'اتجاه السوق' : 'Market Trend',
        locationQuality: isRTL ? 'جودة الموقع' : 'Location Quality',
        breakEven: isRTL ? 'نقطة التعادل:' : 'Break-even:',
        years: isRTL ? 'سنة' : 'years',
        strongGrowth: isRTL ? 'نمو قوي' : 'Strong growth',
        declining: isRTL ? 'هبوط' : 'Declining',
        steadyMarket: isRTL ? 'سوق مستقر' : 'Steady market',
        locationDesc: isRTL ? 'بناءً على البنية التحتية والمدارس والمستشفيات وإمكانية الوصول' : 'Based on infrastructure, schools, hospitals, and accessibility',
        aiAnalysis: isRTL ? 'تحليل أصول الذكي' : 'Osool AI Analysis',
        currency: isRTL ? 'ج.م' : 'EGP',
        riskLabels: {
            Low: isRTL ? 'منخفض' : 'Low',
            Medium: isRTL ? 'متوسط' : 'Medium',
            High: isRTL ? 'مرتفع' : 'High'
        },
        trendLabels: {
            Bullish: isRTL ? 'صاعد' : 'Bullish',
            Bearish: isRTL ? 'هابط' : 'Bearish',
            Stable: isRTL ? 'مستقر' : 'Stable'
        }
    };

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
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, type: "spring", stiffness: 100, damping: 18 }}
            className="bg-[var(--color-surface)]/80 backdrop-blur-sm rounded-2xl p-6 border border-[var(--color-border)] shadow-2xl"
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-1">{property.title}</h3>
                <p className="text-[var(--color-text-secondary)] text-sm">{property.location}</p>
                <div className="mt-2 flex items-center gap-2">
                    <span className="text-2xl font-bold text-blue-400">
                        {(property.price / 1000000).toFixed(1)}M {labels.currency}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)] px-2 py-1 bg-[var(--color-surface-elevated)]/50 rounded">
                        {price_verdict}
                    </span>
                </div>
            </div>

            {/* Main Metrics Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Match Score */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1, type: "spring", stiffness: 120, damping: 16 }}
                    className="bg-[var(--color-surface-elevated)]/50 backdrop-blur-sm rounded-xl p-4 border border-[var(--color-border)]"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[var(--color-text-secondary)] text-xs">{labels.matchScore}</span>
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="text-3xl font-bold text-[var(--color-text-primary)]">{match_score}</span>
                        <span className="text-[var(--color-text-muted)] text-sm mb-1">/100</span>
                    </div>
                    <div className="mt-2 w-full bg-[var(--color-border)] rounded-full h-2.5 overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${match_score}%` }}
                            transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
                            className="bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 h-2.5 rounded-full shadow-[0_0_8px_rgba(56,189,248,0.4)]"
                        />
                    </div>
                </motion.div>

                {/* ROI Projection */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 120, damping: 16 }}
                    className="bg-[var(--color-surface-elevated)]/50 backdrop-blur-sm rounded-xl p-4 border border-[var(--color-border)]"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[var(--color-text-secondary)] text-xs">{labels.roiProjection}</span>
                        <TrendingUp className="w-4 h-4 text-green-400" />
                    </div>
                    <div className="flex items-end gap-2">
                        <span className="text-3xl font-bold text-green-400">{roi_projection.toFixed(1)}</span>
                        <span className="text-[var(--color-text-muted)] text-sm mb-1">{labels.annual}</span>
                    </div>
                    {annual_return > 0 && (
                        <p className="text-xs text-[var(--color-text-secondary)] mt-2">
                            ~{(annual_return / 1000).toFixed(0)}K {labels.currency}/{isRTL ? 'سنة' : 'year'}
                        </p>
                    )}
                </motion.div>

                {/* Risk Level */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.3, type: "spring", stiffness: 120, damping: 16 }}
                    className={`backdrop-blur-sm rounded-xl p-4 border ${riskColors[risk_level]}`}
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[var(--color-text-secondary)] text-xs">{labels.riskLevel}</span>
                        <AlertTriangle className={`w-4 h-4 ${risk_level === "Low" ? "text-green-400" : risk_level === "High" ? "text-red-400" : "text-yellow-400"}`} />
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{labels.riskLabels[risk_level]}</span>
                    </div>
                    {break_even_years > 0 && (
                        <p className="text-xs mt-2 opacity-80">
                            {labels.breakEven} {break_even_years} {labels.years}
                        </p>
                    )}
                </motion.div>

                {/* Market Trend */}
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.4, type: "spring", stiffness: 120, damping: 16 }}
                    className={`backdrop-blur-sm rounded-xl p-4 border border-[var(--color-border)] ${trendColors[market_trend]}`}
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[var(--color-text-secondary)] text-xs">{labels.marketTrend}</span>
                        {trendIcons[market_trend]}
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold">{labels.trendLabels[market_trend]}</span>
                    </div>
                    <div className="flex items-center gap-1 mt-2">
                        {market_trend === "Bullish" && (
                            <>
                                <TrendingUp className="w-3 h-3 text-green-400" />
                                <span className="text-xs text-green-400">{labels.strongGrowth}</span>
                            </>
                        )}
                        {market_trend === "Bearish" && (
                            <>
                                <TrendingDown className="w-3 h-3 text-red-400" />
                                <span className="text-xs text-red-400">{labels.declining}</span>
                            </>
                        )}
                        {market_trend === "Stable" && (
                            <>
                                <Activity className="w-3 h-3 text-blue-400" />
                                <span className="text-xs text-blue-400">{labels.steadyMarket}</span>
                            </>
                        )}
                    </div>
                </motion.div>
            </div>

            {/* Location Quality */}
            {location_quality > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, type: "spring", stiffness: 120, damping: 16 }}
                    className="bg-[var(--color-surface-elevated)]/50 backdrop-blur-sm rounded-xl p-4 border border-[var(--color-border)]"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-[var(--color-text-secondary)] text-sm">{labels.locationQuality}</span>
                        <span className="text-yellow-400 text-lg font-bold">{location_quality.toFixed(1)} ⭐</span>
                    </div>
                    <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <motion.div
                                key={star}
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ delay: 0.5 + star * 0.05 }}
                                className={`h-2 flex-1 rounded ${star <= location_quality ? "bg-yellow-400" : "bg-[var(--color-border)]"}`}
                            />
                        ))}
                    </div>
                    <p className="text-xs text-[var(--color-text-secondary)] mt-2">
                        {labels.locationDesc}
                    </p>
                </motion.div>
            )}

            {/* AI Badge */}
            <div className="mt-6 pt-4 border-t border-[var(--color-border)]">
                <div className="flex items-center justify-center gap-2 text-xs text-[var(--color-text-muted)]">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span>{labels.aiAnalysis}</span>
                </div>
            </div>
        </motion.div>
    );
}

