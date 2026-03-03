'use client';

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, BarChart2, GitCompare, Target, CheckCircle,
    Zap, Sparkles, TrendingUp, Check,
} from 'lucide-react';

/* ─── Stage Config ─── */
const STAGES = [
    {
        key: 'discovery', icon: Search,
        label_en: 'Discovery', label_ar: 'اكتشاف',
        hint_en: 'Exploring the market', hint_ar: 'استكشاف السوق',
        gradient: 'from-blue-500 to-cyan-400',
        glow: 'rgba(59,130,246,0.5)',
        bg: 'bg-blue-500', text: 'text-blue-500', ring: 'ring-blue-500/30',
        bgSoft: 'bg-blue-500/10',
    },
    {
        key: 'research', icon: BarChart2,
        label_en: 'Research', label_ar: 'بحث',
        hint_en: 'Analyzing data', hint_ar: 'تحليل البيانات',
        gradient: 'from-violet-500 to-purple-400',
        glow: 'rgba(139,92,246,0.5)',
        bg: 'bg-violet-500', text: 'text-violet-500', ring: 'ring-violet-500/30',
        bgSoft: 'bg-violet-500/10',
    },
    {
        key: 'comparison', icon: GitCompare,
        label_en: 'Compare', label_ar: 'مقارنة',
        hint_en: 'Comparing options', hint_ar: 'مقارنة الخيارات',
        gradient: 'from-amber-500 to-orange-400',
        glow: 'rgba(245,158,11,0.5)',
        bg: 'bg-amber-500', text: 'text-amber-500', ring: 'ring-amber-500/30',
        bgSoft: 'bg-amber-500/10',
    },
    {
        key: 'decision', icon: Target,
        label_en: 'Decision', label_ar: 'قرار',
        hint_en: 'Making a choice', hint_ar: 'اتخاذ القرار',
        gradient: 'from-rose-500 to-pink-400',
        glow: 'rgba(244,63,94,0.5)',
        bg: 'bg-rose-500', text: 'text-rose-500', ring: 'ring-rose-500/30',
        bgSoft: 'bg-rose-500/10',
    },
    {
        key: 'action', icon: CheckCircle,
        label_en: 'Action', label_ar: 'تنفيذ',
        hint_en: 'Ready to invest!', hint_ar: '!جاهز للاستثمار',
        gradient: 'from-emerald-500 to-teal-400',
        glow: 'rgba(16,185,129,0.5)',
        bg: 'bg-emerald-500', text: 'text-emerald-500', ring: 'ring-emerald-500/30',
        bgSoft: 'bg-emerald-500/10',
    },
];

function getStageFromScore(leadScore: number): number {
    if (leadScore >= 80) return 4;
    if (leadScore >= 60) return 3;
    if (leadScore >= 40) return 2;
    if (leadScore >= 20) return 1;
    return 0;
}

interface FunnelIndicatorProps {
    leadScore: number;
    readinessScore?: number;
    language?: string;
}

/* ─── Floating Particle ─── */
function Particle({ delay, x, stage }: { delay: number; x: number; stage: typeof STAGES[0] }) {
    return (
        <motion.div
            className={`absolute w-1 h-1 rounded-full ${stage.bg} opacity-60`}
            initial={{ y: 0, x, opacity: 0, scale: 0 }}
            animate={{
                y: [0, -18, -28],
                opacity: [0, 0.8, 0],
                scale: [0, 1.2, 0],
            }}
            transition={{
                duration: 2.2,
                delay,
                repeat: Infinity,
                repeatDelay: 1.5,
                ease: 'easeOut',
            }}
        />
    );
}

/**
 * Funnel Indicator V7 — Creative Dynamic Design
 * Stage-colored nodes, animated particles, glowing current stage,
 * insight text, and a sleek readiness gauge.
 */
export default function FunnelIndicator({ leadScore, readinessScore, language = 'en' }: FunnelIndicatorProps) {
    const currentStage = getStageFromScore(leadScore);
    const stage = STAGES[currentStage];
    const isAr = language === 'ar';
    const progressPct = (currentStage / (STAGES.length - 1)) * 100;

    // Memoize particles so they don't re-randomize on every render
    const particles = useMemo(
        () => Array.from({ length: 5 }, (_, i) => ({
            id: i,
            delay: i * 0.35,
            x: (Math.random() - 0.5) * 16,
        })),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [currentStage],
    );

    return (
        <div className="w-full flex flex-col items-center gap-2 py-1" dir={isAr ? 'rtl' : 'ltr'}>

            {/* ── Stage Track ── */}
            <div className="relative w-full max-w-[420px] flex items-center justify-between px-1">

                {/* Background rail */}
                <div className="absolute top-1/2 -translate-y-1/2 left-5 right-5 h-[3px] rounded-full bg-[var(--color-border)] overflow-hidden">
                    {/* Animated gradient fill */}
                    <motion.div
                        className={`h-full rounded-full bg-gradient-to-r ${stage.gradient}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${progressPct}%` }}
                        transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
                    />
                    {/* Shimmer overlay on the filled portion */}
                    <motion.div
                        className="absolute inset-y-0 left-0 w-[60%] bg-gradient-to-r from-transparent via-white/25 to-transparent"
                        animate={{ x: ['-100%', '200%'] }}
                        transition={{ duration: 2.5, repeat: Infinity, repeatDelay: 3, ease: 'easeInOut' }}
                        style={{ maxWidth: `${progressPct}%` }}
                    />
                </div>

                {STAGES.map((s, i) => {
                    const Icon = s.icon;
                    const isCompleted = i < currentStage;
                    const isCurrent = i === currentStage;
                    const isLocked = i > currentStage;

                    return (
                        <div key={s.key} className="relative z-10 flex flex-col items-center">
                            {/* Glow ring for current */}
                            {isCurrent && (
                                <motion.div
                                    className={`absolute inset-0 rounded-full ${s.bg} opacity-20 blur-md`}
                                    animate={{ scale: [1, 1.8, 1], opacity: [0.15, 0.3, 0.15] }}
                                    transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
                                    style={{ width: 36, height: 36, margin: 'auto', top: 0, bottom: 0, left: 0, right: 0 }}
                                />
                            )}

                            {/* Floating particles above current node */}
                            {isCurrent && (
                                <div className="absolute -top-1 left-1/2 -translate-x-1/2 pointer-events-none">
                                    {particles.map(p => (
                                        <Particle key={p.id} delay={p.delay} x={p.x} stage={s} />
                                    ))}
                                </div>
                            )}

                            {/* Node */}
                            <motion.div
                                initial={{ scale: 0.6, opacity: 0 }}
                                animate={{
                                    scale: isCurrent ? [1, 1.1, 1] : 1,
                                    opacity: 1,
                                }}
                                transition={
                                    isCurrent
                                        ? { scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' }, opacity: { duration: 0.4, delay: i * 0.08 } }
                                        : { duration: 0.4, delay: i * 0.08 }
                                }
                                className={`relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-500 ${
                                    isCurrent
                                        ? `bg-gradient-to-br ${s.gradient} text-white shadow-lg ring-2 ${s.ring}`
                                        : isCompleted
                                            ? `${s.bgSoft} ${s.text} ring-1 ring-inset ${s.ring}`
                                            : 'bg-[var(--color-surface)] text-[var(--color-text-muted)] ring-1 ring-inset ring-[var(--color-border)] opacity-50'
                                }`}
                            >
                                {isCompleted ? (
                                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', stiffness: 400, damping: 15 }}>
                                        <Check className="w-4 h-4" strokeWidth={3} />
                                    </motion.div>
                                ) : (
                                    <Icon className="w-4 h-4" strokeWidth={isCurrent ? 2.5 : 1.8} />
                                )}
                            </motion.div>

                            {/* Label */}
                            <motion.span
                                initial={{ opacity: 0, y: 4 }}
                                animate={{ opacity: isLocked ? 0.35 : 1, y: 0 }}
                                transition={{ duration: 0.4, delay: 0.2 + i * 0.06 }}
                                className={`mt-1.5 text-[10px] md:text-[11px] leading-none whitespace-nowrap transition-all ${
                                    isCurrent
                                        ? `font-bold ${s.text}`
                                        : isCompleted
                                            ? 'font-semibold text-[var(--color-text-secondary)]'
                                            : 'font-medium text-[var(--color-text-muted)]'
                                }`}
                            >
                                {isAr ? s.label_ar : s.label_en}
                            </motion.span>
                        </div>
                    );
                })}
            </div>

            {/* ── Stage Insight + Readiness ── */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentStage}
                    initial={{ opacity: 0, y: 8, filter: 'blur(4px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -6, filter: 'blur(4px)' }}
                    transition={{ duration: 0.35 }}
                    className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mt-0.5"
                >
                    {/* Current-stage hint */}
                    <div className="flex items-center gap-1.5">
                        <motion.div
                            animate={{ rotate: [0, 15, -15, 0] }}
                            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                        >
                            <Sparkles className={`w-3 h-3 ${stage.text}`} />
                        </motion.div>
                        <span className={`text-[11px] font-medium ${stage.text}`}>
                            {isAr ? stage.hint_ar : stage.hint_en}
                        </span>
                    </div>

                    {/* Readiness gauge (inline) */}
                    {readinessScore !== undefined && (
                        <div className="flex items-center gap-2">
                            <div className={`p-0.5 rounded-full ${readinessScore > 50 ? stage.bgSoft : 'bg-orange-500/10'}`}>
                                <Zap className={`w-3 h-3 ${readinessScore > 50 ? stage.text : 'text-orange-500'}`} fill="currentColor" />
                            </div>
                            <span className="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
                                {isAr ? 'الجاهزية' : 'Readiness'}
                            </span>
                            <div className="w-20 h-[5px] rounded-full bg-[var(--color-border)] overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${readinessScore}%` }}
                                    transition={{ duration: 1.2, ease: 'easeOut', delay: 0.4 }}
                                    className={`h-full rounded-full bg-gradient-to-r ${
                                        readinessScore >= 60 ? stage.gradient : 'from-orange-400 to-amber-400'
                                    }`}
                                />
                            </div>
                            <span className={`text-[11px] font-bold tabular-nums ${readinessScore >= 60 ? stage.text : 'text-orange-500'}`}>
                                {Math.round(readinessScore)}%
                            </span>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
