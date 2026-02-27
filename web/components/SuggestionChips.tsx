'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestionChipsProps {
    suggestions: string[];
    onSelect: (suggestion: string) => void;
    isRTL?: boolean;
}

/**
 * Suggestion Chips V5 — B/W + Emerald
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
                    className="group flex items-center gap-1.5 px-4 py-2 rounded-full
                             bg-[var(--color-surface)] hover:bg-[var(--color-surface-elevated)]
                             border border-[var(--color-border)]
                             hover:border-emerald-500/30 text-sm text-[var(--color-text-secondary)]
                             hover:text-[var(--color-text-primary)]
                             transition-all duration-200 hover:shadow-sm
                             transform hover:-translate-y-0.5"
                >
                    <Sparkles className="w-3 h-3 text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="truncate max-w-[200px]" dir="auto">{suggestion}</span>
                </button>
            ))}
        </div>
    );
}
