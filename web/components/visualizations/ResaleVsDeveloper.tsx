"use client";

import { motion } from "framer-motion";
import { 
    ArrowLeftRight,
    Store,
    Home,
    Check,
    X
} from "lucide-react";

interface ResaleVsDeveloperProps {
    recommendation: {
        recommendation: "resale" | "developer" | "depends";
        reason_ar: string;
        reason_en: string;
    };
    resale_discount?: number;
    comparison?: {
        resale_avg_price_per_sqm: number;
        developer_avg_price_per_sqm: number;
        resale_ready: boolean;
        developer_payment_plan: boolean;
    };
}

export default function ResaleVsDeveloper({ recommendation, resale_discount, comparison }: ResaleVsDeveloperProps) {
    // Defensive check for required props
    if (!recommendation || !recommendation.recommendation) {
        console.warn('ResaleVsDeveloper: Missing required recommendation data');
        return null;
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            maximumFractionDigits: 0
        }).format(value);
    };

    const getRecommendationColor = () => {
        switch (recommendation.recommendation) {
            case 'resale': return 'from-purple-600/20 to-violet-600/20';
            case 'developer': return 'from-blue-600/20 to-indigo-600/20';
            default: return 'from-amber-600/20 to-orange-600/20';
        }
    };

    const getRecommendationEmoji = () => {
        switch (recommendation.recommendation) {
            case 'resale': return '🏪';
            case 'developer': return '🏗️';
            default: return '⚖️';
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-slate-950/30 to-zinc-950/20"
        >
            {/* Header */}
            <div className={`bg-gradient-to-r ${getRecommendationColor()} px-6 py-4 border-b border-[var(--color-border)]`}>
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                        <ArrowLeftRight className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">ريسيل vs من المطور {getRecommendationEmoji()}</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">مقارنة شاملة</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Recommendation */}
                <div className={`bg-gradient-to-r ${getRecommendationColor()} rounded-xl p-4 border border-white/10`}>
                    <p className="text-sm text-[var(--color-text-secondary)] mb-2">توصيتنا</p>
                    <p className="text-lg font-bold text-white mb-2">
                        {recommendation.recommendation === 'resale' && '🏪 ريسيل - أفضل لك'}
                        {recommendation.recommendation === 'developer' && '🏗️ من المطور - أفضل لك'}
                        {recommendation.recommendation === 'depends' && '⚖️ يعتمد على أولوياتك'}
                    </p>
                    <p className="text-sm text-[var(--color-text-secondary)]">{recommendation.reason_ar}</p>
                </div>

                {/* Discount Highlight */}
                {resale_discount !== undefined && resale_discount > 0 && (
                    <div className="bg-green-950/30 rounded-xl p-4 border border-green-500/20 text-center">
                        <p className="text-sm text-green-400 mb-1">الريسيل أرخص بـ</p>
                        <p className="text-3xl font-bold text-green-400">{resale_discount}%</p>
                        <p className="text-xs text-[var(--color-text-secondary)]">من متوسط أسعار المطور</p>
                    </div>
                )}

                {/* Comparison Table */}
                <div className="grid grid-cols-3 gap-4 text-center">
                    <div></div>
                    <div className="bg-purple-500/20 rounded-t-xl p-2">
                        <Store className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                        <p className="text-xs text-purple-400 font-medium">ريسيل</p>
                    </div>
                    <div className="bg-blue-500/20 rounded-t-xl p-2">
                        <Home className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                        <p className="text-xs text-blue-400 font-medium">من المطور</p>
                    </div>
                </div>

                <div className="space-y-2">
                    {/* Price Comparison */}
                    {comparison && (
                        <>
                            <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                                <p className="text-sm text-[var(--color-text-secondary)]">سعر المتر</p>
                                <p className="text-sm text-purple-400 text-center font-medium">
                                    {formatCurrency(comparison.resale_avg_price_per_sqm)}
                                </p>
                                <p className="text-sm text-blue-400 text-center font-medium">
                                    {formatCurrency(comparison.developer_avg_price_per_sqm)}
                                </p>
                            </div>
                        </>
                    )}

                    {/* Features */}
                    <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                        <p className="text-sm text-[var(--color-text-secondary)]">جاهز للتسليم</p>
                        <div className="flex justify-center">
                            <Check className="w-5 h-5 text-green-400" />
                        </div>
                        <div className="flex justify-center">
                            <X className="w-5 h-5 text-red-400" />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                        <p className="text-sm text-[var(--color-text-secondary)]">خطة تقسيط طويلة</p>
                        <div className="flex justify-center">
                            <X className="w-5 h-5 text-red-400" />
                        </div>
                        <div className="flex justify-center">
                            <Check className="w-5 h-5 text-green-400" />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                        <p className="text-sm text-[var(--color-text-secondary)]">ضمان المطور</p>
                        <div className="flex justify-center">
                            <X className="w-5 h-5 text-red-400" />
                        </div>
                        <div className="flex justify-center">
                            <Check className="w-5 h-5 text-green-400" />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                        <p className="text-sm text-[var(--color-text-secondary)]">سعر أقل</p>
                        <div className="flex justify-center">
                            <Check className="w-5 h-5 text-green-400" />
                        </div>
                        <div className="flex justify-center">
                            <X className="w-5 h-5 text-red-400" />
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 items-center bg-[var(--color-surface)]/30 rounded-xl p-3">
                        <p className="text-sm text-[var(--color-text-secondary)]">تفاوض على السعر</p>
                        <div className="flex justify-center">
                            <Check className="w-5 h-5 text-green-400" />
                        </div>
                        <div className="flex justify-center">
                            <X className="w-5 h-5 text-red-400" />
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
