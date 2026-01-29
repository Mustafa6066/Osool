"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    TrendingUp,
    Shield,
    Building2,
    MapPin,
    Flame,
    BarChart3,
    ChevronDown,
    Sparkles,
    Target,
    AlertTriangle,
    ArrowRight,
    Check,
} from "lucide-react";

interface UnifiedAnalyticsProps {
    visualizations: Array<{
        type: string;
        data: any;
    }>;
    isRTL?: boolean;
}

// Format price compactly
const formatPrice = (price: number): string => {
    if (!price) return "—";
    if (price >= 1_000_000) return `${(price / 1_000_000).toFixed(1)}M`;
    if (price >= 1_000) return `${(price / 1_000).toFixed(0)}K`;
    return price.toString();
};

// Analytics category with icon and color
const ANALYTICS_CONFIG: Record<string, { icon: any; label: string; labelAr: string; color: string; bgColor: string }> = {
    investment_scorecard: {
        icon: Target,
        label: "Investment",
        labelAr: "الاستثمار",
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10",
    },
    comparison_matrix: {
        icon: BarChart3,
        label: "Compare",
        labelAr: "مقارنة",
        color: "text-blue-400",
        bgColor: "bg-blue-500/10",
    },
    inflation_killer: {
        icon: Shield,
        label: "Protection",
        labelAr: "حماية",
        color: "text-purple-400",
        bgColor: "bg-purple-500/10",
    },
    area_analysis: {
        icon: MapPin,
        label: "Area",
        labelAr: "المنطقة",
        color: "text-cyan-400",
        bgColor: "bg-cyan-500/10",
    },
    developer_analysis: {
        icon: Building2,
        label: "Developer",
        labelAr: "المطور",
        color: "text-indigo-400",
        bgColor: "bg-indigo-500/10",
    },
    la2ta_alert: {
        icon: Flame,
        label: "Hot Deal",
        labelAr: "لقطة",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10",
    },
    reality_check: {
        icon: AlertTriangle,
        label: "Alert",
        labelAr: "تنبيه",
        color: "text-orange-400",
        bgColor: "bg-orange-500/10",
    },
    market_trend_chart: {
        icon: TrendingUp,
        label: "Trends",
        labelAr: "الاتجاهات",
        color: "text-teal-400",
        bgColor: "bg-teal-500/10",
    },
};

// Check if visualization has meaningful content
const hasContent = (viz: { type: string; data: any }): boolean => {
    const { type, data } = viz;
    if (!data) return false;

    switch (type) {
        case "la2ta_alert":
            return data.properties?.length > 0;
        case "reality_check":
            return data.alternatives?.length > 0 || data.message_ar || data.message_en;
        case "comparison_matrix":
            return data.properties?.length > 0;
        case "investment_scorecard":
            return data.property || data.analysis;
        case "area_analysis":
            return data.area || data.areas?.length > 0;
        case "developer_analysis":
            return data.developer || data.developers?.length > 0;
        case "inflation_killer":
            return data.projections || data.summary;
        default:
            return true;
    }
};

// Compact insight card for each visualization type
function InsightCard({
    viz,
    isRTL,
    isExpanded,
    onToggle,
}: {
    viz: { type: string; data: any };
    isRTL: boolean;
    isExpanded: boolean;
    onToggle: () => void;
}) {
    const config = ANALYTICS_CONFIG[viz.type] || {
        icon: Sparkles,
        label: viz.type,
        labelAr: viz.type,
        color: "text-gray-400",
        bgColor: "bg-gray-500/10",
    };

    const Icon = config.icon;
    const label = isRTL ? config.labelAr : config.label;

    // Extract key metric based on type
    const getKeyMetric = (): { value: string; label: string } => {
        const { type, data } = viz;
        switch (type) {
            case "investment_scorecard":
                return {
                    value: `${data?.analysis?.match_score || data?.property?.wolf_score || "—"}/100`,
                    label: isRTL ? "تقييم" : "Score",
                };
            case "comparison_matrix":
                return {
                    value: `${data?.properties?.length || 0}`,
                    label: isRTL ? "عقار" : "Props",
                };
            case "la2ta_alert":
                return {
                    value: `${data?.properties?.length || 0}`,
                    label: isRTL ? "فرصة" : "Deals",
                };
            case "area_analysis":
                const avgPrice = data?.area?.avg_price_per_sqm || data?.areas?.[0]?.avg_price_per_sqm;
                return {
                    value: avgPrice ? `${Math.round(avgPrice / 1000)}K` : "—",
                    label: isRTL ? "متر²" : "/sqm",
                };
            case "developer_analysis":
                return {
                    value: `${data?.developer?.trust_score || "—"}%`,
                    label: isRTL ? "ثقة" : "Trust",
                };
            case "inflation_killer":
                return {
                    value: data?.protection_rate ? `+${data.protection_rate}%` : "—",
                    label: isRTL ? "حماية" : "Shield",
                };
            default:
                return { value: "—", label: "" };
        }
    };

    const metric = getKeyMetric();

    // Get summary text
    const getSummary = (): string => {
        const { type, data } = viz;
        switch (type) {
            case "investment_scorecard":
                return isRTL
                    ? data?.analysis?.verdict_ar || "تحليل الاستثمار"
                    : data?.analysis?.verdict_en || "Investment analysis";
            case "la2ta_alert":
                return isRTL
                    ? `${data?.properties?.length || 0} فرصة تحت سعر السوق`
                    : `${data?.properties?.length || 0} opportunities below market`;
            case "area_analysis":
                return isRTL
                    ? data?.area?.name || "تحليل المنطقة"
                    : data?.area?.name || "Area analysis";
            case "developer_analysis":
                return isRTL
                    ? data?.developer?.name || "تحليل المطور"
                    : data?.developer?.name || "Developer analysis";
            case "comparison_matrix":
                return isRTL
                    ? `مقارنة ${data?.properties?.length || 0} عقارات`
                    : `Comparing ${data?.properties?.length || 0} properties`;
            case "reality_check":
                return isRTL
                    ? data?.message_ar?.slice(0, 50) + "..." || "تنبيه ذكي"
                    : data?.message_en?.slice(0, 50) + "..." || "Smart alert";
            default:
                return "";
        }
    };

    return (
        <motion.div
            layout
            className="bg-[#1a2a32] rounded-xl border border-white/5 overflow-hidden"
        >
            {/* Header - Always visible */}
            <button
                onClick={onToggle}
                className="w-full p-3 flex items-center gap-3 hover:bg-white/5 transition-colors"
                dir={isRTL ? "rtl" : "ltr"}
            >
                {/* Icon */}
                <div className={`p-2 rounded-lg ${config.bgColor}`}>
                    <Icon className={`w-4 h-4 ${config.color}`} />
                </div>

                {/* Label & Summary */}
                <div className="flex-1 text-start min-w-0">
                    <div className="flex items-center gap-2">
                        <span className={`text-sm font-semibold ${config.color}`}>
                            {label}
                        </span>
                    </div>
                    <p className="text-xs text-gray-400 truncate mt-0.5">
                        {getSummary()}
                    </p>
                </div>

                {/* Metric */}
                <div className="text-end flex-shrink-0">
                    <div className="text-sm font-bold text-white">{metric.value}</div>
                    <div className="text-[10px] text-gray-500">{metric.label}</div>
                </div>

                {/* Expand Arrow */}
                <ChevronDown
                    className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                />
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-3 pt-0 border-t border-white/5">
                            <ExpandedContent viz={viz} isRTL={isRTL} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// Expanded content for each visualization type
function ExpandedContent({ viz, isRTL }: { viz: { type: string; data: any }; isRTL: boolean }) {
    const { type, data } = viz;

    switch (type) {
        case "investment_scorecard":
            return (
                <div className="space-y-2 pt-2">
                    {data?.property && (
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-400">{isRTL ? "العقار" : "Property"}</span>
                            <span className="text-white font-medium">{data.property.title}</span>
                        </div>
                    )}
                    {data?.analysis?.factors && (
                        <div className="grid grid-cols-2 gap-2 mt-2">
                            {Object.entries(data.analysis.factors).slice(0, 4).map(([key, val]: [string, any]) => (
                                <div key={key} className="bg-white/5 rounded-lg p-2 text-center">
                                    <div className="text-xs text-gray-400 capitalize">{key}</div>
                                    <div className="text-sm font-semibold text-emerald-400">{val}/100</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            );

        case "la2ta_alert":
            return (
                <div className="space-y-2 pt-2">
                    {data?.properties?.slice(0, 2).map((prop: any, idx: number) => (
                        <div
                            key={idx}
                            className="flex items-center justify-between bg-amber-500/5 rounded-lg p-2 border border-amber-500/20"
                        >
                            <div className="min-w-0">
                                <div className="text-sm text-white font-medium truncate">{prop.title}</div>
                                <div className="text-xs text-gray-400">{prop.location}</div>
                            </div>
                            <div className="text-end flex-shrink-0">
                                <div className="text-sm font-bold text-amber-400">{formatPrice(prop.price)}</div>
                                {prop.savings > 0 && (
                                    <div className="text-[10px] text-green-400">
                                        {isRTL ? "وفّر" : "Save"} {formatPrice(prop.savings)}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            );

        case "comparison_matrix":
            return (
                <div className="space-y-2 pt-2">
                    {data?.properties?.slice(0, 3).map((prop: any, idx: number) => (
                        <div
                            key={idx}
                            className={`flex items-center justify-between rounded-lg p-2 ${
                                idx === 0 ? "bg-blue-500/10 border border-blue-500/30" : "bg-white/5"
                            }`}
                        >
                            <div className="flex items-center gap-2 min-w-0">
                                {idx === 0 && <Check className="w-3 h-3 text-blue-400 flex-shrink-0" />}
                                <div className="text-sm text-white truncate">{prop.title}</div>
                            </div>
                            <div className="text-sm font-semibold text-white">{formatPrice(prop.price)}</div>
                        </div>
                    ))}
                </div>
            );

        case "area_analysis":
            const area = data?.area || data?.areas?.[0];
            return (
                <div className="space-y-3 pt-2">
                    {area && (
                        <>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="bg-white/5 rounded-lg p-2">
                                    <div className="text-[10px] text-gray-400">{isRTL ? "سعر المتر" : "Price/sqm"}</div>
                                    <div className="text-sm font-semibold text-cyan-400">
                                        {formatPrice(area.avg_price_per_sqm)}
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-lg p-2">
                                    <div className="text-[10px] text-gray-400">{isRTL ? "النمو" : "Growth"}</div>
                                    <div className="text-sm font-semibold text-green-400">
                                        +{area.yearly_growth || 15}%
                                    </div>
                                </div>
                            </div>
                            {area.pros?.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {area.pros.slice(0, 3).map((pro: string, idx: number) => (
                                        <span
                                            key={idx}
                                            className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 text-[10px] rounded-full"
                                        >
                                            {pro}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>
            );

        case "reality_check":
            return (
                <div className="space-y-2 pt-2">
                    <p className="text-xs text-gray-300 leading-relaxed">
                        {isRTL ? data?.message_ar : data?.message_en}
                    </p>
                    {data?.alternatives?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {data.alternatives.slice(0, 2).map((alt: any, idx: number) => (
                                <button
                                    key={idx}
                                    className="flex items-center gap-1 px-2 py-1 bg-orange-500/10 text-orange-400 text-xs rounded-lg hover:bg-orange-500/20 transition-colors"
                                >
                                    {isRTL ? alt.label_ar : alt.label_en}
                                    <ArrowRight className={`w-3 h-3 ${isRTL ? "rotate-180" : ""}`} />
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            );

        default:
            return (
                <div className="text-xs text-gray-400 pt-2">
                    {isRTL ? "تفاصيل إضافية" : "Additional details"}
                </div>
            );
    }
}

export default function UnifiedAnalytics({ visualizations, isRTL = true }: UnifiedAnalyticsProps) {
    const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

    // Filter out empty visualizations
    const validVisualizations = useMemo(() => {
        return visualizations.filter(hasContent);
    }, [visualizations]);

    if (validVisualizations.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
            dir={isRTL ? "rtl" : "ltr"}
        >
            {/* Header */}
            <div className="flex items-center gap-2 px-1 mb-3">
                <Sparkles className="w-4 h-4 text-teal-400" />
                <span className="text-sm font-semibold text-white">
                    {isRTL ? "تحليلات ذكية" : "Smart Insights"}
                </span>
                <span className="px-1.5 py-0.5 bg-teal-500/20 text-teal-400 text-[10px] font-medium rounded">
                    {validVisualizations.length}
                </span>
            </div>

            {/* Analytics Cards */}
            <div className="space-y-2">
                {validVisualizations.map((viz, idx) => (
                    <InsightCard
                        key={`${viz.type}-${idx}`}
                        viz={viz}
                        isRTL={isRTL}
                        isExpanded={expandedIndex === idx}
                        onToggle={() => setExpandedIndex(expandedIndex === idx ? null : idx)}
                    />
                ))}
            </div>
        </motion.div>
    );
}
