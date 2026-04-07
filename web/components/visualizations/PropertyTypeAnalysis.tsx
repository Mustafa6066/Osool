"use client";

import { motion } from "framer-motion";
import {
    Home,
    DollarSign,
    Maximize,
    Users
} from "lucide-react";

interface PropertyTypeAnalysisProps {
    analysis: {
        type: string;
        count: number;
        avg_price: number;
        avg_size: number;
        avg_price_per_sqm: number;
        best_for: string;
        typical_sizes: string;
    };
    comparison?: Array<{
        type: string;
        avg_price: number;
        avg_price_per_sqm: number;
        count: number;
    }>;
}

export default function PropertyTypeAnalysis({ analysis, comparison }: PropertyTypeAnalysisProps) {
    // Defensive check for required props
    if (!analysis || !analysis.type) {
        console.warn('PropertyTypeAnalysis: Missing required analysis data');
        return null;
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            maximumFractionDigits: 0
        }).format(value);
    };

    const getTypeIcon = (type: string) => {
        const icons: Record<string, string> = {
            'apartment': '🏢',
            'villa': '🏠',
            'townhouse': '🏘️',
            'twinhouse': '🏡',
            'penthouse': '🌆',
            'duplex': '🔲',
            'studio': '📦'
        };
        return icons[type.toLowerCase()] || '🏠';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-emerald-950/30 to-emerald-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-600/20 to-emerald-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-2xl">
                        {getTypeIcon(analysis.type)}
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">تحليل نوع العقار 🏠</h3>
                        <p className="text-sm text-[var(--color-text-secondary)] capitalize">{analysis.type}</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <DollarSign className="w-5 h-5 text-emerald-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">متوسط السعر</p>
                        <p className="text-sm font-bold text-emerald-400">{formatCurrency(analysis.avg_price)}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <Maximize className="w-5 h-5 text-blue-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">متوسط المساحة</p>
                        <p className="text-sm font-bold text-blue-400">{Math.round(analysis.avg_size)} م²</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <Home className="w-5 h-5 text-amber-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">سعر المتر</p>
                        <p className="text-sm font-bold text-amber-400">{formatCurrency(analysis.avg_price_per_sqm)}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/50 rounded-xl p-4 text-center">
                        <Users className="w-5 h-5 text-purple-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">عدد متاح</p>
                        <p className="text-sm font-bold text-purple-400">{analysis.count} وحدة</p>
                    </div>
                </div>

                {/* Best For & Sizes */}
                <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <p className="text-sm text-[var(--color-text-secondary)] mb-2">مناسب لـ</p>
                        <p className="text-white font-medium">{analysis.best_for}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <p className="text-sm text-[var(--color-text-secondary)] mb-2">المساحات الشائعة</p>
                        <p className="text-white font-medium">{analysis.typical_sizes}</p>
                    </div>
                </div>

                {/* Type Comparison */}
                {comparison && comparison.length > 0 && (
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <p className="text-sm font-medium text-white mb-4">مقارنة الأنواع</p>
                        <div className="space-y-3">
                            {comparison.map((item, i) => (
                                <div key={i} className="flex items-center gap-4">
                                    <span className="text-2xl">{getTypeIcon(item.type)}</span>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm text-white capitalize">{item.type}</span>
                                            <span className="text-xs text-[var(--color-text-secondary)]">
                                                {item.count} وحدة
                                            </span>
                                        </div>
                                        <div className="h-2 bg-[var(--color-surface)] rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full"
                                                style={{
                                                    width: `${Math.min((item.avg_price_per_sqm / Math.max(...comparison.map(c => c.avg_price_per_sqm))) * 100, 100)}%`
                                                }}
                                            />
                                        </div>
                                    </div>
                                    <span className="text-sm text-emerald-400 font-medium w-24 text-right">
                                        {formatCurrency(item.avg_price_per_sqm)}/م²
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
