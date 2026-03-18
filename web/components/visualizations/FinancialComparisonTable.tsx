"use client";

import { motion } from "framer-motion";
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from "@heroicons/react/24/outline";

interface ComparisonRow {
    label: string;
    icon?: string;
    values: {
        name: string;
        value: number | string;
        change?: number;
        trend?: 'up' | 'down' | 'neutral';
        color?: string;
    }[];
}

interface FinancialComparisonTableProps {
    title: string;
    subtitle?: string;
    rows: ComparisonRow[];
    isRTL?: boolean;
    colorScheme?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
    showTrends?: boolean;
}

export default function FinancialComparisonTable({
    title,
    subtitle,
    rows,
    isRTL = true,
    colorScheme = 'info',
    showTrends = true
}: FinancialComparisonTableProps) {
    if (!rows || rows.length === 0) return null;

    // Extract column names from first row
    const firstRow = rows[0];
    const columnHeaders = (firstRow.values || []).map(v => v.name);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)]"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600/20 to-blue-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                        <span className="text-xl">📊</span>
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">{title}</h3>
                        {subtitle && (
                            <p className="text-sm text-[var(--color-text-secondary)]">{subtitle}</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 sm:p-6">
                <div className="md:hidden space-y-2.5">
                    {rows.map((row, rowIdx) => (
                        <div key={`mobile-${rowIdx}`} className="rounded-xl border border-[var(--color-border)]/50 bg-[var(--color-surface)]/20 p-3">
                            <div className="flex items-center justify-end gap-2">
                                <span className="text-sm font-semibold text-white">{row.label}</span>
                                {row.icon && <span className="text-base">{row.icon}</span>}
                            </div>
                            <div className="mt-2.5 space-y-2">
                                {row.values.map((val, colIdx) => {
                                    const trendColor =
                                        val.trend === 'up' ? 'text-green-400' :
                                        val.trend === 'down' ? 'text-red-400' :
                                        'text-yellow-400';

                                    return (
                                        <div key={`mobile-val-${colIdx}`} className="flex items-center justify-between gap-3 rounded-lg bg-[var(--color-surface)]/35 px-3 py-2">
                                            <span className="text-xs text-[var(--color-text-secondary)]">{val.name}</span>
                                            <div className="text-end">
                                                <div className={`text-sm font-bold ${val.color || trendColor}`}>
                                                    {typeof val.value === 'number' ? `${val.value.toFixed(1)}%` : val.value}
                                                </div>
                                                {showTrends && val.change !== undefined && (
                                                    <div className={`text-[11px] mt-0.5 inline-flex items-center gap-1 ${trendColor}`}>
                                                        {val.trend === 'up' && <ArrowTrendingUpIcon className="w-3 h-3" />}
                                                        {val.trend === 'down' && <ArrowTrendingDownIcon className="w-3 h-3" />}
                                                        {Math.abs(val.change).toFixed(1)}%
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="hidden md:block overflow-x-auto">
                <table className="w-full min-w-[680px] border-collapse">
                    <thead>
                        <tr className="border-b border-[var(--color-border)]">
                            <th className="px-4 py-3 text-right text-xs font-medium text-[var(--color-text-secondary)] uppercase">
                                المقارنة
                            </th>
                            {columnHeaders.map((header) => (
                                <th
                                    key={header}
                                    className="px-4 py-3 text-center text-xs font-medium text-[var(--color-text-secondary)] uppercase"
                                >
                                    {header}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, rowIdx) => (
                            <tr
                                key={rowIdx}
                                className={`border-b border-[var(--color-border)] last:border-b-0 transition-colors ${
                                    rowIdx % 2 === 0 ? 'bg-[var(--color-surface)]/5' : ''
                                } hover:bg-[var(--color-surface)]/10`}
                            >
                                {/* Label Column */}
                                <td className="px-4 py-4 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        {row.icon && (
                                            <span className="text-xl">{row.icon}</span>
                                        )}
                                        <span className="text-sm font-medium text-white">
                                            {row.label}
                                        </span>
                                    </div>
                                </td>

                                {/* Value Columns */}
                                {row.values.map((val, colIdx) => {
                                    const trendColor =
                                        val.trend === 'up' ? 'text-green-400' :
                                        val.trend === 'down' ? 'text-red-400' :
                                        'text-yellow-400';

                                    return (
                                        <td
                                            key={colIdx}
                                            className="px-4 py-4 text-center"
                                        >
                                            <div className="flex flex-col items-center gap-1">
                                                {/* Main Value */}
                                                <div className={`text-lg font-bold ${val.color || trendColor}`}>
                                                    {typeof val.value === 'number'
                                                        ? `${val.value.toFixed(1)}%`
                                                        : val.value
                                                    }
                                                </div>

                                                {/* Change Indicator */}
                                                {showTrends && val.change !== undefined && (
                                                    <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
                                                        {val.trend === 'up' && (
                                                            <ArrowTrendingUpIcon className="w-3 h-3" />
                                                        )}
                                                        {val.trend === 'down' && (
                                                            <ArrowTrendingDownIcon className="w-3 h-3" />
                                                        )}
                                                        {Math.abs(val.change).toFixed(1)}%
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
                </div>
            </div>
        </motion.div>
    );
}

/**
 * Specific component for Bank vs Property comparison
 * Matches the image provided (العائد الشهري vs العائد الحقيقي)
 */
export function BankVsPropertyComparisonTable(props: {
    bankMonthly: number;
    bankActual: number;
    propertyMonthly: number;
    propertyActual: number;
    isRTL?: boolean;
}) {
    const rows: ComparisonRow[] = [
        {
            label: 'الكاش (5 مليون جنيه)',
            icon: '💰',
            values: [
                {
                    name: 'البنك البيضاء',
                    value: props.bankMonthly,
                    trend: 'neutral',
                    color: 'text-yellow-400'
                },
                {
                    name: 'شقة درك',
                    value: props.propertyMonthly,
                    trend: 'up',
                    color: 'text-green-400'
                }
            ]
        },
        {
            label: '% العائد الحقيقي',
            icon: '📊',
            values: [
                {
                    name: 'البنك البيضاء',
                    value: props.bankActual,
                    trend: 'neutral',
                    color: 'text-yellow-400'
                },
                {
                    name: 'شقة درك',
                    value: props.propertyActual,
                    trend: 'up',
                    color: 'text-green-400'
                }
            ]
        }
    ];

    return (
        <FinancialComparisonTable
            title="مقارنة العائد الشهري vs العائد الحقيقي"
            subtitle="على 5 مليون جنيه"
            rows={rows}
            isRTL={props.isRTL}
            colorScheme="info"
            showTrends={true}
        />
    );
}
