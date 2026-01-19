"use client";

import ChatInterface from "@/components/ChatInterface";
import ProtectedRoute from "@/components/ProtectedRoute";

/**
 * Chat Page - Protected Route
 * ----------------------------
 * Only authenticated users can access the chat with AMR.
 * Unauthenticated users are redirected to /login.
 *
 * New Agentic Workspace UI with:
 * - Dark theme with glass morphism
 * - Animated background blobs
 * - 3-column layout (sidebar, chat, contextual pane)
 * - Property cards with appreciation charts
 */
export default function ChatPage() {
    return (
        <ProtectedRoute>
            <ChatInterface />
        </ProtectedRoute>
    );
}
