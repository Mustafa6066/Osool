'use client';

import { Plus, Building2, Building, Home, TrendingUp, Calculator, Settings, FolderOpen, LogOut, X, MessageSquare } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

interface Conversation {
    id: string;
    title: string;
    preview: string;
    timestamp: Date;
}

interface ChatSidebarProps {
    isOpen?: boolean;
    onClose?: () => void;
    onNewInquiry?: () => void;
    conversations?: Conversation[];
    activeConversationId?: string;
    onSelectConversation?: (id: string) => void;
    isRTL?: boolean;
}

export default function ChatSidebar({
    isOpen = true,
    onClose,
    onNewInquiry,
    conversations = [],
    activeConversationId,
    onSelectConversation,
    isRTL = false,
}: ChatSidebarProps) {
    const { logout } = useAuth();

    const sidebarContent = (
        <>
            <div className="p-5">
                <button
                    onClick={onNewInquiry}
                    className="w-full flex items-center justify-center gap-2 new-inquiry-button"
                >
                    <Plus size={20} />
                    <span>{isRTL ? 'استفسار جديد' : 'New Property Inquiry'}</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-8 chat-scrollbar">
                {/* Conversations */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-3">
                        {isRTL ? 'المحادثات الأخيرة' : 'Recent Conversations'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        {conversations.length === 0 ? (
                            <div className="px-4 py-8 text-center">
                                <MessageSquare size={32} className="mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                                <p className="text-sm text-gray-400 dark:text-gray-500">
                                    {isRTL ? 'لا توجد محادثات بعد' : 'No conversations yet'}
                                </p>
                                <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                                    {isRTL ? 'ابدأ محادثة جديدة' : 'Start a new inquiry'}
                                </p>
                            </div>
                        ) : (
                            conversations.map((conversation) => (
                                <button
                                    key={conversation.id}
                                    onClick={() => onSelectConversation?.(conversation.id)}
                                    className={`recent-search-item ${conversation.id === activeConversationId ? 'active' : ''} w-full text-left`}
                                    dir={isRTL ? 'rtl' : 'ltr'}
                                >
                                    <MessageSquare
                                        size={20}
                                        className={conversation.id === activeConversationId ? 'text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]' : 'text-gray-500'}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-bold truncate ${conversation.id === activeConversationId ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                                            {conversation.title}
                                        </p>
                                        <p className="text-[10px] text-gray-500 truncate">{conversation.preview}</p>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Tools */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-3">
                        {isRTL ? 'الأدوات' : 'Tools'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors w-full text-left" dir={isRTL ? 'rtl' : 'ltr'}>
                            <TrendingUp size={20} />
                            <span className="text-sm font-medium truncate">{isRTL ? 'توقعات السوق' : 'Market Forecaster'}</span>
                        </button>
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors w-full text-left" dir={isRTL ? 'rtl' : 'ltr'}>
                            <Calculator size={20} />
                            <span className="text-sm font-medium truncate">{isRTL ? 'حاسبة العائد' : 'ROI Calculator'}</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-gray-200 dark:border-[var(--chat-border-dark)] mt-auto">
                <div className="flex items-center justify-around text-gray-500 dark:text-[var(--chat-text-secondary)]">
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2">
                        <Settings size={20} />
                        <span className="text-[9px]">{isRTL ? 'إعدادات' : 'Settings'}</span>
                    </button>
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2">
                        <FolderOpen size={20} />
                        <span className="text-[9px]">{isRTL ? 'ملفات' : 'Docs'}</span>
                    </button>
                    <button
                        onClick={() => logout()}
                        className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2"
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
            <aside className={`chat-sidebar chat-glass-panel flex-col hidden lg:flex z-20 ${isRTL ? 'border-l border-r-0' : ''}`}>
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
                            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                        />

                        {/* Mobile Sidebar */}
                        <motion.aside
                            initial={{ x: isRTL ? 280 : -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? 280 : -280 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'right-0' : 'left-0'} top-0 h-full w-[280px] chat-glass-panel flex flex-col z-50 lg:hidden`}
                        >
                            {/* Close button */}
                            <div className={`flex ${isRTL ? 'justify-start' : 'justify-end'} p-4`}>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
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
