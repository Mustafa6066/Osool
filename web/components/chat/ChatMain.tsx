'use client';

import { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Send, Loader2, Copy, Check, ChevronDown, Sparkles, Plus, BarChart3, RotateCcw, ThumbsUp, ThumbsDown, Square, AlertTriangle, RefreshCw, MessageCircle } from 'lucide-react';
import { type RecordingStatus } from '@/hooks/useVoiceRecording';
import { type Property } from '@/stores/useChatStore';
import {
    useChatEngine,
    isArabic,
    formatPrice,
    cleanMessageContent,
    getGreeting,
    SUGGESTION_CARDS,
} from '@/lib/chat-engine';
import VoiceOrb from '@/components/VoiceOrb';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import PropertyCardEnhanced from './PropertyCardEnhanced';
import { PropertyContext, UIActionData } from './ContextualPane';
import VisualizationRenderer from '../visualizations/VisualizationRenderer';
import WhatsAppHandoffModal from '../WhatsAppHandoffModal';
import { StatusDot } from '@/components/ui/primitives';

// Types
type UIAction = UIActionData;

// User Message Component - ChatGPT mobile style
function UserMessage({ content, timestamp, isRTL }: { content: string; timestamp?: Date; isRTL: boolean }) {
    const messageIsArabic = isArabic(content) || isRTL;

    return (
        <div className={`flex w-full mb-6 px-4 ${messageIsArabic ? 'justify-start' : 'justify-end'}`}>
            <div
                className="max-w-[85%] rounded-3xl bg-[var(--user-surface)] px-5 py-3 text-[15px] leading-relaxed text-[var(--user-surface-text)]"
                dir={messageIsArabic ? 'rtl' : 'ltr'}
            >
                {content}
            </div>
        </div>
    );
}

function CollapsibleVisualization({ viz, isRTL }: { viz: UIAction; isRTL: boolean }) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="overflow-hidden rounded-xl border border-[var(--color-border)]/50 bg-[var(--color-surface)]/60">
            <button
                onClick={() => setIsOpen((prev) => !prev)}
                className={`flex min-h-11 w-full items-center justify-between p-3 text-sm font-medium transition-colors hover:bg-[var(--chatgpt-hover-bg)] ${isRTL ? 'flex-row-reverse text-end' : 'text-start'}`}
                aria-expanded={isOpen}
            >
                <div className={`flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <BarChart3 size={16} className="text-emerald-600" />
                    <span>{viz.chart_reference || (isRTL ? 'عرض التحليل' : 'View Analysis')}</span>
                </div>
                <ChevronDown size={16} className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scaleY: 0.96 }}
                        animate={{ opacity: 1, scaleY: 1 }}
                        exit={{ opacity: 0, scaleY: 0.96 }}
                        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                        style={{ transformOrigin: 'top' }}
                        className="border-t border-[var(--color-border)]/50"
                    >
                        <div className="p-3 sm:p-4">
                            <VisualizationRenderer type={viz.type} data={viz.data} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// AI Message Component - ChatGPT mobile style (transparent response stream)
function AIMessage({
    content,
    properties,
    visualizations,
    timestamp,
    isStreaming = false,
    onCopy,
    copied,
    onRegenerate,
    isRTL,
    onPropertySelect,
    isError,
    onRetry,
    onFeedback,
    feedback,
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
    isError?: boolean;
    onRetry?: () => void;
    onFeedback?: (type: 'up' | 'down') => void;
    feedback?: 'up' | 'down' | null;
}) {
    const messageIsArabic = isArabic(content) || isRTL;

    // Error state UI
    if (isError) {
        return (
            <div className={`flex w-full mb-8 px-4 gap-4 ${messageIsArabic ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] mt-1">
                    <div className="chatgpt-avatar-ai flex h-6 w-6 items-center justify-center rounded-full">
                        <AlertTriangle size={16} className="text-amber-500" />
                    </div>
                </div>
                <div className="flex-1 min-w-0" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                            <p className={`text-sm text-[var(--color-text-secondary)] mb-3 ${messageIsArabic ? 'text-end' : 'text-start'}`}>
                                {content}
                            </p>
                            {onRetry && (
                                <button
                                    onClick={onRetry}
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-primary)]/10 hover:bg-[var(--color-primary)]/20 text-[var(--color-primary)] text-sm font-medium transition-colors"
                                >
                                    <RefreshCw size={14} />
                                    {messageIsArabic ? 'حاول مرة أخرى' : 'Try Again'}
                                </button>
                            )}
                        </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`flex w-full mb-8 px-4 gap-4 ${messageIsArabic ? 'flex-row-reverse' : 'flex-row'}`}>
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] mt-1">
                <Sparkles size={16} className="text-emerald-600" />
            </div>
            <div className="flex-1 min-w-0" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                <div className={`text-[15px] leading-relaxed text-[var(--color-text-primary)] prose prose-sm dark:prose-invert max-w-none prose-p:mt-0 prose-p:mb-4 prose-headings:mt-5 prose-headings:mb-2 prose-blockquote:border-s-2 prose-blockquote:ps-3 prose-blockquote:italic prose-blockquote:text-inherit prose-blockquote:bg-transparent prose-blockquote:rounded-none prose-strong:text-inherit ${messageIsArabic ? 'text-end prose-rtl' : 'text-start'}`}>
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            p: ({ node, ...props }) => <p className={`mb-4 last:mb-0 leading-relaxed ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                            ul: ({ node, ...props }) => <ul className={`list-disc mb-4 ${messageIsArabic ? 'pe-6' : 'ps-6'}`} {...props} />,
                            ol: ({ node, ...props }) => <ol className={`list-decimal mb-4 ${messageIsArabic ? 'pe-6' : 'ps-6'}`} {...props} />,
                            h1: ({ node, ...props }) => <h1 className={`text-xl font-semibold ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                            h2: ({ node, ...props }) => <h2 className={`text-lg font-semibold ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                            h3: ({ node, ...props }) => <h3 className={`text-base font-semibold ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                            a: ({ node, ...props }) => <a className="text-emerald-600 hover:underline dark:text-emerald-400" target="_blank" rel="noopener noreferrer" {...props} />,
                            table: ({ node, ...props }) => (
                                <div className="my-4 overflow-x-auto rounded-xl border border-[var(--color-border)]/40">
                                    <table className={`w-full border-collapse text-sm ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                                </div>
                            ),
                            thead: ({ node, ...props }) => <thead className="bg-[var(--color-surface)]/50" {...props} />,
                            th: ({ node, ...props }) => (
                                <th className={`border border-[var(--color-border)]/40 px-3 py-2 font-semibold ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                            ),
                            td: ({ node, ...props }) => (
                                <td className={`border border-[var(--color-border)]/40 px-3 py-2 text-[var(--color-text-secondary)] ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                            ),
                        }}
                    >
                        {cleanMessageContent(content)}
                    </ReactMarkdown>
                    {isStreaming && <span className={`inline-block w-2 h-4 bg-emerald-500 animate-pulse align-middle ${messageIsArabic ? 'mr-1' : 'ml-1'}`} />}
                </div>

                {/* Visualizations - Collapsible cards for mobile focus */}
                {visualizations && visualizations.length > 0 && !isStreaming && (
                    <div className="mt-4 flex flex-col gap-2">
                        {visualizations.map((viz, index) => (
                            <CollapsibleVisualization key={`${viz.type}-${index}`} viz={viz} isRTL={messageIsArabic} />
                        ))}
                    </div>
                )}

                {/* Properties - Horizontal carousel to avoid long vertical stacks */}
                {properties && properties.length > 0 && !isStreaming && (
                    <div className="mt-5 -mx-4 px-4 overflow-x-auto snap-x snap-mandatory flex gap-3 pb-4 hide-scrollbar">
                        {properties.map((prop) => (
                            <div
                                key={prop.id}
                                className="snap-center shrink-0 w-[280px] sm:w-[320px]"
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
                                    onSelect={() => onPropertySelect?.(prop, visualizations)}
                                />
                            </div>
                        ))}
                    </div>
                )}

                {/* Message Actions */}
                {!isStreaming && (
                    <div className="chatgpt-message-actions">
                        {onCopy && (
                            <button onClick={onCopy} className="chatgpt-action-btn">
                                {copied ? <Check size={14} /> : <Copy size={14} />}
                                <span>{copied ? (isRTL ? 'تم النسخ' : 'Copied') : (isRTL ? 'نسخ' : 'Copy')}</span>
                            </button>
                        )}
                        {onRegenerate && (
                            <button onClick={onRegenerate} className="chatgpt-action-btn">
                                <RotateCcw size={14} />
                                <span>{isRTL ? 'إعادة التوليد' : 'Regenerate'}</span>
                            </button>
                        )}
                        {onFeedback && (
                            <>
                                <button
                                    onClick={() => onFeedback('up')}
                                    className={`chatgpt-action-btn ${feedback === 'up' ? 'text-green-500' : ''}`}
                                    aria-label={isRTL ? 'إعجاب' : 'Thumbs up'}
                                >
                                    <ThumbsUp size={14} className={feedback === 'up' ? 'fill-current' : ''} />
                                </button>
                                <button
                                    onClick={() => onFeedback('down')}
                                    className={`chatgpt-action-btn ${feedback === 'down' ? 'text-red-500' : ''}`}
                                    aria-label={isRTL ? 'عدم إعجاب' : 'Thumbs down'}
                                >
                                    <ThumbsDown size={14} className={feedback === 'down' ? 'fill-current' : ''} />
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

// Typing Indicator - Simple dots
function TypingIndicator({ isRTL }: { isRTL: boolean }) {
    return (
        <div className="chatgpt-message chatgpt-message-ai">
            <div className="chatgpt-message-layout chatgpt-container">
                <div className="chatgpt-avatar chatgpt-avatar-ai">
                    <Sparkles size={16} className="animate-pulse" />
                </div>
                <div className="flex items-center gap-1 py-2">
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
            </div>
        </div>
    );
}

// Chat Input Component - ChatGPT Style with voice & stop
function ChatInput({
    value,
    onChange,
    onSend,
    onKeyDown,
    isTyping,
    inputRef,
    isRTL,
    onStop,
    onVoiceInput,
    isListening,
    voiceStatus = 'idle',
    amplitude = 0,
    transcriptHighlight = false,
}: {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
    onSend: () => void;
    onKeyDown: (e: React.KeyboardEvent) => void;
    isTyping: boolean;
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    isRTL: boolean;
    onStop?: () => void;
    onVoiceInput?: () => void;
    isListening?: boolean;
    voiceStatus?: RecordingStatus;
    amplitude?: number;
    transcriptHighlight?: boolean;
}) {
    return (
        <div className="chatgpt-input-area">
            <div className="chatgpt-input-wrapper">
                {/* Stop Generating Button */}
                {isTyping && onStop && (
                    <div className="flex justify-center mb-2">
                        <button
                            onClick={onStop}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] text-sm text-[var(--color-text-secondary)] transition-colors"
                        >
                            <Square size={14} className="fill-current" />
                            {isRTL ? 'إيقاف التوليد' : 'Stop generating'}
                        </button>
                    </div>
                )}
                <div className={`chatgpt-input ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <button
                        className="chatgpt-input-btn"
                        aria-label={isRTL ? 'إرفاق ملف' : 'Attach file'}
                        title={isRTL ? 'إرفاق ملف' : 'Attach file'}
                    >
                        <Plus size={20} />
                    </button>
                    <textarea
                        ref={inputRef}
                        value={value}
                        onChange={onChange}
                        onKeyDown={onKeyDown}
                        placeholder={isRTL ? 'اسأل عن العقارات، اتجاهات السوق، حسابات العائد...' : 'Ask about properties, market trends, ROI calculations...'}
                        rows={1}
                        dir="auto"
                        aria-label={isRTL ? 'رسالتك' : 'Your message'}
                        className={transcriptHighlight ? 'transition-colors duration-300 ring-2 ring-[var(--osool-deep-teal)]/40 rounded' : ''}
                    />
                    <VoiceOrb
                        status={voiceStatus}
                        amplitude={amplitude}
                        onClick={onVoiceInput ?? (() => {})}
                        isRTL={isRTL}
                        size="md"
                    />
                    <button
                        onClick={onSend}
                        disabled={!value.trim() || isTyping}
                        aria-label={isRTL ? 'إرسال الرسالة' : 'Send message'}
                        className="chatgpt-send-btn"
                    >
                        {isTyping ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} className={isRTL ? 'rotate-180' : ''} />}
                    </button>
                </div>
                <p className="chatgpt-disclaimer">
                    {isRTL ? 'الذكاء الاصطناعي يمكنه تقديم رؤى. تحقق من البيانات المالية بشكل مستقل.' : 'AI can generate insights. Verify financial data independently.'}
                </p>
            </div>
        </div>
    );
}

interface ChatMainProps {
    onNewConversation?: () => void;
    onPropertySelect?: (property: PropertyContext, uiActions?: UIAction[]) => void;
    onChatContextUpdate?: (context: {
        property?: PropertyContext;
        uiActions?: UIAction[];
        insight?: string;
    }) => void;
    isRTL?: boolean;
}

export default function ChatMain({ onNewConversation, onPropertySelect, onChatContextUpdate, isRTL = false }: ChatMainProps) {
    const prefersReducedMotion = useReducedMotion();

    const {
        messages,
        streamStatus,
        streamingMessageId,
        effectiveRTL,
        isStreaming,
        hasMessages,
        stop: handleStop,
        copyMessage: handleCopy,
        setFeedback: handleFeedback,
        input,
        showScrollButton,
        showWhatsApp,
        setShowWhatsApp,
        transcriptHighlight,
        voiceStatus,
        isListening,
        amplitude,
        scrollRef,
        inputRef,
        streamStatusLabel,
        handleSend,
        handleKeyDown,
        handleInputChange,
        handleScroll,
        scrollToBottom,
        handleVoiceInput,
        handlePropertySelect,
        retry: handleRetry,
        regenerate: handleRegenerate,
    } = useChatEngine({ isRTL, onPropertySelect });

    return (
        <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-background)] relative" dir={effectiveRTL ? 'rtl' : 'ltr'} role="region" aria-label={effectiveRTL ? 'محادثة AI' : 'AI chat'}>
            {/* Empty State */}
            {!hasMessages ? (
                <div className="flex-1 flex flex-col">
                    <motion.div
                        className="chatgpt-empty-state"
                        initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
                    >
                        <motion.div
                            className="chatgpt-empty-logo"
                            initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.9 }}
                            animate={
                                prefersReducedMotion
                                    ? { opacity: 1, scale: 1 }
                                    : { opacity: 1, scale: 1, y: [0, -3, 0] }
                            }
                            transition={
                                prefersReducedMotion
                                    ? { duration: 0 }
                                    : {
                                        opacity: { duration: 0.35 },
                                        scale: { duration: 0.45, ease: [0.16, 1, 0.3, 1] },
                                        y: { duration: 4, ease: 'easeInOut', repeat: Infinity, repeatDelay: 0.3 },
                                    }
                            }
                        >
                            <Sparkles size={24} />
                        </motion.div>
                        <motion.h2
                            className="chatgpt-empty-title"
                            initial={prefersReducedMotion ? false : { opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.4, delay: 0.06, ease: [0.16, 1, 0.3, 1] }}
                        >
                            {getGreeting(effectiveRTL)}
                        </motion.h2>
                        <motion.p
                            className="chatgpt-empty-subtitle"
                            initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.36, delay: 0.11, ease: [0.16, 1, 0.3, 1] }}
                        >
                            {effectiveRTL ? 'كيف أقدر أساعدك في الاستثمار العقاري اليوم؟' : 'How can I help with your real estate investment today?'}
                        </motion.p>

                        <motion.div
                            className="chatgpt-suggestions"
                            initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.42, delay: 0.16, ease: [0.16, 1, 0.3, 1] }}
                        >
                            {SUGGESTION_CARDS.map((suggestion, idx) => (
                                <motion.button
                                    key={idx}
                                    onClick={() => handleSend(suggestion.query)}
                                    className="chatgpt-suggestion"
                                    initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={
                                        prefersReducedMotion
                                            ? { duration: 0 }
                                            : {
                                                duration: 0.34,
                                                delay: 0.2 + idx * 0.08,
                                                ease: [0.16, 1, 0.3, 1],
                                            }
                                    }
                                    whileHover={prefersReducedMotion ? undefined : { y: -2, scale: 1.01 }}
                                    whileTap={prefersReducedMotion ? undefined : { scale: 0.99 }}
                                >
                                    <p className="chatgpt-suggestion-title">
                                        {effectiveRTL ? suggestion.titleAr : suggestion.titleEn}
                                    </p>
                                    <p className="chatgpt-suggestion-desc">
                                        {effectiveRTL ? suggestion.descAr : suggestion.descEn}
                                    </p>
                                </motion.button>
                            ))}
                        </motion.div>

                        {/* WhatsApp handoff CTA */}
                        <motion.button
                            onClick={() => setShowWhatsApp(true)}
                            className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-5 py-2.5 text-sm font-semibold text-emerald-600 transition-colors hover:bg-emerald-500/20 dark:text-emerald-400"
                            initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.34, delay: 0.34, ease: [0.16, 1, 0.3, 1] }}
                            whileHover={prefersReducedMotion ? undefined : { scale: 1.015 }}
                            whileTap={prefersReducedMotion ? undefined : { scale: 0.985 }}
                        >
                            <MessageCircle className="h-4 w-4" />
                            {effectiveRTL ? 'تحدث مع مستشار بشري' : 'Talk to a human advisor'}
                        </motion.button>
                    </motion.div>

                    <ChatInput
                        value={input}
                        onChange={handleInputChange}
                        onSend={() => handleSend()}
                        onKeyDown={handleKeyDown}
                        isTyping={isStreaming}
                        inputRef={inputRef}
                        isRTL={effectiveRTL}
                        onStop={handleStop}
                        onVoiceInput={handleVoiceInput}
                        isListening={isListening}
                        voiceStatus={voiceStatus}
                        amplitude={amplitude}
                        transcriptHighlight={transcriptHighlight}
                    />
                </div>
            ) : (
                <>
                    {/* Chat History */}
                    <div
                        ref={scrollRef}
                        onScroll={handleScroll}
                        className="flex-1 overflow-y-auto chatgpt-scrollbar"
                    >
                        {/* Stream status indicator */}
                        {streamStatusLabel && (
                            <div className="flex items-center justify-center gap-2 py-2 text-xs text-[var(--color-text-muted)]">
                                <StatusDot color="green" pulse />
                                <span>{streamStatusLabel}</span>
                            </div>
                        )}
                        <div className="chatgpt-thread" role="log" aria-live="polite" aria-relevant="additions">
                            {messages.map((message, index) => (
                                message.role === 'user' ? (
                                    <UserMessage
                                        key={message.id}
                                        content={message.content}
                                        timestamp={message.timestamp}
                                        isRTL={effectiveRTL}
                                    />
                                ) : (
                                    <AIMessage
                                        key={message.id}
                                        content={message.content}
                                        properties={message.properties}
                                        visualizations={message.visualizations}
                                        timestamp={message.timestamp}
                                        isStreaming={!!message.isStreaming}
                                        onCopy={() => handleCopy(message.id)}
                                        copied={message.copied}
                                        isRTL={effectiveRTL}
                                        onPropertySelect={handlePropertySelect}
                                        isError={message.isError}
                                        onRetry={message.isError ? () => handleRetry(message.id) : undefined}
                                        onRegenerate={!message.isError && index === messages.length - 1 && !message.isStreaming ? () => handleRegenerate(message.id) : undefined}
                                        onFeedback={!message.isError ? (type) => handleFeedback(message.id, type) : undefined}
                                        feedback={message.feedback}
                                    />
                                )
                            ))}

                            {isStreaming && streamStatus === 'connecting' && messages[messages.length - 1]?.role === 'user' && (
                                <TypingIndicator isRTL={effectiveRTL} />
                            )}
                        </div>
                        <div className="h-6 sm:h-4" />
                    </div>

                    {/* Scroll to Bottom Button */}
                    <AnimatePresence>
                        {showScrollButton && (
                            <motion.button
                                initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={prefersReducedMotion ? { opacity: 0 } : { opacity: 0, y: 16 }}
                                transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
                                onClick={scrollToBottom}
                                className={`absolute bottom-28 ${effectiveRTL ? 'start-4' : 'end-4'} z-20 p-2 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] shadow-md hover:shadow-lg transition-shadow`}
                                whileHover={prefersReducedMotion ? undefined : { y: -1, scale: 1.04 }}
                                whileTap={prefersReducedMotion ? undefined : { scale: 0.96 }}
                            >
                                <ChevronDown size={20} className="text-[var(--color-text-muted)]" />
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Bottom Input Area */}
                    <ChatInput
                        value={input}
                        onChange={handleInputChange}
                        onSend={() => handleSend()}
                        onKeyDown={handleKeyDown}
                        isTyping={isStreaming}
                        inputRef={inputRef}
                        isRTL={effectiveRTL}
                        onStop={handleStop}
                        onVoiceInput={handleVoiceInput}
                        isListening={isListening}
                        voiceStatus={voiceStatus}
                        amplitude={amplitude}
                        transcriptHighlight={transcriptHighlight}
                    />
                </>
            )}

            <WhatsAppHandoffModal
                isOpen={showWhatsApp}
                onClose={() => setShowWhatsApp(false)}
                context={messages.length > 0 ? {
                    chatSummary: messages.filter(m => m.role === 'user').slice(-1)[0]?.content?.slice(0, 200),
                } : undefined}
            />
        </main>
    );
}
