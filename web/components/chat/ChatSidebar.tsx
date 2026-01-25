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
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[var(--color-primary)] text-white font-semibold hover:bg-[var(--color-primary-light)] transition-colors shadow-lg"
                >
                    <Plus size={20} />
                    <span>{isRTL ? 'استفسار جديد' : 'New Property Inquiry'}</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-8 no-scrollbar">
                {/* Conversations */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                        {isRTL ? 'المحادثات الأخيرة' : 'Recent Conversations'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        {conversations.length === 0 ? (
                            <div className="px-4 py-8 text-center">
                                <MessageSquare size={32} className="mx-auto mb-3 text-[var(--color-text-muted)]/40" />
                                <p className="text-sm text-[var(--color-text-muted)]">
                                    {isRTL ? 'لا توجد محادثات بعد' : 'No conversations yet'}
                                </p>
                                <p className="text-xs text-[var(--color-text-muted)]/60 mt-1">
                                    {isRTL ? 'ابدأ محادثة جديدة' : 'Start a new inquiry'}
                                </p>
                            </div>
                        ) : (
                            conversations.map((conversation) => (
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
                                        size={20}
                                        className={conversation.id === activeConversationId ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-bold truncate ${conversation.id === activeConversationId ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}`}>
                                            {conversation.title}
                                        </p>
                                        <p className="text-[10px] text-[var(--color-text-muted)] truncate">{conversation.preview}</p>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Tools */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                        {isRTL ? 'الأدوات' : 'Tools'}
                    </h3>
                    <div className="flex flex-col gap-1">
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] transition-colors w-full text-left" dir={isRTL ? 'rtl' : 'ltr'}>
                            <TrendingUp size={20} />
                            <span className="text-sm font-medium truncate">{isRTL ? 'توقعات السوق' : 'Market Forecaster'}</span>
                        </button>
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] transition-colors w-full text-left" dir={isRTL ? 'rtl' : 'ltr'}>
                            <Calculator size={20} />
                            <span className="text-sm font-medium truncate">{isRTL ? 'حاسبة العائد' : 'ROI Calculator'}</span>
                        </button>
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
            <aside className={`w-[280px] border-r border-[var(--color-border)] bg-[var(--color-surface)] flex-col hidden lg:flex z-20 ${isRTL ? 'border-l border-r-0' : ''}`}>
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
