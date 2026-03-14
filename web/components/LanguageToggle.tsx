"use client";

import { useLanguage } from '@/contexts/LanguageContext';
import { motion } from 'framer-motion';

export default function LanguageToggle() {
    const { language, toggleLanguage } = useLanguage();

    return (
        <button
            onClick={toggleLanguage}
            className="relative flex items-center gap-1.5 px-3 py-2 rounded-lg
                 bg-[var(--color-surface)] border border-[var(--color-border)]
                 hover:border-[var(--color-primary)] transition-colors duration-300
                 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2"
            aria-label={`Switch to ${language === 'en' ? 'Arabic' : 'English'}`}
        >
            <div className="flex items-center gap-1.5">
                <motion.span
                    className={`text-sm font-semibold transition-colors ${language === 'en'
                            ? 'text-[var(--color-primary)]'
                            : 'text-[var(--color-text-muted)]'
                        }`}
                    animate={{ scale: language === 'en' ? 1.05 : 1 }}
                >
                    EN
                </motion.span>
                <span className="text-[var(--color-border)]">/</span>
                <motion.span
                    className={`text-sm font-semibold transition-colors ${language === 'ar'
                            ? 'text-[var(--color-primary)]'
                            : 'text-[var(--color-text-muted)]'
                        }`}
                    animate={{ scale: language === 'ar' ? 1.05 : 1 }}
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    عربي
                </motion.span>
            </div>
        </button>
    );
}
