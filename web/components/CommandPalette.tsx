'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Sparkles, Heart, TrendingUp, MessageCircle, Ticket, Moon, Sun, Globe, X, Terminal, Clock, ArrowUpRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
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

const RECENT_KEY = 'osool-recent-queries';
const MAX_RECENTS = 5;

function getRecentQueries(): string[] {
    if (typeof window === 'undefined') return [];
    try {
        const data = localStorage.getItem(RECENT_KEY);
        return data ? JSON.parse(data) : [];
    } catch { return []; }
}

function saveRecentQuery(q: string) {
    if (typeof window === 'undefined' || !q.trim()) return;
    try {
        const prev = getRecentQueries().filter((r) => r !== q.trim());
        const next = [q.trim(), ...prev].slice(0, MAX_RECENTS);
        localStorage.setItem(RECENT_KEY, JSON.stringify(next));
    } catch { /* noop */ }
}

export default function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [recents, setRecents] = useState<string[]>([]);
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

    // Load recents when palette opens
    useEffect(() => {
        if (open) setRecents(getRecentQueries());
    }, [open]);

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
            id: 'terminal',
            label: 'Open Terminal',
            description: 'Developer analysis & telemetry command center',
            icon: Terminal,
            action: () => { router.push('/terminal'); close(); },
            keywords: ['terminal', 'telemetry', 'developer', 'analysis', 'command'],
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
                    saveRecentQuery(query.trim());
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

    // AI fallback: if query doesn't match anything, show "Ask Osool" option
    const showAskOsool = query.trim().length > 0 && filtered.length === 0;
    const showAnalyze = query.trim().toLowerCase().startsWith('analyze ') && query.trim().length > 8;

    // Build the display list
    const displayItems: Command[] = [...filtered];
    if (showAnalyze) {
        const devName = query.trim().slice(8);
        displayItems.unshift({
            id: 'analyze-dev',
            label: `Analyze "${devName}"`,
            description: 'Open developer analysis in Terminal',
            icon: Terminal,
            action: () => {
                router.push(`/terminal?q=${encodeURIComponent(devName)}`);
                close();
            },
            keywords: [],
        });
    }
    if (showAskOsool) {
        displayItems.push({
            id: 'ask-osool',
            label: `Ask Osool: "${query.trim()}"`,
            description: 'Send to AI advisor for intelligent analysis',
            icon: Sparkles,
            action: () => {
                saveRecentQuery(query.trim());
                router.push(`/chat?q=${encodeURIComponent(query.trim())}`);
                close();
            },
            keywords: [],
        });
    }

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
            setSelectedIndex((prev) => (prev + 1) % displayItems.length);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex((prev) => (prev - 1 + displayItems.length) % displayItems.length);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (displayItems[selectedIndex]) {
                displayItems[selectedIndex].action();
            } else if (query.trim()) {
                // Fallback: send to chat as AI query
                saveRecentQuery(query.trim());
                router.push(`/chat?q=${encodeURIComponent(query.trim())}`);
                close();
            }
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
        <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-[12vh] sm:pt-[15vh]" onClick={close}>
            {/* Backdrop */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            />

            {/* Palette */}
            <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: 'spring', damping: 24, stiffness: 200 }}
                className="relative w-full max-w-lg rounded-2xl liquid-glass border border-[var(--color-border)] shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Search input */}
                <div className="flex items-center gap-3 border-b border-[var(--color-border)] px-4 py-3.5">
                    <Sparkles className="h-4 w-4 text-emerald-500 shrink-0" />
                    <input
                        ref={inputRef}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={language === 'ar' ? 'اكتب أمراً أو اسأل أصول...' : 'Type a command or ask Osool...'}
                        className="flex-1 bg-transparent text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
                    />
                    <kbd className="hidden rounded-lg border border-[var(--color-border)] bg-[var(--color-background)]/50 px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)] sm:inline">
                        ESC
                    </kbd>
                </div>

                {/* Recent queries (when no search query) */}
                {!query.trim() && recents.length > 0 && (
                    <div className="px-3 pt-2 pb-1">
                        <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] px-1 mb-1.5">
                            {language === 'ar' ? 'البحث الأخير' : 'Recent'}
                        </div>
                        <div className="flex flex-wrap gap-1.5 mb-1">
                            {recents.map((r) => (
                                <button
                                    key={r}
                                    onClick={() => {
                                        saveRecentQuery(r);
                                        router.push(`/chat?q=${encodeURIComponent(r)}`);
                                        close();
                                    }}
                                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] text-[var(--color-text-secondary)] bg-[var(--color-surface-elevated)]/60 hover:bg-emerald-500/10 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                                >
                                    <Clock className="w-3 h-3 opacity-50" />
                                    {r.length > 30 ? r.slice(0, 30) + '…' : r}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Results */}
                <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
                    {displayItems.length === 0 && !showAskOsool ? (
                        <div className="px-4 py-8 text-center text-sm text-[var(--color-text-muted)]">
                            {language === 'ar' ? 'لم يتم العثور على أوامر.' : 'No commands found.'}
                        </div>
                    ) : (
                        displayItems.map((cmd, i) => {
                            const Icon = cmd.icon;
                            const isAI = cmd.id === 'ask-osool' || cmd.id === 'analyze-dev';
                            return (
                                <button
                                    key={cmd.id}
                                    onClick={cmd.action}
                                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${
                                        i === selectedIndex
                                            ? isAI
                                                ? 'bg-gradient-to-r from-emerald-500/15 to-teal-500/10 text-emerald-600 dark:text-emerald-400'
                                                : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                                            : 'text-[var(--color-text-primary)] hover:bg-[var(--color-background)]'
                                    }`}
                                >
                                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                                        i === selectedIndex
                                            ? isAI
                                                ? 'bg-emerald-500/25'
                                                : 'bg-emerald-500/20'
                                            : 'bg-[var(--color-background)]'
                                    }`}>
                                        <Icon className="h-4 w-4" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="flex items-center gap-1.5 text-sm font-medium">
                                            {cmd.label}
                                            {isAI && <ArrowUpRight className="w-3 h-3 opacity-50" />}
                                        </div>
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
                <div className="border-t border-[var(--color-border)] px-4 py-2 text-[10px] text-[var(--color-text-muted)] flex items-center justify-between">
                    <div>
                        <span className="inline-flex items-center gap-1">
                            <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↑</kbd>
                            <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↓</kbd>
                            {language === 'ar' ? 'تنقل' : 'navigate'}
                        </span>
                        <span className="ml-3 inline-flex items-center gap-1">
                            <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">↵</kbd>
                            {language === 'ar' ? 'اختر' : 'select'}
                        </span>
                        <span className="ml-3 inline-flex items-center gap-1">
                            <kbd className="rounded border border-[var(--color-border)] px-1 py-0.5">esc</kbd>
                            {language === 'ar' ? 'إغلاق' : 'close'}
                        </span>
                    </div>
                    <span className="text-emerald-500/60 hidden sm:inline">
                        {language === 'ar' ? 'مدعوم بالذكاء الاصطناعي' : 'AI-powered'}
                    </span>
                </div>
            </motion.div>
        </div>
    );
}
