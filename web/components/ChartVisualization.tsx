'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface ChartVisualizationProps {
    type: 'line' | 'bar' | 'comparison';
    title: string;
    data: number[];
    labels: string[];
    trend?: string;
    subtitle?: string;
}

export default function ChartVisualization({
    type,
    title,
    data,
    labels,
    trend,
    subtitle
}: ChartVisualizationProps) {
    // Safeguard: Ensure data is an array of numbers
    const cleanData = Array.isArray(data) ? data : [];
    const cleanLabels = Array.isArray(labels) ? labels : [];
    const maxValue = cleanData.length > 0 ? Math.max(...cleanData) : 100;
    const trendColor = trend?.includes('+') ? 'text-green-400' : 'text-red-400';
    const TrendIcon = trend?.includes('+') ? TrendingUp : TrendingDown;

    return (
        <div className="w-full max-w-3xl bg-[var(--osool-surface)] border border-[var(--osool-border)] rounded-2xl overflow-hidden shadow-xl p-6 mt-4">
            {/* Chart Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-[var(--osool-text)] font-bold text-lg">{title}</h3>
                    {subtitle && (
                        <p className="text-[var(--osool-muted)] text-sm mt-1">{subtitle}</p>
                    )}
                </div>
                {trend && (
                    <span className={`flex items-center gap-1 font-bold text-sm ${trendColor}`}>
                        <TrendIcon size={16} />
                        {trend}
                    </span>
                )}
            </div>

            {/* Chart Body */}
            {type === 'bar' && (
                <div className="space-y-4">
                    <div className="h-64 flex items-end gap-2">
                        {cleanData.map((value, idx) => {
                            const heightPercent = (value / maxValue) * 100;
                            return (
                                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                                    <div className="w-full flex items-end justify-center h-full">
                                        <div
                                            className="w-full bg-gradient-to-t from-[var(--osool-accent-dark)] to-[var(--osool-accent)] rounded-t-lg transition-all duration-500 hover:opacity-80 relative group"
                                            style={{ height: `${heightPercent}%` }}
                                        >
                                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[var(--osool-surface-3)] text-[var(--osool-text)] text-xs font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                                {value.toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="flex justify-between text-xs text-[var(--osool-muted)]">
                        {cleanLabels.map((label, idx) => (
                            <span key={idx} className="flex-1 text-center">{label}</span>
                        ))}
                    </div>
                </div>
            )}

            {type === 'line' && (
                <div className="space-y-4">
                    <div className="h-64 relative">
                        <svg className="w-full h-full" viewBox="0 0 500 200" preserveAspectRatio="none">
                            <defs>
                                <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="var(--osool-accent)" stopOpacity="0.3" />
                                    <stop offset="100%" stopColor="var(--osool-accent)" stopOpacity="0" />
                                </linearGradient>
                            </defs>
                            {/* Grid Lines */}
                            {[0, 1, 2, 3, 4].map((i) => (
                                <line
                                    key={i}
                                    x1="0"
                                    y1={i * 50}
                                    x2="500"
                                    y2={i * 50}
                                    stroke="var(--osool-border)"
                                    strokeWidth="1"
                                    strokeDasharray="4 4"
                                />
                            ))}
                            {/* Line Path */}
                            <path
                                d={`M ${cleanData.map((val, idx) => {
                                    const x = (idx / (cleanData.length - 1)) * 500;
                                    const y = 200 - (val / maxValue) * 180;
                                    return `${x},${y}`;
                                }).join(' L ')}`}
                                fill="none"
                                stroke="var(--osool-accent)"
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                            {/* Area Fill */}
                            <path
                                d={`M ${cleanData.map((val, idx) => {
                                    const x = (idx / (cleanData.length - 1)) * 500;
                                    const y = 200 - (val / maxValue) * 180;
                                    return `${x},${y}`;
                                }).join(' L ')} L 500,200 L 0,200 Z`}
                                fill="url(#lineGradient)"
                            />
                            {/* Data Points */}
                            {cleanData.map((val, idx) => {
                                const x = (idx / (cleanData.length - 1)) * 500;
                                const y = 200 - (val / maxValue) * 180;
                                return (
                                    <circle
                                        key={idx}
                                        cx={x}
                                        cy={y}
                                        r="4"
                                        fill="var(--osool-surface)"
                                        stroke="var(--osool-accent)"
                                        strokeWidth="2"
                                        className="hover:r-6 transition-all"
                                    />
                                );
                            })}
                        </svg>
                    </div>
                    <div className="flex justify-between text-xs text-[var(--osool-muted)]">
                        {cleanLabels.map((label, idx) => (
                            <span key={idx}>{label}</span>
                        ))}
                    </div>
                </div>
            )}

            {type === 'comparison' && (
                <div className="space-y-3">
                    {cleanLabels.map((label, idx) => {
                        const value = cleanData[idx];
                        const percent = (value / maxValue) * 100;
                        return (
                            <div key={idx}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-[var(--osool-text)] font-medium">{label}</span>
                                    <span className="text-[var(--osool-accent)] font-bold">{value.toLocaleString()}</span>
                                </div>
                                <div className="h-8 bg-[var(--osool-surface-2)] rounded-lg overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-[var(--osool-accent-dark)] to-[var(--osool-accent)] transition-all duration-500"
                                        style={{ width: `${percent}%` }}
                                    />
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
