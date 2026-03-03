'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    MessageSquare, LayoutDashboard, TrendingUp, Building2,
    Heart, LogOut, Sun, Moon, Gift, Menu, X,
    ChevronDown
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import LanguageToggle from '@/components/LanguageToggle';
import InvitationModal from '@/components/InvitationModal';

const NAV_ITEMS = [
    { key: 'chat', label: 'Chat', labelAr: 'محادثة', icon: MessageSquare, href: '/chat' },
    { key: 'dashboard', label: 'Dashboard', labelAr: 'لوحة التحكم', icon: LayoutDashboard, href: '/dashboard' },
    { key: 'market', label: 'Market', labelAr: 'السوق', icon: TrendingUp, href: '/market' },
    { key: 'properties', label: 'Properties', labelAr: 'العقارات', icon: Building2, href: '/properties' },
    { key: 'favorites', label: 'Saved', labelAr: 'المفضلة', icon: Heart, href: '/favorites' },
];

interface SmartNavProps {
    children: React.ReactNode;
}

export default function SmartNav({ children }: SmartNavProps) {
    const pathname = usePathname();
    const { user, isAuthenticated, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const { language, t } = useLanguage();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);

    useEffect(() => {
        setMobileMenuOpen(false);
        setUserMenuOpen(false);
    }, [pathname]);

    useEffect(() => {
        if (!userMenuOpen) return;
        const handleClick = () => setUserMenuOpen(false);
        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
    }, [userMenuOpen]);

    const getActiveKey = () => {
        if (pathname === '/chat') return 'chat';
        if (pathname === '/dashboard') return 'dashboard';
        if (pathname === '/market') return 'market';
        if (pathname.startsWith('/properties') || pathname.startsWith('/property/')) return 'properties';
        if (pathname === '/favorites') return 'favorites';
        return '';
    };

    const activeKey = getActiveKey();

    return (
        <>
            <InvitationModal isOpen={showInviteModal} onClose={() => setShowInviteModal(false)} />

            <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100vh', overflow: 'hidden' }}>

                {/* Header */}
                <header className="fixed top-0 left-0 right-0 z-50 bg-[var(--color-background)]/80 backdrop-blur-xl border-b border-[var(--color-border)]">
                    <div className="max-w-[1440px] mx-auto px-4 md:px-6">
                        <div className="flex items-center justify-between h-12">

                            {/* Logo */}
                            <Link href="/chat" className="flex items-center gap-2 flex-shrink-0 group">
                                <div className="w-7 h-7 rounded-lg bg-[var(--color-text-primary)] flex items-center justify-center text-[var(--color-background)] transition-transform group-hover:scale-105">
                                    <Building2 className="w-3.5 h-3.5" strokeWidth={2.5} />
                                </div>
                                <span className="text-[var(--color-text-primary)] text-sm font-semibold tracking-tight hidden sm:block">
                                    Osool<span className="text-emerald-500">.ai</span>
                                </span>
                            </Link>

                            {/* Center Nav — Pill tabs */}
                            <nav className="hidden md:flex items-center gap-0.5 bg-[var(--color-surface)] rounded-full px-1 py-0.5 border border-[var(--color-border)]">
                                {NAV_ITEMS.map((item) => {
                                    const isActive = item.key === activeKey;
                                    const Icon = item.icon;
                                    return (
                                        <Link
                                            key={item.key}
                                            href={item.href}
                                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-medium transition-all duration-150
                                                ${isActive
                                                    ? 'bg-[var(--color-text-primary)] text-[var(--color-background)] shadow-sm'
                                                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                                                }`}
                                        >
                                            <Icon className="w-3.5 h-3.5" strokeWidth={2} />
                                            <span>{language === 'ar' ? item.labelAr : item.label}</span>
                                        </Link>
                                    );
                                })}
                            </nav>

                            {/* Right — Actions */}
                            <div className="hidden md:flex items-center gap-1.5">
                                {/* Language Toggle */}
                                <LanguageToggle />

                                {/* Theme */}
                                <button
                                    onClick={toggleTheme}
                                    title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                                    className="w-8 h-8 rounded-full flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-colors"
                                >
                                    {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                </button>

                                {/* User */}
                                {isAuthenticated && (
                                    <div className="relative">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setUserMenuOpen(!userMenuOpen); }}
                                            className="flex items-center gap-1 px-2 py-1.5 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-colors"
                                        >
                                            <div className="w-6 h-6 rounded-full bg-[var(--color-surface-elevated)] flex items-center justify-center border border-[var(--color-border)]">
                                                <span className="text-[10px] font-semibold text-[var(--color-text-primary)]">
                                                    {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <ChevronDown className={`w-3 h-3 transition-transform duration-150 ${userMenuOpen ? 'rotate-180' : ''}`} />
                                        </button>

                                        {userMenuOpen && (
                                            <div className="absolute right-0 top-full mt-1.5 w-52 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-lg shadow-black/8 py-1 z-50 animate-fade-in">
                                                <div className="px-3 py-2.5 border-b border-[var(--color-border)]">
                                                    <div className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                                                        {user?.full_name || 'User'}
                                                    </div>
                                                    <div className="text-[11px] text-[var(--color-text-muted)] truncate mt-0.5">
                                                        {user?.email}
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => setShowInviteModal(true)}
                                                    className="flex items-center gap-2.5 w-full px-3 py-2.5 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-[var(--color-surface-elevated)] transition-colors"
                                                >
                                                    <Gift className="w-4 h-4" />
                                                    Invite Friends
                                                </button>
                                                <button
                                                    onClick={() => logout()}
                                                    className="flex items-center gap-2.5 w-full px-3 py-2.5 text-sm text-red-500 hover:bg-[var(--color-surface-elevated)] transition-colors"
                                                >
                                                    <LogOut className="w-4 h-4" />
                                                    Sign Out
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Mobile */}
                            <div className="flex md:hidden items-center gap-1.5">
                                <button
                                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                    title={mobileMenuOpen ? 'Close menu' : 'Open menu'}
                                    className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] transition-colors"
                                >
                                    {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Mobile Menu */}
                    {mobileMenuOpen && (
                        <div className="md:hidden border-t border-[var(--color-border)] bg-[var(--color-background)] animate-fade-in">
                            <nav className="px-3 py-2 space-y-0.5">
                                {NAV_ITEMS.map((item) => {
                                    const isActive = item.key === activeKey;
                                    const Icon = item.icon;
                                    return (
                                        <Link
                                            key={item.key}
                                            href={item.href}
                                            onClick={() => setMobileMenuOpen(false)}
                                            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors
                                                ${isActive
                                                    ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)]'
                                                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]'
                                                }`}
                                        >
                                            <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-500' : ''}`} strokeWidth={2} />
                                            <span className="text-sm font-medium">{language === 'ar' ? item.labelAr : item.label}</span>
                                        </Link>
                                    );
                                })}

                                <div className="border-t border-[var(--color-border)] pt-2 mt-2 space-y-1.5">
                                    <div className="px-3 py-2">
                                        <LanguageToggle />
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                    <button
                                        onClick={toggleTheme}
                                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] transition-colors flex-1"
                                    >
                                        {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                        <span className="text-sm">{theme === 'dark' ? t('nav.light') : t('nav.dark')}</span>
                                    </button>
                                    {isAuthenticated && (
                                        <>
                                            <button
                                                onClick={() => { setShowInviteModal(true); setMobileMenuOpen(false); }}
                                                className="flex items-center gap-2 px-3 py-2 rounded-xl text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 transition-colors flex-1"
                                            >
                                                <Gift className="w-4 h-4" />
                                                <span className="text-sm">{t('nav.invite')}</span>
                                            </button>
                                            <button
                                                onClick={() => logout()}
                                                title={t('nav.signOut')}
                                                className="flex items-center gap-2 px-3 py-2 rounded-xl text-red-500 hover:bg-red-500/10 transition-colors"
                                            >
                                                <LogOut className="w-4 h-4" />
                                            </button>
                                        </>
                                    )}
                                </div>
                                </div>
                            </nav>
                        </div>
                    )}
                </header>

                {/* Main Content */}
                <main style={{ flex: '1 1 0%', minWidth: 0, overflow: 'hidden', paddingTop: '3rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    {children}
                </main>
            </div>
        </>
    );
}
