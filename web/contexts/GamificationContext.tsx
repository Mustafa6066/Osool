'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    InvestorProfile,
    AchievementDefinition,
    fetchInvestorProfile,
    fetchAchievements,
} from '@/lib/gamification';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface XPNotification {
    id: number;
    amount: number;
    action: string;
}

interface AchievementNotification {
    id: number;
    key: string;
    titleEn: string;
    titleAr: string;
    icon: string;
    tier: string;
    xpReward: number;
}

interface GamificationContextType {
    profile: InvestorProfile | null;
    achievements: AchievementDefinition[];
    loading: boolean;
    // Notification queues
    xpQueue: XPNotification[];
    achievementQueue: AchievementNotification[];
    // Actions
    triggerXP: (amount: number, action: string) => void;
    triggerAchievement: (data: Omit<AchievementNotification, 'id'>) => void;
    dismissXP: (id: number) => void;
    dismissAchievement: (id: number) => void;
    refreshProfile: () => Promise<void>;
}

const GamificationContext = createContext<GamificationContextType | undefined>(undefined);

// ═══════════════════════════════════════════════════════════════
// PROVIDER
// ═══════════════════════════════════════════════════════════════

let notifIdCounter = 0;

export function GamificationProvider({ children }: { children: ReactNode }) {
    const { isAuthenticated } = useAuth();
    const [profile, setProfile] = useState<InvestorProfile | null>(null);
    const [achievements, setAchievements] = useState<AchievementDefinition[]>([]);
    const [loading, setLoading] = useState(false);
    const [xpQueue, setXpQueue] = useState<XPNotification[]>([]);
    const [achievementQueue, setAchievementQueue] = useState<AchievementNotification[]>([]);

    // Fetch profile on auth change
    const refreshProfile = useCallback(async () => {
        if (!isAuthenticated) {
            setProfile(null);
            setAchievements([]);
            return;
        }
        setLoading(true);
        try {
            const [profileData, achievementsData] = await Promise.all([
                fetchInvestorProfile(),
                fetchAchievements(),
            ]);
            setProfile(profileData);
            setAchievements(achievementsData.achievements || []);
        } catch (err) {
            // Silently fail - gamification is non-critical
            console.warn('[Gamification] Failed to load profile:', err);
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated]);

    useEffect(() => {
        refreshProfile();
    }, [refreshProfile]);

    // Queue XP notification
    const triggerXP = useCallback((amount: number, action: string) => {
        const id = ++notifIdCounter;
        setXpQueue(prev => [...prev, { id, amount, action }]);

        // Auto-refresh profile after XP award to update level/XP display
        setTimeout(() => refreshProfile(), 1000);
    }, [refreshProfile]);

    // Queue achievement notification
    const triggerAchievement = useCallback((data: Omit<AchievementNotification, 'id'>) => {
        const id = ++notifIdCounter;
        setAchievementQueue(prev => [...prev, { id, ...data }]);

        // Refresh to update achievements list
        setTimeout(() => refreshProfile(), 1500);
    }, [refreshProfile]);

    // Dismiss handlers
    const dismissXP = useCallback((id: number) => {
        setXpQueue(prev => prev.filter(n => n.id !== id));
    }, []);

    const dismissAchievement = useCallback((id: number) => {
        setAchievementQueue(prev => prev.filter(n => n.id !== id));
    }, []);

    return (
        <GamificationContext.Provider value={{
            profile,
            achievements,
            loading,
            xpQueue,
            achievementQueue,
            triggerXP,
            triggerAchievement,
            dismissXP,
            dismissAchievement,
            refreshProfile,
        }}>
            {children}
        </GamificationContext.Provider>
    );
}

// ═══════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════

export function useGamification() {
    const context = useContext(GamificationContext);
    if (!context) {
        throw new Error('useGamification must be used within a GamificationProvider');
    }
    return context;
}
