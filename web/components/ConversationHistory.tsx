"use client";

import { useState } from "react";
import { MessageSquare, Search, Trash2, Clock, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
}

export default function ConversationHistory({
    isOpen,
    onClose,
    onSelectConversation,
    onNewConversation,
    currentConversationId
}: ConversationHistoryProps) {
    const [searchQuery, setSearchQuery] = useState("");
    const [conversations, setConversations] = useState<Conversation[]>([
        {
            id: "1",
            title: "بحث عن شقة في القاهرة الجديدة",
            preview: "أبحث عن شقة 3 غرف نوم...",
            timestamp: new Date(),
            messageCount: 12
        },
        {
            id: "2",
            title: "Property Investment Analysis",
            preview: "Can you analyze the ROI for...",
            timestamp: new Date(Date.now() - 86400000),
            messageCount: 8
        },
        {
            id: "3",
            title: "Legal Contract Review",
            preview: "I need help reviewing this contract...",
            timestamp: new Date(Date.now() - 172800000),
            messageCount: 5
        }
    ]);

    const filteredConversations = conversations.filter(conv =>
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.preview.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleDelete = (conversationId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setConversations(prev => prev.filter(c => c.id !== conversationId));
    };

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

    return (
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
                        className="fixed left-0 top-0 h-full w-80 bg-gradient-to-b from-[#0f111a] to-[#1a1c2e] border-r border-white/10 z-50 flex flex-col shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-white/10">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <MessageSquare className="w-5 h-5 text-blue-400" />
                                    Conversations
                                </h2>
                                <button
                                    onClick={onClose}
                                    className="md:hidden text-gray-400 hover:text-white transition-colors"
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Search */}
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Search conversations..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full bg-[#1e293b] border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                />
                            </div>

                            {/* New Chat Button */}
                            <button
                                onClick={() => {
                                    onNewConversation();
                                    onClose();
                                }}
                                className="w-full mt-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold py-2 px-4 rounded-lg transition-all shadow-lg shadow-blue-600/30 flex items-center justify-center gap-2"
                            >
                                <MessageSquare className="w-4 h-4" />
                                New Conversation
                            </button>
                        </div>

                        {/* Conversations List */}
                        <div className="flex-1 overflow-y-auto p-2 space-y-2">
                            {filteredConversations.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
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
                                        className={`group relative p-3 rounded-lg cursor-pointer transition-all ${
                                            currentConversationId === conv.id
                                                ? "bg-blue-600/20 border border-blue-500/30"
                                                : "bg-[#1e293b]/50 hover:bg-[#1e293b] border border-transparent hover:border-white/10"
                                        }`}
                                    >
                                        {/* Conversation Content */}
                                        <div className="flex items-start gap-3">
                                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                                                <MessageSquare className="w-4 h-4 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="text-sm font-semibold text-white truncate mb-1">
                                                    {conv.title}
                                                </h3>
                                                <p className="text-xs text-gray-400 truncate mb-2">
                                                    {conv.preview}
                                                </p>
                                                <div className="flex items-center gap-3 text-xs text-gray-500">
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
                                            onClick={(e) => handleDelete(conv.id, e)}
                                            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </motion.div>
                                ))
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-white/10">
                            <div className="text-xs text-gray-500 text-center">
                                <p>Total: {conversations.length} conversations</p>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
