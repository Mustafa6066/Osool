"use client";

import { motion } from "framer-motion";
import { 
    Building2, 
    Star,
    Trophy,
    Clock,
    BadgeCheck
} from "lucide-react";

interface DeveloperAnalysisProps {
    developer: {
        name: string;
        tier: string;
        reputation_score: number;
        avg_price_premium: string;
        delivery_rating: string;
        popular_projects: string[];
        strengths: string[];
    };
    rankings?: {
        by_reputation: string[];
        by_value: string[];
        by_delivery: string[];
    };
}

export default function DeveloperAnalysis({ developer, rankings }: DeveloperAnalysisProps) {
    // Defensive check for required props
    if (!developer || !developer.name) {
        console.warn('DeveloperAnalysis: Missing required developer data');
        return null;
    }

    const getScoreColor = (score: number) => {
        if (score >= 90) return 'text-emerald-400';
        if (score >= 80) return 'text-blue-400';
        if (score >= 70) return 'text-amber-400';
        return 'text-red-400';
    };

    const getScoreBarColor = (score: number) => {
        if (score >= 90) return 'from-emerald-500 to-emerald-400';
        if (score >= 80) return 'from-blue-500 to-blue-400';
        if (score >= 70) return 'from-amber-500 to-amber-400';
        return 'from-red-500 to-red-400';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-indigo-950/30 to-purple-950/20"
        >
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600/20 to-purple-600/20 px-6 py-4 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">تحليل المطور 🏢</h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">{developer.name}</p>
                    </div>
                    <div className="mr-auto px-3 py-1 bg-purple-500/20 rounded-full">
                        <span className="text-sm text-purple-300">{developer.tier}</span>
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Reputation Score */}
                <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-amber-400" />
                            <p className="text-sm font-medium text-white">تقييم السمعة</p>
                        </div>
                        <span className={`text-2xl font-bold ${getScoreColor(developer.reputation_score)}`}>
                            {developer.reputation_score}/100
                        </span>
                    </div>
                    <div className="h-3 bg-[var(--color-surface)] rounded-full overflow-hidden">
                        <motion.div 
                            initial={{ scaleX: 0 }}
                            animate={{ scaleX: developer.reputation_score / 100 }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            style={{ transformOrigin: 'left' }}
                            className={`h-full bg-gradient-to-r ${getScoreBarColor(developer.reputation_score)} rounded-full`}
                        />
                    </div>
                </div>

                {/* Key Metrics */}
                <div className="grid md:grid-cols-2 gap-4">
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Trophy className="w-4 h-4 text-amber-400" />
                            <p className="text-sm text-[var(--color-text-secondary)]">علاوة السعر</p>
                        </div>
                        <p className="text-white font-medium">{developer.avg_price_premium}</p>
                    </div>
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <Clock className="w-4 h-4 text-blue-400" />
                            <p className="text-sm text-[var(--color-text-secondary)]">تقييم التسليم</p>
                        </div>
                        <p className="text-white font-medium">{developer.delivery_rating}</p>
                    </div>
                </div>

                {/* Popular Projects */}
                <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                        <Building2 className="w-4 h-4 text-indigo-400" />
                        <p className="text-sm font-medium text-white">أشهر المشاريع</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {(developer.popular_projects || []).map((project, i) => (
                            <span key={i} className="px-3 py-1 bg-indigo-500/20 text-indigo-300 text-sm rounded-full">
                                {project}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Strengths */}
                <div className="bg-gradient-to-r from-emerald-950/30 to-emerald-950/30 rounded-xl p-4 border border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-3">
                        <BadgeCheck className="w-4 h-4 text-emerald-400" />
                        <p className="text-sm font-medium text-emerald-400">نقاط القوة</p>
                    </div>
                    <ul className="space-y-2">
                        {(developer.strengths || []).map((strength, i) => (
                            <li key={i} className="text-sm text-[var(--color-text-secondary)] flex items-start gap-2">
                                <span className="text-emerald-400">✓</span> {strength}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Rankings Comparison */}
                {rankings && (
                    <div className="bg-[var(--color-surface)]/30 rounded-xl p-4">
                        <p className="text-sm font-medium text-white mb-4">ترتيب المطورين</p>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                                <p className="text-[var(--color-text-secondary)] mb-2 text-xs">بالسمعة</p>
                                {(rankings.by_reputation || []).slice(0, 3).map((dev, i) => (
                                    <p key={i} className={`${i === 0 ? 'text-amber-400' : 'text-[var(--color-text-secondary)]'}`}>
                                        {i + 1}. {dev}
                                    </p>
                                ))}
                            </div>
                            <div>
                                <p className="text-[var(--color-text-secondary)] mb-2 text-xs">بالقيمة</p>
                                {(rankings.by_value || []).slice(0, 3).map((dev, i) => (
                                    <p key={i} className={`${i === 0 ? 'text-emerald-400' : 'text-[var(--color-text-secondary)]'}`}>
                                        {i + 1}. {dev}
                                    </p>
                                ))}
                            </div>
                            <div>
                                <p className="text-[var(--color-text-secondary)] mb-2 text-xs">بالتسليم</p>
                                {(rankings.by_delivery || []).slice(0, 3).map((dev, i) => (
                                    <p key={i} className={`${i === 0 ? 'text-blue-400' : 'text-[var(--color-text-secondary)]'}`}>
                                        {i + 1}. {dev}
                                    </p>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
