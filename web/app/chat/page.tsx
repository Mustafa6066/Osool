"use client";

import AgentInterface from "@/components/AgentInterface";
import ProtectedRoute from "@/components/ProtectedRoute";
import SmartNav from "@/components/SmartNav";

/**
 * Chat Page - Protected Route with Smart Navigation
 */
export default function ChatPage() {
    return (
        <ProtectedRoute>
            <SmartNav>
                <AgentInterface />
            </SmartNav>
        </ProtectedRoute>
    );
}
