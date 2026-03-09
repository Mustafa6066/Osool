/**
 * Orchestrator Session Helpers
 * ----------------------------
 * Provides consistent anonymousId and sessionId for tracking
 * visitor interactions across the Osool platform.
 */

/** Persistent anonymous ID — survives across sessions */
export function getAnonymousId(): string {
    if (typeof window === 'undefined') return crypto.randomUUID();
    let id = localStorage.getItem('osool_anon_id');
    if (!id) {
        id = crypto.randomUUID();
        localStorage.setItem('osool_anon_id', id);
    }
    return id;
}

/** Session-scoped ID — resets when the tab closes */
export function getSessionId(): string {
    if (typeof window === 'undefined') return crypto.randomUUID();
    let id = sessionStorage.getItem('osool_session_id');
    if (!id) {
        id = crypto.randomUUID();
        sessionStorage.setItem('osool_session_id', id);
    }
    return id;
}
