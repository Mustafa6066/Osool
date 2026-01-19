'use client';

import { Plus, Building2, Building, Home, TrendingUp, Calculator, Settings, FolderOpen, LogOut, X } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';

interface RecentSearch {
    id: string;
    title: string;
    subtitle: string;
    icon: 'city' | 'apartment' | 'villa';
    active?: boolean;
}

interface ChatSidebarProps {
    isOpen?: boolean;
    onClose?: () => void;
    onNewInquiry?: () => void;
    recentSearches?: RecentSearch[];
    onSelectSearch?: (id: string) => void;
}

const iconMap = {
    city: Building2,
    apartment: Building,
    villa: Home,
};

export default function ChatSidebar({
    isOpen = true,
    onClose,
    onNewInquiry,
    recentSearches = [
        { id: '1', title: 'Seaport Waterfront', subtitle: 'High appreciation > 5%', icon: 'city', active: true },
        { id: '2', title: 'Austin Downtown Condos', subtitle: 'Price range $500K-$1M', icon: 'apartment' },
        { id: '3', title: 'Miami Beach Villas', subtitle: 'Luxury beachfront', icon: 'villa' },
    ],
    onSelectSearch,
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
                    <span>New Property Inquiry</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-8 chat-scrollbar">
                {/* Recent Searches */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-3">
                        Recent Searches
                    </h3>
                    <div className="flex flex-col gap-1">
                        {recentSearches.map((search) => {
                            const IconComponent = iconMap[search.icon];
                            return (
                                <button
                                    key={search.id}
                                    onClick={() => onSelectSearch?.(search.id)}
                                    className={`recent-search-item ${search.active ? 'active' : ''} w-full text-left`}
                                >
                                    <IconComponent
                                        size={20}
                                        className={search.active ? 'text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]' : 'text-gray-500'}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm font-bold truncate ${search.active ? 'text-gray-900 dark:text-white' : 'text-gray-600 dark:text-gray-400'}`}>
                                            {search.title}
                                        </p>
                                        {search.active && (
                                            <p className="text-[10px] text-gray-500 truncate">{search.subtitle}</p>
                                        )}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Tools */}
                <div>
                    <h3 className="px-4 text-[11px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-3">
                        Tools
                    </h3>
                    <div className="flex flex-col gap-1">
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors w-full text-left">
                            <TrendingUp size={20} />
                            <span className="text-sm font-medium truncate">Market Forecaster</span>
                        </button>
                        <button className="group flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors w-full text-left">
                            <Calculator size={20} />
                            <span className="text-sm font-medium truncate">ROI Calculator</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="p-4 border-t border-gray-200 dark:border-[var(--chat-border-dark)] mt-auto">
                <div className="flex items-center justify-around text-gray-500 dark:text-[var(--chat-text-secondary)]">
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2">
                        <Settings size={20} />
                        <span className="text-[9px]">Settings</span>
                    </button>
                    <button className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2">
                        <FolderOpen size={20} />
                        <span className="text-[9px]">Docs</span>
                    </button>
                    <button
                        onClick={() => logout()}
                        className="flex flex-col items-center gap-1 hover:text-[var(--chat-primary)] dark:hover:text-white transition-colors p-2"
                    >
                        <LogOut size={20} />
                        <span className="text-[9px]">Logout</span>
                    </button>
                </div>
            </div>
        </>
    );

    return (
        <>
            {/* Desktop Sidebar */}
            <aside className="chat-sidebar chat-glass-panel flex-col hidden lg:flex z-20">
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
                            initial={{ x: -280 }}
                            animate={{ x: 0 }}
                            exit={{ x: -280 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className="fixed left-0 top-0 h-full w-[280px] chat-glass-panel flex flex-col z-50 lg:hidden"
                        >
                            {/* Close button */}
                            <div className="flex justify-end p-4">
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
