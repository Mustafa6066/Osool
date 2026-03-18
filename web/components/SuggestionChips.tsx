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
            className={`flex flex-wrap gap-2 mt-4 ${isRTL ? 'flex-row-reverse' : ''}`}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {suggestions.map((suggestion, i) => (
                isRichSuggestion(suggestion) ? (
                    <button
                        key={`${suggestion.prompt}-${i}`}
                        onClick={() => onSelect(suggestion.prompt)}
                        className="group min-w-[180px] max-w-[260px] rounded-2xl border border-[var(--color-border)]/50 bg-[var(--color-surface)]/70 px-3.5 py-3 text-start shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-500/30 hover:shadow-[0_10px_24px_rgba(16,185,129,0.08)]"
                    >
                        <div className="flex items-start gap-2.5">
                            {suggestion.icon && (
                                <div className="mt-0.5 rounded-xl bg-emerald-500/10 p-2 text-emerald-600 dark:text-emerald-400">
                                    <suggestion.icon className="h-3.5 w-3.5" />
                                </div>
                            )}
                            <div className="min-w-0 flex-1">
                                <div className="truncate text-[13px] font-semibold text-[var(--color-text-primary)]" dir="auto">
                                    {suggestion.label}
                                </div>
                                {(suggestion.snippet || suggestion.snippetAr) && (
                                    <div
                                        className={`mt-1.5 truncate text-[11px] font-medium ${
                                            suggestion.trend === 'up'
                                                ? 'text-emerald-600 dark:text-emerald-400'
                                                : suggestion.trend === 'down'
                                                    ? 'text-rose-500'
                                                    : 'text-[var(--color-text-muted)]'
                                        }`}
                                        dir="auto"
                                    >
                                        {isRTL ? suggestion.snippetAr || suggestion.snippet : suggestion.snippet || suggestion.snippetAr}
                                    </div>
                                )}
                            </div>
                        </div>
                    </button>
                ) : (
                    <button
                        key={`${suggestion}-${i}`}
                        onClick={() => onSelect(suggestion)}
                        className="px-4 py-2 rounded-full text-[13px] font-medium
                             text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]
                             bg-gray-50/50 hover:bg-gray-100 dark:bg-gray-800/30 dark:hover:bg-gray-800/80
                             border border-[var(--color-border)]/50 hover:border-[var(--color-border)]
                             hover:shadow-sm transition-all duration-200"
                    >
                        <span className="truncate max-w-[200px]" dir="auto">{suggestion}</span>
                    </button>
                )
            ))}
        </div>
    );
}
