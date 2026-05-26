"use client";

import { motion } from "framer-motion";
import { 
    ChevronUp, 
    ChevronDown,
    TrendingUp,
    TrendingDown
} from "lucide-react";
import { isValidElement, useMemo, useState, type ReactNode } from "react";

type DataTableRow = Record<string, unknown>;
type ColumnFormatter = { bivarianceHack(value: unknown): ReactNode }['bivarianceHack'];

interface Column {
    key: string;
    header: string;
    align?: 'left' | 'center' | 'right';
    format?: ColumnFormatter;
    width?: string;
}

interface DataTableProps {
    title?: string;
    subtitle?: string;
    columns: Column[];
    data: DataTableRow[];
    sortable?: boolean;
    striped?: boolean;
    hoverable?: boolean;
    isRTL?: boolean;
    icon?: React.ReactNode;
    colorScheme?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'neutral';
    maxHeight?: string;
    defaultSortKey?: string;
    defaultSortOrder?: 'asc' | 'desc';
    onRowClick?: (row: DataTableRow, index: number) => void;
    emptyMessage?: string;
}

function renderCellValue(value: unknown): ReactNode {
    if (value === null || value === undefined) {
        return null;
    }

    if (isValidElement(value)) {
        return value;
    }

    if (value instanceof Date) {
        return value.toLocaleDateString('en-EG');
    }

    if (typeof value === 'object') {
        return JSON.stringify(value);
    }

    return String(value);
}

export default function DataTable({
    title,
    subtitle,
    columns,
    data,
    sortable = true,
    striped = true,
    hoverable = true,
    isRTL = true,
    icon,
    colorScheme = 'neutral',
    maxHeight = '600px',
    defaultSortKey,
    defaultSortOrder = 'asc',
    onRowClick,
    emptyMessage = 'لا توجد بيانات'
}: DataTableProps) {
    const [sortKey, setSortKey] = useState<string | null>(defaultSortKey || null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(defaultSortOrder);

    const schemeColors = {
        primary: 'from-teal-600/20 to-cyan-600/20 border-teal-500/20',
        success: 'from-green-600/20 to-emerald-600/20 border-green-500/20',
        warning: 'from-amber-600/20 to-orange-600/20 border-amber-500/20',
        danger: 'from-red-600/20 to-rose-600/20 border-red-500/20',
        info: 'from-blue-600/20 to-indigo-600/20 border-blue-500/20',
        neutral: 'from-slate-600/20 to-gray-600/20 border-slate-500/20'
    };

    const schemeAccent = {
        primary: 'text-teal-400',
        success: 'text-green-400',
        warning: 'text-amber-400',
        danger: 'text-red-400',
        info: 'text-blue-400',
        neutral: 'text-slate-400'
    };

    const sortedData = useMemo(() => {
        if (!sortable || !sortKey) return data;

        const sorted = [...data].sort((a, b) => {
            const aVal = a[sortKey];
            const bVal = b[sortKey];

            // Handle numbers
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
            }

            // Handle strings
            const aStr = String(aVal || '').toLowerCase();
            const bStr = String(bVal || '').toLowerCase();
            
            if (sortOrder === 'asc') {
                return aStr.localeCompare(bStr, 'ar');
            } else {
                return bStr.localeCompare(aStr, 'ar');
            }
        });

        return sorted;
    }, [data, sortKey, sortOrder, sortable]);

    const handleSort = (key: string) => {
        if (!sortable) return;

        if (sortKey === key) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(key);
            setSortOrder('asc');
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-2xl overflow-hidden border bg-gradient-to-br ${schemeColors[colorScheme]}`}
        >
            {/* Header */}
            {(title || subtitle) && (
                <div className={`px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-surface)]/20`}>
                    <div className="flex items-center gap-3">
                        {icon && (
                            <div className="w-10 h-10 rounded-xl bg-[var(--color-surface)]/50 flex items-center justify-center">
                                {icon}
                            </div>
                        )}
                        <div>
                            {title && (
                                <h3 className="text-lg font-semibold text-white">
                                    {title}
                                </h3>
                            )}
                            {subtitle && (
                                <p className="text-sm text-[var(--color-text-secondary)]">
                                    {subtitle}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Table Container */}
            <div style={{ maxHeight, overflow: 'auto' }} className="overflow-x-auto overflow-y-auto">
                {data.length === 0 ? (
                    <div className="p-8 text-center">
                        <p className="text-[var(--color-text-secondary)]">
                            {emptyMessage}
                        </p>
                    </div>
                ) : (
                    <>
                        <div className="md:hidden space-y-2.5 p-3" dir={isRTL ? 'rtl' : 'ltr'}>
                            {sortedData.map((row, idx) => (
                                <div
                                    key={`mobile-row-${idx}`}
                                    className={`rounded-xl border border-[var(--color-border)]/60 bg-[var(--color-surface)]/30 px-3 py-2.5 ${
                                        onRowClick ? 'cursor-pointer active:scale-[0.99] transition-transform' : ''
                                    }`}
                                    onClick={() => onRowClick?.(row, idx)}
                                >
                                    <div className="mb-2 flex items-center justify-between gap-2">
                                        <span className={`text-[11px] font-semibold uppercase tracking-wider ${schemeAccent[colorScheme]}`}>
                                            Row {idx + 1}
                                        </span>
                                    </div>

                                    <div className="space-y-1.5">
                                        {columns.map((col) => (
                                            <div
                                                key={`mobile-cell-${idx}-${col.key}`}
                                                className="flex items-start justify-between gap-3 rounded-lg bg-[var(--color-surface)]/40 px-2.5 py-2"
                                            >
                                                <div className="text-[11px] text-[var(--color-text-secondary)]">
                                                    {col.header}
                                                </div>
                                                <div
                                                    className={`text-xs text-[var(--color-text-primary)] ${
                                                        col.align === 'left' ? 'text-left' :
                                                        col.align === 'right' ? 'text-right' :
                                                        'text-center'
                                                    }`}
                                                >
                                                    {col.format
                                                        ? col.format(row[col.key])
                                                        : renderCellValue(row[col.key])
                                                    }
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="hidden md:block">
                            <table className="w-full min-w-[620px] border-collapse">
                                {/* Header */}
                                <thead>
                                    <tr className="bg-[var(--color-surface)]/30 border-b border-[var(--color-border)]">
                                        {columns.map((col) => (
                                            <th
                                                key={col.key}
                                                className={`px-2.5 sm:px-4 py-2.5 sm:py-3 text-[11px] sm:text-xs font-medium text-[var(--color-text-secondary)] uppercase tracking-wider cursor-${
                                                    sortable ? 'pointer hover:text-white' : 'default'
                                                } transition-colors ${
                                                    col.align === 'left' ? 'text-left' :
                                                    col.align === 'right' ? 'text-right' :
                                                    'text-center'
                                                }`}
                                                style={{ width: col.width }}
                                                onClick={() => handleSort(col.key)}
                                            >
                                                <div className="flex items-center gap-2 justify-${
                                                    col.align === 'left' ? 'start' :
                                                    col.align === 'right' ? 'end' :
                                                    'center'
                                                }">
                                                    {col.header}
                                                    {sortable && sortKey === col.key && (
                                                        sortOrder === 'asc' ? (
                                                            <ChevronUp className="w-4 h-4" />
                                                        ) : (
                                                            <ChevronDown className="w-4 h-4" />
                                                        )
                                                    )}
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                </thead>

                                {/* Body */}
                                <tbody>
                                    {sortedData.map((row, idx) => (
                                        <tr
                                            key={idx}
                                            className={`border-t border-[var(--color-border)] transition-colors ${
                                                striped && idx % 2 === 0 ? 'bg-[var(--color-surface)]/10' : ''
                                            } ${
                                                hoverable ? 'hover:bg-[var(--color-surface)]/20' : ''
                                            } ${
                                                onRowClick ? 'cursor-pointer' : ''
                                            }`}
                                            onClick={() => onRowClick?.(row, idx)}
                                        >
                                            {columns.map((col) => (
                                                <td
                                                    key={`${idx}-${col.key}`}
                                                    className={`px-2.5 sm:px-4 py-2.5 sm:py-3 text-xs sm:text-sm ${
                                                        col.align === 'left' ? 'text-left' :
                                                        col.align === 'right' ? 'text-right' :
                                                        'text-center'
                                                    }`}
                                                >
                                                    {col.format
                                                        ? col.format(row[col.key])
                                                        : renderCellValue(row[col.key])
                                                    }
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}
            </div>
        </motion.div>
    );
}

/**
 * Utility formatters for common data types
 */
export const tableFormatters = {
    // Format currency
    currency: (value: number, currency = 'EGP') =>
        new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency,
            maximumFractionDigits: 0
        }).format(value),

    // Format percentage with arrow
    percentageWithTrend: (value: number, icon = true) => (
        <span className={`flex items-center gap-1 ${value > 0 ? 'text-green-400' : value < 0 ? 'text-red-400' : ''}`}>
            {icon && value > 0 && <TrendingUp className="w-4 h-4" />}
            {icon && value < 0 && <TrendingDown className="w-4 h-4" />}
            {Math.abs(value).toFixed(1)}%
        </span>
    ),

    // Format percentage
    percentage: (value: number) =>
        `${(value * 100).toFixed(1)}%`,

    // Format number with commas
    number: (value: number) =>
        value.toLocaleString('en-EG'),

    // Format area (square meters)
    area: (value: number) =>
        `${value.toLocaleString('en-EG')} م²`,

    // Format date
    date: (value: string | Date) => {
        const date = typeof value === 'string' ? new Date(value) : value;
        return new Intl.DateTimeFormat('ar-EG').format(date);
    },

    // Format text with ellipsis
    ellipsis: (value: string, maxLength = 30) =>
        value.length > maxLength ? `${value.substring(0, maxLength)}...` : value,

    // Format with badge
    badge: (value: string, color = 'blue') => (
        <span className={`px-3 py-1 rounded-full text-xs font-medium bg-${color}-500/20 text-${color}-400`}>
            {value}
        </span>
    ),

    // Format with color based on value
    conditional: (value: number, options = { positive: 'green', negative: 'red', neutral: 'gray' }) => (
        <span className={
            value > 0 ? `text-${options.positive}-400` :
            value < 0 ? `text-${options.negative}-400` :
            `text-${options.neutral}-400`
        }>
            {value > 0 ? '+' : ''}{value}
        </span>
    ),

    // Format ROI
    roi: (value: number) => (
        <span className={`${value > 8 ? 'text-green-400' : value > 4 ? 'text-yellow-400' : 'text-red-400'}`}>
            {value.toFixed(1)}%
        </span>
    ),

    // Format boolean as yes/no in Arabic
    yesNo: (value: boolean) =>
        value ? <span className="text-green-400">✓ نعم</span> : <span className="text-red-400">✗ لا</span>,
};
