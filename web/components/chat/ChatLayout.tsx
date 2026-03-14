'use client';

import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import ChatHeader from './ChatHeader';
import ChatSidebar from './ChatSidebar';
import ChatMain from './ChatMain';
import ContextualPane, { PropertyContext, UIActionData } from './ContextualPane';

// Recent search type
interface RecentSearch {
    id: string;
    query: string;
    type: 'location' | 'property' | 'developer' | 'general';
    timestamp: Date;
}

export default function ChatLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    // Modal state for property insights
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState<PropertyContext | null>(null);
    const [activeUIActions, setActiveUIActions] = useState<UIActionData[]>([]);
    const [chatInsight, setChatInsight] = useState<string | null>(null);
    const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);

    // Reference to ChatMain to trigger messages
    const chatMainRef = useRef<{ sendMessage: (text: string) => void } | null>(null);

    const handleNewInquiry = () => {
        // Reset conversation - this will be handled by ChatMain
        setSelectedProperty(null);
        setActiveUIActions([]);
        setChatInsight(null);
        setIsModalOpen(false);
        window.location.reload(); // Simple reset for now
    };

    // Handle property selection from card click - Opens modal
    const handlePropertySelect = useCallback((property: PropertyContext, uiActions?: UIActionData[]) => {
        setSelectedProperty(property);
        if (uiActions) {
            setActiveUIActions(uiActions);
        }
        setIsModalOpen(true); // Open modal instead of side panel
    }, []);

    // Handle context updates from AI chat messages (not card clicks)
    const handleChatContextUpdate = useCallback((context: {
        property?: PropertyContext;
        uiActions?: UIActionData[];
        insight?: string;
    }) => {
        if (context.property) {
            setSelectedProperty(context.property);
            // Don't auto-open modal - only open when user clicks property card
        }
        if (context.uiActions) {
            setActiveUIActions(context.uiActions);
        }
        if (context.insight) {
            setChatInsight(context.insight);
        }
    }, []);

    // Handle tool clicks from sidebar - trigger chat messages
    const handleToolClick = useCallback((query: string) => {
        // Close sidebar on mobile
        setIsSidebarOpen(false);

        // Add to recent searches
        const searchType: RecentSearch['type'] =
            query.toLowerCase().includes('area') || query.includes('منطقة') ? 'location' :
            query.toLowerCase().includes('developer') || query.includes('مطور') ? 'developer' :
            query.toLowerCase().includes('property') || query.includes('عقار') ? 'property' : 'general';

        setRecentSearches(prev => [{
            id: `search-${Date.now()}`,
            query: query.slice(0, 50),
            type: searchType,
            timestamp: new Date()
        }, ...prev.slice(0, 4)]);

        // Trigger message in ChatMain
        window.dispatchEvent(new CustomEvent('triggerChatMessage', { detail: { message: query } }));
    }, []);

    // Handle recent search click
    const handleSearchClick = useCallback((search: RecentSearch) => {
        setIsSidebarOpen(false);
        window.dispatchEvent(new CustomEvent('triggerChatMessage', { detail: { message: search.query } }));
    }, []);

    // Close modal
    const handleCloseModal = useCallback(() => {
        setIsModalOpen(false);
    }, []);

    return (
        <div className="flex flex-col h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-[var(--color-teal-accent)] selection:text-black">
            {/* Top Navigation */}
            <ChatHeader
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                showMenuButton={true}
            />

            {/* Main Workspace Layout - 2 Panel (Sidebar + Chat) */}
            <div className="flex flex-1 overflow-hidden relative">
                {/* Left Sidebar: Navigation & History */}
                <ChatSidebar
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                    onNewInquiry={handleNewInquiry}
                    recentSearches={recentSearches}
                    onToolClick={handleToolClick}
                    onSearchClick={handleSearchClick}
                />

                {/* Central Chat Area - Full Width */}
                <ChatMain
                    onNewConversation={handleNewInquiry}
                    onPropertySelect={handlePropertySelect}
                    onChatContextUpdate={handleChatContextUpdate}
                />
            </div>

            {/* Property Insights Modal */}
            <AnimatePresence>
                {isModalOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={handleCloseModal}
                            className="chatgpt-modal-overlay"
                        />

                        {/* Modal Content */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className="fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-lg md:max-h-[85vh] z-50 flex flex-col"
                        >
                            <div className="chatgpt-modal flex-1 flex flex-col overflow-hidden">
                                {/* Modal Header */}
                                <div className="chatgpt-modal-header">
                                    <h3 className="chatgpt-modal-title">
                                        Property Insights
                                    </h3>
                                    <button
                                        onClick={handleCloseModal}
                                        className="chatgpt-modal-close"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>

                                {/* Modal Body - ContextualPane Content */}
                                <div className="chatgpt-modal-body flex-1 overflow-y-auto">
                                    <ContextualPane
                                        isOpen={true}
                                        onClose={handleCloseModal}
                                        property={selectedProperty}
                                        uiActions={activeUIActions}
                                        chatInsight={chatInsight}
                                        isModal={true}
                                    />
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
