"use client";

import AgentInterface from "@/components/AgentInterface";
import SmartNav from "@/components/SmartNav";

/**
 * Chat Page — accessible to anon users (3 free messages) and full access for authenticated users.
 */
export default function ChatPage() {
    return (
        <SmartNav>
            <AgentInterface />
        </SmartNav>
    );
}
