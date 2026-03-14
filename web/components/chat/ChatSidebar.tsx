'use client';

import { useEffect, useRef, useState } from 'react';
import {
    Plus, Settings, LogOut, X, MessageSquare, Building2, MapPin, Home,
    MoreHorizontal, Trash2, Edit2, Check
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

interface Conversation {
    id: string;
    title: string;
    preview: string;
    timestamp: Date;
}

interface RecentSearch {
    id: string;
    query: string;
    type: 'location' | 'property' | 'developer' | 'general';
    timestamp: Date;
}

interface ChatSidebarProps {
    isOpen?: boolean;
    onClose?: () => void;
    onNewInquiry?: () => void;
    conversations?: Conversation[];
    recentSearches?: RecentSearch[];
    activeConversationId?: string;
    onSelectConversation?: (id: string) => void;
    onToolClick?: (toolType: string) => void;
    onSearchClick?: (search: RecentSearch) => void;
    isRTL?: boolean;
}

// Get icon for search type
function getSearchIcon(type: RecentSearch['type']) {
    switch (type) {
        case 'location': return MapPin;
        case 'property': return Home;
        case 'developer': return Building2;
        default: return MessageSquare;
    }
}

// Group conversations by date
function groupByDate(items: (Conversation | RecentSearch)[], isRTL: boolean) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);
    const weekAgo = new Date(today.getTime() - 7 * 86400000);

    const groups: { title: string; items: typeof items }[] = [];
    const todayItems: typeof items = [];
    const yesterdayItems: typeof items = [];
    const weekItems: typeof items = [];
    const olderItems: typeof items = [];

    items.forEach(item => {
        const itemDate = new Date(item.timestamp);
        if (itemDate >= today) {
            todayItems.push(item);
        } else if (itemDate >= yesterday) {
            yesterdayItems.push(item);
        } else if (itemDate >= weekAgo) {
            weekItems.push(item);
        } else {
            olderItems.push(item);
        }
    });

    if (todayItems.length > 0) {
        groups.push({ title: isRTL ? 'اليوم' : 'Today', items: todayItems });
    }
    if (yesterdayItems.length > 0) {
        groups.push({ title: isRTL ? 'أمس' : 'Yesterday', items: yesterdayItems });
    }
    if (weekItems.length > 0) {
        groups.push({ title: isRTL ? 'الأسبوع الماضي' : 'Previous 7 Days', items: weekItems });
    }
    if (olderItems.length > 0) {
        groups.push({ title: isRTL ? 'أقدم' : 'Older', items: olderItems });
    }

    return groups;
}

export default function ChatSidebar({
    isOpen = true,
    onClose,
    onNewInquiry,
    conversations = [],
    recentSearches = [],
    activeConversationId,
    onSelectConversation,
    onToolClick,
    onSearchClick,
    isRTL = false,
}: ChatSidebarProps) {
    const { logout } = useAuth();
    const [hoveredItem, setHoveredItem] = useState<string | null>(null);

    // Combine conversations and recent searches for display
    const allItems = [
        ...recentSearches.map(s => ({ ...s, isSearch: true as const })),
    ];

    const groupedItems = groupByDate(allItems as any, isRTL);

    const sidebarContent = (
        <>
            {/* New Chat Button - Prominent at top */}
            <div className="chatgpt-sidebar-header">
                <button
                    onClick={onNewInquiry}
                    className="chatgpt-new-chat-btn"
                >
                    <Plus size={18} />
                    <span>{isRTL ? 'محادثة جديدة' : 'New chat'}</span>
                </button>
            </div>

            {/* Conversation History */}
            <div className="flex-1 overflow-y-auto px-2 py-2 chatgpt-scrollbar">
                {groupedItems.length === 0 ? (
                    <div className="px-3 py-8 text-center">
                        <MessageSquare size={32} className="mx-auto mb-3 text-[var(--color-text-muted)]/30" />
                        <p className="text-sm text-[var(--color-text-muted)]">
                            {isRTL ? 'لا توجد محادثات بعد' : 'No conversations yet'}
                        </p>
                        <p className="text-xs text-[var(--color-text-muted)]/70 mt-1">
                            {isRTL ? 'ابدأ محادثة جديدة للبدء' : 'Start a new chat to begin'}
                        </p>
                    </div>
                ) : (
                    groupedItems.map((group, groupIndex) => (
                        <div key={group.title} className="chatgpt-conv-group">
                            <p className="chatgpt-conv-group-title">{group.title}</p>
                            {group.items.map((item: any) => {
                                const isSearch = 'query' in item;
                                const IconComponent = isSearch ? getSearchIcon(item.type) : MessageSquare;
                                const title = isSearch ? item.query : item.title;
                                const isActive = !isSearch && item.id === activeConversationId;
                                const isHovered = hoveredItem === item.id;

                                return (
                                    <div
                                        key={item.id}
                                        className={`chatgpt-conv-item ${isActive ? 'active' : ''}`}
                                        onClick={() => isSearch ? onSearchClick?.(item) : onSelectConversation?.(item.id)}
                                        onMouseEnter={() => setHoveredItem(item.id)}
                                        onMouseLeave={() => setHoveredItem(null)}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                    >
                                        <IconComponent size={16} className="text-[var(--color-text-muted)] flex-shrink-0" />
                                        <span className="chatgpt-conv-item-title">{title}</span>

                                        {/* Action buttons on hover */}
                                        {isHovered && (
                                            <div className="flex items-center gap-1 ml-auto">
                                                <button
                                                    className="p-1 rounded hover:bg-[var(--chatgpt-hover-bg)]"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        // Edit action
                                                    }}
                                                >
                                                    <Edit2 size={14} className="text-[var(--color-text-muted)]" />
                                                </button>
                                                <button
                                                    className="p-1 rounded hover:bg-[var(--chatgpt-hover-bg)]"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        // Delete action
                                                    }}
                                                >
                                                    <Trash2 size={14} className="text-[var(--color-text-muted)]" />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ))
                )}
            </div>

            {/* Footer - User Menu */}
            <div className="p-3 border-t border-[var(--color-border)]">
                <div className="flex items-center justify-between">
                    <button
                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-[var(--chatgpt-hover-bg)] transition-colors flex-1"
                        title={isRTL ? 'إعدادات' : 'Settings'}
                    >
                        <Settings size={18} className="text-[var(--color-text-muted)]" />
                        <span className="text-sm text-[var(--color-text-muted)]">{isRTL ? 'إعدادات' : 'Settings'}</span>
                    </button>
                    <button
                        onClick={() => logout()}
                        className="p-2 rounded-lg hover:bg-[var(--chatgpt-hover-bg)] transition-colors"
                        title={isRTL ? 'خروج' : 'Logout'}
                    >
                        <LogOut size={18} className="text-[var(--color-text-muted)]" />
                    </button>
                </div>
            </div>
        </>
    );

    return (
        <>
            {/* Desktop Sidebar */}
            <aside className={`chatgpt-sidebar hidden lg:flex ${isRTL ? 'border-l border-r-0' : ''}`}>
                {sidebarContent}
            </aside>

            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                        />

                        {/* Mobile Sidebar */}
                        <motion.aside
                            initial={{ x: isRTL ? 280 : -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? 280 : -280 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'right-0' : 'left-0'} top-0 h-full chatgpt-sidebar z-50 lg:hidden`}
                        >
                            {/* Close button */}
                            <div className={`absolute top-4 ${isRTL ? 'left-4' : 'right-4'}`}>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--chatgpt-hover-bg)] transition-colors"
                                    title={isRTL ? 'إغلاق' : 'Close'}
                                >
                                    <X size={20} />
                                </button>
                            </div>
                            {sidebarContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
