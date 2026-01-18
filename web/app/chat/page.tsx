"use client";

import ChatInterface from "@/components/ChatInterface";
import ProtectedRoute from "@/components/ProtectedRoute";

/**
 * Chat Page - Protected Route
 * ----------------------------
 * Only authenticated users can access the chat with AMR.
 * Unauthenticated users are redirected to /login.
 */
export default function ChatPage() {
    return (
        <ProtectedRoute>
            <ChatInterface />
        </ProtectedRoute>
    );
}
