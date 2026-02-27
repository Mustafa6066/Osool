'use client';

import React from 'react';
import { Flame, TrendingUp, Award, ChevronRight } from 'lucide-react';
import { InvestorProfile, LEVEL_COLORS, LEVEL_GRADIENTS } from '@/lib/gamification';

interface InvestorProfileCardProps {
    profile: InvestorProfile;
    language?: string;
    compact?: boolean;
}

/**
 * Investor Profile Card - Level, XP bar, streak, readiness
 * Used in dashboard and chat sidebar.
 * Theme-aware: uses CSS custom properties.
 */
export default function InvestorProfileCard({ profile, language = 'en', compact = false }: InvestorProfileCardProps) {
    const levelColor = LEVEL_COLORS[profile.level] || LEVEL_COLORS.curious;
    const levelGradient = LEVEL_GRADIENTS[profile.level] || LEVEL_GRADIENTS.curious;

    // Calculate XP progress within current level
    const xpProgress = profile.next_level
        ? Math.min(((profile.xp - (profile.next_level.xp_required - profile.next_level.xp_remaining)) / profile.next_level.xp_remaining) * 100, 100)
        : 100;

    const levelTitle = language === 'ar' ? profile.level_title_ar : profile.level_title_en;
    const nextLevelTitle = profile.next_level
        ? (language === 'ar' ? profile.next_level.title_ar : profile.next_level.title_en)
        : null;

    if (compact) {
        return (
            <div className="flex items-center gap-3 px-3 py-2">
                {/* Level Badge */}
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${levelGradient} flex items-center justify-center shadow-lg`}>
                    <span className="text-xs font-bold text-white">{profile.xp}</span>
                </div>
                <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--color-text-primary)]">{levelTitle}</div>
                    <div className="w-full h-1 bg-[var(--color-surface-elevated)] rounded-full mt-1">
                        <div
                            className={`h-full rounded-full bg-gradient-to-r ${levelGradient} transition-all duration-500`}
                            style={{ width: `${Math.max(xpProgress, 5)}%` }}
                        />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] p-6 space-y-5">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${levelGradient}
                                    flex items-center justify-center shadow-lg`}>
                        <Award className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <div className="text-lg font-medium text-[var(--color-text-primary)]">{levelTitle}</div>
                        <div className="text-xs text-[var(--color-text-muted)]">
                            {profile.xp.toLocaleString()} XP
                        </div>
                    </div>
                </div>

                {/* Streak */}
                {profile.login_streak > 0 && (
                    <div className="flex items-center gap-1.5 px-3 py-1.5 bg-orange-900/20 rounded-full border border-orange-800/30">
                        <Flame className="w-4 h-4 text-orange-400" />
                        <span className="text-sm font-bold text-orange-400">{profile.login_streak}</span>
                    </div>
                )}
            </div>

            {/* XP Progress Bar */}
            <div>
                <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs text-[var(--color-text-muted)]">
                        {language === 'ar' ? 'التقدم' : 'Progress'}
                    </span>
                    {nextLevelTitle && (
                        <span className="text-xs text-[var(--color-text-secondary)] flex items-center gap-1">
                            {language === 'ar' ? 'التالي:' : 'Next:'} {nextLevelTitle}
                            <ChevronRight className="w-3 h-3" />
                        </span>
                    )}
                </div>
                <div className="w-full h-2.5 bg-[var(--color-surface-elevated)] rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full bg-gradient-to-r ${levelGradient}
                                   transition-all duration-700 ease-out`}
                        style={{ width: `${Math.max(xpProgress, 3)}%` }}
                    />
                </div>
                {profile.next_level && (
                    <div className="text-right mt-1">
                        <span className="text-[10px] text-[var(--color-text-secondary)]">
                            {profile.next_level.xp_remaining.toLocaleString()} XP {language === 'ar' ? 'متبقي' : 'remaining'}
                        </span>
                    </div>
                )}
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-[var(--color-background)] rounded-xl p-3 text-center">
                    <div className="text-lg font-bold text-emerald-500 dark:text-emerald-400">{profile.investment_readiness_score}</div>
                    <div className="text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wider">
                        {language === 'ar' ? 'الجاهزية' : 'Readiness'}
                    </div>
                </div>
                <div className="bg-[var(--color-background)] rounded-xl p-3 text-center">
                    <div className="text-lg font-bold text-[var(--color-text-primary)]">{profile.properties_analyzed}</div>
                    <div className="text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wider">
                        {language === 'ar' ? 'محلل' : 'Analyzed'}
                    </div>
                </div>
                <div className="bg-[var(--color-background)] rounded-xl p-3 text-center">
                    <div className="text-lg font-bold text-[var(--color-text-primary)]">{profile.achievement_count}</div>
                    <div className="text-[10px] text-[var(--color-text-secondary)] uppercase tracking-wider">
                        {language === 'ar' ? 'إنجازات' : 'Badges'}
                    </div>
                </div>
            </div>
        </div>
    );
}
