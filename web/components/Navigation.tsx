"use client";

import { useState } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import LanguageToggle from './LanguageToggle';
import InvitationModal from './InvitationModal';
import { Menu, X, User, LogOut, Gift } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navigation() {
    const { t } = useLanguage();
    const { user, isAuthenticated, logout } = useAuth();
    const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);

    const navLinks = [
        { href: '/', label: t('nav.home') },
        { href: '/ai-advisor', label: 'Chat with AMR' },
        { href: '/properties', label: t('nav.properties') },
    ];

    return (
        <>
            <header className="sticky top-0 z-50 backdrop-blur-xl bg-[var(--color-background)]/80 border-b border-[var(--color-border)]">
                <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Logo */}
                        <Link href="/" className="flex items-center gap-3 group">
                            <div className="w-10 h-10 rounded-full border border-[var(--color-primary)]/30 bg-[var(--color-primary)]/10 flex items-center justify-center backdrop-blur-md">
                                <span className="material-symbols-outlined text-[var(--color-primary)] text-lg">hub</span>
                            </div>
                            <span className="text-xl font-display font-medium tracking-widest uppercase text-[var(--color-text-primary)]">
                                Osool<span className="text-[var(--color-primary)] font-bold">AI</span>
                            </span>
                        </Link>

                        {/* Desktop Navigation */}
                        <div className="hidden md:flex items-center gap-8">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.href}
                                    href={link.href}
                                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] 
                               font-medium transition-colors duration-200"
                                >
                                    {link.label}
                                </Link>
                            ))}
                        </div>

                        {/* Right Side Actions */}
                        <div className="flex items-center gap-3">
                            {/* Theme & Language Toggles */}
                            <div className="hidden sm:flex items-center gap-2">
                                <LanguageToggle />
                                <ThemeToggle />
                            </div>

                            {/* User Menu / Sign In */}
                            {isAuthenticated ? (
                                <div className="relative">
                                    <button
                                        onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                        className="flex items-center gap-2 px-3 py-2 rounded-lg
                                 bg-[var(--color-surface)] border border-[var(--color-border)]
                                 hover:border-[var(--color-primary)] transition-colors"
                                    >
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)]
                                      flex items-center justify-center text-white font-semibold text-sm">
                                            {user?.full_name?.[0] || user?.email?.[0] || 'U'}
                                        </div>
                                        <span className="hidden lg:block text-sm font-medium text-[var(--color-text-primary)]">
                                            {(() => {
                                                const email = user?.email?.toLowerCase();
                                                if (email === 'mustafa@osool.eg') return 'Mustafa';
                                                if (email === 'hani@osool.eg') return 'Hani';
                                                if (email === 'abady@osool.eg') return 'Abady';
                                                if (email === 'sama@osool.eg') return 'Mrs. Mustafa';
                                                return user?.full_name || user?.email?.split('@')[0] || 'User';
                                            })()}
                                        </span>
                                    </button>

                                    {/* Dropdown Menu */}
                                    <AnimatePresence>
                                        {isUserMenuOpen && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: 10 }}
                                                className="absolute right-0 mt-2 w-56 py-2 rounded-xl
                                     bg-[var(--color-surface-elevated)] border border-[var(--color-border)]
                                     shadow-xl overflow-hidden z-50"
                                            >
                                                <div className="px-4 py-2 border-b border-[var(--color-border)] mb-1">
                                                    <p className="text-xs text-[var(--color-text-muted)]">Signed in as</p>
                                                    <p className="text-sm font-semibold truncate">{user?.email}</p>
                                                </div>

                                                <button
                                                    onClick={() => {
                                                        setInvitationModalOpen(true);
                                                        setUserMenuOpen(false);
                                                    }}
                                                    className="flex items-center gap-2 w-full px-4 py-2.5 text-sm
                                       text-green-600 hover:bg-green-50 dark:hover:bg-green-900/10 transition-colors font-medium"
                                                >
                                                    <Gift className="w-4 h-4" />
                                                    Generate Invitation Link
                                                </button>

                                                <Link
                                                    href="/dashboard"
                                                    className="flex items-center gap-2 px-4 py-2.5 text-sm
                                       text-[var(--color-text-secondary)] hover:text-[var(--color-primary)]
                                       hover:bg-[var(--color-surface)] transition-colors"
                                                    onClick={() => setUserMenuOpen(false)}
                                                >
                                                    <User className="w-4 h-4" />
                                                    {t('nav.dashboard')}
                                                </Link>

                                                <div className="border-t border-[var(--color-border)] my-1"></div>

                                                <button
                                                    onClick={() => {
                                                        logout();
                                                        setUserMenuOpen(false);
                                                    }}
                                                    className="flex items-center gap-2 w-full px-4 py-2.5 text-sm
                                       text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors"
                                                >
                                                    <LogOut className="w-4 h-4" />
                                                    {t('nav.signOut')}
                                                </button>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            ) : (
                                <Link
                                    href="/login"
                                    className="px-4 py-2 rounded-lg font-semibold text-sm
                               bg-[var(--color-primary)] text-white
                               hover:bg-[var(--color-primary-hover)] transition-colors"
                                >
                                    {t('nav.signIn')}
                                </Link>
                            )}

                            {/* Mobile Menu Button */}
                            <button
                                onClick={() => setMobileMenuOpen(!isMobileMenuOpen)}
                                className="md:hidden p-2 rounded-lg text-[var(--color-text-secondary)]
                             hover:bg-[var(--color-surface)] transition-colors"
                                aria-label="Toggle menu"
                            >
                                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                            </button>
                        </div>
                    </div>

                    {/* Mobile Menu */}
                    <AnimatePresence>
                        {isMobileMenuOpen && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="md:hidden border-t border-[var(--color-border)] py-4"
                            >
                                <div className="flex flex-col gap-2">
                                    {navLinks.map((link) => (
                                        <Link
                                            key={link.href}
                                            href={link.href}
                                            className="px-4 py-3 rounded-lg text-[var(--color-text-secondary)] 
                                   hover:text-[var(--color-primary)] hover:bg-[var(--color-surface)]
                                   font-medium transition-colors"
                                            onClick={() => setMobileMenuOpen(false)}
                                        >
                                            {link.label}
                                        </Link>
                                    ))}

                                    {isAuthenticated && (
                                        <button
                                            onClick={() => {
                                                setInvitationModalOpen(true);
                                                setMobileMenuOpen(false);
                                            }}
                                            className="px-4 py-3 rounded-lg text-green-600 
                                            hover:bg-green-50 dark:hover:bg-green-900/10
                                            font-medium transition-colors text-left flex items-center gap-2"
                                        >
                                            <Gift className="w-4 h-4" />
                                            Generate Invitation Link
                                        </button>
                                    )}

                                    {/* Mobile Theme & Language */}
                                    <div className="flex items-center gap-2 px-4 pt-4 border-t border-[var(--color-border)] mt-2">
                                        <LanguageToggle />
                                        <ThemeToggle />
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </nav>
            </header >

            {/* Invitation Modal */}
            < InvitationModal
                isOpen={isInvitationModalOpen}
                onClose={() => setInvitationModalOpen(false)
                }
            />
        </>
    );
}
