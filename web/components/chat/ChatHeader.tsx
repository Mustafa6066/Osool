'use client';

import { useEffect, useRef } from 'react';
import { Bell, Menu, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import anime from 'animejs';

interface ChatHeaderProps {
    onToggleSidebar?: () => void;
    showMenuButton?: boolean;
    isRTL?: boolean;
}

export default function ChatHeader({ onToggleSidebar, showMenuButton = false, isRTL = false }: ChatHeaderProps) {
    const { user } = useAuth();
    const headerRef = useRef<HTMLElement>(null);
    const logoRef = useRef<HTMLDivElement>(null);
    const statusRef = useRef<HTMLDivElement>(null);

    // Entrance animation
    useEffect(() => {
        if (headerRef.current) {
            anime({
                targets: headerRef.current,
                opacity: [0, 1],
                translateY: [-10, 0],
                easing: 'easeOutExpo',
                duration: 600,
            });
        }
        if (logoRef.current) {
            anime({
                targets: logoRef.current,
                scale: [0.8, 1],
                opacity: [0, 1],
                easing: 'easeOutExpo',
                duration: 500,
                delay: 200,
            });
        }
        if (statusRef.current) {
            anime({
                targets: statusRef.current,
                opacity: [0, 1],
                translateX: [20, 0],
                easing: 'easeOutExpo',
                duration: 500,
                delay: 400,
            });
        }
    }, []);

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
        <header
            ref={headerRef}
            className="flex-none h-16 border-b border-[var(--color-border)] flex items-center justify-between px-6 bg-[var(--color-surface)]/80 backdrop-blur-sm z-30 relative"
            style={{ opacity: 0 }}
        >
            <div className={`flex items-center gap-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                {/* Mobile menu button */}
                {showMenuButton && (
                    <button
                        onClick={onToggleSidebar}
                        className="lg:hidden p-2 rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] transition-colors"
                    >
                        <Menu size={20} />
                    </button>
                )}

                {/* Logo */}
                <Link href="/" className={`flex items-center gap-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <div
                        ref={logoRef}
                        className="size-9 rounded-xl bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-teal-accent)] flex items-center justify-center text-white shadow-lg shadow-[var(--color-primary)]/20"
                        style={{ opacity: 0 }}
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M19 9.3V4h-3v2.6L12 3 2 12h3v8h5v-6h4v6h5v-8h3l-3-2.7zm-9 .7c0-1.1.9-2 2-2s2 .9 2 2h-4z" />
                        </svg>
                    </div>
                    <div className={isRTL ? 'text-right' : ''}>
                        <h1 className="text-base font-bold tracking-tight leading-none text-[var(--color-text-primary)]">
                            {isRTL ? 'أصول' : 'Agentic'}
                            <span className="text-[var(--color-primary)] font-light"> {isRTL ? 'AI' : 'Workspace'}</span>
                        </h1>
                        <p className="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                            {isRTL ? 'ذكاء عقاري' : 'Professional Suite'}
                        </p>
                    </div>
                </Link>
            </div>

            {/* Center Status Indicator */}
            <div
                ref={statusRef}
                className="hidden md:flex items-center gap-3 px-4 py-1.5 rounded-full bg-[var(--color-surface-elevated)] border border-[var(--color-border)] shadow-inner"
                style={{ opacity: 0 }}
            >
                <div className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-teal-accent)] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-teal-accent)]"></span>
                </div>
                <span className="text-xs font-semibold text-[var(--color-text-muted)]">
                    {isRTL ? 'وضع التحليل: ' : 'Market Analysis Mode: '}
                    <span className="text-[var(--color-primary)]">{isRTL ? 'نشط' : 'Active'}</span>
                </span>
            </div>

            {/* User Profile & Actions */}
            <div className={`flex items-center gap-2 sm:gap-4 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <button className="size-9 flex items-center justify-center rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary)] transition-all relative">
                    <Bell size={20} />
                    {/* Notification dot */}
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[var(--color-teal-accent)] rounded-full"></span>
                </button>
                <div className="h-6 w-px bg-[var(--color-border)] mx-1"></div>
                <div className={`flex items-center gap-3 cursor-pointer group ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <div className={`hidden sm:block ${isRTL ? 'text-left' : 'text-right'}`}>
                        <p className="text-xs font-bold text-[var(--color-text-primary)]">{getDisplayName()}</p>
                        <p className="text-[10px] text-[var(--color-text-muted)]">{isRTL ? 'مستخدم مميز' : 'Premium User'}</p>
                    </div>
                    <div className="size-9 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-teal-accent)] flex items-center justify-center text-white text-sm font-bold ring-2 ring-[var(--color-border)] group-hover:ring-[var(--color-primary)] transition-all shadow-md">
                        {getInitials()}
                    </div>
                </div>
            </div>
        </header>
    );
}
