'use client';

import { ReactNode } from 'react';
import {
    Bed,
    Bath,
    Ruler,
    DollarSign,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    CheckCircle,
    Target,
    Building2,
    Calendar
} from 'lucide-react';

// Metric item configuration
export interface MetricItem {
    id: string;
    label: string;
    value: string | number;
    icon?: ReactNode;
    trend?: 'up' | 'down' | 'stable';
    highlight?: 'success' | 'warning' | 'danger' | 'default';
    suffix?: string;
}

interface MetricsGridProps {
    metrics: MetricItem[];
    columns?: 2 | 3 | 6;
    isRTL?: boolean;
    className?: string;
}

// Icon mapping for common metric types
export const metricIcons: Record<string, ReactNode> = {
    bedrooms: <Bed size={16} />,
    bathrooms: <Bath size={16} />,
    size: <Ruler size={16} />,
    price_per_sqm: <DollarSign size={16} />,
    cap_rate: <Target size={16} />,
    risk: <AlertTriangle size={16} />,
    developer: <Building2 size={16} />,
    delivery: <Calendar size={16} />,
    roi: <TrendingUp size={16} />,
};

// Highlight color mapping
const highlightColors = {
    success: {
        bg: 'bg-[var(--semantic-success)]/10',
        text: 'text-[var(--semantic-success)]',
        icon: <CheckCircle size={14} className="text-[var(--semantic-success)]" />
    },
    warning: {
        bg: 'bg-[var(--semantic-warning)]/10',
        text: 'text-[var(--semantic-warning)]',
        icon: <AlertTriangle size={14} className="text-[var(--semantic-warning)]" />
    },
    danger: {
        bg: 'bg-[var(--semantic-danger)]/10',
        text: 'text-[var(--semantic-danger)]',
        icon: <AlertTriangle size={14} className="text-[var(--semantic-danger)]" />
    },
    default: {
        bg: 'bg-[var(--semantic-surface-elevated)]',
        text: 'text-[var(--semantic-text-primary)]',
        icon: null
    }
};

export default function MetricsGrid({
    metrics,
    columns = 3,
    isRTL = false,
    className = ''
}: MetricsGridProps) {
    const gridColsClass = {
        2: 'grid-cols-2',
        3: 'grid-cols-3',
        6: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6'
    }[columns];

    return (
        <div
            className={`grid ${gridColsClass} gap-3 ${className}`}
            style={{ gap: 'var(--space-3, 12px)' }}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {metrics.map((metric, index) => {
                const highlight = highlightColors[metric.highlight || 'default'];

                return (
                    <div
                        key={metric.id}
                        className={`
                            flex flex-col items-center justify-center
                            p-3 rounded-lg
                            ${highlight.bg}
                            border border-[var(--semantic-border)]
                            transition-all duration-200
                            hover:scale-[1.02] hover:shadow-sm
                        `}
                        style={{
                            padding: 'var(--space-3, 12px)',
                            borderRadius: 'var(--radius-md, 12px)',
                            animationDelay: `${index * 0.05}s`
                        }}
                    >
                        {/* Icon */}
                        {metric.icon && (
                            <div className="mb-1 text-[var(--semantic-text-muted)]">
                                {metric.icon}
                            </div>
                        )}

                        {/* Value */}
                        <div className={`
                            text-lg font-bold flex items-center gap-1
                            ${highlight.text}
                        `}>
                            {metric.trend === 'up' && (
                                <TrendingUp size={14} className="text-[var(--semantic-success)]" />
                            )}
                            {metric.trend === 'down' && (
                                <TrendingDown size={14} className="text-[var(--semantic-danger)]" />
                            )}
                            {metric.value}
                            {metric.suffix && (
                                <span className="text-sm font-normal text-[var(--semantic-text-muted)]">
                                    {metric.suffix}
                                </span>
                            )}
                        </div>

                        {/* Label */}
                        <div className="text-xs text-[var(--semantic-text-muted)] mt-0.5 text-center">
                            {metric.label}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// Pre-configured metric generators for common use cases
export function generatePropertyMetrics(property: {
    bedrooms?: number;
    bathrooms?: number;
    sqft?: number;
    pricePerSqm?: number;
    capRate?: string;
    riskLevel?: 'Low' | 'Medium' | 'High';
}, isRTL: boolean = false): MetricItem[] {
    const metrics: MetricItem[] = [];

    if (property.bedrooms !== undefined) {
        metrics.push({
            id: 'bedrooms',
            label: isRTL ? 'غرف النوم' : 'Bedrooms',
            value: property.bedrooms,
            icon: metricIcons.bedrooms
        });
    }

    if (property.bathrooms !== undefined) {
        metrics.push({
            id: 'bathrooms',
            label: isRTL ? 'الحمامات' : 'Bathrooms',
            value: property.bathrooms,
            icon: metricIcons.bathrooms
        });
    }

    if (property.sqft !== undefined) {
        metrics.push({
            id: 'size',
            label: isRTL ? 'المساحة' : 'Size',
            value: property.sqft.toLocaleString(),
            suffix: isRTL ? 'م²' : 'sqm',
            icon: metricIcons.size
        });
    }

    if (property.pricePerSqm !== undefined) {
        metrics.push({
            id: 'price_per_sqm',
            label: isRTL ? 'السعر/م²' : 'Price/sqm',
            value: `${(property.pricePerSqm / 1000).toFixed(1)}K`,
            icon: metricIcons.price_per_sqm
        });
    }

    if (property.capRate) {
        metrics.push({
            id: 'cap_rate',
            label: isRTL ? 'معدل العائد' : 'Cap Rate',
            value: property.capRate,
            icon: metricIcons.cap_rate,
            highlight: 'success'
        });
    }

    if (property.riskLevel) {
        const riskHighlight = {
            'Low': 'success' as const,
            'Medium': 'warning' as const,
            'High': 'danger' as const
        }[property.riskLevel];

        metrics.push({
            id: 'risk',
            label: isRTL ? 'مستوى المخاطر' : 'Risk Level',
            value: isRTL ?
                { 'Low': 'منخفض', 'Medium': 'متوسط', 'High': 'مرتفع' }[property.riskLevel] :
                property.riskLevel,
            icon: metricIcons.risk,
            highlight: riskHighlight
        });
    }

    return metrics;
}
