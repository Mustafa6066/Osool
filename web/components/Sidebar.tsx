'use client';

import Link from 'next/link';
import ThemeToggle from '@/components/ThemeToggle';

// Utility for Material Symbols (matching ChatInterface)
const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => (
    <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>
        {name}
    </span>
);

interface SidebarProps {
    onNewChat?: () => void;
    activePage?: 'dashboard' | 'chat' | 'market';
}

const Sidebar = ({ onNewChat, activePage = 'chat' }: SidebarProps) => {
    return (
        <aside className="hidden md:flex flex-col w-[260px] h-full border-r border-[var(--color-border)] bg-[var(--color-surface-glass)] backdrop-blur-md flex-shrink-0 z-20 transition-all">
            {/* Logo / Brand */}
            <div className="p-5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center text-white shadow-lg shadow-[var(--color-primary)]/20">
                    <MaterialIcon name="real_estate_agent" size="18px" />
                </div>
                <h1 className="text-[var(--color-text-primary)] text-sm font-bold tracking-tight">Osool<span className="font-light opacity-80">AI</span></h1>
            </div>

            {/* New Chat Action */}
            <div className="px-4 pb-2">
                <button
                    onClick={onNewChat}
                    className="flex w-full items-center gap-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] hover:border-[var(--color-primary)]/30 hover:shadow-md px-3 py-2.5 text-[var(--color-text-primary)] text-sm font-medium transition-all group"
                >
                    <div className="w-6 h-6 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)] flex items-center justify-center group-hover:bg-[var(--color-primary)] group-hover:text-white transition-colors">
                        <MaterialIcon name="add" size="16px" />
                    </div>
                    <span>New Inquiry</span>
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-1 scrollbar-hide">
                <p className="px-2 text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2 opacity-70">Workspace</p>

                <Link
                    href="/"
                    className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors group w-full"
                >
                    <MaterialIcon name="home" size="18px" className="group-hover:text-[var(--color-primary)] transition-colors" />
                    <span className="text-sm font-medium">Home</span>
                </Link>

                <Link
                    href="/dashboard"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'dashboard'
                        ? 'bg-[var(--color-primary)]/5 text-[var(--color-primary)] font-semibold'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                        }`}
                >
                    <MaterialIcon name="dashboard" size="18px" />
                    <span className="text-sm">Dashboard</span>
                </Link>

                <Link
                    href="/market"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group w-full ${activePage === 'market'
                        ? 'bg-[var(--color-primary)]/5 text-[var(--color-primary)] font-semibold'
                        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                        }`}
                >
                    <MaterialIcon name="trending_up" size="18px" />
                    <span className="text-sm">Market Analysis</span>
                </Link>

                {/* Tools Section (Simplified, no mock data) */}
                <div className="mt-6">
                    <p className="px-2 text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-2 opacity-70">Tools</p>
                    <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors group w-full">
                        <MaterialIcon name="calculate" size="18px" />
                        <span className="text-sm font-medium">ROI Calculator</span>
                    </Link>
                    <Link href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors group w-full">
                        <MaterialIcon name="description" size="18px" />
                        <span className="text-sm font-medium">Reports</span>
                    </Link>
                </div>
            </nav>

            {/* Footer / User Settings */}
            <div className="p-4 border-t border-[var(--color-border)]">
                <button className="flex items-center gap-3 w-full p-2 rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors">
                    <MaterialIcon name="settings" className="text-[var(--color-text-muted)]" />
                    <span className="text-sm font-medium text-[var(--color-text-secondary)]">Settings</span>
                </button>
                <div className="mt-2 pt-2 border-t border-[var(--color-border)]">
                    <ThemeToggle />
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
