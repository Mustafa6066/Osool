'use client';

import { useMemo, useEffect, useRef, useState } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    TooltipProps
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, Sparkles } from 'lucide-react';
import anime from 'animejs';

interface ChartDataPoint {
    year: string;
    price: number;
    projected?: boolean;
}

interface EmbeddedChartProps {
    data: ChartDataPoint[];
    title?: string;
    subtitle?: string;
    height?: number;
    isRTL?: boolean;
    showGrid?: boolean;
    showTooltip?: boolean;
    trend?: 'up' | 'down' | 'stable';
    trendValue?: string;
    enableDrawAnimation?: boolean;
}

// Custom tooltip component
function CustomTooltip({
    active,
    payload,
    label,
    isRTL
}: TooltipProps<number, string> & { isRTL?: boolean }) {
    if (!active || !payload || !payload.length) return null;

    const value = payload[0].value as number;
    const isProjected = payload[0].payload?.projected;

    return (
        <div
            className="px-3 py-2 rounded-lg shadow-lg border"
            style={{
                background: 'var(--semantic-surface-card)',
                borderColor: 'var(--semantic-border)',
                borderRadius: 'var(--radius-md, 12px)'
            }}
        >
            <p className="text-xs text-[var(--semantic-text-muted)] mb-1">
                {label} {isProjected && (isRTL ? '(متوقع)' : '(Projected)')}
            </p>
            <p className="text-sm font-semibold text-[var(--semantic-text-primary)]">
                {formatPrice(value)}
            </p>
        </div>
    );
}

// Price formatter
function formatPrice(value: number): string {
    if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M EGP`;
    }
    if (value >= 1000) {
        return `${(value / 1000).toFixed(0)}K EGP`;
    }
    return `${value} EGP`;
}

// AI Drawing indicator component
function AIDrawingIndicator({ isDrawing, isRTL }: { isDrawing: boolean; isRTL: boolean }) {
    if (!isDrawing) return null;

    return (
        <div className="absolute top-3 right-3 flex items-center gap-2 px-2 py-1 rounded-full bg-[var(--semantic-primary)]/10 z-10">
            <Sparkles size={12} className="text-[var(--semantic-primary)] animate-pulse" />
            <span className="text-[10px] font-semibold text-[var(--semantic-primary)]">
                {isRTL ? 'AI يرسم...' : 'AI Drawing...'}
            </span>
        </div>
    );
}

export default function EmbeddedChart({
    data,
    title,
    subtitle,
    height = 200,
    isRTL = false,
    showGrid = true,
    showTooltip = true,
    trend,
    trendValue,
    enableDrawAnimation = true
}: EmbeddedChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const [isDrawing, setIsDrawing] = useState(enableDrawAnimation);
    const [chartReady, setChartReady] = useState(!enableDrawAnimation);

    // Anime.js drawing animation
    useEffect(() => {
        if (!enableDrawAnimation || !chartContainerRef.current) {
            setChartReady(true);
            return;
        }

        setIsDrawing(true);
        setChartReady(false);

        // Small delay to ensure SVG is rendered
        const initTimer = setTimeout(() => {
            const container = chartContainerRef.current;
            if (!container) return;

            // Find the area path and animate it
            const areaPath = container.querySelector('.recharts-area-area');
            const linePath = container.querySelector('.recharts-area-curve');

            if (linePath) {
                const pathElement = linePath as SVGPathElement;
                const pathLength = pathElement.getTotalLength();

                // Set initial state
                pathElement.style.strokeDasharray = `${pathLength}`;
                pathElement.style.strokeDashoffset = `${pathLength}`;

                // Animate the line drawing
                anime({
                    targets: pathElement,
                    strokeDashoffset: [pathLength, 0],
                    easing: 'easeOutExpo',
                    duration: 1500,
                    delay: 200,
                    complete: () => {
                        setIsDrawing(false);
                    }
                });
            }

            // Fade in the area fill
            if (areaPath) {
                anime({
                    targets: areaPath,
                    opacity: [0, 1],
                    easing: 'easeOutQuad',
                    duration: 800,
                    delay: 800,
                });
            }

            // Animate the chart container
            anime({
                targets: container,
                opacity: [0.3, 1],
                easing: 'easeOutExpo',
                duration: 600,
            });

            setChartReady(true);
        }, 100);

        return () => clearTimeout(initTimer);
    }, [data, enableDrawAnimation]);

    // Calculate trend if not provided
    const calculatedTrend = useMemo(() => {
        if (trend) return trend;
        if (data.length < 2) return 'stable';

        const firstValue = data[0].price;
        const lastValue = data[data.length - 1].price;
        const change = ((lastValue - firstValue) / firstValue) * 100;

        if (change > 1) return 'up';
        if (change < -1) return 'down';
        return 'stable';
    }, [data, trend]);

    const calculatedTrendValue = useMemo(() => {
        if (trendValue) return trendValue;
        if (data.length < 2) return '0%';

        const firstValue = data[0].price;
        const lastValue = data[data.length - 1].price;
        const change = ((lastValue - firstValue) / firstValue) * 100;

        return `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`;
    }, [data, trendValue]);

    const TrendIcon = calculatedTrend === 'up'
        ? TrendingUp
        : calculatedTrend === 'down'
            ? TrendingDown
            : Minus;

    const trendColorClass = calculatedTrend === 'up'
        ? 'text-[var(--semantic-success)]'
        : calculatedTrend === 'down'
            ? 'text-[var(--semantic-danger)]'
            : 'text-[var(--semantic-text-muted)]';

    return (
        <div
            className="rounded-xl border overflow-hidden relative"
            style={{
                background: 'var(--chart-embedded-bg)',
                borderColor: 'var(--semantic-border)',
                borderRadius: 'var(--radius-lg, 16px)'
            }}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* AI Drawing Indicator */}
            <AIDrawingIndicator isDrawing={isDrawing} isRTL={isRTL} />

            {/* Header */}
            {(title || trend) && (
                <div
                    className="flex items-center justify-between px-4 py-3 border-b"
                    style={{
                        padding: 'var(--space-3, 12px) var(--space-4, 16px)',
                        borderColor: 'var(--semantic-border)'
                    }}
                >
                    <div>
                        {title && (
                            <h4 className="text-sm font-semibold text-[var(--semantic-text-primary)]">
                                {title}
                            </h4>
                        )}
                        {subtitle && (
                            <p className="text-xs text-[var(--semantic-text-muted)] mt-0.5">
                                {subtitle}
                            </p>
                        )}
                    </div>
                    <div className={`flex items-center gap-1 ${trendColorClass}`}>
                        <TrendIcon size={16} />
                        <span className="text-sm font-semibold">{calculatedTrendValue}</span>
                    </div>
                </div>
            )}

            {/* Chart */}
            <div
                ref={chartContainerRef}
                className="p-4"
                style={{ padding: 'var(--space-4, 16px)', opacity: enableDrawAnimation ? 0.3 : 1 }}
            >
                <ResponsiveContainer width="100%" height={height}>
                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id="chartAreaFill" x1="0" y1="0" x2="0" y2="1">
                                <stop
                                    offset="0%"
                                    stopColor="var(--chart-primary-semantic, var(--chart-primary, #124759))"
                                    stopOpacity={0.3}
                                />
                                <stop
                                    offset="100%"
                                    stopColor="var(--chart-primary-semantic, var(--chart-primary, #124759))"
                                    stopOpacity={0}
                                />
                            </linearGradient>
                        </defs>

                        {showGrid && (
                            <CartesianGrid
                                strokeDasharray="3 3"
                                stroke="var(--chart-grid, #E5E7EB)"
                                strokeOpacity={0.5}
                                vertical={false}
                            />
                        )}

                        <XAxis
                            dataKey="year"
                            tick={{
                                fontSize: 10,
                                fill: 'var(--semantic-text-muted, #6B7280)'
                            }}
                            axisLine={{ stroke: 'var(--chart-grid, #E5E7EB)' }}
                            tickLine={false}
                        />

                        <YAxis
                            tick={{
                                fontSize: 10,
                                fill: 'var(--semantic-text-muted, #6B7280)'
                            }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(value) => {
                                if (value >= 1000000) return `${(value / 1000000).toFixed(0)}M`;
                                if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
                                return value;
                            }}
                            width={40}
                        />

                        {showTooltip && chartReady && (
                            <Tooltip
                                content={<CustomTooltip isRTL={isRTL} />}
                                cursor={{
                                    stroke: 'var(--chart-primary-semantic, #124759)',
                                    strokeWidth: 1,
                                    strokeDasharray: '4 4'
                                }}
                            />
                        )}

                        <Area
                            type="monotone"
                            dataKey="price"
                            stroke="var(--chart-primary-semantic, var(--chart-primary, #124759))"
                            strokeWidth={2}
                            fill="url(#chartAreaFill)"
                            animationDuration={enableDrawAnimation ? 0 : 1000}
                            animationEasing="ease-out"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}

// Helper to generate sample projection data
export function generateProjectionData(
    currentPrice: number,
    yearsForward: number = 5,
    annualGrowthRate: number = 0.08
): ChartDataPoint[] {
    const currentYear = new Date().getFullYear();
    const data: ChartDataPoint[] = [];

    // Add 2 years of "historical" data
    for (let i = -2; i <= 0; i++) {
        const yearMultiplier = Math.pow(1 + annualGrowthRate, i);
        data.push({
            year: String(currentYear + i),
            price: Math.round(currentPrice * yearMultiplier),
            projected: false
        });
    }

    // Add projection data
    for (let i = 1; i <= yearsForward; i++) {
        const yearMultiplier = Math.pow(1 + annualGrowthRate, i);
        data.push({
            year: String(currentYear + i),
            price: Math.round(currentPrice * yearMultiplier),
            projected: true
        });
    }

    return data;
}
