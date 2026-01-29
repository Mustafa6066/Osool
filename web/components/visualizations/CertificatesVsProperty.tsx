"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Banknote, Building2, AlertTriangle, ArrowRight } from "lucide-react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine
} from "recharts";

interface DataPoint {
    year: number;
    label: string;
    label_en: string;
    bank_nominal: number;
    bank_real: number;
    property_total: number;
    property_value: number;
    cumulative_rent: number;
}

interface CertificatesVsPropertyProps {
    initial_investment: number;
    years: number;
    data_points: DataPoint[];
    summary: {
        bank_nominal_final: number;
        bank_nominal_gain: number;
        bank_real_final: number;
        bank_real_loss: number;
        bank_real_loss_percent: number;
        property_final: number;
        property_value_only: number;
        total_rent_earned: number;
        property_gain_percent: number;
        difference: number;
        winner: string;
    };
    assumptions: {
        bank_cd_rate: number;
        inflation_rate: number;
        property_appreciation: number;
        rental_yield: number;
        source: string;
    };
    verdict: {
        winner: string;
        message_ar: string;
        message_en: string;
        headline_ar: string;
        headline_en: string;
    };
    isRTL?: boolean;
}

// Format numbers
const formatCurrency = (value: number): string => {
    if (value >= 1_000_000) {
        return `${(value / 1_000_000).toFixed(1)}M`;
    }
    return `${(value / 1_000).toFixed(0)}K`;
};

const formatCurrencyFull = (value: number): string => {
    return new Intl.NumberFormat("en-EG", {
        style: "decimal",
        maximumFractionDigits: 0,
    }).format(value);
};

export default function CertificatesVsProperty({
    initial_investment,
    years,
    data_points,
    summary,
    assumptions,
    verdict,
    isRTL = true
}: CertificatesVsPropertyProps) {
    if (!data_points || data_points.length === 0) return null;

    // Prepare chart data for the comparison (Year 5 only to keep it clean, or all years?)
    // Let's show the final year comparison primarily
    const finalYear = data_points[data_points.length - 1];

    // Creating a comparison dataset for the chart
    const comparisonData = [
        {
            name: isRTL ? 'شهادة بنكية (قيمة حقيقية)' : 'Bank CD (Real Value)',
            value: finalYear.bank_real,
            color: '#ef4444', // Red for danger/loss
            original: initial_investment,
            type: 'bank'
        },
        {
            name: isRTL ? 'عقار (أصل + إيجار)' : 'Property (Asset + Rent)',
            value: finalYear.property_total,
            color: '#10b981', // Green for success
            original: initial_investment,
            type: 'property'
        }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-[#1a1c2e] rounded-2xl p-6 border border-white/10 shadow-xl overflow-hidden"
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="bg-red-500/20 text-red-400 text-xs font-bold px-2 py-0.5 rounded uppercase">
                            {isRTL ? 'الحقيقة الصادمة' : 'REALITY CHECK'}
                        </span>
                    </div>
                    <h3 className="text-xl font-bold text-white leading-tight">
                        {isRTL ? verdict.headline_ar : verdict.headline_en}
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">
                        {isRTL
                            ? `مقارنة استثمار ${formatCurrency(initial_investment)} جنيه لمدة ${years} سنوات`
                            : `Comparing ${formatCurrency(initial_investment)} EGP investment over ${years} years`
                        }
                    </p>
                </div>
            </div>

            {/* Verdict Box */}
            <div className="bg-gradient-to-r from-red-900/40 to-transparent border-l-4 border-red-500 p-4 rounded-r-lg mb-6">
                <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="text-white font-medium text-sm">
                            {isRTL ? verdict.message_ar.split('\n')[0] : verdict.message_en.split('\n')[0]}
                        </p>
                        <p className="text-gray-300 text-xs mt-1">
                            {isRTL ? verdict.message_ar.split('\n')[1] : verdict.message_en.split('\n')[1]}
                        </p>
                    </div>
                </div>
            </div>

            {/* Main Comparison Chart */}
            <div className="h-64 w-full mb-6">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={comparisonData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                        barSize={40}
                    >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#374151" />
                        <XAxis type="number" hide />
                        <YAxis
                            dataKey="name"
                            type="category"
                            width={isRTL ? 150 : 180}
                            tick={{ fill: '#9ca3af', fontSize: 12 }}
                        />
                        <Tooltip
                            cursor={{ fill: 'transparent' }}
                            content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                    const data = payload[0].payload;
                                    return (
                                        <div className="bg-gray-900 border border-gray-700 p-3 rounded-lg shadow-xl">
                                            <p className="text-white font-bold mb-1">{data.name}</p>
                                            <p className="text-2xl font-bold" style={{ color: data.color }}>
                                                {formatCurrency(data.value)}
                                            </p>
                                            <p className="text-xs text-gray-400 mt-1">
                                                {data.type === 'bank'
                                                    ? `${summary.bank_real_loss_percent}% Loss in Purchasing Power`
                                                    : `+${summary.property_gain_percent}% Growth & Income`
                                                }
                                            </p>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {comparisonData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                        {/* Reference line for initial investment */}
                        <ReferenceLine x={initial_investment} stroke="#6b7280" strokeDasharray="3 3" label={{ position: 'top', value: 'Initial Capital', fill: '#6b7280', fontSize: 10 }} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Detailed Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
                {/* Bank Stats */}
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                    <div className="flex items-center gap-2 mb-2">
                        <Banknote className="w-4 h-4 text-red-400" />
                        <span className="text-xs text-red-300 font-bold uppercase">Bank Certificate</span>
                    </div>
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-xs text-gray-400">Yield</span>
                        <span className="text-sm text-white font-mono">{(assumptions.bank_cd_rate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-xs text-gray-400">Inflation</span>
                        <span className="text-sm text-red-400 font-mono">-{(assumptions.inflation_rate * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-px bg-red-500/20 my-2" />
                    <div className="flex justify-between items-end">
                        <span className="text-xs text-gray-300">Real Outcome</span>
                        <span className="text-lg font-bold text-red-500">{formatCurrency(summary.bank_real_final)}</span>
                    </div>
                </div>

                {/* Property Stats */}
                <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3">
                    <div className="flex items-center gap-2 mb-2">
                        <Building2 className="w-4 h-4 text-green-400" />
                        <span className="text-xs text-green-300 font-bold uppercase">Property</span>
                    </div>
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-xs text-gray-400">Appreciation</span>
                        <span className="text-sm text-green-400 font-mono">+{(assumptions.property_appreciation * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-xs text-gray-400">Rent</span>
                        <span className="text-sm text-green-400 font-mono">+{(assumptions.rental_yield * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-px bg-green-500/20 my-2" />
                    <div className="flex justify-between items-end">
                        <span className="text-xs text-gray-300">Real Outcome</span>
                        <span className="text-lg font-bold text-green-500">{formatCurrency(summary.property_final)}</span>
                    </div>
                </div>
            </div>

            {/* Bottom Logic Line */}
            <div className="mt-4 pt-3 border-t border-white/5 text-center">
                <p className="text-xs text-gray-400">
                    {isRTL
                        ? 'العقار هو الحل الوحيد للحفاظ على قيمة فلوسك من التضخم.'
                        : 'Real estate is the only shield against inflation eroding your savings.'
                    }
                </p>
            </div>
        </motion.div>
    );
}
