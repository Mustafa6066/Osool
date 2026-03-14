'use client';

/**
 * OrchestratorTracker — Auto-tracking component
 * -----------------------------------------------
 * Mounts once in the root layout to:
 *  1. Track page views on route changes
 *  2. Detect UTM parameters for ad click attribution
 *
 * This component renders nothing visible.
 */

import { useEffect, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { getAnonymousId } from '@/lib/session';
import { trackPageView, trackAdClick } from '@/lib/orchestrator';

/** Map URL paths to orchestrator page types */
function detectPageType(pathname: string): 'landing' | 'comparison' | 'roi' | 'project' | 'guide' | 'chat' | 'other' {
    if (pathname === '/') return 'landing';
    if (pathname.startsWith('/chat')) return 'chat';
    if (pathname.startsWith('/compare')) return 'comparison';
    if (pathname.startsWith('/projects') || pathname.startsWith('/property')) return 'project';
    if (pathname.startsWith('/developers') || pathname.startsWith('/areas')) return 'guide';
    if (pathname.startsWith('/market')) return 'roi';
    return 'other';
}

export default function OrchestratorTracker() {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const prevPath = useRef('');
    const adClickTracked = useRef(false);

    useEffect(() => {
        // Avoid duplicate tracking on same path
        const fullPath = `${pathname}?${searchParams.toString()}`;
        if (fullPath === prevPath.current) return;
        prevPath.current = fullPath;

        const anonymousId = getAnonymousId();

        // Track page view
        trackPageView({
            anonymousId,
            pageType: detectPageType(pathname),
        });

        // Track ad click (only once per session)
        if (!adClickTracked.current && searchParams.get('utm_source')) {
            trackAdClick({ anonymousId });
            adClickTracked.current = true;
        }
    }, [pathname, searchParams]);

    return null;
}
