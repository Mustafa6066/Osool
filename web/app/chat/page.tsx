"use client";

import AgentInterface from "@/components/AgentInterface";
import ProtectedRoute from "@/components/ProtectedRoute";

/**
 * Chat Page - Protected Route
 * ----------------------------
 * Modern ChatGPT/Gemini-inspired interface with:
 * - Clean, content-focused dark theme
 * - Centralized chat stream with max reading width
 * - Floating pill-shaped "Omnibar" input
 * - Minimalist message styling (no heavy containers)
 * - Right pane "Canvas" for property deep dives
 */
export default function ChatPage() {
    return (
        <ProtectedRoute>
            <AgentInterface />
        </ProtectedRoute>
    );
}
