'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Search, BarChart2, GitCompare, Target, CheckCircle, Zap } from 'lucide-react';

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
 * Funnel Indicator V6 — Dynamic & Smart
 * Shows where user is in the buying journey with animated motion and modern UI.
 */
export default function FunnelIndicator({ leadScore, readinessScore, language = 'en' }: FunnelIndicatorProps) {
    const currentStage = getStageFromScore(leadScore);
    const isAr = language === 'ar';

    // Calculate progression percentage (0 to 1) mapped to stages
    // 4 segments between 5 stages. Each segment is 25% of the bar.
    const progressFill = (currentStage / (STAGES.length - 1)) * 100;

    return (
        <div className="w-full flex flex-col items-center justify-center py-2" dir={isAr ? 'rtl' : 'ltr'}>
            
            {/* Dynamic Segmented Track */}
            <div className="relative w-full max-w-md flex items-center justify-between mt-2 mb-8">
                
                {/* Background Connecting Line */}
                <div className="absolute top-1/2 -translate-y-1/2 left-4 right-4 h-[3px] bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                    <motion.div 
                        className="h-full bg-emerald-500 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${progressFill}%` }}
                        transition={{ duration: 1.2, ease: "easeInOut" }}
                    />
                </div>

                {STAGES.map((stage, i) => {
                    const Icon = stage.icon;
                    const isActive = i <= currentStage;
                    const isCurrent = i === currentStage;

                    return (
                        <div key={stage.key} className="relative z-10 flex flex-col items-center">
                            {/* Animated Node */}
                            <motion.div
                                animate={isCurrent ? { scale: [1, 1.15, 1], boxShadow: ["0px 0px 0px rgba(16,185,129,0)", "0px 0px 20px rgba(16,185,129,0.4)", "0px 0px 0px rgba(16,185,129,0)"] } : { scale: 1 }}
                                transition={{ repeat: isCurrent ? Infinity : 0, duration: 2.5, ease: "easeInOut" }}
                                className={`w-8 h-8 md:w-9 md:h-9 rounded-full flex items-center justify-center backdrop-blur-md transition-all duration-700 border-2 ${
                                    isCurrent 
                                        ? 'bg-emerald-500 text-white border-emerald-500'
                                        : isActive
                                            ? 'bg-white dark:bg-gray-900 text-emerald-500 border-emerald-500/40'
                                            : 'bg-white dark:bg-gray-900 text-gray-400 dark:text-gray-600 border-gray-200 dark:border-gray-800'
                                }`}
                            >
                                <Icon className="w-4 h-4 md:w-4 md:h-4" strokeWidth={isCurrent ? 2.5 : 2} />
                            </motion.div>
                            
                            {/* Text Label - Highlighted for current */}
                            <div className="absolute top-[2.5rem] md:top-[2.75rem] whitespace-nowrap text-center">
                                <span className={`text-[10px] md:text-[11px] block transition-all duration-500 ${
                                    isCurrent 
                                        ? 'font-bold text-emerald-600 dark:text-emerald-400 translate-y-0.5 opacity-100' 
                                        : isActive 
                                            ? 'font-medium text-[var(--color-text-secondary)] opacity-80'
                                            : 'font-medium text-[var(--color-text-muted)] opacity-40'
                                }`}>
                                    {isAr ? stage.label_ar : stage.label_en}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Smart Readiness Score Pill */}
            {readinessScore !== undefined && (
                <motion.div 
                    initial={{ opacity: 0, y: 15, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.6, delay: 0.3 }}
                    className="flex flex-col sm:flex-row items-center gap-3 sm:gap-4 px-5 py-2.5 bg-gradient-to-r from-[var(--color-surface)] to-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.03)]"
                >
                    <div className="flex items-center gap-2">
                        <div className={`p-1.5 rounded-full ${readinessScore > 50 ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'}`}>
                            <Zap className="w-3.5 h-3.5" fill="currentColor" />
                        </div>
                        <span className="text-[11px] md:text-[12px] text-[var(--color-text-primary)] font-semibold uppercase tracking-wider">
                            {isAr ? 'مؤشر جاهزية الاستثمار' : 'Investment Readiness Index'}
                        </span>
                    </div>

                    <div className="flex items-center gap-3 w-[160px] sm:w-[200px]">
                        <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden shadow-inner">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${readinessScore}%` }}
                                transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
                                className={`h-full rounded-full ${
                                    readinessScore >= 75 ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : 
                                    readinessScore >= 40 ? 'bg-gradient-to-r from-emerald-400 to-yellow-400' : 
                                    'bg-gradient-to-r from-orange-400 to-red-400'
                                }`}
                            />
                        </div>
                        <span className="text-[13px] font-bold text-[var(--color-text-primary)] min-w-[34px] text-right">
                            {Math.round(readinessScore)}%
                        </span>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
