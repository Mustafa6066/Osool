'use client';

import React from 'react';

export interface SuggestionChipItem {
    icon?: React.ComponentType<{ className?: string }>;
    label: string;
    prompt: string;
    snippet?: string;
    snippetAr?: string;
    trend?: 'up' | 'down' | 'neutral';
}

interface SuggestionChipsProps {
    suggestions: Array<string | SuggestionChipItem>;
    onSelect: (suggestion: string) => void;
    isRTL?: boolean;
}

function isRichSuggestion(suggestion: string | SuggestionChipItem): suggestion is SuggestionChipItem {
    return typeof suggestion !== 'string';
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
                isRichSuggestion(suggestion) ? (
                    <button
                        key={`${suggestion.prompt}-${i}`}
                        onClick={() => onSelect(suggestion.prompt)}
                        className="group rounded-full border border-[var(--color-border)]/60 bg-[var(--color-surface)] px-3 py-1.5 text-start transition-colors hover:border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)]"
                    >
                        <div className="flex items-center gap-1.5">
                            {suggestion.icon && (
                                <suggestion.icon className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                            )}
                            <div className="min-w-0">
                                <div className="truncate text-[12px] font-medium text-[var(--color-text-secondary)] group-hover:text-[var(--color-text-primary)]" dir="auto">
                                    {suggestion.label}
                                </div>
                            </div>
                        </div>
                    </button>
                ) : (
                    <button
                        key={`${suggestion}-${i}`}
                        onClick={() => onSelect(suggestion)}
                        className="px-3 py-1.5 rounded-full text-[12px] font-medium
                             text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]
                             bg-[var(--color-surface)] border border-[var(--color-border)]/60
                             transition-colors"
                    >
                        <span className="truncate max-w-[180px]" dir="auto">{suggestion}</span>
                    </button>
                )
            ))}
        </div>
    );
}
