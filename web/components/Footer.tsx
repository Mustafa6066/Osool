"use client";

import { useLanguage } from '@/contexts/LanguageContext';
import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export default function Footer() {
    const { t, language } = useLanguage();

    const quickLinks = [
        { href: '/', label: t('nav.home') },
        { href: '/ai-advisor', label: 'Chat with AMR' },
        { href: '/properties', label: t('nav.properties') },
    ];

    const legalLinks = [
        { href: '/privacy', label: t('footer.privacy') },
        { href: '/terms', label: t('footer.terms') },
        { href: '/contact', label: t('footer.contact') },
    ];

    return (
        <footer className="bg-[var(--color-surface)] border-t border-[var(--color-border)]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Main Footer */}
                <div className="py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div className="md:col-span-2">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center text-white font-bold text-xl">
                                O
                            </div>
                            <span className="text-2xl font-bold text-[var(--color-text-primary)]">Osool</span>
                        </div>
                        <p className="text-[var(--color-text-secondary)] mb-6 max-w-sm">
                            {t('footer.tagline')}
                        </p>

                        {/* AI Badge */}
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/20 to-indigo-500/20 border border-purple-500/30">
                            <Sparkles className="w-4 h-4 text-purple-400" />
                            <span className="text-sm font-medium text-purple-300">{t('footer.poweredBy')}</span>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h4 className="text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider mb-4">
                            {t('footer.quickLinks')}
                        </h4>
                        <ul className="space-y-3">
                            {quickLinks.map((link) => (
                                <li key={link.href}>
                                    <Link
                                        href={link.href}
                                        className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
                                    >
                                        {link.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Legal */}
                    <div>
                        <h4 className="text-sm font-semibold text-[var(--color-text-primary)] uppercase tracking-wider mb-4">
                            {t('footer.legal')}
                        </h4>
                        <ul className="space-y-3">
                            {legalLinks.map((link) => (
                                <li key={link.href}>
                                    <Link
                                        href={link.href}
                                        className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors"
                                    >
                                        {link.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="py-6 border-t border-[var(--color-border)] flex flex-col sm:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-[var(--color-text-muted)]">
                        © {new Date().getFullYear()} Osool. All rights reserved.
                    </p>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        {t('footer.compliance')}
                    </p>
                </div>
            </div>
        </footer>
    );
}
