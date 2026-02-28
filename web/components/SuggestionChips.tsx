'use client';

import React from 'react';

interface SuggestionChipsProps {
    suggestions: string[];
    onSelect: (suggestion: string) => void;
    isRTL?: boolean;
}

/**
 * Suggestion Chips V6 — Minimal
 * Contextual follow-up suggestions rendered below each AI response.
 */
export default function SuggestionChips({ suggestions, onSelect, isRTL = false }: SuggestionChipsProps) {
    if (!suggestions || suggestions.length === 0) return null;

    return (
        <div
            className={`flex flex-wrap gap-2 mt-4 ${isRTL ? 'flex-row-reverse' : ''}`}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {suggestions.map((suggestion, i) => (
                <button
                    key={i}
                    onClick={() => onSelect(suggestion)}
                    className="px-4 py-2 rounded-full text-[13px] font-medium
                             text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]
                             bg-gray-50/50 hover:bg-gray-100 dark:bg-gray-800/30 dark:hover:bg-gray-800/80
                             border border-[var(--color-border)]/50 hover:border-[var(--color-border)]
                             hover:shadow-sm transition-all duration-200"
                >
                    <span className="truncate max-w-[200px]" dir="auto">{suggestion}</span>
                </button>
            ))}
        </div>
    );
}
