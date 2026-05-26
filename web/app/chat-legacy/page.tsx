"use client";

import { Suspense } from "react";
import AgentInterface from "@/components/AgentInterface";
import AppShell from '@/components/nav/AppShell';
import { Loader2 } from "lucide-react";

/**
 * Legacy chat — preserves the original AgentInterface (real backend wiring,
 * 3-free-message gating for anon users, full access for authed users).
 *
 * Kept under /chat-legacy until the new /chat design is wired to the same
 * backend. When that happens, this route can be deleted.
 */
export default function ChatLegacyPage() {
    return (
        <AppShell>
            <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-emerald-500" /></div>}>
                <AgentInterface />
            </Suspense>
        </AppShell>
    );
}
