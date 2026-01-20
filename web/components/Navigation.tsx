"use client";

import { useState } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import LanguageToggle from './LanguageToggle';
import InvitationModal from './InvitationModal';
import { Menu, X, User, LogOut, Gift, PlusCircle, History } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navigation() {
    const { t } = useLanguage();
    const { user, isAuthenticated, logout } = useAuth();
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);

    // Reload page to start fresh session (simple way)
    const handleNewSession = () => {
        window.location.href = '/';
    };

    return (
        <>
            <nav className="absolute top-0 left-0 w-full z-50 p-6 md:p-8 flex justify-between items-center pointer-events-none">
                {/* Enable pointer events only for interactive elements */}
                <div className="flex items-center gap-3 pointer-events-auto">
                    <Link href="/" className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 flex items-center justify-center backdrop-blur-md">
                            <span className="material-symbols-outlined text-[var(--color-primary)] text-lg">hub</span>
                        </div>
                        <span className="text-xl font-display font-medium tracking-widest uppercase text-slate-800 dark:text-gray-200">
                            Osool<span className="text-[var(--color-primary)] font-bold">AI</span>
                        </span>
                    </Link>
                </div>

                <div className="flex items-center gap-3 md:gap-4 pointer-events-auto">
                    {/* Theme Toggle */}
                    <ThemeToggle />

                    {/* Authenticated Actions */}
                    {isAuthenticated ? (
                        <>
                            {/* Profile / History Button */}
                            <div className="relative">
                                <button
                                    onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                    className="px-5 py-2 rounded-full border border-slate-300 dark:border-white/10 text-sm hover:bg-white/5 transition text-slate-600 dark:text-slate-300 font-display tracking-wide backdrop-blur-sm bg-white/5 flex items-center gap-2"
                                >
                                    <User size={16} />
                                    <span className="hidden sm:inline">
                                        {user?.full_name?.split(' ')[0] || user?.email?.split('@')[0]}
                                    </span>
                                </button>

                                {/* Dropdown */}
                                <AnimatePresence>
                                    {isUserMenuOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                            className="absolute right-0 mt-2 w-56 rounded-xl bg-[var(--color-surface)] dark:bg-[var(--color-surface-dark)] border border-[var(--color-border)] shadow-xl overflow-hidden z-[60]"
                                        >
                                            <div className="p-2 space-y-1">
                                                <button
                                                    onClick={() => setInvitationModalOpen(true)}
                                                    className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-[var(--color-background-light)] dark:hover:bg-white/5 transition-colors text-green-600"
                                                >
                                                    <Gift size={16} />
                                                    Invite Friends
                                                </button>
                                                <Link href="/dashboard" className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-[var(--color-background-light)] dark:hover:bg-white/5 transition-colors text-[var(--color-text-primary)]">
                                                    <History size={16} />
                                                    History
                                                </Link>
                                                <div className="h-px bg-[var(--color-border)] my-1"></div>
                                                <button
                                                    onClick={() => logout()}
                                                    className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors text-red-500"
                                                >
                                                    <LogOut size={16} />
                                                    Sign Out
                                                </button>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* New Session Button */}
                            <button
                                onClick={handleNewSession}
                                className="px-5 py-2 rounded-full bg-slate-800 dark:bg-white/10 text-white dark:text-[var(--color-tertiary)] border border-transparent dark:border-[var(--color-tertiary)]/20 text-sm font-medium tracking-wide hover:bg-slate-700 dark:hover:bg-white/20 transition shadow-lg shadow-black/10 flex items-center gap-2 backdrop-blur-md"
                            >
                                <PlusCircle size={16} />
                                <span className="hidden sm:inline">New Session</span>
                            </button>
                        </>
                    ) : (
                        <Link
                            href="/login"
                            className="px-6 py-2 rounded-full bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary)]/90 transition shadow-lg shadow-[var(--color-primary)]/20 text-sm font-bold tracking-wide"
                        >
                            Sign In
                        </Link>
                    )}
                </div>
            </nav>

            <InvitationModal
                isOpen={isInvitationModalOpen}
                onClose={() => setInvitationModalOpen(false)}
            />
        </>
    );
}
