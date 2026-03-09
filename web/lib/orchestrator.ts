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

const ORCHESTRATOR_URL = (
    process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || ''
).replace(/\/$/, '');

const WEBHOOK_SECRET = process.env.ORCHESTRATOR_WEBHOOK_SECRET || '';

/** Check if orchestrator is configured */
function isConfigured(): boolean {
    return !!ORCHESTRATOR_URL;
}

/** Send a fire-and-forget webhook to the orchestrator */
async function sendWebhook(path: string, payload: Record<string, unknown>): Promise<void> {
    if (!isConfigured()) return;

    try {
        fetch(`${ORCHESTRATOR_URL}/webhooks${path}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(WEBHOOK_SECRET ? { 'x-webhook-secret': WEBHOOK_SECRET } : {}),
            },
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
