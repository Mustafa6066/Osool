"use client";

import { motion } from "framer-motion";
import { 
    BanknotesIcon, 
    CalendarDaysIcon,
    ArrowTrendingDownIcon,
    SparklesIcon
} from "@heroicons/react/24/outline";

interface PaymentPlan {
    property_id?: string;
    property_title: string;
    total_price: number;
    down_payment_percent: number;
    down_payment_amount: number;
    installment_years: number;
    monthly_installment: number;
    delivery_date?: string;
}

interface PaymentPlanComparisonProps {
    plans: PaymentPlan[];
    best_down_payment?: PaymentPlan;
    longest_installment?: PaymentPlan;
    lowest_monthly?: PaymentPlan;
}

export default function PaymentPlanComparison({ 
    plans, 
    best_down_payment,
    longest_installment,
    lowest_monthly 
}: PaymentPlanComparisonProps) {
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
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-amber-950/30 to-orange-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-amber-600/20 to-orange-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                        <BanknotesIcon className="w-5 h-5 text-amber-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">مقارنة خطط السداد 💳</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">أفضل عروض التقسيط</p>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Best Options Highlight */}
                <div className="grid md:grid-cols-3 gap-4">
                    {best_down_payment && (
                        <div className="bg-gradient-to-br from-green-950/40 to-emerald-950/30 rounded-xl p-4 border border-green-500/20">
                            <div className="flex items-center gap-2 mb-3">
                                <ArrowTrendingDownIcon className="w-4 h-4 text-green-400" />
                                <p className="text-xs text-green-400 font-medium">أقل مقدم</p>
                            </div>
                            <p className="text-2xl font-bold text-green-400 mb-1">
                                {best_down_payment.down_payment_percent}%
                            </p>
                            <p className="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                                {best_down_payment.property_title}
                            </p>
                        </div>
                    )}
                    
                    {longest_installment && (
                        <div className="bg-gradient-to-br from-blue-950/40 to-indigo-950/30 rounded-xl p-4 border border-blue-500/20">
                            <div className="flex items-center gap-2 mb-3">
                                <CalendarDaysIcon className="w-4 h-4 text-blue-400" />
                                <p className="text-xs text-blue-400 font-medium">أطول فترة</p>
                            </div>
                            <p className="text-2xl font-bold text-blue-400 mb-1">
                                {longest_installment.installment_years} سنوات
                            </p>
                            <p className="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                                {longest_installment.property_title}
                            </p>
                        </div>
                    )}
                    
                    {lowest_monthly && (
                        <div className="bg-gradient-to-br from-purple-950/40 to-violet-950/30 rounded-xl p-4 border border-purple-500/20">
                            <div className="flex items-center gap-2 mb-3">
                                <SparklesIcon className="w-4 h-4 text-purple-400" />
                                <p className="text-xs text-purple-400 font-medium">أقل قسط شهري</p>
                            </div>
                            <p className="text-2xl font-bold text-purple-400 mb-1">
                                {formatCurrency(lowest_monthly.monthly_installment)}
                            </p>
                            <p className="text-xs text-[var(--color-text-secondary)] line-clamp-1">
                                {lowest_monthly.property_title}
                            </p>
                        </div>
                    )}
                </div>

                {/* Plans Table */}
                {plans.length > 0 && (
                    <div className="bg-[var(--color-surface)]/30 rounded-xl overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="bg-[var(--color-surface)]/50">
                                        <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-secondary)]">العقار</th>
                                        <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-secondary)]">السعر</th>
                                        <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-secondary)]">المقدم</th>
                                        <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-secondary)]">المدة</th>
                                        <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-secondary)]">الشهري</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {plans.map((plan, i) => (
                                        <tr key={i} className="border-t border-[var(--color-border)]">
                                            <td className="px-4 py-3">
                                                <p className="text-sm text-white line-clamp-1">{plan.property_title}</p>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-[var(--color-text-secondary)]">
                                                {formatCurrency(plan.total_price)}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">
                                                    {plan.down_payment_percent}%
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-[var(--color-text-secondary)]">
                                                {plan.installment_years} سنوات
                                            </td>
                                            <td className="px-4 py-3 text-sm text-amber-400 font-medium">
                                                {formatCurrency(plan.monthly_installment)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
