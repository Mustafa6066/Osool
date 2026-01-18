"use client";

import { useTheme } from '@/contexts/ThemeContext';
import { Sun, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <motion.button
            onClick={toggleTheme}
            whileTap={{ scale: 0.95 }}
            className="relative w-10 h-10 rounded-xl flex items-center justify-center
                 bg-[var(--color-surface-elevated)] border border-[var(--color-border)]
                 hover:border-[var(--color-primary)] transition-all duration-300
                 focus:outline-none focus-ring overflow-hidden group"
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
            {/* Background glow effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-amber-400/0 to-purple-500/0 
                          group-hover:from-amber-400/10 group-hover:to-purple-500/10 
                          transition-all duration-500" />

            <AnimatePresence mode="wait">
                {theme === 'dark' ? (
                    <motion.div
                        key="moon"
                        initial={{ rotate: -90, scale: 0, opacity: 0 }}
                        animate={{ rotate: 0, scale: 1, opacity: 1 }}
                        exit={{ rotate: 90, scale: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                        <Moon className="w-5 h-5 text-purple-400" />
                    </motion.div>
                ) : (
                    <motion.div
                        key="sun"
                        initial={{ rotate: 90, scale: 0, opacity: 0 }}
                        animate={{ rotate: 0, scale: 1, opacity: 1 }}
                        exit={{ rotate: -90, scale: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                        <Sun className="w-5 h-5 text-amber-500" />
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.button>
    );
}
