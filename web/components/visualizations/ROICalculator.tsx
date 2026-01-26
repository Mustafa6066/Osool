"use client";

import { motion } from "framer-motion";
import { 
    CalculatorIcon,
    BanknotesIcon,
    BuildingOffice2Icon,
    ChartBarIcon,
    ArrowTrendingUpIcon
} from "@heroicons/react/24/outline";

interface ROICalculatorProps {
    roi: {
        property_id?: string;
        property_title: string;
        price: number;
        location: string;
        rental_yield_percent: number;
        estimated_annual_rent: number;
        estimated_monthly_rent: number;
        capital_appreciation_percent: number;
        total_annual_return: number;
        break_even_years: number;
        "5_year_projection": {
            rental_income: number;
            capital_gain: number;
            total_return: number;
        };
    };
    comparisons?: {
        bank?: {
            bank_annual_return: number;
            property_annual_return: number;
            winner: string;
        };
        gold?: {
            gold_annual_return: number;
            property_annual_return: number;
            winner: string;
        };
        stocks?: {
            stocks_annual_return: number;
            property_annual_return: number;
            winner: string;
        };
    };
}

export default function ROICalculator({ roi, comparisons }: ROICalculatorProps) {
    // Defensive check for required props
    if (!roi || !roi.property_title) {
        console.warn('ROICalculator: Missing required roi data');
        return null;
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            maximumFractionDigits: 0
        }).format(value);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-cyan-950/30 to-teal-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-cyan-600/20 to-teal-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                        <CalculatorIcon className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">حاسبة العائد على الاستثمار 📊</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">{roi.property_title}</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Main Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-green-950/40 to-emerald-950/30 rounded-xl p-4 text-center border border-green-500/20">
                        <BanknotesIcon className="w-5 h-5 text-green-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">العائد السنوي الإجمالي</p>
                        <p className="text-xl font-bold text-green-400">{roi.total_annual_return.toFixed(1)}%</p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-950/40 to-indigo-950/30 rounded-xl p-4 text-center border border-blue-500/20">
                        <BuildingOffice2Icon className="w-5 h-5 text-blue-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">عائد الإيجار</p>
                        <p className="text-xl font-bold text-blue-400">{roi.rental_yield_percent}%</p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-950/40 to-violet-950/30 rounded-xl p-4 text-center border border-purple-500/20">
                        <ArrowTrendingUpIcon className="w-5 h-5 text-purple-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">نمو رأس المال</p>
                        <p className="text-xl font-bold text-purple-400">{roi.capital_appreciation_percent}%</p>
                    </div>
                    <div className="bg-gradient-to-br from-amber-950/40 to-orange-950/30 rounded-xl p-4 text-center border border-amber-500/20">
                        <ChartBarIcon className="w-5 h-5 text-amber-400 mx-auto mb-2" />
                        <p className="text-xs text-[var(--color-text-secondary)] mb-1">نقطة التعادل</p>
                        <p className="text-xl font-bold text-amber-400">{roi.break_even_years} سنوات</p>
                    </div>
                </div>

                {/* Rental Income */}
                <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                    <p className="text-sm font-medium text-white mb-4">دخل الإيجار المتوقع</p>
                    <div className="grid md:grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs text-[var(--color-text-secondary)] mb-1">شهرياً</p>
                            <p className="text-lg font-bold text-cyan-400">{formatCurrency(roi.estimated_monthly_rent)}</p>
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-secondary)] mb-1">سنوياً</p>
                            <p className="text-lg font-bold text-cyan-400">{formatCurrency(roi.estimated_annual_rent)}</p>
                        </div>
                    </div>
                </div>

                {/* 5 Year Projection */}
                <div className="bg-gradient-to-r from-emerald-950/30 to-teal-950/30 rounded-xl p-4 border border-emerald-500/20">
                    <p className="text-sm font-medium text-emerald-400 mb-4">توقعات 5 سنوات 🚀</p>
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                            <p className="text-xs text-[var(--color-text-secondary)] mb-1">دخل الإيجار</p>
                            <p className="text-sm font-bold text-white">{formatCurrency(roi["5_year_projection"].rental_income)}</p>
                        </div>
                        <div>
                            <p className="text-xs text-[var(--color-text-secondary)] mb-1">زيادة القيمة</p>
                            <p className="text-sm font-bold text-white">{formatCurrency(roi["5_year_projection"].capital_gain)}</p>
                        </div>
                        <div className="bg-emerald-500/20 rounded-lg p-2">
                            <p className="text-xs text-emerald-300 mb-1">إجمالي العائد</p>
                            <p className="text-sm font-bold text-emerald-400">{formatCurrency(roi["5_year_projection"].total_return)}</p>
                        </div>
                    </div>
                </div>

                {/* Investment Comparisons */}
                {comparisons && (
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <p className="text-sm font-medium text-white mb-4">مقارنة مع استثمارات أخرى</p>
                        <div className="space-y-3">
                            {comparisons.bank && (
                                <div className="flex items-center justify-between bg-[var(--color-surface)]/50 rounded-lg p-3">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">🏦</span>
                                        <span className="text-sm text-white">ودائع البنك</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-sm text-[var(--color-text-secondary)]">
                                            {comparisons.bank.bank_annual_return.toFixed(1)}%
                                        </span>
                                        <span className={`text-sm font-medium ${comparisons.bank.winner === 'property' ? 'text-green-400' : 'text-red-400'}`}>
                                            {comparisons.bank.winner === 'property' ? '✓ العقار أفضل' : '✗ البنك أفضل'}
                                        </span>
                                    </div>
                                </div>
                            )}
                            {comparisons.gold && (
                                <div className="flex items-center justify-between bg-[var(--color-surface)]/50 rounded-lg p-3">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">🥇</span>
                                        <span className="text-sm text-white">الذهب</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-sm text-[var(--color-text-secondary)]">
                                            {comparisons.gold.gold_annual_return.toFixed(1)}%
                                        </span>
                                        <span className={`text-sm font-medium ${comparisons.gold.winner === 'property' ? 'text-green-400' : 'text-amber-400'}`}>
                                            {comparisons.gold.winner === 'property' ? '✓ العقار أفضل' : '≈ متقارب'}
                                        </span>
                                    </div>
                                </div>
                            )}
                            {comparisons.stocks && (
                                <div className="flex items-center justify-between bg-[var(--color-surface)]/50 rounded-lg p-3">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xl">📈</span>
                                        <span className="text-sm text-white">البورصة</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-sm text-[var(--color-text-secondary)]">
                                            {comparisons.stocks.stocks_annual_return.toFixed(1)}%
                                        </span>
                                        <span className={`text-sm font-medium ${comparisons.stocks.winner === 'property' ? 'text-green-400' : 'text-amber-400'}`}>
                                            {comparisons.stocks.winner === 'property' ? '✓ العقار أقل مخاطرة' : '⚠️ مخاطرة أعلى'}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
