/**
 * Gamification Client Library
 * ----------------------------
 * Hooks and utilities for frontend gamification state.
 */

import api from '@/lib/api';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface InvestorProfile {
    xp: number;
    level: string;
    level_title_en: string;
    level_title_ar: string;
    level_unlocks: string;
    next_level: {
        key: string;
        title_en: string;
        title_ar: string;
        xp_required: number;
        xp_remaining: number;
    } | null;
    investment_readiness_score: number;
    login_streak: number;
    longest_streak: number;
    properties_analyzed: number;
    achievements: AchievementUnlock[];
    achievement_count: number;
    areas_explored: Record<string, number>;
    tools_used: Record<string, number>;
}

export interface AchievementUnlock {
    key: string;
    title_en: string;
    title_ar: string;
    icon: string;
    tier: string;
    category: string;
    unlocked_at: string | null;
}

export interface AchievementDefinition extends AchievementUnlock {
    description_en: string;
    description_ar: string;
    xp_reward: number;
    unlocked: boolean;
}

export interface XPEvent {
    awarded: number;
    total: number;
    action: string;
}

export interface AchievementEvent {
    key: string;
    title_en: string;
    title_ar: string;
    xp_reward: number;
}

export interface LevelUpEvent {
    from: string;
    to: string;
    title_en: string;
    title_ar: string;
    unlocks: string;
}

export interface FavoriteProperty {
    id: number;
    property_id: number;
    title: string;
    location: string;
    developer: string;
    price: number;
    price_per_sqm: number;
    size_sqm: number;
    bedrooms: number;
    image_url: string;
    notes: string | null;
    added_at: string;
}

// ═══════════════════════════════════════════════════════════════
// LEVEL DISPLAY HELPERS
// ═══════════════════════════════════════════════════════════════

export const LEVEL_COLORS: Record<string, string> = {
    curious: '#6B7280',      // Gray
    informed: '#3B82F6',     // Blue
    analyst: '#8B5CF6',      // Purple
    strategist: '#F59E0B',   // Amber
    mogul: '#EF4444',        // Red/Gold
};

export const LEVEL_GRADIENTS: Record<string, string> = {
    curious: 'from-gray-500 to-gray-600',
    informed: 'from-blue-500 to-blue-600',
    analyst: 'from-purple-500 to-purple-600',
    strategist: 'from-amber-500 to-amber-600',
    mogul: 'from-red-500 via-amber-500 to-yellow-400',
};

export const TIER_COLORS: Record<string, string> = {
    bronze: '#CD7F32',
    silver: '#C0C0C0',
    gold: '#FFD700',
};

export function getXPProgress(profile: InvestorProfile): number {
    if (!profile.next_level) return 100;
    if (profile.next_level.xp_remaining <= 0) return 100;
    const xpIntoLevel = profile.next_level.xp_required - profile.next_level.xp_remaining;
    if (xpIntoLevel <= 0) return 0;
    const progress = (xpIntoLevel / profile.next_level.xp_required) * 100;
    return Math.min(Math.max(progress, 0), 100);
}

// ═══════════════════════════════════════════════════════════════
// API FUNCTIONS
// ═══════════════════════════════════════════════════════════════

export async function fetchInvestorProfile(): Promise<InvestorProfile> {
    const response = await api.get('/api/gamification/profile');
    return response.data;
}

export async function fetchAchievements(): Promise<{ total: number; unlocked: number; achievements: AchievementDefinition[] }> {
    const response = await api.get('/api/gamification/achievements');
    return response.data;
}

export async function fetchLeaderboard(): Promise<{ leaderboard: any[] }> {
    const response = await api.get('/api/gamification/leaderboard');
    return response.data;
}

export async function toggleFavorite(propertyId: number, notes?: string): Promise<any> {
    const response = await api.post(`/api/gamification/favorite/${propertyId}`, { notes });
    return response.data;
}

export async function fetchFavorites(): Promise<{ total: number; favorites: FavoriteProperty[] }> {
    const response = await api.get('/api/gamification/favorites');
    return response.data;
}

export async function createSavedSearch(data: {
    name: string;
    location?: string;
    budget_min?: number;
    budget_max?: number;
    bedrooms?: number;
    property_type?: string;
}): Promise<any> {
    const response = await api.post('/api/gamification/saved-search', data);
    return response.data;
}

export async function fetchSavedSearches(): Promise<any> {
    const response = await api.get('/api/gamification/saved-searches');
    return response.data;
}
