"use client";

import { useState } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from './ThemeToggle';
import LanguageToggle from './LanguageToggle';
import { Menu, X, User, LogOut } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navigation() {
    const { t } = useLanguage();
    const { user, isAuthenticated, logout } = useAuth();
    const [isMobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);

    const navLinks = [
        { href: '/', label: t('nav.home') },
        { href: '/ai-advisor', label: 'Chat with AMR' },
        { href: '/properties', label: t('nav.properties') },
    ];

    return (
        <header className="sticky top-0 z-50 backdrop-blur-xl bg-[var(--color-background)]/80 border-b border-[var(--color-border)]">
            <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-3 group">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] 
                            flex items-center justify-center text-white font-bold text-xl 
                            shadow-lg shadow-[var(--color-primary)]/20 
                            group-hover:shadow-[var(--color-primary)]/40 transition-shadow">
                            O
                        </div>
                        <span className="text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">
                            Osool
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
                                        {user?.full_name || user?.email?.split('@')[0] || 'User'}
                                    </span>
                                </button>

                                {/* Dropdown Menu */}
                                <AnimatePresence>
                                    {isUserMenuOpen && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 10 }}
                                            className="absolute right-0 mt-2 w-48 py-2 rounded-xl
                                 bg-[var(--color-surface-elevated)] border border-[var(--color-border)]
                                 shadow-xl"
                                        >
                                            <Link
                                                href="/dashboard"
                                                className="flex items-center gap-2 px-4 py-2 text-sm
                                   text-[var(--color-text-secondary)] hover:text-[var(--color-primary)]
                                   hover:bg-[var(--color-surface)] transition-colors"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                <User className="w-4 h-4" />
                                                {t('nav.dashboard')}
                                            </Link>
                                            <button
                                                onClick={() => {
                                                    logout();
                                                    setUserMenuOpen(false);
                                                }}
                                                className="flex items-center gap-2 w-full px-4 py-2 text-sm
                                   text-red-500 hover:bg-[var(--color-surface)] transition-colors"
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
        </header>
    );
}
