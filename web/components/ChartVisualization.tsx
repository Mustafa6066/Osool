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
    const maxValue = Math.max(...data);
    const trendColor = trend?.includes('+') ? 'text-green-400' : 'text-red-400';
    const TrendIcon = trend?.includes('+') ? TrendingUp : TrendingDown;

    return (
        <div className="w-full max-w-3xl bg-[#1c2b31] border border-[#273d44] rounded-2xl overflow-hidden shadow-xl p-6 mt-4">
            {/* Chart Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-white font-bold text-lg">{title}</h3>
                    {subtitle && (
                        <p className="text-[#97b8c3] text-sm mt-1">{subtitle}</p>
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
                        {data.map((value, idx) => {
                            const heightPercent = (value / maxValue) * 100;
                            return (
                                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                                    <div className="w-full flex items-end justify-center h-full">
                                        <div
                                            className="w-full bg-gradient-to-t from-[#267360] to-[#2dd4bf] rounded-t-lg transition-all duration-500 hover:opacity-80 relative group"
                                            style={{ height: `${heightPercent}%` }}
                                        >
                                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#2c3533] text-white text-xs font-bold px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                                {value.toLocaleString()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="flex justify-between text-xs text-[#97b8c3]">
                        {labels.map((label, idx) => (
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
                                    <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.3" />
                                    <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
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
                                    stroke="#273d44"
                                    strokeWidth="1"
                                    strokeDasharray="4 4"
                                />
                            ))}
                            {/* Line Path */}
                            <path
                                d={`M ${data.map((val, idx) => {
                                    const x = (idx / (data.length - 1)) * 500;
                                    const y = 200 - (val / maxValue) * 180;
                                    return `${x},${y}`;
                                }).join(' L ')}`}
                                fill="none"
                                stroke="#2dd4bf"
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                            {/* Area Fill */}
                            <path
                                d={`M ${data.map((val, idx) => {
                                    const x = (idx / (data.length - 1)) * 500;
                                    const y = 200 - (val / maxValue) * 180;
                                    return `${x},${y}`;
                                }).join(' L ')} L 500,200 L 0,200 Z`}
                                fill="url(#lineGradient)"
                            />
                            {/* Data Points */}
                            {data.map((val, idx) => {
                                const x = (idx / (data.length - 1)) * 500;
                                const y = 200 - (val / maxValue) * 180;
                                return (
                                    <circle
                                        key={idx}
                                        cx={x}
                                        cy={y}
                                        r="4"
                                        fill="#1c2b31"
                                        stroke="#2dd4bf"
                                        strokeWidth="2"
                                        className="hover:r-6 transition-all"
                                    />
                                );
                            })}
                        </svg>
                    </div>
                    <div className="flex justify-between text-xs text-[#97b8c3]">
                        {labels.map((label, idx) => (
                            <span key={idx}>{label}</span>
                        ))}
                    </div>
                </div>
            )}

            {type === 'comparison' && (
                <div className="space-y-3">
                    {labels.map((label, idx) => {
                        const value = data[idx];
                        const percent = (value / maxValue) * 100;
                        return (
                            <div key={idx}>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-white font-medium">{label}</span>
                                    <span className="text-[#2dd4bf] font-bold">{value.toLocaleString()}</span>
                                </div>
                                <div className="h-8 bg-[#121615] rounded-lg overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-[#267360] to-[#2dd4bf] transition-all duration-500"
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
