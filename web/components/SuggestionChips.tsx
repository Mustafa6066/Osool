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
            className={`flex flex-wrap gap-1.5 mt-3 ${isRTL ? 'flex-row-reverse' : ''}`}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {suggestions.map((suggestion, i) => (
                <button
                    key={i}
                    onClick={() => onSelect(suggestion)}
                    className="px-3.5 py-1.5 rounded-lg text-[13px]
                             text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]
                             bg-[var(--color-surface)] hover:bg-[var(--color-surface-elevated)]
                             border border-[var(--color-border)] hover:border-[var(--color-text-muted)]/20
                             transition-all duration-150"
                >
                    <span className="truncate max-w-[200px]" dir="auto">{suggestion}</span>
                </button>
            ))}
        </div>
    );
}
