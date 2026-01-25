'use client';

import { useEffect, useRef, useState } from 'react';
import {
    Plus, TrendingUp, Calculator, Settings, FolderOpen, LogOut, X,
    MessageSquare, Building2, MapPin, Home, Landmark, FileText,
    BarChart2, Map, Calendar, Users, Activity
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import anime from 'animejs';

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
    const toolsRef = useRef<HTMLDivElement>(null);
    const [animatedOnce, setAnimatedOnce] = useState(false);

    // Animate tools on mount
    useEffect(() => {
        if (toolsRef.current && !animatedOnce) {
            anime({
                targets: toolsRef.current.querySelectorAll('.tool-item'),
                opacity: [0, 1],
                translateX: [-20, 0],
                delay: anime.stagger(80, { start: 300 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
            setAnimatedOnce(true);
        }
    }, [animatedOnce]);

    // Tools configuration
    const tools = [
        {
            id: 'market_forecaster',
            icon: TrendingUp,
            labelEn: 'Market Forecaster',
            labelAr: 'توقعات السوق',
            triggerQuery: isRTL ? 'عايز أعرف توقعات السوق' : 'Show me market forecast'
        },
        {
            id: 'roi_calculator',
            icon: Calculator,
            labelEn: 'ROI Calculator',
            labelAr: 'حاسبة العائد',
            triggerQuery: isRTL ? 'احسبلي العائد على الاستثمار' : 'Calculate ROI for investment'
        },
        {
            id: 'area_analysis',
            icon: Map,
            labelEn: 'Area Analysis',
            labelAr: 'تحليل المناطق',
            triggerQuery: isRTL ? 'حللي المناطق المتاحة' : 'Analyze available areas'
        },
        {
            id: 'developer_rankings',
            icon: Building2,
            labelEn: 'Developer Rankings',
            labelAr: 'تصنيف المطورين',
            triggerQuery: isRTL ? 'أفضل المطورين العقاريين' : 'Show top developers ranking'
        },
        {
            id: 'payment_plans',
            icon: Calendar,
            labelEn: 'Payment Plans',
            labelAr: 'خطط السداد',
            triggerQuery: isRTL ? 'قارن خطط السداد' : 'Compare payment plans'
        },
    ];

    const sidebarContent = (
        <>
            {/* Status Indicator */}
            <div className="px-5 pt-5 pb-3">
                <div className="status-badge">
                    <div className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-teal-accent)] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-teal-accent)]"></span>
                    </div>
                    <span className="text-xs font-semibold text-[var(--color-text-muted)]">
                        {isRTL ? 'وضع التحليل: ' : 'Analysis Mode: '}
                        <span className="text-[var(--color-primary)]">{isRTL ? 'نشط' : 'Active'}</span>
                    </span>
                </div>
            </div>

            {/* New Inquiry Button */}
            <div className="px-5 pb-4">
                <button
                    onClick={onNewInquiry}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[var(--color-primary)] text-white font-semibold hover:bg-[var(--color-primary-light)] transition-all shadow-lg shadow-[var(--color-primary)]/20 hover:shadow-[var(--color-primary)]/30 transform hover:-translate-y-0.5"
                >
                    <Plus size={20} />
                    <span>{isRTL ? 'استفسار جديد' : 'New Property Inquiry'}</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-6 no-scrollbar">
                {/* Recent Searches */}
                {recentSearches.length > 0 && (
                    <div>
                        <h3 className="px-4 text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                            {isRTL ? 'عمليات البحث الأخيرة' : 'Recent Searches'}
                        </h3>
                        <div className="flex flex-col gap-1">
                            {recentSearches.slice(0, 5).map((search, index) => {
                                const IconComponent = getSearchIcon(search.type);
                                return (
                                    <button
                                        key={search.id}
                                        onClick={() => onSearchClick?.(search)}
                                        className={`group flex items-center gap-3 px-4 py-3 rounded-xl transition-all w-full text-left relative overflow-hidden ${
                                            index === 0
                                                ? 'bg-[var(--color-surface)] border border-[var(--color-border)] shadow-sm'
                                                : 'hover:bg-[var(--color-surface-hover)]'
                                        }`}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                    >
                                        <div className="absolute inset-0 bg-[var(--color-primary)]/5 w-0 group-hover:w-full transition-all duration-300" />
                                        <IconComponent
                                            size={18}
                                            className={index === 0 ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'}
                                        />
                                        <div className="flex-1 min-w-0 relative z-10">
                                            <p className={`text-sm font-bold truncate ${index === 0 ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}`}>
                                                {search.query}
                                            </p>
                                            {index === 0 && (
                                                <p className="text-[10px] text-[var(--color-text-muted)] truncate">
                                                    {search.type === 'location' ? (isRTL ? 'تحليل منطقة' : 'Area analysis') :
                                                     search.type === 'developer' ? (isRTL ? 'تحليل مطور' : 'Developer analysis') :
                                                     search.type === 'property' ? (isRTL ? 'بحث عقاري' : 'Property search') :
                                                     (isRTL ? 'بحث عام' : 'General search')}
                                                </p>
                                            )}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Conversations */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                        {isRTL ? 'المحادثات' : 'Conversations'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        {conversations.length === 0 ? (
                            <div className="px-4 py-6 text-center">
                                <MessageSquare size={28} className="mx-auto mb-3 text-[var(--color-text-muted)]/30" />
                                <p className="text-xs text-[var(--color-text-muted)]">
                                    {isRTL ? 'لا توجد محادثات بعد' : 'No conversations yet'}
                                </p>
                            </div>
                        ) : (
                            conversations.slice(0, 5).map((conversation) => (
                                <button
                                    key={conversation.id}
                                    onClick={() => onSelectConversation?.(conversation.id)}
                                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-colors w-full text-left ${
                                        conversation.id === activeConversationId
                                            ? 'bg-[var(--color-primary)]/10 border border-[var(--color-primary)]/20'
                                            : 'hover:bg-[var(--color-surface-hover)]'
                                    }`}
                                    dir={isRTL ? 'rtl' : 'ltr'}
                                >
                                    <MessageSquare
                                        size={18}
                                        className={conversation.id === activeConversationId ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-medium truncate ${conversation.id === activeConversationId ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}`}>
                                            {conversation.title}
                                        </p>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Tools */}
                <div ref={toolsRef}>
                    <h3 className="px-4 text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                        {isRTL ? 'أدوات التحليل' : 'Analytics Tools'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        {tools.map((tool) => (
                            <button
                                key={tool.id}
                                onClick={() => onToolClick?.(tool.triggerQuery)}
                                className="tool-item group flex items-center gap-3 px-4 py-2.5 rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text-primary)] transition-all w-full text-left"
                                dir={isRTL ? 'rtl' : 'ltr'}
                                style={{ opacity: 0 }}
                            >
                                <tool.icon size={18} className="group-hover:text-[var(--color-primary)] transition-colors" />
                                <span className="text-sm font-medium truncate">{isRTL ? tool.labelAr : tool.labelEn}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-[var(--color-border)] mt-auto">
                <div className="flex items-center justify-around text-[var(--color-text-muted)]">
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--color-primary)] transition-colors p-2" title={isRTL ? 'إعدادات' : 'Settings'}>
                        <Settings size={20} />
                        <span className="text-[9px]">{isRTL ? 'إعدادات' : 'Settings'}</span>
                    </button>
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--color-primary)] transition-colors p-2" title={isRTL ? 'ملفات' : 'Docs'}>
                        <FolderOpen size={20} />
                        <span className="text-[9px]">{isRTL ? 'ملفات' : 'Docs'}</span>
                    </button>
                    <button
                        onClick={() => logout()}
                        className="flex flex-col items-center gap-1 hover:text-[var(--color-primary)] transition-colors p-2"
                        title={isRTL ? 'خروج' : 'Logout'}
                    >
                        <LogOut size={20} />
                        <span className="text-[9px]">{isRTL ? 'خروج' : 'Logout'}</span>
                    </button>
                </div>
            </div>
        </>
    );

    return (
        <>
            {/* Desktop Sidebar */}
            <aside className={`w-[280px] border-r border-[var(--color-border)] glass-panel flex-col hidden lg:flex z-20 ${isRTL ? 'border-l border-r-0' : ''}`}>
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
                            className={`fixed ${isRTL ? 'right-0' : 'left-0'} top-0 h-full w-[280px] bg-[var(--color-surface)] flex flex-col z-50 lg:hidden border-r border-[var(--color-border)]`}
                        >
                            {/* Close button */}
                            <div className={`flex ${isRTL ? 'justify-start' : 'justify-end'} p-4`}>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] transition-colors"
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
