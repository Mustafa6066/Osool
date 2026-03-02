"use client";

import { motion } from "framer-motion";
import { TrendingUp, MapPinIcon, CalendarIcon } from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    ReferenceLine,
} from "recharts";

// Color palette for developer lines
const COLORS = [
    "#3b82f6", // blue
    "#10b981", // emerald
    "#f59e0b", // amber
    "#ef4444", // red
    "#8b5cf6", // violet
];

interface DataPoint {
    year: number;
    price_sqm: number;
    yoy_growth: number;
}

interface DeveloperLine {
    name: string;
    type: string;
    data_points: { year: number; price_sqm: number }[];
    total_growth: number;
}

interface PriceGrowthChartProps {
    found?: boolean;
    location?: string;
    location_ar?: string;
    data_points?: DataPoint[];
    total_growth_pct?: number;
    start_year?: number;
    end_year?: number;
    start_price?: number;
    end_price?: number;
    developer_lines?: DeveloperLine[];
    current_growth_rate?: number;
}

const safeNum = (v: any, fallback = 0): number => {
    const n = typeof v === "number" ? v : Number(v);
    return isFinite(n) ? n : fallback;
};

const fmtPrice = (v: number): string => {
    if (!v || isNaN(v)) return "N/A";
    if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
    return `${(v / 1_000).toFixed(0)}K`;
};

const fmtPriceFull = (v: number): string => {
    if (!v || isNaN(v)) return "N/A";
    return v.toLocaleString("en-EG");
};

export default function PriceGrowthChart(props: PriceGrowthChartProps) {
    const {
        location,
        location_ar,
        data_points = [],
        total_growth_pct = 0,
        start_year = 2021,
        end_year = 2026,
        start_price = 0,
        end_price = 0,
        developer_lines = [],
        current_growth_rate = 0,
    } = props;

    // Guard: skip rendering if no data
    if (!data_points || data_points.length < 2) return null;

    // Build chart data — merge area data + developer lines into one dataset
    const chartData = data_points.map((dp) => {
        const row: any = {
            year: dp.year,
            area_price: safeNum(dp.price_sqm),
            yoy: safeNum(dp.yoy_growth),
        };
        // Add each developer line as a separate key
        developer_lines.forEach((dev, idx) => {
            const devPoint = dev.data_points.find((p) => p.year === dp.year);
            row[`dev_${idx}`] = devPoint ? safeNum(devPoint.price_sqm) : null;
        });
        return row;
    });

    const displayName = location_ar || location || "";
    const growthRatePct =
        current_growth_rate && current_growth_rate < 10
            ? (current_growth_rate * 100).toFixed(0)
            : safeNum(current_growth_rate).toFixed(0);

    // Custom tooltip
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (!active || !payload?.length) return null;
        return (
            <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl px-4 py-3 shadow-xl text-xs" dir="rtl">
                <p className="font-bold text-[var(--color-text-primary)] mb-1.5">{label}</p>
                {payload.map((entry: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 mb-0.5">
                        <span
                            className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-[var(--color-text-muted)]">{entry.name}:</span>
                        <span className="font-semibold text-[var(--color-text-primary)] tabular-nums">
                            {fmtPriceFull(entry.value)} EGP/م²
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden"
        >
            {/* Header */}
            <div className="flex items-center gap-3 px-5 py-3.5 border-b border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
                <TrendingUp className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-[var(--color-text-primary)]" dir="rtl">
                        تطور الأسعار في {displayName}
                    </h3>
                    <p className="text-[10px] text-[var(--color-text-muted)]" dir="rtl">
                        {start_year} — {end_year} | سعر المتر المربع (EGP/م²)
                    </p>
                </div>
                {total_growth_pct > 0 && (
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500">
                        +{safeNum(total_growth_pct).toFixed(0)}%
                    </span>
                )}
            </div>

            <div className="px-5 py-4 space-y-4" dir="rtl">
                {/* Key numbers — inline */}
                <div className="flex flex-wrap gap-x-6 gap-y-1.5 text-sm">
                    <div>
                        <span className="text-[var(--color-text-muted)]">سعر {start_year}: </span>
                        <span className="font-bold text-[var(--color-text-secondary)]">{fmtPriceFull(start_price)} ج.م/م²</span>
                    </div>
                    <div>
                        <span className="text-[var(--color-text-muted)]">سعر {end_year}: </span>
                        <span className="font-bold text-[var(--color-text-primary)]">{fmtPriceFull(end_price)} ج.م/م²</span>
                    </div>
                    {Number(growthRatePct) > 0 && (
                        <div>
                            <span className="text-[var(--color-text-muted)]">النمو السنوي: </span>
                            <span className="font-bold text-emerald-500">+{growthRatePct}%</span>
                        </div>
                    )}
                </div>

                {/* Line Chart */}
                <div className="h-64 w-full" dir="ltr">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.4} />
                            <XAxis
                                dataKey="year"
                                tick={{ fill: "var(--color-text-muted)", fontSize: 11 }}
                                tickLine={false}
                                axisLine={{ stroke: "var(--color-border)" }}
                            />
                            <YAxis
                                tick={{ fill: "var(--color-text-muted)", fontSize: 10 }}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(v) => fmtPrice(v)}
                                width={50}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Legend
                                wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                                iconType="circle"
                                iconSize={8}
                            />

                            {/* Main area line — thicker, solid */}
                            <Line animationDuration={2500} 
                                type="monotone"
                                dataKey="area_price"
                                name={displayName || "متوسط المنطقة"}
                                stroke="#3b82f6"
                                strokeWidth={3}
                                dot={{ r: 4, fill: "#3b82f6", stroke: "#fff", strokeWidth: 2 }}
                                activeDot={{ r: 6 }}
                            />

                            {/* Developer lines — thinner, dashed */}
                            {developer_lines.map((dev, idx) => (
                                <Line animationDuration={2500} 
                                    key={dev.name}
                                    type="monotone"
                                    dataKey={`dev_${idx}`}
                                    name={dev.name}
                                    stroke={COLORS[(idx + 1) % COLORS.length]}
                                    strokeWidth={2}
                                    strokeDasharray="5 3"
                                    dot={{ r: 3, fill: COLORS[(idx + 1) % COLORS.length] }}
                                    connectNulls
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* YoY Growth Bars — small underneath */}
                {data_points.some((dp) => dp.yoy_growth > 0) && (
                    <div className="space-y-1.5">
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)] flex items-center gap-1.5">
                            <CalendarIcon className="w-3 h-3" />
                            النمو السنوي (YoY%)
                        </p>
                        <div className="flex gap-1.5 items-end h-10">
                            {data_points.map((dp) => {
                                const maxYoy = Math.max(...data_points.map((d) => Math.abs(d.yoy_growth)));
                                const barH = maxYoy > 0 ? (Math.abs(dp.yoy_growth) / maxYoy) * 100 : 0;
                                const isPositive = dp.yoy_growth >= 0;
                                return (
                                    <div key={dp.year} className="flex-1 flex flex-col items-center gap-0.5">
                                        <span className={`text-[9px] font-bold tabular-nums ${isPositive ? "text-emerald-500" : "text-red-400"}`}>
                                            {dp.yoy_growth > 0 ? "+" : ""}{dp.yoy_growth.toFixed(0)}%
                                        </span>
                                        <motion.div
                                            initial={{ height: 0 }}
                                            animate={{ height: `${Math.max(barH, 5)}%` }}
                                            transition={{ duration: 0.6, delay: 0.1 }}
                                            className={`w-full rounded-t-sm ${isPositive ? "bg-emerald-500/40" : "bg-red-400/40"}`}
                                        />
                                        <span className="text-[9px] text-[var(--color-text-muted)]">{dp.year}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Developer growth summary */}
                {developer_lines.length > 0 && (
                    <div className="space-y-1.5 pt-2 border-t border-[var(--color-border)]">
                        <p className="text-[11px] font-semibold text-[var(--color-text-muted)]">نمو المطورين (5 سنوات)</p>
                        <div className="flex flex-wrap gap-2">
                            {developer_lines.map((dev, idx) => (
                                <span
                                    key={dev.name}
                                    className="text-[11px] px-2.5 py-1 rounded-lg bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)]"
                                >
                                    {dev.name}:{" "}
                                    <span className="font-bold text-emerald-500">+{safeNum(dev.total_growth).toFixed(0)}%</span>
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
