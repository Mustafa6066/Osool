'use client';

import { useState } from 'react';
import ChatHeader from './ChatHeader';
import ChatSidebar from './ChatSidebar';
import ChatMain from './ChatMain';
import ContextualPane from './ContextualPane';

export default function ChatLayout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isContextPaneOpen, setIsContextPaneOpen] = useState(false);

    const handleNewInquiry = () => {
        // Reset conversation - this will be handled by ChatMain
        window.location.reload(); // Simple reset for now
    };

    return (
        <div className="flex flex-col h-screen bg-[var(--chat-background-light)] dark:bg-[var(--chat-background-dark)] text-slate-800 dark:text-gray-100 overflow-hidden selection:bg-[var(--chat-teal-accent)] selection:text-black">
            {/* Top Navigation */}
            <ChatHeader
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
                showMenuButton={true}
            />

            {/* Main Workspace Layout */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left Sidebar: Navigation & History */}
                <ChatSidebar
                    isOpen={isSidebarOpen}
                    onClose={() => setIsSidebarOpen(false)}
                    onNewInquiry={handleNewInquiry}
                />

                {/* Central Chat Area */}
                <ChatMain onNewConversation={handleNewInquiry} />

                {/* Right Contextual Pane: Details */}
                <ContextualPane
                    isOpen={isContextPaneOpen}
                    onClose={() => setIsContextPaneOpen(false)}
                />
            </div>
        </div>
    );
}
