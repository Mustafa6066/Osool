'use client';

import { Bell, Menu } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface ChatHeaderProps {
    onToggleSidebar?: () => void;
    showMenuButton?: boolean;
}

export default function ChatHeader({ onToggleSidebar, showMenuButton = false }: ChatHeaderProps) {
    const { user } = useAuth();

    // Get display name with specific admin titles
    const getDisplayName = () => {
        const email = user?.email?.toLowerCase();
        if (email === 'mustafa@osool.eg') return 'Mr.Mustafa';
        if (email === 'hani@osool.eg') return 'Mr.Hani';
        if (email === 'abady@osool.eg') return 'Mr.Abady';
        if (email === 'sama@osool.eg') return 'Mrs.Sama';

        if (user?.full_name && user.full_name !== 'Wallet User') return user.full_name;
        return user?.email?.split('@')[0] || 'User';
    };

    // Get user initials for avatar
    const getInitials = () => {
        let name = getDisplayName();
        if (name.startsWith('Mr.')) {
            name = name.substring(3);
        } else if (name.startsWith('Mrs.')) {
            name = name.substring(4);
        }
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <header className="flex-none h-16 border-b border-gray-200 dark:border-[var(--chat-border-dark)] flex items-center justify-between px-6 bg-white/80 dark:bg-[var(--chat-background-dark)]/80 backdrop-blur-sm z-30 relative">
            <div className="flex items-center gap-3">
                {/* Mobile menu button */}
                {showMenuButton && (
                    <button
                        onClick={onToggleSidebar}
                        className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
                    >
                        <Menu size={20} />
                    </button>
                )}

                {/* Logo */}
                <Link href="/" className="flex items-center gap-3">
                    <div className="size-9 rounded-xl bg-gradient-to-tr from-[var(--chat-primary)] to-teal-800 flex items-center justify-center text-white shadow-lg">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M19 9.3V4h-3v2.6L12 3 2 12h3v8h5v-6h4v6h5v-8h3l-3-2.7zm-9 .7c0-1.1.9-2 2-2s2 .9 2 2h-4z" />
                        </svg>
                    </div>
                    <div>
                        <h1 className="text-base font-bold tracking-tight leading-none text-gray-900 dark:text-white">
                            Agentic<span className="text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)] font-light">Workspace</span>
                        </h1>
                        <p className="text-[10px] font-medium text-gray-500 dark:text-[var(--chat-text-secondary)] uppercase tracking-wider">
                            Professional Suite
                        </p>
                    </div>
                </Link>
            </div>

            {/* Center Status Indicator */}
            <div className="hidden md:flex items-center gap-3 px-4 py-1.5 rounded-full bg-gray-100 dark:bg-[var(--chat-surface-dark)] border border-transparent dark:border-[var(--chat-border-dark)]/50 shadow-inner">
                <div className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
                </div>
                <span className="text-xs font-semibold text-gray-600 dark:text-[var(--chat-text-secondary)]">
                    Market Analysis Mode: <span className="text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]">Active</span>
                </span>
            </div>

            {/* User Profile & Actions */}
            <div className="flex items-center gap-2 sm:gap-4">
                <button className="size-9 flex items-center justify-center rounded-lg text-gray-500 dark:text-[var(--chat-text-secondary)] hover:bg-gray-100 dark:hover:bg-white/5 transition-all">
                    <Bell size={20} />
                </button>
                <div className="h-6 w-px bg-gray-200 dark:bg-[var(--chat-border-dark)] mx-1"></div>
                <div className="flex items-center gap-3 cursor-pointer group">
                    <div className="text-right hidden sm:block">
                        <p className="text-xs font-bold text-gray-900 dark:text-white">{getDisplayName()}</p>
                        <p className="text-[10px] text-gray-500 dark:text-[var(--chat-text-secondary)]">Premium User</p>
                    </div>
                    <div className="size-9 rounded-full bg-gradient-to-br from-[var(--chat-primary)] to-teal-600 flex items-center justify-center text-white text-sm font-bold ring-2 ring-gray-100 dark:ring-[var(--chat-border-dark)] group-hover:ring-[var(--chat-primary)] transition-all">
                        {getInitials()}
                    </div>
                </div>
            </div>
        </header>
    );
}
