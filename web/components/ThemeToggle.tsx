"use client";

import { useTheme } from '@/contexts/ThemeContext';

export default function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="p-2 rounded-full border border-slate-300 dark:border-white/10 hover:bg-white/5 transition-colors text-slate-500 dark:text-slate-400 flex items-center justify-center"
            aria-label="Toggle Dark Mode"
        >
            <span className="material-symbols-outlined text-xl">
                {theme === 'dark' ? 'light_mode' : 'dark_mode'}
            </span>
        </button>
    );
}
