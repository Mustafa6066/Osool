import React from 'react';
import { User, Sparkles, Check, Copy, RotateCcw, BarChart3, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import VisualizationRenderer from '../visualizations/VisualizationRenderer';
import PropertyCardEnhanced from './PropertyCardEnhanced';
import { PropertyContext, UIActionData } from './ContextualPane';

// Types
export type UIAction = {
    type: string;
    priority: number;
    data: any;
    trigger_reason?: string;
    chart_reference?: string;
};

export type Property = {
    id: number;
    title: string;
    price: number;
    location: string;
    size_sqm: number;
    bedrooms: number;
    wolf_score?: number;
    developer?: string;
    [key: string]: any;
};

export type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    visualizations?: UIAction[];
    properties?: Property[];
    timestamp?: Date;
    copied?: boolean;
};

// Detect if text is Arabic
export function isArabic(text: string): boolean {
    const arabicPattern = /[\u0600-\u06FF\u0750-\u077F]/;
    return arabicPattern.test(text);
}

// Format price
export const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M EGP`;
    }
    return `${(price / 1_000).toFixed(0)}K EGP`;
};

// User Message Component
export function UserMessage({ content, timestamp, isRTL }: { content: string; timestamp?: Date; isRTL: boolean }) {
    const messageIsArabic = isArabic(content);

    return (
        <div className="chatgpt-message chatgpt-message-user">
            <div className="chatgpt-message-layout chatgpt-container">
                <div className="chatgpt-avatar chatgpt-avatar-user">
                    <User size={16} />
                </div>
                <div className="chatgpt-message-content" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>
                </div>
            </div>
        </div>
    );
}

// AI Message Component
export function AIMessage({
    content,
    properties,
    visualizations,
    timestamp,
    isStreaming = false,
    onCopy,
    copied,
    onRegenerate,
    isRTL,
    onPropertySelect
}: {
    content: string;
    properties?: Property[];
    visualizations?: UIAction[];
    timestamp?: Date;
    isStreaming?: boolean;
    onCopy?: () => void;
    copied?: boolean;
    onRegenerate?: () => void;
    isRTL: boolean;
    onPropertySelect?: (property: Property, uiActions?: UIAction[]) => void;
}) {
    const messageIsArabic = isArabic(content);

    return (
        <div className="chatgpt-message chatgpt-message-ai">
            <div className="chatgpt-message-layout chatgpt-container">
                <div className="chatgpt-avatar chatgpt-avatar-ai">
                    <Sparkles size={16} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="chatgpt-message-content markdown-content" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                strong: ({ children }) => <strong className="font-bold text-[var(--color-text)]">{children}</strong>,
                                ul: ({ children }) => <ul className={`list-disc list-inside mb-3 space-y-1 ${messageIsArabic ? 'pr-2' : 'pl-2'}`}>{children}</ul>,
                                ol: ({ children }) => <ol className={`list-decimal list-inside mb-3 space-y-1 ${messageIsArabic ? 'pr-2' : 'pl-2'}`}>{children}</ol>,
                                li: ({ children }) => <li className="text-[var(--color-text-secondary)]">{children}</li>,
                                h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4 text-[var(--color-text)]">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 text-[var(--color-text)]">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-base font-semibold mb-2 mt-2">{children}</h3>,
                                code: ({ node, inline, className, children, ...props }: any) => {
                                    return (
                                        <code className={`${className} bg-[var(--color-surface-hover)] px-1 py-0.5 rounded text-sm font-mono`} {...props}>
                                            {children}
                                        </code>
                                    );
                                },
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                        {isStreaming && <span className="chatgpt-cursor" />}
                    </div>

                    {/* Visualizations */}
                    {visualizations && visualizations.length > 0 && !isStreaming && (
                        <div className="mt-4 space-y-4 animate-in fade-in duration-500 delay-150">
                            <div className={`flex items-center gap-2 text-sm font-medium text-[var(--color-text-muted)] ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                                <BarChart3 size={16} />
                                <span>{isRTL ? 'التحليلات' : 'Analytics'}</span>
                            </div>
                            <div className="grid gap-3">
                                {visualizations.map((viz, index) => (
                                    <div
                                        key={`${viz.type}-${index}`}
                                        className="rounded-xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)]"
                                    >
                                        {viz.chart_reference && (
                                            <div className={`px-4 py-2 bg-[var(--chatgpt-hover-bg)] border-b border-[var(--color-border)] ${messageIsArabic ? 'text-right' : 'text-left'}`}>
                                                <p className="text-xs text-[var(--color-text-muted)] font-medium flex items-center gap-2">
                                                    <TrendingUp size={12} />
                                                    {viz.chart_reference}
                                                </p>
                                            </div>
                                        )}
                                        <div className="p-2">
                                            <VisualizationRenderer
                                                type={viz.type}
                                                data={viz.data}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Property Cards */}
                    {properties && properties.length > 0 && !isStreaming && (
                        <div className="mt-4 space-y-3 animate-in slide-in-from-bottom-2 duration-500 delay-300">
                            {properties.map((prop) => (
                                <div
                                    key={prop.id}
                                    onClick={() => onPropertySelect?.(prop, visualizations)}
                                    className="cursor-pointer transition-transform hover:scale-[1.01]"
                                >
                                    <PropertyCardEnhanced
                                        property={{
                                            id: String(prop.id),
                                            title: prop.title,
                                            address: prop.location,
                                            price: formatPrice(prop.price),
                                            bedrooms: prop.bedrooms,
                                            bathrooms: 2,
                                            sqft: prop.size_sqm,
                                            rating: prop.wolf_score ? prop.wolf_score / 10 : undefined,
                                            badge: prop.developer,
                                            growthBadge: prop.wolf_score && prop.wolf_score >= 80 ? (isRTL ? 'نمو مرتفع' : 'High Growth') : undefined,
                                        }}
                                    />
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Message Actions */}
                    {!isStreaming && (
                        <div className={`chatgpt-message-actions ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                            {onCopy && (
                                <button onClick={onCopy} className="chatgpt-action-btn" title={isRTL ? 'نسخ' : 'Copy'}>
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                            )}
                            {onRegenerate && (
                                <button onClick={onRegenerate} className="chatgpt-action-btn" title={isRTL ? 'إعادة التوليد' : 'Regenerate'}>
                                    <RotateCcw size={14} />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
