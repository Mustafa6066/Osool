'use client';

import Link from 'next/link';
import { Home, MessageSquare, BarChart3, Plus, TrendingUp } from 'lucide-react';

interface SidebarProps {
    onNewChat?: () => void;
    activePage?: 'dashboard' | 'chat' | 'market';
}

const Sidebar = ({ onNewChat, activePage = 'chat' }: SidebarProps) => {
    return (
        <aside className="hidden md:flex flex-col w-72 h-full border-r border-[var(--color-border)] bg-[var(--color-background)] flex-shrink-0 z-20">
            <div className="p-6 flex flex-col gap-1">
                <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                    <h1 className="text-[var(--color-text-primary)] text-xl font-bold tracking-tight">AMR Advisor</h1>
                </Link>
                <p className="text-[var(--color-text-muted)] text-xs">Real Estate Intelligence</p>
            </div>
            <div className="px-4 pb-4">
                {onNewChat ? (
                    <button
                        onClick={onNewChat}
                        className="flex w-full items-center gap-3 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text-primary)] text-sm transition-all"
                    >
                        <Plus size={16} />
                        <span>New chat</span>
                    </button>
                ) : (
                    <Link
                        href="/chat"
                        className="flex w-full items-center gap-3 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text-primary)] text-sm transition-all"
                    >
                        <Plus size={16} />
                        <span>New chat</span>
                    </Link>
                )}
            </div>

            <nav className="flex-1 overflow-y-auto px-4 space-y-1 scrollbar-hide">
                <p className="px-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2 mt-4">Platform</p>
                <Link
                    href="/"
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-colors group w-full"
                >
                    <Home size={18} />
                    <span className="text-sm">Home</span>
                </Link>
                <Link
                    href="/dashboard"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'dashboard'
                        ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)]'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]'
                        }`}
                >
                    <BarChart3 size={18} />
                    <span className="text-sm">Dashboard</span>
                </Link>
                <Link
                    href="/market"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'market'
                        ? 'bg-[var(--color-surface)] text-[var(--color-text-primary)]'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]'
                        }`}
                >
                    <TrendingUp size={18} />
                    <span className="text-sm">Market Analysis</span>
                </Link>
            </nav>
        </aside>
    );
};

export default Sidebar;
