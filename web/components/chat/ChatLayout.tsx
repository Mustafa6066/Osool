'use client';

import { useState, useCallback } from 'react';
import ChatHeader from './ChatHeader';
import ChatSidebar from './ChatSidebar';
import ChatMain from './ChatMain';
import ContextualPane, { PropertyContext, UIActionData } from './ContextualPane';

export default function ChatLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isContextPaneOpen, setIsContextPaneOpen] = useState(false);
    const [selectedProperty, setSelectedProperty] = useState<PropertyContext | null>(null);
    const [activeUIActions, setActiveUIActions] = useState<UIActionData[]>([]);
    const [chatInsight, setChatInsight] = useState<string | null>(null);

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

    return (
        <div className="flex flex-col h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-[var(--color-teal-accent)] selection:text-black">
            {/* Top Navigation */}
            <ChatHeader
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                showMenuButton={true}
            />

            {/* Main Workspace Layout */}
            <div className="flex flex-1 overflow-hidden relative">
                {/* Left Sidebar: Navigation & History */}
                <ChatSidebar
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                    onNewInquiry={handleNewInquiry}
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
