'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Sparkles, Heart, TrendingUp, MessageCircle, Ticket, Moon, Sun, Globe, X } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';

interface Command {
    id: string;
    label: string;
    description?: string;
    icon: React.ElementType;
    action: () => void;
    keywords: string[];
}

export default function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);
    const router = useRouter();
    const { theme, toggleTheme } = useTheme();
    const { language, setLanguage } = useLanguage();

    const close = useCallback(() => {
        setOpen(false);
        setQuery('');
        setSelectedIndex(0);
    }, []);

    const commands: Command[] = [
        {
            id: 'chat',
            label: 'Open Advisor Chat',
            description: 'Ask CoInvestor anything about the Egyptian market',
            icon: Sparkles,
            action: () => { router.push('/chat'); close(); },
            keywords: ['chat', 'advisor', 'ask', 'ai', 'coinvestor'],
        },
        {
            id: 'favorites',
            label: 'Open Shortlist',
            description: 'View and compare your saved properties',
            icon: Heart,
            action: () => { router.push('/favorites'); close(); },
            keywords: ['favorites', 'shortlist', 'saved', 'properties', 'compare'],
        },
        {
            id: 'explore',
            label: 'Explore Market',
            description: 'Browse areas, developers, and live data',
            icon: TrendingUp,
            action: () => { router.push('/explore'); close(); },
            keywords: ['explore', 'market', 'areas', 'developers', 'browse'],
        },
        {
            id: 'dashboard',
            label: 'Go to Dashboard',
            description: 'Your investment workspace overview',
            icon: MessageCircle,
            action: () => { router.push('/dashboard'); close(); },
            keywords: ['dashboard', 'home', 'workspace'],
        },
        {
            id: 'tickets',
            label: 'Support Tickets',
            description: 'View or create support tickets',
            icon: Ticket,
            action: () => { router.push('/tickets'); close(); },
            keywords: ['tickets', 'support', 'help', 'issue'],
        },
        {
            id: 'theme',
            label: `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`,
            description: 'Toggle between light and dark theme',
            icon: theme === 'dark' ? Sun : Moon,
            action: () => { toggleTheme(); close(); },
            keywords: ['theme', 'dark', 'light', 'mode', 'toggle'],
        },
        {
            id: 'language',
            label: `Switch to ${language === 'en' ? 'Arabic' : 'English'}`,
            description: language === 'en' ? 'التبديل إلى العربية' : 'Switch to English',
            icon: Globe,
            action: () => { setLanguage(language === 'en' ? 'ar' : 'en'); close(); },
            keywords: ['language', 'arabic', 'english', 'عربي', 'translate'],
        },
        {
            id: 'search-chat',
            label: 'Search properties via chat...',
            description: 'Type a natural language query — opens the advisor',
            icon: Search,
            action: () => {
                if (query.trim()) {
                    router.push(`/chat?q=${encodeURIComponent(query.trim())}`);
                } else {
                    router.push('/chat');
                }
                close();
            },
            keywords: ['search', 'properties', 'find', 'query', 'natural'],
        },
    ];

    const filtered = query.trim()
        ? commands.filter((cmd) => {
            const q = query.toLowerCase();
            return (
                cmd.label.toLowerCase().includes(q) ||
                (cmd.description?.toLowerCase().includes(q)) ||
                cmd.keywords.some((k) => k.includes(q))
            );
        })
        : commands;

    // Global keyboard shortcut
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setOpen((prev) => !prev);
            }
            if (e.key === 'Escape' && open) {
                e.preventDefault();
                close();
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [open, close]);

    // Focus input when opened
    useEffect(() => {
        if (open) {
            requestAnimationFrame(() => inputRef.current?.focus());
        }
    }, [open]);

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex((prev) => (prev + 1) % filtered.length);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex((prev) => (prev - 1 + filtered.length) % filtered.length);
        } else if (e.key === 'Enter' && filtered[selectedIndex]) {
            e.preventDefault();
            filtered[selectedIndex].action();
        }
    };

    // Reset selection when query changes
    useEffect(() => {
        setSelectedIndex(0);
    }, [query]);

    // Scroll selected into view
    useEffect(() => {
        if (listRef.current) {
            const selected = listRef.current.children[selectedIndex] as HTMLElement | undefined;
            selected?.scrollIntoView({ block: 'nearest' });
        }
    }, [selectedIndex]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-[15vh]" onClick={close}>
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

            {/* Palette */}
            <div
                className="relative w-full max-w-lg rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="flex items-center gap-3 border-b border-[var(--color-border)] px-4 py-3">
                    <Search className="h-5 w-5 text-[var(--color-text-muted)]" />
                    <input
                        ref={inputRef}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a command or search..."
                        className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
                    />
                    <kbd className="hidden rounded-md border border-[var(--color-border)] bg-[var(--color-background)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)] sm:inline">
                        ESC
                    </kbd>
                </div>

                {/* Results */}
                <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
                    {filtered.length === 0 ? (
                        <div className="px-4 py-8 text-center text-sm text-[var(--color-text-muted)]">
                            No commands found. Press Enter to search in chat.
                        </div>
                    ) : (
                        filtered.map((cmd, i) => {
                            const Icon = cmd.icon;
                            return (
                                <button
                                    key={cmd.id}
                                    onClick={cmd.action}
                                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${
                                        i === selectedIndex
                                            ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                            : 'text-[var(--color-text-primary)] hover:bg-[var(--color-background)]'
                                    }`}
                                >
                                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                                        i === selectedIndex ? 'bg-emerald-500/20' : 'bg-[var(--color-background)]'
                                    }`}>
                                        <Icon className="h-4 w-4" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="text-sm font-medium">{cmd.label}</div>
                                        {cmd.description && (
                                            <div className="truncate text-xs text-[var(--color-text-muted)]">{cmd.description}</div>
                                        )}
                                    </div>
                                </button>
                            );
                        })
                    )}
                </div>

                {/* Footer hint */}
                <div className="border-t border-[var(--color-border)] px-4 py-2 text-[10px] text-[var(--color-text-muted)]">
                    <span className="inline-flex items-center gap-1">
                        <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↑</kbd>
                        <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↓</kbd>
                        navigate
                    </span>
                    <span className="ml-3 inline-flex items-center gap-1">
                        <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↵</kbd>
                        select
                    </span>
                    <span className="ml-3 inline-flex items-center gap-1">
                        <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">esc</kbd>
                        close
                    </span>
                </div>
            </div>
        </div>
    );
}
