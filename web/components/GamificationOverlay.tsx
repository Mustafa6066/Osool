'use client';

import React from 'react';
import { useGamification } from '@/contexts/GamificationContext';
import XPToast from '@/components/XPToast';
import AchievementPopup from '@/components/AchievementPopup';
import { playAchievementSound } from '@/lib/celebrations';

/**
 * GamificationOverlay — Global notification layer
 * Rendered once in layout.tsx. Manages XP toasts and achievement popups.
 */
export default function GamificationOverlay() {
    const {
        xpQueue,
        achievementQueue,
        dismissXP,
        dismissAchievement,
    } = useGamification();

    // Show only the first notification from each queue (prevents stacking)
    const currentXP = xpQueue[0] || null;
    const currentAchievement = achievementQueue[0] || null;

    return (
        <>
            {/* XP Toast */}
            {currentXP && (
                <XPToast
                    key={currentXP.id}
                    amount={currentXP.amount}
                    action={currentXP.action}
                    onDone={() => dismissXP(currentXP.id)}
                />
            )}

            {/* Achievement Popup */}
            {currentAchievement && (
                <AchievementPopupWithSound
                    key={currentAchievement.id}
                    data={currentAchievement}
                    onDone={() => dismissAchievement(currentAchievement.id)}
                />
            )}
        </>
    );
}

/**
 * Wrapper that plays sound on mount
 */
function AchievementPopupWithSound({
    data,
    onDone,
}: {
    data: { key: string; titleEn: string; titleAr: string; icon: string; tier: string; xpReward: number };
    onDone: () => void;
}) {
    // Play sound on mount
    React.useEffect(() => {
        playAchievementSound();
    }, []);

    return (
        <AchievementPopup
            achievementKey={data.key}
            titleEn={data.titleEn}
            titleAr={data.titleAr}
            icon={data.icon}
            tier={data.tier}
            xpReward={data.xpReward}
            onDone={onDone}
        />
    );
}
