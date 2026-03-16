/**
 * Osool Orchestrator Integration
 * --------------------------------
 * Fire-and-forget webhook calls to the Osool Orchestrator backend.
 * The orchestrator processes these asynchronously for:
 *  - Intent classification & lead scoring
 *  - Funnel analytics
 *  - Ad audience sync
 *  - Email nurture sequences
 *
 * IMPORTANT: All calls are non-blocking — errors are silently caught
 * so they never impact the user experience.
 */

/**
 * Webhooks are sent to our own Next.js proxy route (/api/webhooks/...) which
 * adds the ORCHESTRATOR_WEBHOOK_SECRET server-side and forwards to the Orchestrator.
 * This keeps the secret out of the browser bundle entirely.
 */
const ORCHESTRATOR_CONFIGURED = !!(
    process.env.NEXT_PUBLIC_ORCHESTRATOR_URL
);

/** Send a fire-and-forget webhook via the server-side proxy */
async function sendWebhook(path: string, payload: Record<string, unknown>): Promise<void> {
    if (!ORCHESTRATOR_CONFIGURED) return;

    try {
        fetch(`/api/webhooks${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            keepalive: true,
        }).catch(() => {
            /* Silently ignore — never block the user */
        });
    } catch {
        /* Silently ignore */
    }
}

// ── Public API ─────────────────────────────────────────────────────────────────

/**
 * Track a chat message (user or assistant).
 * Call after every message exchange.
 */
export function trackChatMessage(params: {
    sessionId: string;
    anonymousId: string;
    userId?: string;
    message: { role: 'user' | 'assistant'; content: string };
    pageUrl?: string;
    locale?: 'en' | 'ar';
}): void {
    sendWebhook('/chat-message', {
        eventType: 'chat_message',
        sessionId: params.sessionId,
        userId: params.userId,
        anonymousId: params.anonymousId,
        message: {
            role: params.message.role,
            content: params.message.content,
            timestamp: new Date().toISOString(),
        },
        pageContext: {
            url: params.pageUrl || (typeof window !== 'undefined' ? window.location.href : ''),
            pageType: 'chat',
            locale: params.locale || 'ar',
        },
    });
}

/**
 * Track a chat session ending.
 * Call when the user navigates away or closes the chat.
 */
export function trackChatSessionEnd(params: {
    sessionId: string;
    anonymousId: string;
    userId?: string;
    messageCount: number;
    durationSeconds: number;
}): void {
    sendWebhook('/chat-session-end', {
        eventType: 'chat_session_end',
        sessionId: params.sessionId,
        userId: params.userId,
        anonymousId: params.anonymousId,
        messageCount: params.messageCount,
        durationSeconds: params.durationSeconds,
        lastPageUrl: typeof window !== 'undefined' ? window.location.href : '',
    });
}

/**
 * Track a page view.
 * Call on every page navigation.
 */
export function trackPageView(params: {
    anonymousId: string;
    userId?: string;
    pageType?: 'landing' | 'comparison' | 'roi' | 'project' | 'guide' | 'chat' | 'other';
}): void {
    sendWebhook('/page-view', {
        eventType: 'page_view',
        userId: params.userId,
        anonymousId: params.anonymousId,
        url: typeof window !== 'undefined' ? window.location.href : '',
        pageType: params.pageType || 'other',
        referrer: typeof document !== 'undefined' ? document.referrer : '',
        utmParams: typeof window !== 'undefined'
            ? Object.fromEntries(new URLSearchParams(window.location.search).entries())
            : {},
        timestamp: new Date().toISOString(),
    });
}

/**
 * Track a signup or waitlist join.
 * Call after successful registration.
 */
export function trackSignup(params: {
    email: string;
    name?: string;
    source: string;
    anonymousId: string;
    userId: string;
    isWaitlist?: boolean;
}): void {
    sendWebhook('/signup', {
        eventType: params.isWaitlist ? 'waitlist_join' : 'signup',
        userId: params.userId,
        email: params.email,
        name: params.name,
        source: params.source,
        anonymousId: params.anonymousId,
    });
}

/**
 * Track a property view.
 * Call when a user opens a property detail page.
 */
export function trackPropertyView(params: {
    anonymousId: string;
    userId?: string;
    propertyId: string;
    developerId?: string;
    location?: string;
    priceRange?: { min: number; max: number };
}): void {
    sendWebhook('/page-view', {
        eventType: 'page_view',
        userId: params.userId,
        anonymousId: params.anonymousId,
        url: typeof window !== 'undefined' ? window.location.href : '',
        pageType: 'project',
        referrer: typeof document !== 'undefined' ? document.referrer : '',
        utmParams: {},
        timestamp: new Date().toISOString(),
        properties: {
            propertyId: params.propertyId,
            developerId: params.developerId,
            location: params.location,
            priceRange: params.priceRange,
        },
    });
}

/**
 * Track a search action.
 * Call when a user performs a property search or filter.
 */
export function trackSearch(params: {
    anonymousId: string;
    userId?: string;
    query?: string;
    filters?: Record<string, unknown>;
    resultCount?: number;
}): void {
    sendWebhook('/page-view', {
        eventType: 'page_view',
        userId: params.userId,
        anonymousId: params.anonymousId,
        url: typeof window !== 'undefined' ? window.location.href : '',
        pageType: 'other',
        referrer: typeof document !== 'undefined' ? document.referrer : '',
        utmParams: {},
        timestamp: new Date().toISOString(),
        properties: {
            action: 'search',
            query: params.query,
            filters: params.filters,
            resultCount: params.resultCount,
        },
    });
}

/**
 * Track a user memory update (budget, location preferences, etc.).
 * Call when the user's investment profile is updated or inferred.
 */
export function trackUserMemoryUpdate(params: {
    anonymousId: string;
    userId?: string;
    budgetRange?: { min: number; max: number; currency: string };
    preferredLocations?: string[];
    preferredDevelopers?: string[];
    propertyTypes?: string[];
}): void {
    sendWebhook('/user-memory-update', {
        eventType: 'user_memory_update',
        userId: params.userId,
        anonymousId: params.anonymousId,
        preferences: {
            budgetRange: params.budgetRange,
            preferredLocations: params.preferredLocations,
            preferredDevelopers: params.preferredDevelopers,
            propertyTypes: params.propertyTypes,
        },
        timestamp: new Date().toISOString(),
    });
}

/**
 * Track an ad click (UTM parameter detection).
 * Call on initial page load if UTM params are present.
 */
export function trackAdClick(params: {
    anonymousId: string;
}): void {
    if (typeof window === 'undefined') return;

    const searchParams = new URLSearchParams(window.location.search);
    const utmSource = searchParams.get('utm_source');

    // Only track if UTM source is present
    if (!utmSource) return;

    const utmParams: Record<string, string> = {};
    for (const [key, value] of searchParams.entries()) {
        if (key.startsWith('utm_')) {
            utmParams[key] = value;
        }
    }

    sendWebhook('/ad-click', {
        eventType: 'ad_click',
        anonymousId: params.anonymousId,
        utmParams,
        landingUrl: window.location.href,
        timestamp: new Date().toISOString(),
    });
}

// ── Data Fetching API ──────────────────────────────────────────────────────────

const ORCHESTRATOR_DATA_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || '';

/** Fetch data from orchestrator data API (non-blocking, returns null on failure) */
async function fetchDataRoute<T>(path: string): Promise<T | null> {
    if (!ORCHESTRATOR_DATA_URL) return null;
    try {
        const res = await fetch(`/api/orchestrator-data${path}`, {
            headers: { 'Content-Type': 'application/json' },
        });
        if (!res.ok) return null;
        return (await res.json()) as T;
    } catch {
        return null;
    }
}

/** Lead context from the orchestrator for the current user */
export interface OrchestratorLeadContext {
    userId: string;
    leadScore: number;
    tier: 'hot' | 'warm' | 'nurture' | 'cold';
    icpSegment: string;
    preferredDevelopers: string[];
    preferredAreas: string[];
    intentTypes: string[];
    signalCount: number;
    suggestedTopics: string[];
}

/** Notification from the orchestrator */
export interface OrchestratorNotification {
    id: string;
    type: string;
    title: string;
    titleAr: string;
    body: string;
    bodyAr: string;
    read: boolean;
    createdAt: string;
    data?: Record<string, unknown>;
}

/**
 * Fetch the current user's lead context and personalization data.
 * Use to adapt the UI based on engagement level.
 */
export async function fetchLeadContext(userId: string): Promise<OrchestratorLeadContext | null> {
    return fetchDataRoute<OrchestratorLeadContext>(`/user-context/${userId}`);
}

/**
 * Fetch unread notifications for the current user.
 */
export async function fetchNotifications(userId: string, limit = 20): Promise<OrchestratorNotification[]> {
    const result = await fetchDataRoute<{ notifications: OrchestratorNotification[] }>(
        `/notifications/${userId}?limit=${limit}`
    );
    return result?.notifications ?? [];
}

/**
 * Fetch trending market data (developers, locations, queries).
 */
export async function fetchTrending(): Promise<{
    trendingDevelopers: { name: string; mentionCount: number; trend: string }[];
    trendingLocations: { name: string; mentionCount: number; trend: string }[];
    trendingQueries: { query: string; count: number }[];
    period: string;
} | null> {
    return fetchDataRoute('/trending');
}

/**
 * Fetch live ROI data for a specific location area (for SEO page enrichment).
 */
export async function fetchAreaROI(locationSlug: string): Promise<{
    location: { location: string; locationAr: string; avgPricePerSqm: number; rentalYieldPercent: number; liquidityScore: number };
    predictedGrowth: { '1yr': number; '3yr': number; '5yr': number };
    topProjects: { id: string; name: string; developerId: string; minPrice: number; maxPrice: number }[];
} | null> {
    return fetchDataRoute(`/roi/${locationSlug}`);
}
