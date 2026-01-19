'use client';

import Link from 'next/link';
import { Home, MessageSquare, BarChart3, Plus } from 'lucide-react';

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
            <nav className="flex-1 overflow-y-auto px-4 space-y-6 scrollbar-hide">
                <div className="space-y-1">
                    <p className="px-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Platform</p>
                    <Link
                        href="/dashboard"
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'dashboard'
                            ? 'text-[var(--color-text-primary)] bg-[var(--color-surface)]'
                            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]'
                            }`}
                    >
                        <Home size={20} className={activePage === 'dashboard' ? 'text-[var(--color-primary)] fill-current' : 'group-hover:text-[var(--color-primary)] transition-colors'} />
                        <span className="text-sm font-medium">Dashboard</span>
                    </Link>
                    <Link
                        href="/chat"
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'chat'
                            ? 'text-[var(--color-text-primary)] bg-[var(--color-surface)]'
                            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]'
                            }`}
                    >
                        <MessageSquare size={20} className={activePage === 'chat' ? 'text-[var(--color-primary)] fill-current' : 'group-hover:text-[var(--color-primary)] transition-colors'} />
                        <span className="text-sm font-medium">Active Chat</span>
                    </Link>
                    <Link
                        href="/market"
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'market'
                            ? 'text-[var(--color-text-primary)] bg-[var(--color-surface)]'
                            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)]'
                            }`}
                    >
                        <BarChart3 size={20} className={activePage === 'market' ? 'text-[var(--color-primary)] fill-current' : 'group-hover:text-[var(--color-primary)] transition-colors'} />
                        <span className="text-sm font-medium">Market Analysis</span>
                    </Link>
                </div>
            </nav>
            <div className="p-4 border-t border-[var(--color-border)]">
                {onNewChat ? (
                    <button
                        onClick={onNewChat}
                        className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] h-10 px-4 text-white text-sm font-bold transition-all shadow-lg shadow-[var(--color-primary)]/20"
                    >
                        <Plus size={18} />
                        <span>New Analysis</span>
                    </button>
                ) : (
                    <Link
                        href="/chat"
                        className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] h-10 px-4 text-white text-sm font-bold transition-all shadow-lg shadow-[var(--color-primary)]/20"
                    >
                        <Plus size={18} />
                        <span>New Analysis</span>
                    </Link>
                )}
            </div>
        </aside>
    );
};

export default Sidebar;
