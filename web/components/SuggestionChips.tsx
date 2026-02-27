'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

interface SuggestionChipsProps {
    suggestions: string[];
    onSelect: (suggestion: string) => void;
    isRTL?: boolean;
}

/**
 * Suggestion Chips - Contextual follow-up suggestions
 * Rendered below each AI response as clickable pills.
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
                             hover:border-teal-500/50 text-sm text-[var(--color-text-secondary)]
                             hover:text-[var(--color-text-primary)]
                             transition-all duration-200 hover:shadow-lg hover:shadow-teal-900/10
                             transform hover:-translate-y-0.5"
                >
                    <Sparkles className="w-3 h-3 text-teal-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="truncate max-w-[200px]" dir="auto">{suggestion}</span>
                </button>
            ))}
        </div>
    );
}
