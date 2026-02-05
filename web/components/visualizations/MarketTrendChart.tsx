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
    isRTL?: boolean;
}

export default function MarketTrendChart({ location, data, isRTL = false }: MarketTrendChartProps) {
    const { historical = [], forecast = [], current_price, trend, yoy_change = 0, momentum = "" } = data;

    // i18n labels
    const labels = {
        marketTrends: isRTL ? 'اتجاهات السوق' : 'Market Trends',
        currentAvgPrice: isRTL ? 'متوسط السعر الحالي' : 'Current Avg Price',
        sqm: isRTL ? 'ج.م/م²' : 'EGP/sqm',
        yoyChange: isRTL ? 'التغير السنوي' : 'YoY Change',
        vsLastYear: isRTL ? 'مقارنة بالعام الماضي' : 'vs last year',
        priceMovement: isRTL ? 'حركة الأسعار' : 'Price Movement',
        historical: isRTL ? 'تاريخي' : 'Historical',
        forecast: isRTL ? 'متوقع' : 'Forecast',
        marketInsights: isRTL ? 'رؤى السوق' : 'Market Insights',
        aiPowered: isRTL ? 'تحليل مدعوم بـ AMR باستخدام 3,000+ معاملة' : 'Analysis powered by AMR using 3,000+ transactions',
        trendLabels: {
            Bullish: isRTL ? 'صاعد' : 'Bullish',
            Bearish: isRTL ? 'هابط' : 'Bearish',
            Stable: isRTL ? 'مستقر' : 'Stable'
        },
        bullishInsights: isRTL ? [
            `• ${location} تشهد نمواً قوياً في الأسعار (${yoy_change > 0 ? `+${yoy_change.toFixed(1)}%` : ""} سنوياً)`,
            '• طلب مرتفع ومعروض محدود يرفعان الأسعار',
            '• يُنصح بالشراء الآن قبل ارتفاع إضافي',
            '• من المتوقع استمرار الاتجاه الصاعد خلال 12-24 شهر'
        ] : [
            `• ${location} is experiencing strong price growth (${yoy_change > 0 ? `+${yoy_change.toFixed(1)}%` : ""} YoY)`,
            '• High demand and limited supply driving prices up',
            '• Consider buying now before further appreciation',
            '• Expected to continue upward trend in next 12-24 months'
        ],
        bearishInsights: isRTL ? [
            `• ${location} تُظهر انخفاضاً في الأسعار (${yoy_change < 0 ? `${yoy_change.toFixed(1)}%` : ""} سنوياً)`,
            '• فرصة شراء محتملة إذا كانت الأساسيات قوية',
            '• فكر في التفاوض للحصول على أسعار أفضل',
            '• راقب السوق لإشارات الاستقرار'
        ] : [
            `• ${location} showing declining prices (${yoy_change < 0 ? `${yoy_change.toFixed(1)}%` : ""} YoY)`,
            '• Potential buying opportunity if fundamentals are strong',
            '• Consider negotiating for better prices',
            '• Monitor market for stabilization signals'
        ],
        stableInsights: isRTL ? [
            `• سوق ${location} مستقر بأسعار ثابتة`,
            '• وقت مناسب للاستثمار طويل الأجل',
            '• عوائد متوقعة مع تقلبات أقل',
            '• ركز على العائد الإيجاري وجودة الموقع'
        ] : [
            `• ${location} market is stable with steady prices`,
            '• Good time for long-term investment',
            '• Predictable returns with lower volatility',
            '• Focus on rental yield and location quality'
        ]
    };

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
                className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-elevated)] rounded-2xl p-6 border border-[var(--color-border)] shadow-2xl"
                dir={isRTL ? 'rtl' : 'ltr'}
            >
                {/* Header */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-bold text-[var(--color-text-primary)] flex items-center gap-2">
                            <Activity className="w-5 h-5 text-blue-400" />
                            {labels.marketTrends}
                        </h3>
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.2, type: "spring" }}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bg} border ${config.border}`}
                        >
                            {config.icon}
                            <span className={`font-semibold text-sm ${config.text}`}>{labels.trendLabels[trend]}</span>
                        </motion.div>
                    </div>
                    <p className="text-[var(--color-text-secondary)] text-sm">{location}</p>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                    {/* Current Price */}
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="bg-[var(--color-surface-elevated)] rounded-xl p-4 border border-[var(--color-border)]"
                    >
                        <div className="text-xs text-[var(--color-text-muted)] mb-1">{labels.currentAvgPrice}</div>
                        <div className="text-2xl font-bold text-[var(--color-text-primary)]">
                            {(current_price / 1000).toFixed(0)}K
                        </div>
                        <div className="text-xs text-[var(--color-text-muted)] mt-1">{labels.sqm}</div>
                    </motion.div>

                    {/* YoY Change */}
                    {yoy_change !== 0 && (
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className={`rounded-xl p-4 border ${config.bg} ${config.border}`}
                        >
                            <div className="text-xs text-[var(--color-text-muted)] mb-1">{labels.yoyChange}</div>
                            <div className={`text-2xl font-bold ${config.text} flex items-center gap-1`}>
                                {yoy_change > 0 ? "+" : ""}{yoy_change.toFixed(1)}%
                                {yoy_change > 0 ? (
                                    <TrendingUp className="w-4 h-4" />
                                ) : (
                                    <TrendingDown className="w-4 h-4" />
                                )}
                            </div>
                            <div className="text-xs text-[var(--color-text-muted)] mt-1">{labels.vsLastYear}</div>
                        </motion.div>
                    )}

                    {/* Momentum */}
                    {momentum && (
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-[var(--color-surface-elevated)] rounded-xl p-4 border border-[var(--color-border)]"
                        >
                            <div className="text-xs text-[var(--color-text-muted)] mb-1">Momentum</div>
                            <div className="text-sm font-semibold text-[var(--color-text-primary)]">
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
                        className="bg-[var(--color-surface-elevated)] rounded-xl p-4 border border-[var(--color-border)] mb-6"
                    >
                        <h4 className="text-sm font-semibold text-[var(--color-text-secondary)] mb-4">{labels.priceMovement}</h4>
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
                                        `${(value / 1000).toFixed(1)}K ${isRTL ? 'ج.م/م²' : 'EGP/sqm'}`,
                                        name === "price" ? (isRTL ? "السعر" : "Price") : name
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
                                <span>{labels.historical}</span>
                            </div>
                            {forecast.length > 0 && (
                                <div className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full border-2" style={{ borderColor: config.color }} />
                                    <span>{labels.forecast}</span>
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
                            <h5 className={`text-sm font-semibold ${config.text} mb-2`}>{labels.marketInsights}</h5>
                            <div className="space-y-2 text-xs text-[var(--color-text-muted)]">
                                {trend === "Bullish" && labels.bullishInsights.map((insight, i) => (
                                    <p key={i}>{insight}</p>
                                ))}
                                {trend === "Bearish" && labels.bearishInsights.map((insight, i) => (
                                    <p key={i}>{insight}</p>
                                ))}
                                {trend === "Stable" && labels.stableInsights.map((insight, i) => (
                                    <p key={i}>{insight}</p>
                                ))}
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Data Source */}
                <div className="mt-6 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                        <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                        <span>{labels.aiPowered}</span>
                    </div>
                </div>
            </motion.div>
        </ClientOnly>
    );
}

