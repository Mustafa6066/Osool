"use client";

import { motion } from "framer-motion";
import { DollarSign, Calendar, TrendingUp, CreditCard, PiggyBank } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface PaymentTimelineProps {
    property: {
        title: string;
        price: number;
    };
    payment: {
        down_payment_percent: number;
        down_payment_amount: number;
        installment_years: number;
        monthly_installment: number;
        total_paid?: number;
        interest_rate?: number;
    };
}

export default function PaymentTimeline({ property, payment }: PaymentTimelineProps) {
    const {
        down_payment_percent,
        down_payment_amount,
        installment_years,
        monthly_installment,
        total_paid = property.price,
        interest_rate = 0
    } = payment;

    // Generate payment schedule data for chart
    const generateSchedule = () => {
        const data = [];
        let remaining = property.price - down_payment_amount;
        const totalMonths = installment_years * 12;

        // Down payment
        data.push({
            month: 0,
            paid: down_payment_amount,
            remaining: remaining,
            label: "Down Payment"
        });

        // Monthly installments (show every 6 months for readability)
        for (let month = 6; month <= totalMonths; month += 6) {
            const paid = down_payment_amount + (monthly_installment * month);
            remaining = Math.max(0, property.price - paid);
            data.push({
                month,
                paid,
                remaining,
                label: `Month ${month}`
            });
        }

        return data;
    };

    const scheduleData = generateSchedule();
    const totalMonths = installment_years * 12;
    const installmentTotal = monthly_installment * totalMonths;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] rounded-2xl p-6 border border-white/10 shadow-2xl"
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-purple-400" />
                    Payment Timeline
                </h3>
                <p className="text-gray-400 text-sm">{property.title}</p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {/* Down Payment */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <PiggyBank className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-gray-400">Down Payment</span>
                    </div>
                    <div className="text-xl font-bold text-blue-400">
                        {(down_payment_amount / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        {down_payment_percent}% upfront
                    </div>
                </motion.div>

                {/* Monthly Payment */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 }}
                    className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <CreditCard className="w-4 h-4 text-purple-400" />
                        <span className="text-xs text-gray-400">Monthly</span>
                    </div>
                    <div className="text-xl font-bold text-purple-400">
                        {(monthly_installment / 1000).toFixed(0)}K
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        EGP/month
                    </div>
                </motion.div>

                {/* Duration */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.3 }}
                    className="bg-green-500/10 border border-green-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <Calendar className="w-4 h-4 text-green-400" />
                        <span className="text-xs text-gray-400">Duration</span>
                    </div>
                    <div className="text-xl font-bold text-green-400">
                        {installment_years}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        years ({totalMonths} months)
                    </div>
                </motion.div>

                {/* Total Paid */}
                <motion.div
                    initial={{ scale: 0.9 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.4 }}
                    className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="w-4 h-4 text-yellow-400" />
                        <span className="text-xs text-gray-400">Total Paid</span>
                    </div>
                    <div className="text-xl font-bold text-yellow-400">
                        {(total_paid / 1000000).toFixed(1)}M
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                        {interest_rate > 0 ? `${interest_rate}% interest` : "No interest"}
                    </div>
                </motion.div>
            </div>

            {/* Payment Schedule Chart */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="bg-white/5 rounded-xl p-4 border border-white/10 mb-6"
            >
                <h4 className="text-sm font-semibold text-gray-300 mb-4">Payment Progress</h4>
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={scheduleData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                        <XAxis
                            dataKey="month"
                            stroke="#94a3b8"
                            tick={{ fill: "#94a3b8", fontSize: 12 }}
                            label={{ value: "Months", position: "insideBottom", offset: -5, fill: "#94a3b8" }}
                        />
                        <YAxis
                            stroke="#94a3b8"
                            tick={{ fill: "#94a3b8", fontSize: 12 }}
                            tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#1a1c2e",
                                border: "1px solid rgba(255,255,255,0.1)",
                                borderRadius: "8px",
                                color: "#fff"
                            }}
                            formatter={(value: number) => `${(value / 1000000).toFixed(2)}M EGP`}
                        />
                        <Line
                            type="monotone"
                            dataKey="paid"
                            stroke="#8b5cf6"
                            strokeWidth={3}
                            dot={{ fill: "#8b5cf6", r: 4 }}
                            name="Amount Paid"
                        />
                        <Line
                            type="monotone"
                            dataKey="remaining"
                            stroke="#ef4444"
                            strokeWidth={2}
                            strokeDasharray="5 5"
                            dot={{ fill: "#ef4444", r: 3 }}
                            name="Remaining"
                        />
                    </LineChart>
                </ResponsiveContainer>
                <div className="flex items-center justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-purple-500" />
                        <span className="text-xs text-gray-400">Amount Paid</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-500" />
                        <span className="text-xs text-gray-400">Remaining</span>
                    </div>
                </div>
            </motion.div>

            {/* Breakdown */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="space-y-3"
            >
                <h4 className="text-sm font-semibold text-gray-300">Payment Breakdown</h4>

                {/* Down Payment Bar */}
                <div>
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Down Payment ({down_payment_percent}%)</span>
                        <span>{(down_payment_amount / 1000000).toFixed(2)}M EGP</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${down_payment_percent}%` }}
                            transition={{ duration: 1, delay: 0.7 }}
                            className="h-full bg-gradient-to-r from-blue-500 to-blue-600"
                        />
                    </div>
                </div>

                {/* Installments Bar */}
                <div>
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Installments ({100 - down_payment_percent}%)</span>
                        <span>{(installmentTotal / 1000000).toFixed(2)}M EGP</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${100 - down_payment_percent}%` }}
                            transition={{ duration: 1, delay: 0.8 }}
                            className="h-full bg-gradient-to-r from-purple-500 to-purple-600"
                        />
                    </div>
                </div>

                {/* Interest (if any) */}
                {interest_rate > 0 && total_paid > property.price && (
                    <div>
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>Interest ({interest_rate}%)</span>
                            <span>{((total_paid - property.price) / 1000000).toFixed(2)}M EGP</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${((total_paid - property.price) / total_paid) * 100}%` }}
                                transition={{ duration: 1, delay: 0.9 }}
                                className="h-full bg-gradient-to-r from-yellow-500 to-orange-600"
                            />
                        </div>
                    </div>
                )}
            </motion.div>

            {/* Tips */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl"
            >
                <div className="flex items-start gap-3">
                    <TrendingUp className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                        <h5 className="text-sm font-semibold text-blue-400 mb-1">💡 Pro Tip</h5>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            Increasing your down payment to {down_payment_percent + 10}% could reduce your monthly payment to{" "}
                            {(monthly_installment * 0.85 / 1000).toFixed(0)}K EGP and save you interest costs.
                        </p>
                    </div>
                </div>
            </motion.div>

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-white/10">
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                    <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
                    <span>Calculated by AMR using CBE rates</span>
                </div>
            </div>
        </motion.div>
    );
}
