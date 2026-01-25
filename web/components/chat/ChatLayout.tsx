'use client';

import { useState, useCallback, useRef } from 'react';
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
    const [isContextPaneOpen, setIsContextPaneOpen] = useState(false);
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
        window.location.reload(); // Simple reset for now
    };

    // Handle property selection from card click
    const handlePropertySelect = useCallback((property: PropertyContext, uiActions?: UIActionData[]) => {
        setSelectedProperty(property);
        if (uiActions) {
            setActiveUIActions(uiActions);
        }
        setIsContextPaneOpen(true);
    }, []);

    // Handle context updates from AI chat messages (not card clicks)
    const handleChatContextUpdate = useCallback((context: {
        property?: PropertyContext;
        uiActions?: UIActionData[];
        insight?: string;
    }) => {
        if (context.property) {
            setSelectedProperty(context.property);
            setIsContextPaneOpen(true);
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
        // The ChatMain component will handle this via window event or ref
        window.dispatchEvent(new CustomEvent('triggerChatMessage', { detail: { message: query } }));
    }, []);

    // Handle recent search click
    const handleSearchClick = useCallback((search: RecentSearch) => {
        setIsSidebarOpen(false);
        window.dispatchEvent(new CustomEvent('triggerChatMessage', { detail: { message: search.query } }));
    }, []);

    return (
        <div className="flex flex-col h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-[var(--color-teal-accent)] selection:text-black">
            {/* Top Navigation */}
            <ChatHeader
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                showMenuButton={true}
            />

            {/* Main Workspace Layout */}
            <div className="flex flex-1 overflow-hidden relative">
                {/* Decorative Background Elements */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                    <div className="decorative-gradient-1" />
                    <div className="decorative-gradient-2" />
                </div>

                {/* Left Sidebar: Navigation & History */}
                <ChatSidebar
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                    onNewInquiry={handleNewInquiry}
                    recentSearches={recentSearches}
                    onToolClick={handleToolClick}
                    onSearchClick={handleSearchClick}
                />

                {/* Central Chat Area */}
                <ChatMain
                    onNewConversation={handleNewInquiry}
                    onPropertySelect={handlePropertySelect}
                    onChatContextUpdate={handleChatContextUpdate}
                />

                {/* Right Contextual Pane: Details */}
                <ContextualPane
                    isOpen={isContextPaneOpen}
                    onClose={() => setIsContextPaneOpen(false)}
                    property={selectedProperty}
                    uiActions={activeUIActions}
                    chatInsight={chatInsight}
                />
            </div>
        </div>
    );
}
