'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    MessageSquare, LayoutDashboard, TrendingUp, Building2,
    Heart, Award, LogOut, Sun, Moon, ChevronLeft, ChevronRight,
    User, Gift, Menu, X
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import { useTheme } from '@/contexts/ThemeContext';
import { LEVEL_COLORS, LEVEL_GRADIENTS } from '@/lib/gamification';
import InvitationModal from '@/components/InvitationModal';

// ═══════════════════════════════════════════════════════════════
// NAV ITEMS
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
    const [expanded, setExpanded] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);

    const levelGradient = profile ? (LEVEL_GRADIENTS[profile.level] || LEVEL_GRADIENTS.curious) : 'from-gray-500 to-gray-600';
    const levelColor = profile ? (LEVEL_COLORS[profile.level] || LEVEL_COLORS.curious) : '#6B7280';
    const levelTitle = profile?.level_title_en || 'Curious';
    const xpProgress = profile?.next_level
        ? Math.min(((profile.xp - (profile.next_level.xp_required - profile.next_level.xp_remaining)) / profile.next_level.xp_remaining) * 100, 100)
        : 100;

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

            <div className="flex h-screen w-screen overflow-hidden bg-[var(--color-background)]">
                {/* ═══════════════════════════════════════════════════════
                 * DESKTOP SIDE RAIL (hidden on mobile)
                 * ═══════════════════════════════════════════════════════ */}
                <aside
                    className={`hidden md:flex flex-col flex-shrink-0 h-full border-r border-[var(--color-border)]
                               bg-[var(--color-surface)]/95 backdrop-blur-md z-40
                               transition-all duration-300 ease-[var(--ease-out-expo)]
                               ${expanded ? 'w-[220px]' : 'w-[68px]'}`}
                    onMouseEnter={() => setExpanded(true)}
                    onMouseLeave={() => setExpanded(false)}
                >
                    {/* Logo */}
                    <div className={`flex items-center gap-3 px-4 h-16 flex-shrink-0 border-b border-[var(--color-border)] ${expanded ? '' : 'justify-center'}`}>
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[var(--color-primary)] to-teal-500 flex items-center justify-center text-white shadow-lg flex-shrink-0">
                            <Building2 className="w-5 h-5" />
                        </div>
                        {expanded && (
                            <span className="text-[var(--color-text-primary)] text-sm font-bold tracking-tight whitespace-nowrap overflow-hidden">
                                Osool<span className="font-light opacity-70">AI</span>
                            </span>
                        )}
                    </div>

                    {/* Nav Links */}
                    <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto scrollbar-hide">
                        {NAV_ITEMS.map((item) => {
                            const isActive = item.key === activeKey;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.key}
                                    href={item.href}
                                    className={`flex items-center gap-3 rounded-xl transition-all duration-200 group relative
                                               ${expanded ? 'px-3 py-2.5' : 'px-0 py-2.5 justify-center'}
                                               ${isActive
                                            ? 'bg-[var(--color-primary)]/10 text-[var(--color-primary)]'
                                            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                                        }`}
                                    title={!expanded ? item.label : undefined}
                                >
                                    {/* Active indicator bar */}
                                    {isActive && (
                                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-[var(--color-primary)]" />
                                    )}
                                    <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-[var(--color-primary)]' : ''}`} />
                                    {expanded && (
                                        <span className={`text-sm whitespace-nowrap overflow-hidden ${isActive ? 'font-semibold' : 'font-medium'}`}>
                                            {item.label}
                                        </span>
                                    )}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* Level Badge */}
                    {isAuthenticated && profile && (
                        <div className={`px-3 py-3 border-t border-[var(--color-border)] ${expanded ? '' : 'flex justify-center'}`}>
                            {expanded ? (
                                <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${levelGradient} flex items-center justify-center shadow-md flex-shrink-0`}>
                                        <Award className="w-4 h-4 text-white" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs font-semibold text-[var(--color-text-primary)] truncate">{levelTitle}</div>
                                        <div className="w-full h-1 bg-[var(--color-surface-elevated)] rounded-full mt-1">
                                            <div
                                                className={`h-full rounded-full bg-gradient-to-r ${levelGradient} transition-all duration-500`}
                                                style={{ width: `${Math.max(xpProgress, 5)}%` }}
                                            />
                                        </div>
                                        <div className="text-[9px] text-[var(--color-text-muted)] mt-0.5">{profile.xp} XP</div>
                                    </div>
                                </div>
                            ) : (
                                <div
                                    className={`w-8 h-8 rounded-lg bg-gradient-to-br ${levelGradient} flex items-center justify-center shadow-md`}
                                    title={`${levelTitle} — ${profile.xp} XP`}
                                >
                                    <Award className="w-4 h-4 text-white" />
                                </div>
                            )}
                        </div>
                    )}

                    {/* Bottom Actions */}
                    <div className={`px-3 py-3 border-t border-[var(--color-border)] space-y-1 ${expanded ? '' : 'flex flex-col items-center'}`}>
                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            className={`flex items-center gap-3 rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors
                                       ${expanded ? 'px-3 py-2 w-full' : 'p-2 justify-center'}`}
                            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
                        >
                            {theme === 'dark' ? <Sun className="w-4 h-4 flex-shrink-0" /> : <Moon className="w-4 h-4 flex-shrink-0" />}
                            {expanded && <span className="text-sm font-medium">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
                        </button>

                        {/* User Menu */}
                        {isAuthenticated && (
                            <>
                                <button
                                    onClick={() => setShowInviteModal(true)}
                                    className={`flex items-center gap-3 rounded-xl text-emerald-500 hover:bg-emerald-500/10 transition-colors
                                               ${expanded ? 'px-3 py-2 w-full' : 'p-2 justify-center'}`}
                                    title="Invite Friends"
                                >
                                    <Gift className="w-4 h-4 flex-shrink-0" />
                                    {expanded && <span className="text-sm font-medium">Invite</span>}
                                </button>

                                <button
                                    onClick={() => logout()}
                                    className={`flex items-center gap-3 rounded-xl text-red-400 hover:bg-red-500/10 transition-colors
                                               ${expanded ? 'px-3 py-2 w-full' : 'p-2 justify-center'}`}
                                    title="Sign Out"
                                >
                                    <LogOut className="w-4 h-4 flex-shrink-0" />
                                    {expanded && <span className="text-sm font-medium">Sign Out</span>}
                                </button>
                            </>
                        )}
                    </div>
                </aside>

                {/* ═══════════════════════════════════════════════════════
                 * MAIN CONTENT
                 * ═══════════════════════════════════════════════════════ */}
                <main className="flex-1 min-w-0 h-full overflow-hidden relative">
                    {children}
                </main>

                {/* ═══════════════════════════════════════════════════════
                 * MOBILE BOTTOM TAB BAR (hidden on desktop)
                 * ═══════════════════════════════════════════════════════ */}
                <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur-xl safe-area-bottom">
                    <nav className="flex items-center justify-around h-14 px-1">
                        {NAV_ITEMS.map((item) => {
                            const isActive = item.key === activeKey;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.key}
                                    href={item.href}
                                    className={`flex flex-col items-center justify-center gap-0.5 flex-1 py-1 rounded-lg transition-colors
                                               ${isActive
                                            ? 'text-[var(--color-primary)]'
                                            : 'text-[var(--color-text-muted)]'
                                        }`}
                                >
                                    <div className="relative">
                                        <Icon className={`w-5 h-5 ${isActive ? 'text-[var(--color-primary)]' : ''}`} />
                                        {isActive && (
                                            <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-teal-400" />
                                        )}
                                    </div>
                                    <span className={`text-[10px] ${isActive ? 'font-bold' : 'font-medium'}`}>
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                {/* Mobile Level Badge (floating top-right) */}
                {isAuthenticated && profile && (
                    <div className="md:hidden fixed top-3 right-3 z-50">
                        <Link
                            href="/dashboard"
                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r ${levelGradient}
                                       shadow-lg border border-white/20 backdrop-blur-md`}
                        >
                            <Award className="w-3 h-3 text-white" />
                            <span className="text-[10px] font-bold text-white">{profile.xp} XP</span>
                        </Link>
                    </div>
                )}
            </div>
        </>
    );
}
