"use client";

import { useState, useEffect, useCallback } from "react";
import { MessageSquare, Search, Trash2, Clock, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ClientOnly from "./ClientOnly";
import { getUserChatSessions, deleteChatSession } from "@/lib/api";

interface Conversation {
    id: string;
    title: string;
    preview: string;
    timestamp: Date;
    messageCount: number;
}
interface ConversationHistoryProps {
    isOpen: boolean;
    onClose: () => void;
    onSelectConversation: (conversationId: string) => void;
    onNewConversation: () => void;
    currentConversationId?: string;
    isDesktopSidebar?: boolean;
}

export default function ConversationHistory({
    isOpen,
    onClose,
    onSelectConversation,
    onNewConversation,
    currentConversationId,
    isDesktopSidebar = false
}: ConversationHistoryProps) {
    const [searchQuery, setSearchQuery] = useState("");
    const [conversations, setConversations] = useState<Conversation[]>([]);

    const loadSessions = useCallback(async () => {
        try {
            const sessions = await getUserChatSessions();
            setConversations(sessions.map(s => ({
                id: s.session_id,
                title: s.preview ? s.preview.slice(0, 50) : s.session_id,
                preview: s.preview ?? "",
                timestamp: new Date(s.last_message_at ?? s.started_at ?? Date.now()),
                messageCount: s.message_count,
            })));
        } catch {
            // Silently fail — sidebar stays empty rather than crashing
        }
    }, []);

    useEffect(() => {
        const timer = setTimeout(() => {
            void loadSessions();
        }, 0);

        return () => clearTimeout(timer);
    }, [loadSessions]);

    const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        try {
            await deleteChatSession(conversationId);
        } catch {
            // Re-load to restore accurate state if delete failed
            loadSessions();
        }
    };

    const filteredConversations = conversations.filter(conv =>
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.preview.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatTimestamp = (date: Date) => {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) {
            return `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ago`;
        } else if (diffDays === 1) {
            return "Yesterday";
        } else if (diffDays < 7) {
            return `${diffDays}d ago`;
        } else {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
    };

    // Desktop sidebar mode - render inline without modal
    if (isDesktopSidebar) {
        return (
            <div className="flex flex-col h-full">
                {/* Search */}
                <div className="p-2">
                    <div className="relative">
                        <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                        <input
                            type="text"
                            placeholder="Search..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            aria-label="Search conversations"
                            className="w-full bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-2xl ps-9 pe-3 py-2.5 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:border-transparent transition-all"
                        />
                    </div>
                </div>

                {/* Conversations List */}
                <div className="flex-1 overflow-y-auto space-y-1 px-2 custom-scrollbar">
                    {filteredConversations.length === 0 ? (
                        <div className="text-center py-8 text-[var(--color-text-muted)]">
                            <MessageSquare className="w-10 h-10 mx-auto mb-2 opacity-30" />
                            <p className="text-xs">
                                {searchQuery ? "No matches" : "No chats yet"}
                            </p>
                        </div>
                    ) : (
                        filteredConversations.map((conv) => (
                            <motion.div
                                key={conv.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                onClick={() => onSelectConversation(conv.id)}
                                className={`group relative p-3 rounded-2xl cursor-pointer transition-all duration-200 ${currentConversationId === conv.id
                                    ? "bg-[var(--color-primary-light)] border border-[var(--color-primary)]/30"
                                    : "hover:bg-[var(--color-surface-elevated)] border border-transparent"
                                    }`}
                            >
                                <h3 className="text-sm font-medium text-[var(--color-text-primary)] truncate mb-1">
                                    {conv.title}
                                </h3>
                                <p className="text-xs text-[var(--color-text-muted)] truncate mb-1">
                                    {conv.preview}
                                </p>
                                <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
                                    <Clock className="w-3 h-3" />
                                    <span>{formatTimestamp(conv.timestamp)}</span>
                                </div>

                                {/* Delete Button */}
                                <button
                                    aria-label="Delete conversation"
                                    onClick={(e) => handleDelete(conv.id, e)}
                                    className="absolute right-2 top-2 flex min-h-11 min-w-11 items-center justify-center rounded-xl text-[var(--color-text-muted)] transition-opacity hover:bg-red-500/10 hover:text-red-500 opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </motion.div>
                        ))
                    )}
                </div>
            </div>
        );
    }

    // Mobile modal mode
    return (
        <ClientOnly>
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
                        />

                        {/* Sidebar */}
                        <motion.div
                            initial={{ x: -300 }}
                            animate={{ x: 0 }}
                            exit={{ x: -300 }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="fixed left-0 top-0 z-50 flex h-full w-[min(90vw,22rem)] flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl md:hidden"
                        >
                            {/* Header */}
                            <div className="p-4 border-b border-[var(--color-border)]">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-xl font-bold text-[var(--color-text-primary)] flex items-center gap-2">
                                        <MessageSquare className="w-5 h-5 text-[var(--color-primary)]" />
                                        Conversations
                                    </h2>
                                    <button
                                        aria-label="Close"
                                        onClick={onClose}
                                        className="md:hidden flex h-11 w-11 items-center justify-center rounded-xl text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)]"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Search */}
                                <div className="relative">
                                    <Search className="absolute start-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                                    <input
                                        type="text"
                                        placeholder="Search conversations..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        aria-label="Search conversations"
                                        className="w-full bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-2xl ps-10 pe-4 py-2.5 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:border-transparent transition-all"
                                    />
                                </div>

                                {/* New Chat Button */}
                                <button
                                    onClick={() => {
                                        onNewConversation();
                                        onClose();
                                    }}
                                    className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-500 px-4 py-2.5 font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:from-emerald-600 hover:to-emerald-600 hover:shadow-emerald-500/40"
                                >
                                    <MessageSquare className="w-4 h-4" />
                                    New Conversation
                                </button>
                            </div>

                            {/* Conversations List */}
                            <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                                {filteredConversations.length === 0 ? (
                                    <div className="text-center py-8 text-[var(--color-text-muted)]">
                                        <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">
                                            {searchQuery ? "No conversations found" : "No conversations yet"}
                                        </p>
                                    </div>
                                ) : (
                                    filteredConversations.map((conv) => (
                                        <motion.div
                                            key={conv.id}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -10 }}
                                            onClick={() => {
                                                onSelectConversation(conv.id);
                                                onClose();
                                            }}
                                            className={`group relative p-3 rounded-2xl cursor-pointer transition-all duration-200 ${currentConversationId === conv.id
                                                ? "bg-[var(--color-primary-light)] border border-[var(--color-primary)]/30"
                                                : "bg-[var(--color-surface-elevated)]/50 hover:bg-[var(--color-surface-elevated)] border border-transparent hover:border-[var(--color-border)]"
                                                }`}
                                        >
                                            {/* Conversation Content */}
                                            <div className="flex items-start gap-3">
                                                <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-500 flex items-center justify-center shadow-md">
                                                    <MessageSquare className="w-4 h-4 text-white" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)] truncate mb-1">
                                                        {conv.title}
                                                    </h3>
                                                    <p className="text-xs text-[var(--color-text-muted)] truncate mb-2">
                                                        {conv.preview}
                                                    </p>
                                                    <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="w-3 h-3" />
                                                            {formatTimestamp(conv.timestamp)}
                                                        </span>
                                                        <span>{conv.messageCount} messages</span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Delete Button */}
                                            <button
                                                aria-label="Delete conversation"
                                                onClick={(e) => handleDelete(conv.id, e)}
                                                className="absolute right-2 top-2 flex min-h-11 min-w-11 items-center justify-center rounded-xl text-[var(--color-text-muted)] transition-opacity hover:bg-red-500/10 hover:text-red-500 opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </motion.div>
                                    ))
                                )}
                            </div>

                            {/* Footer */}
                            <div className="p-4 border-t border-[var(--color-border)]">
                                <div className="text-xs text-[var(--color-text-muted)] text-center">
                                    <p>Total: {conversations.length} conversations</p>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </ClientOnly>
    );
}
