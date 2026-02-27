'use client';

import React from 'react';
import { Search, BarChart2, GitCompare, Target, CheckCircle } from 'lucide-react';

const STAGES = [
    { key: 'discovery', icon: Search, label_en: 'Discovery', label_ar: 'اكتشاف' },
    { key: 'research', icon: BarChart2, label_en: 'Research', label_ar: 'بحث' },
    { key: 'comparison', icon: GitCompare, label_en: 'Compare', label_ar: 'مقارنة' },
    { key: 'decision', icon: Target, label_en: 'Decision', label_ar: 'قرار' },
    { key: 'action', icon: CheckCircle, label_en: 'Action', label_ar: 'تنفيذ' },
];

function getStageFromScore(leadScore: number): number {
    if (leadScore >= 80) return 4; // Action
    if (leadScore >= 60) return 3; // Decision
    if (leadScore >= 40) return 2; // Comparison
    if (leadScore >= 20) return 1; // Research
    return 0; // Discovery
}

interface FunnelIndicatorProps {
    leadScore: number;
    readinessScore?: number;
    language?: string;
}

/**
 * Funnel Indicator V5 — B/W + Emerald
 * Shows where user is in the buying journey.
 * Compact bar for chat header or sidebar.
 */
export default function FunnelIndicator({ leadScore, readinessScore, language = 'en' }: FunnelIndicatorProps) {
    const currentStage = getStageFromScore(leadScore);

    return (
        <div className="px-4 py-3">
            {/* Stage Dots */}
            <div className="flex items-center justify-between mb-2">
                {STAGES.map((stage, i) => {
                    const Icon = stage.icon;
                    const isActive = i <= currentStage;
                    const isCurrent = i === currentStage;

                    return (
                        <React.Fragment key={stage.key}>
                            <div className="flex flex-col items-center gap-1">
                                <div
                                    className={`w-7 h-7 rounded-full flex items-center justify-center transition-all duration-500
                                        ${isCurrent
                                            ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20 scale-110'
                                            : isActive
                                                ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                                                : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                                        }`}
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                </div>
                                <span className={`text-[9px] font-medium transition-colors
                                    ${isCurrent ? 'text-emerald-500' : isActive ? 'text-[var(--color-text-muted)]' : 'text-[var(--color-text-muted)] opacity-50'}`}>
                                    {language === 'ar' ? stage.label_ar : stage.label_en}
                                </span>
                            </div>

                            {/* Connector line */}
                            {i < STAGES.length - 1 && (
                                <div className="flex-1 h-px mx-1 mb-4">
                                    <div
                                        className={`h-full transition-colors duration-500
                                            ${i < currentStage ? 'bg-emerald-500/40' : 'bg-[var(--color-border)]'}`}
                                    />
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>

            {/* Readiness Score */}
            {readinessScore !== undefined && (
                <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wider whitespace-nowrap">
                        {language === 'ar' ? 'جاهزية الاستثمار' : 'Investment Readiness'}
                    </span>
                    <div className="flex-1 h-1.5 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-700"
                            style={{ width: `${readinessScore}%` }}
                        />
                    </div>
                    <span className="text-xs font-bold text-emerald-500">{readinessScore}%</span>
                </div>
            )}
        </div>
    );
}
