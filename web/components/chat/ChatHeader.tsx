'use client';

import { Menu, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface ChatHeaderProps {
    onToggleSidebar?: () => void;
    showMenuButton?: boolean;
    isRTL?: boolean;
}

export default function ChatHeader({ onToggleSidebar, showMenuButton = false, isRTL = false }: ChatHeaderProps) {
    const { user } = useAuth();

    // Get display name
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
        <header className="flex-none h-14 border-b border-[var(--color-border)] flex items-center justify-between px-4 bg-[var(--color-surface)] z-30">
            <div className={`flex items-center gap-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                {/* Mobile menu button */}
                {showMenuButton && (
                    <button
                        onClick={onToggleSidebar}
                        className="lg:hidden p-2 rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--chatgpt-hover-bg)] transition-colors"
                    >
                        <Menu size={20} />
                    </button>
                )}

                {/* Logo - Simplified */}
                <Link href="/" className={`flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <div className="size-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-teal-accent)] flex items-center justify-center text-white">
                        <Sparkles size={18} />
                    </div>
                    <span className="font-semibold text-[var(--color-text-primary)]">
                        {isRTL ? 'عمرو' : 'AMR AI'}
                    </span>
                </Link>
            </div>

            {/* User Avatar - Simplified */}
            <div className={`flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <span className="text-sm text-[var(--color-text-muted)] hidden sm:block">
                    {getDisplayName()}
                </span>
                <div className="size-8 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white text-sm font-medium">
                    {getInitials()}
                </div>
            </div>
        </header>
    );
}
