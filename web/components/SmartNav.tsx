'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    MessageSquare, LayoutDashboard, TrendingUp, Building2,
    Heart, Award, LogOut, Sun, Moon, Gift, Menu, X,
    Zap, ChevronDown
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import { useTheme } from '@/contexts/ThemeContext';
import { LEVEL_COLORS, LEVEL_GRADIENTS } from '@/lib/gamification';
import InvitationModal from '@/components/InvitationModal';

// ═══════════════════════════════════════════════════════════════
// NAV ITEMS — Professional minimal icons
// ═══════════════════════════════════════════════════════════════

const NAV_ITEMS = [
    { key: 'chat', label: 'Chat', labelAr: 'محادثة', icon: MessageSquare, href: '/chat' },
    { key: 'dashboard', label: 'Dashboard', labelAr: 'لوحة التحكم', icon: LayoutDashboard, href: '/dashboard' },
    { key: 'market', label: 'Market', labelAr: 'السوق', icon: TrendingUp, href: '/market' },
    { key: 'properties', label: 'Properties', labelAr: 'العقارات', icon: Building2, href: '/properties' },
    { key: 'favorites', label: 'Favorites', labelAr: 'المفضلة', icon: Heart, href: '/favorites' },
];

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

interface SmartNavProps {
    children: React.ReactNode;
}

export default function SmartNav({ children }: SmartNavProps) {
    const pathname = usePathname();
    const { user, isAuthenticated, logout } = useAuth();
    const { profile } = useGamification();
    const { theme, toggleTheme } = useTheme();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [scrolled, setScrolled] = useState(false);

    const levelGradient = profile ? (LEVEL_GRADIENTS[profile.level] || LEVEL_GRADIENTS.curious) : 'from-gray-500 to-gray-600';
    const levelTitle = profile?.level_title_en || 'Curious';
    const xpProgress = profile?.next_level
        ? Math.min(((profile.xp - (profile.next_level.xp_required - profile.next_level.xp_remaining)) / profile.next_level.xp_remaining) * 100, 100)
        : 100;

    // Track scroll for header shadow
    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 8);
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Close mobile menu on route change
    useEffect(() => {
        setMobileMenuOpen(false);
        setUserMenuOpen(false);
    }, [pathname]);

    // Close user menu on outside click
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

            <div className="flex flex-col h-screen w-screen overflow-hidden bg-[var(--color-background)]">
                {/* ═══════════════════════════════════════════════════════
                 * FLOATING HEADER — Glassmorphism minimal bar
                 * ═══════════════════════════════════════════════════════ */}
                <header
                    className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300
                               ${scrolled
                            ? 'bg-[var(--color-surface)]/90 backdrop-blur-xl shadow-lg shadow-black/5 border-b border-[var(--color-border)]'
                            : 'bg-[var(--color-surface)]/70 backdrop-blur-md border-b border-transparent'
                        }`}
                >
                    <div className="max-w-[1440px] mx-auto px-4 md:px-6">
                        <div className="flex items-center justify-between h-14 md:h-[56px]">

                            {/* ── LEFT: Logo ── */}
                            <Link href="/chat" className="flex items-center gap-2.5 flex-shrink-0 group">
                                <div className="w-8 h-8 rounded-lg bg-[var(--color-text-primary)] flex items-center justify-center text-[var(--color-background)] shadow-sm group-hover:shadow-md transition-shadow">
                                    <Building2 className="w-4 h-4" />
                                </div>
                                <span className="text-[var(--color-text-primary)] text-sm font-bold tracking-tight hidden sm:block">
                                    Osool<span className="text-[var(--color-primary)] font-bold">.ai</span>
                                </span>
                            </Link>

                            {/* ── CENTER: Nav Tabs (desktop) ── */}
                            <nav className="hidden md:flex items-center gap-0.5 bg-[var(--color-surface)]/60 rounded-xl px-1 py-1 border border-[var(--color-border)]/40 backdrop-blur-sm">
                                {NAV_ITEMS.map((item) => {
                                    const isActive = item.key === activeKey;
                                    const Icon = item.icon;
                                    return (
                                        <Link
                                            key={item.key}
                                            href={item.href}
                                            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-200
                                                       ${isActive
                                                    ? 'bg-[var(--color-primary)]/12 text-[var(--color-primary)] shadow-sm'
                                                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]/80'
                                                }`}
                                        >
                                            <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--color-primary)]' : ''}`} />
                                            <span>{item.label}</span>
                                        </Link>
                                    );
                                })}
                            </nav>

                            {/* ── RIGHT: Level + Theme + User (desktop) ── */}
                            <div className="hidden md:flex items-center gap-2">
                                {/* XP Level Pill */}
                                {isAuthenticated && profile && (
                                    <Link
                                        href="/dashboard"
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r ${levelGradient}
                                                   text-white text-xs font-semibold shadow-md hover:shadow-lg transition-shadow group`}
                                        title={`${levelTitle} — ${profile.xp} XP`}
                                    >
                                        <Zap className="w-3.5 h-3.5" />
                                        <span>{profile.xp} XP</span>
                                        {/* Mini progress bar */}
                                        <div className="w-8 h-1 bg-white/25 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-white/80 rounded-full transition-all duration-500"
                                                style={{ width: `${Math.max(xpProgress, 8)}%` }}
                                            />
                                        </div>
                                    </Link>
                                )}

                                {/* Theme Toggle */}
                                <button
                                    onClick={toggleTheme}
                                    className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
                                    title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
                                >
                                    {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                </button>

                                {/* User Menu */}
                                {isAuthenticated && (
                                    <div className="relative">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setUserMenuOpen(!userMenuOpen); }}
                                            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
                                        >
                                            <div className="w-6 h-6 rounded-full bg-[var(--color-primary)]/20 flex items-center justify-center text-[var(--color-primary)]">
                                                <span className="text-[10px] font-bold">
                                                    {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                                                </span>
                                            </div>
                                            <ChevronDown className={`w-3 h-3 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
                                        </button>

                                        {/* Dropdown */}
                                        {userMenuOpen && (
                                            <div className="absolute right-0 top-full mt-2 w-48 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-2xl shadow-black/20 py-1.5 z-50">
                                                <div className="px-3 py-2 border-b border-[var(--color-border)]">
                                                    <div className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                                                        {user?.full_name || 'User'}
                                                    </div>
                                                    <div className="text-[10px] text-[var(--color-text-muted)] truncate">
                                                        {user?.email}
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => setShowInviteModal(true)}
                                                    className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-emerald-500 hover:bg-[var(--color-surface-elevated)] transition-colors"
                                                >
                                                    <Gift className="w-4 h-4" />
                                                    Invite Friends
                                                </button>
                                                <button
                                                    onClick={() => logout()}
                                                    className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-red-400 hover:bg-[var(--color-surface-elevated)] transition-colors"
                                                >
                                                    <LogOut className="w-4 h-4" />
                                                    Sign Out
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* ── MOBILE: Hamburger + XP ── */}
                            <div className="flex md:hidden items-center gap-2">
                                {isAuthenticated && profile && (
                                    <Link
                                        href="/dashboard"
                                        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r ${levelGradient}
                                                   text-white text-[10px] font-bold shadow-md`}
                                    >
                                        <Zap className="w-3 h-3" />
                                        {profile.xp} XP
                                    </Link>
                                )}
                                <button
                                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                    className="w-9 h-9 rounded-lg flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] transition-colors"
                                >
                                    {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* ── MOBILE: Slide-down menu ── */}
                    {mobileMenuOpen && (
                        <div className="md:hidden border-t border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur-xl animate-in slide-in-from-top-2 duration-200">
                            <nav className="px-4 py-3 space-y-1">
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
                                                    ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
                                                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)]'
                                                }`}
                                        >
                                            <Icon className={`w-5 h-5 ${isActive ? 'text-[var(--color-primary)]' : ''}`} />
                                            <span className={`text-sm ${isActive ? 'font-semibold' : 'font-medium'}`}>{item.label}</span>
                                        </Link>
                                    );
                                })}

                                {/* Mobile footer actions */}
                                <div className="border-t border-[var(--color-border)] pt-2 mt-2 flex items-center gap-2">
                                    <button
                                        onClick={toggleTheme}
                                        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] transition-colors flex-1"
                                    >
                                        {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                        <span className="text-sm">{theme === 'dark' ? 'Light' : 'Dark'}</span>
                                    </button>
                                    {isAuthenticated && (
                                        <>
                                            <button
                                                onClick={() => { setShowInviteModal(true); setMobileMenuOpen(false); }}
                                                className="flex items-center gap-2 px-3 py-2 rounded-xl text-emerald-500 hover:bg-emerald-500/10 transition-colors flex-1"
                                            >
                                                <Gift className="w-4 h-4" />
                                                <span className="text-sm">Invite</span>
                                            </button>
                                            <button
                                                onClick={() => logout()}
                                                className="flex items-center gap-2 px-3 py-2 rounded-xl text-red-400 hover:bg-red-500/10 transition-colors"
                                            >
                                                <LogOut className="w-4 h-4" />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </nav>
                        </div>
                    )}
                </header>

                {/* ═══════════════════════════════════════════════════════
                 * MAIN CONTENT — Below floating header
                 * ═══════════════════════════════════════════════════════ */}
                <main className="flex-1 min-w-0 overflow-hidden pt-14 md:pt-[56px]">
                    {children}
                </main>
            </div>
        </>
    );
}
