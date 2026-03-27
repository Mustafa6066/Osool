'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import {
    Plus, Settings, LogOut, X, MessageSquare, Building2, MapPin, Home,
    Trash2, Edit2, Search,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

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

type SearchDisplayItem = RecentSearch & { isSearch: true };

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

function getSearchIcon(type: RecentSearch['type']) {
    switch (type) {
        case 'location': return MapPin;
        case 'property': return Home;
        case 'developer': return Building2;
        default: return MessageSquare;
    }
}

function groupByDate<T extends { timestamp: Date }>(items: T[], isRTL: boolean) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);
    const weekAgo = new Date(today.getTime() - 7 * 86400000);

    const todayItems: T[] = [];
    const yesterdayItems: T[] = [];
    const weekItems: T[] = [];
    const olderItems: T[] = [];

    items.forEach(item => {
        const d = new Date(item.timestamp);
        if (d >= today) todayItems.push(item);
        else if (d >= yesterday) yesterdayItems.push(item);
        else if (d >= weekAgo) weekItems.push(item);
        else olderItems.push(item);
    });

    const groups: { title: string; items: T[] }[] = [];
    if (todayItems.length > 0) groups.push({ title: isRTL ? 'اليوم' : 'Today', items: todayItems });
    if (yesterdayItems.length > 0) groups.push({ title: isRTL ? 'أمس' : 'Yesterday', items: yesterdayItems });
    if (weekItems.length > 0) groups.push({ title: isRTL ? 'الأسبوع الماضي' : 'Previous 7 Days', items: weekItems });
    if (olderItems.length > 0) groups.push({ title: isRTL ? 'أقدم' : 'Older', items: olderItems });
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
    const [searchQuery, setSearchQuery] = useState('');

    // Merge conversations + recentSearches for display
    const allItems: SearchDisplayItem[] = useMemo(() => [
        ...conversations.map(c => ({
            id: c.id,
            query: c.title,
            type: 'general' as const,
            timestamp: c.timestamp instanceof Date ? c.timestamp : new Date(c.timestamp),
            isSearch: true as const,
        })),
        ...recentSearches.map(s => ({ ...s, isSearch: true as const })),
    ], [conversations, recentSearches]);

    const filteredItems = useMemo(() => {
        if (!searchQuery.trim()) return allItems;
        const q = searchQuery.toLowerCase();
        return allItems.filter(item => item.query.toLowerCase().includes(q));
    }, [allItems, searchQuery]);

    const groupedItems = groupByDate(filteredItems, isRTL);

    const sidebarContent = (
        <div className="flex h-full flex-col">
            {/* Header — New chat button */}
            <div className="flex-shrink-0 px-3 pt-3 pb-2 border-b border-[var(--color-border)]">
                <button
                    onClick={onNewInquiry}
                    className="flex w-full items-center gap-2 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] px-3 py-2.5 text-[13px] font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-border)] transition-colors"
                >
                    <Plus size={15} strokeWidth={2.2} />
                    <span>{isRTL ? 'محادثة جديدة' : 'New chat'}</span>
                </button>
            </div>

            {/* Search */}
            <div className="flex-shrink-0 px-3 py-2">
                <div className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-3 py-2">
                    <Search size={13} className="text-[var(--color-text-muted)] shrink-0" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder={isRTL ? 'بحث في المحادثات' : 'Search conversations'}
                        className="flex-1 bg-transparent text-[12px] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] outline-none"
                        dir={isRTL ? 'rtl' : 'ltr'}
                    />
                    {searchQuery && (
                        <button onClick={() => setSearchQuery('')} className="shrink-0">
                            <X size={12} className="text-[var(--color-text-muted)]" />
                        </button>
                    )}
                </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto px-2 py-1 [scrollbar-width:thin] [scrollbar-color:var(--color-border)_transparent]">
                {groupedItems.length === 0 ? (
                    <div className="px-3 py-8 text-center">
                        <MessageSquare size={28} className="mx-auto mb-3 text-[var(--color-text-muted)]/30" />
                        <p className="text-[13px] text-[var(--color-text-muted)]">
                            {searchQuery
                                ? (isRTL ? 'لا توجد نتائج' : 'No results found')
                                : (isRTL ? 'لا توجد محادثات بعد' : 'No conversations yet')}
                        </p>
                        {!searchQuery && (
                            <p className="mt-1 text-[11px] text-[var(--color-text-muted)]/60">
                                {isRTL ? 'ابدأ محادثة للبدء' : 'Start a new chat to begin'}
                            </p>
                        )}
                    </div>
                ) : (
                    groupedItems.map((group) => (
                        <div key={group.title} className="mb-3">
                            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                                {group.title}
                            </p>
                            {group.items.map((item) => {
                                const IconComponent = getSearchIcon(item.type);
                                const isHovered = hoveredItem === item.id;
                                const isActive = item.id === activeConversationId;

                                return (
                                    <div
                                        key={item.id}
                                        className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-[13px] cursor-pointer transition-colors ${
                                            isActive
                                                ? 'bg-emerald-500/10 text-[var(--color-text-primary)]'
                                                : 'hover:bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)]'
                                        }`}
                                        onClick={() => {
                                            onSearchClick?.(item);
                                            if (item.id) onSelectConversation?.(item.id);
                                        }}
                                        onMouseEnter={() => setHoveredItem(item.id)}
                                        onMouseLeave={() => setHoveredItem(null)}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                    >
                                        <IconComponent size={14} className="text-[var(--color-text-muted)] shrink-0" />
                                        <span className="flex-1 truncate text-[13px] text-[var(--color-text-primary)] leading-tight">
                                            {item.query}
                                        </span>

                                        {isHovered && (
                                            <div className="flex items-center gap-0.5 shrink-0">
                                                <button
                                                    className="p-1 rounded-lg hover:bg-[var(--color-border)] transition-colors"
                                                    onClick={e => e.stopPropagation()}
                                                    aria-label="Rename"
                                                >
                                                    <Edit2 size={12} className="text-[var(--color-text-muted)]" />
                                                </button>
                                                <button
                                                    className="p-1 rounded-lg hover:bg-red-500/10 transition-colors"
                                                    onClick={e => e.stopPropagation()}
                                                    aria-label="Delete"
                                                >
                                                    <Trash2 size={12} className="text-[var(--color-text-muted)] hover:text-red-500" />
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

            {/* Footer */}
            <div className="flex-shrink-0 border-t border-[var(--color-border)] px-3 py-3">
                <div className="flex items-center gap-1">
                    <Link
                        href="/settings"
                        className="flex flex-1 items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] font-medium text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)] transition-colors"
                    >
                        <Settings size={15} strokeWidth={1.8} />
                        <span>{isRTL ? 'إعدادات' : 'Settings'}</span>
                    </Link>
                    <button
                        onClick={() => logout()}
                        className="flex items-center justify-center h-9 w-9 rounded-xl text-[var(--color-text-muted)] hover:bg-red-500/10 hover:text-red-500 transition-colors"
                        title={isRTL ? 'خروج' : 'Sign out'}
                    >
                        <LogOut size={15} strokeWidth={1.8} />
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <>
            {/* Desktop sidebar */}
            <aside
                className={`hidden lg:flex flex-col w-[260px] shrink-0 border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-xl h-full overflow-hidden ${
                    isRTL ? 'border-l' : 'border-r'
                }`}
            >
                {sidebarContent}
            </aside>

            {/* Mobile sidebar overlay */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                        />
                        <motion.aside
                            initial={{ x: isRTL ? 280 : -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? 280 : -280 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'right-0' : 'left-0'} top-0 h-full w-[280px] z-50 lg:hidden bg-[var(--color-surface)] border-[var(--color-border)] ${isRTL ? 'border-l' : 'border-r'}`}
                        >
                            <button
                                onClick={onClose}
                                className={`absolute top-4 ${isRTL ? 'left-4' : 'right-4'} flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors`}
                            >
                                <X size={16} />
                            </button>
                            {sidebarContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
