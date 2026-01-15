"use client";

import { useTheme } from '@/contexts/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="relative w-10 h-10 rounded-lg flex items-center justify-center
                 bg-[var(--color-surface)] border border-[var(--color-border)]
                 hover:border-[var(--color-primary)] transition-colors duration-300
                 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
            <motion.div
                initial={false}
                animate={{ rotate: theme === 'dark' ? 0 : 180, scale: 1 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
            >
                {theme === 'dark' ? (
                    <Moon className="w-5 h-5 text-[var(--color-text-secondary)]" />
                ) : (
                    <Sun className="w-5 h-5 text-amber-500" />
                )}
            </motion.div>
        </button>
    );
}
