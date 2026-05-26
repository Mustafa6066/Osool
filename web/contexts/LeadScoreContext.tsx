'use client';

/**
 * LeadScoreProvider — Real-time lead score context
 * --------------------------------------------------
 * Polls the orchestrator for the current user's lead score and tier.
 * When the score crosses thresholds (hot/warm), it triggers UI changes:
 *  - Priority callback modal
 *  - WhatsApp handoff button
 *  - Personalized chat suggestions
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchLeadContext, type OrchestratorLeadContext } from '@/lib/orchestrator';

interface LeadScoreContextValue {
    leadScore: number;
    tier: 'hot' | 'warm' | 'nurture' | 'cold';
    icpSegment: string;
    preferredDevelopers: string[];
    preferredAreas: string[];
    suggestedTopics: string[];
    isHotLead: boolean;
    isWarmLead: boolean;
    loading: boolean;
}

const LeadScoreContext = createContext<LeadScoreContextValue>({
    leadScore: 0,
    tier: 'cold',
    icpSegment: 'first_time_buyer',
    preferredDevelopers: [],
    preferredAreas: [],
    suggestedTopics: [],
    isHotLead: false,
    isWarmLead: false,
    loading: true,
});

export function useLeadScore() {
    return useContext(LeadScoreContext);
}

export function LeadScoreProvider({ children }: { children: ReactNode }) {
    const { user, isAuthenticated } = useAuth();
    const [context, setContext] = useState<OrchestratorLeadContext | null>(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        if (!isAuthenticated || !user?.id) {
            setLoading(false);
            return;
        }
        try {
            const data = await fetchLeadContext(String(user.id));
            if (data) setContext(data);
        } catch {
            // Silent
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, user?.id]);

    // Poll every 2 minutes
    useEffect(() => {
        load();
        const interval = setInterval(load, 120_000);
        return () => clearInterval(interval);
    }, [load]);

    const leadScore = context?.leadScore ?? 0;
    const tier = (context?.tier ?? 'cold') as 'hot' | 'warm' | 'nurture' | 'cold';

    return (
        <LeadScoreContext.Provider
            value={{
                leadScore,
                tier,
                icpSegment: context?.icpSegment ?? 'first_time_buyer',
                preferredDevelopers: context?.preferredDevelopers ?? [],
                preferredAreas: context?.preferredAreas ?? [],
                suggestedTopics: context?.suggestedTopics ?? [],
                isHotLead: tier === 'hot',
                isWarmLead: tier === 'warm' || tier === 'hot',
                loading,
            }}
        >
            {children}
        </LeadScoreContext.Provider>
    );
}
