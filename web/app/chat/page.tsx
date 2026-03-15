"use client";

import { Suspense } from "react";
import AgentInterface from "@/components/AgentInterface";
import AppShell from '@/components/nav/AppShell';
import { Loader2 } from "lucide-react";

/**
 * Chat Page â€” accessible to anon users (3 free messages) and full access for authenticated users.
 * Suspense boundary required because AgentInterface uses useSearchParams().
 */
export default function ChatPage() {
    return (
        <AppShell>
            <Suspense fallback={<div className="flex h-full items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-emerald-500" /></div>}>
                <AgentInterface />
            </Suspense>
        </AppShell>
    );
}
