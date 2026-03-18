'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Copy, Check, ChevronDown, Sparkles, Plus, BarChart3, TrendingUp, RotateCcw, User, ThumbsUp, ThumbsDown, Square, AlertTriangle, RefreshCw, MessageCircle } from 'lucide-react';
import { useVoiceRecording, type RecordingStatus } from '@/hooks/useVoiceRecording';
import VoiceOrb from '@/components/VoiceOrb';
import ReactMarkdown from 'react-markdown'; //
import remarkGfm from 'remark-gfm'; //
import rehypeRaw from 'rehype-raw'; // DISABLED - kept import for reference
import PropertyCardEnhanced from './PropertyCardEnhanced';
import { PropertyContext, UIActionData } from './ContextualPane';
import api from '@/lib/api';
import VisualizationRenderer from '../visualizations/VisualizationRenderer';
import WhatsAppHandoffModal from '../WhatsAppHandoffModal';

// Types
type UIAction = UIActionData;

type Property = {
    id: number;
    title: string;
    price: number;
    location: string;
    size_sqm: number;
    bedrooms: number;
    wolf_score?: number;
    developer?: string;
    [key: string]: unknown;
};

type Message = {
    id: string;
    role: 'user' | 'coinvestor';
    content: string;
    visualizations?: UIAction[];
    properties?: Property[];
    timestamp?: Date;
    copied?: boolean;
    isError?: boolean;
    feedback?: 'up' | 'down' | null;
};

// Detect if text is Arabic
function isArabic(text: string): boolean {
    const arabicPattern = /[\u0600-\u06FF\u0750-\u077F]/;
    return arabicPattern.test(text);
}

// Format price
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M EGP`;
    }
    return `${(price / 1_000).toFixed(0)}K EGP`;
};

// User Message Component - ChatGPT Style (clean, no bubble)
function UserMessage({ content, timestamp, isRTL }: { content: string; timestamp?: Date; isRTL: boolean }) {
    const messageIsArabic = isArabic(content);

    return (
        <div className="chatgpt-message chatgpt-message-user">
            <div className="chatgpt-message-layout chatgpt-container">
                <div className="chatgpt-avatar chatgpt-avatar-user">
                    <User size={16} />
                </div>
                <div className="chatgpt-message-content" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                    <p>{content}</p>
                </div>
            </div>
        </div>
    );
}

// Fix malformed markdown tables so remark-gfm can parse them
function fixMarkdownTables(text: string): string {
    const lines = text.split('\n');
    const result: string[] = [];
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        if (/^\s*\|/.test(line)) {
            const tableLines: string[] = [];
            while (i < lines.length && /^\s*\|/.test(lines[i])) { tableLines.push(lines[i]); i++; }
            if (tableLines.length >= 2) {
                const headerCols = (tableLines[0].match(/\|/g) || []).length - 1;
                const isSep = (l: string) => /^\s*\|[\s\-:|]+\|\s*$/.test(l);
                if (isSep(tableLines[1])) {
                    const sepCols = (tableLines[1].match(/\|/g) || []).length - 1;
                    if (sepCols !== headerCols) {
                        tableLines[1] = '| ' + Array(headerCols).fill('---').join(' | ') + ' |';
                    }
                } else if (headerCols >= 2) {
                    tableLines.splice(1, 0, '| ' + Array(headerCols).fill('---').join(' | ') + ' |');
                }
                for (let r = 2; r < tableLines.length; r++) {
                    if (isSep(tableLines[r])) continue;
                    const rowCols = (tableLines[r].match(/\|/g) || []).length - 1;
                    if (rowCols < headerCols) {
                        tableLines[r] = tableLines[r].trimEnd().replace(/\|$/, '') + '| '.repeat(headerCols - rowCols) + '|';
                    }
                }
                result.push(...tableLines);
            } else { result.push(...tableLines); }
        } else { result.push(line); i++; }
    }
    return result.join('\n');
}

// Strip bracketed action annotations from AI responses (e.g. [يفتح حاسبة القوة الشرائية])
function cleanMessageContent(text: string): string {
    return fixMarkdownTables(
        text
            .replace(/\[[\u0600-\u06FF\u0621-\u064A\w\s،,.:()\/-]+\]/g, '') // Arabic bracket text
            .replace(/\[\s*[a-zA-Z\s_]+\s*\]/g, '')                               // English bracket actions
            .replace(/\n{3,}/g, '\n\n')                                            // Collapse excess blank lines
            .trim()
    );
}

// AI Message Component - ChatGPT Style (subtle bg, avatar)
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
    const messageIsArabic = isArabic(content);

    // Error state UI
    if (isError) {
        return (
            <div className="chatgpt-message chatgpt-message-ai">
                <div className="chatgpt-message-layout chatgpt-container">
                    <div className="chatgpt-avatar chatgpt-avatar-ai">
                        <AlertTriangle size={16} className="text-amber-500" />
                    </div>
                    <div className="flex-1 min-w-0">
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
            </div>
        );
    }

    return (
        <div className="chatgpt-message chatgpt-message-ai">
            <div className="chatgpt-message-layout chatgpt-container">
                <div className="chatgpt-avatar chatgpt-avatar-ai">
                    <Sparkles size={16} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className={`chatgpt-message-content prose dark:prose-invert max-w-none ${messageIsArabic ? 'prose-rtl text-end' : 'text-start'}`} dir={messageIsArabic ? 'rtl' : 'ltr'}>
                        {/* Markdown Rendering Implementation */}
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            // rehypePlugins removed - rehypeRaw can cause XSS
                            components={{
                                p: ({ node, ...props }) => <p className={`mb-3 last:mb-0 leading-relaxed ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                                ul: ({ node, ...props }) => <ul className={`list-disc mb-3 ${messageIsArabic ? 'pe-6' : 'ps-6'}`} {...props} />,
                                ol: ({ node, ...props }) => <ol className={`list-decimal mb-3 ${messageIsArabic ? 'pe-6' : 'ps-6'}`} {...props} />,
                                strong: ({ node, ...props }) => <strong className="font-bold text-[var(--color-primary)] dark:text-[var(--color-teal-accent)]" {...props} />,
                                h1: ({ node, ...props }) => <h1 className={`text-xl font-bold mb-2 mt-4 ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                                h2: ({ node, ...props }) => <h2 className={`text-lg font-bold mb-2 mt-3 ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                                h3: ({ node, ...props }) => <h3 className={`text-md font-bold mb-1 mt-2 ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />,
                                blockquote: ({ node, ...props }) => (
                                    <blockquote className={`${messageIsArabic ? 'border-e-4 pe-4 rounded-l' : 'border-s-4 ps-4 rounded-r'} border-[var(--color-primary)] py-1 my-2 bg-[var(--color-surface-hover)]`} {...props} />
                                ),
                                a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                table: ({ node, ...props }) => (
                                    <div className="overflow-x-auto my-4 rounded-xl border border-[var(--color-border)]/40">
                                        <table className={`w-full border-collapse text-sm ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                                    </div>
                                ),
                                thead: ({ node, ...props }) => <thead className="bg-[var(--color-surface)]/50" {...props} />,
                                th: ({ node, ...props }) => (
                                    <th className={`border border-[var(--color-border)]/40 px-3 py-2 font-semibold text-[var(--color-primary)] bg-[var(--color-surface)]/30 ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                                ),
                                td: ({ node, ...props }) => (
                                    <td className={`border border-[var(--color-border)]/40 px-3 py-2 text-[var(--color-text-secondary)] ${messageIsArabic ? 'text-end' : 'text-start'}`} {...props} />
                                ),
                                tr: ({ node, ...props }) => (
                                    <tr className="even:bg-[var(--color-surface)]/10 hover:bg-[var(--color-surface)]/20 transition-colors" {...props} />
                                ),
                            }}
                        >
                            {cleanMessageContent(content)}
                        </ReactMarkdown>
                        {isStreaming && <span className="chatgpt-cursor" />}
                    </div>

                    {/* Visualizations */}
                    {visualizations && visualizations.length > 0 && !isStreaming && (
                        <div className="mt-4 space-y-3 sm:space-y-4">
                            <div className={`flex items-center gap-2 text-sm font-medium text-[var(--color-text-muted)] ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                                <BarChart3 size={16} />
                                <span>{isRTL ? 'التحليلات' : 'Analytics'}</span>
                            </div>
                            <div className="grid gap-3">
                                {visualizations.map((viz, index) => (
                                    <div
                                        key={`${viz.type}-${index}`}
                                        className="w-full max-w-full rounded-xl overflow-hidden border border-[var(--color-border)]/30 bg-transparent ai-visualization"
                                    >
                                        {viz.chart_reference && (
                                            <div className={`px-3 sm:px-4 py-2 bg-transparent border-b border-[var(--color-border)]/30 ${messageIsArabic ? 'text-end' : 'text-start'}`}>
                                                <p className="text-xs text-[var(--color-text-muted)] font-medium flex items-center gap-2">
                                                    <TrendingUp size={12} />
                                                    {viz.chart_reference}
                                                </p>
                                            </div>
                                        )}
                                        <div className="p-1.5 sm:p-2">
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
                        <div className="mt-4 space-y-3">
                            {properties.map((prop) => (
                                <div
                                    key={prop.id}
                                    onClick={() => onPropertySelect?.(prop, visualizations)}
                                    className="cursor-pointer"
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
                        className={transcriptHighlight ? 'transition-colors duration-300 ring-2 ring-[var(--osool-deep-teal,#0d9488)]/40 rounded' : ''}
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

// Suggestion Cards with time-based context
function getGreeting(isRTL: boolean): string {
    const hour = new Date().getHours();
    if (isRTL) {
        if (hour < 12) return 'صباح الخير! ☀️';
        if (hour < 18) return 'مساء الخير! 🌤️';
        return 'مساء النور! 🌙';
    }
    if (hour < 12) return 'Good morning! ☀️';
    if (hour < 18) return 'Good afternoon! 🌤️';
    return 'Good evening! 🌙';
}

const suggestions = [
    {
        titleEn: 'Market Analysis',
        titleAr: 'تحليل السوق',
        descEn: 'Get insights on current market trends',
        descAr: 'احصل على رؤى حول اتجاهات السوق',
        query: 'Show me the current market analysis for New Cairo'
    },
    {
        titleEn: 'ROI Calculator',
        titleAr: 'حاسبة العائد',
        descEn: 'Calculate potential returns',
        descAr: 'احسب العوائد المحتملة',
        query: 'Calculate ROI for a 2M EGP investment'
    },
    {
        titleEn: 'Top Properties',
        titleAr: 'أفضل العقارات',
        descEn: 'Discover high-performing listings',
        descAr: 'اكتشف أفضل العقارات',
        query: 'Show me top investment properties'
    },
    {
        titleEn: 'Area Comparison',
        titleAr: 'مقارنة المناطق',
        descEn: 'Compare different locations',
        descAr: 'قارن بين المناطق المختلفة',
        query: 'Compare New Cairo vs Sheikh Zayed'
    }
];

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
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [showWhatsApp, setShowWhatsApp] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);
    const [transcriptHighlight, setTranscriptHighlight] = useState(false);

    const {
        status: voiceStatus,
        isListening,
        amplitude,
        startRecording,
        stopRecording,
    } = useVoiceRecording({
        language: isRTL ? 'ar-EG' : 'auto',
        silenceThresholdMs: 2000,
        onTranscript: (text) => {
            setInput(text);
            setTranscriptHighlight(true);
            setTimeout(() => setTranscriptHighlight(false), 600);
        },
        onError: (msg) => {
            console.warn('[Voice]', msg);
        },
    });
    // Generate a stable session ID for this conversation
    const [sessionId] = useState(() => {
        if (typeof window !== 'undefined') {
            // Check for existing session or create new one
            const existingSession = sessionStorage.getItem('osool_chat_session');
            if (existingSession) return existingSession;
            const newSession = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
            sessionStorage.setItem('osool_chat_session', newSession);
            return newSession;
        }
        return `session_${Date.now()}`;
    });
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const hasMessages = messages.length > 0;

    // Auto-detect RTL based on input
    const [detectedRTL, setDetectedRTL] = useState(isRTL);

    // Listen for triggered messages from sidebar tools
    useEffect(() => {
        const handleTriggeredMessage = (event: CustomEvent<{ message: string }>) => {
            if (event.detail?.message && !isTyping) {
                handleSend(event.detail.message);
            }
        };

        window.addEventListener('triggerChatMessage', handleTriggeredMessage as EventListener);
        return () => window.removeEventListener('triggerChatMessage', handleTriggeredMessage as EventListener);
    }, [isTyping]);

    useEffect(() => {
        if (scrollRef.current && hasMessages) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages, isTyping, hasMessages]);

    const handleScroll = useCallback(() => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
        }
    }, []);

    const scrollToBottom = () => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    };

    const handleCopy = (messageId: string) => {
        const message = messages.find(m => m.id === messageId);
        if (message) {
            navigator.clipboard.writeText(message.content);
            setMessages(prev => prev.map(m =>
                m.id === messageId ? { ...m, copied: true } : m
            ));
            setTimeout(() => {
                setMessages(prev => prev.map(m =>
                    m.id === messageId ? { ...m, copied: false } : m
                ));
            }, 2000);
        }
    };

    const handleFeedback = (messageId: string, type: 'up' | 'down') => {
        setMessages(prev => prev.map(m =>
            m.id === messageId ? { ...m, feedback: m.feedback === type ? null : type } : m
        ));
    };

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        setIsTyping(false);
    };

    const handleVoiceInput = useCallback(() => {
        if (isListening || voiceStatus === 'processing') {
            stopRecording();
        } else {
            startRecording();
        }
    }, [isListening, voiceStatus, startRecording, stopRecording]);

    const handleRetry = (messageId: string) => {
        // Find the user message that preceded this error
        const msgIndex = messages.findIndex(m => m.id === messageId);
        if (msgIndex <= 0) return;
        const prevUserMsg = messages.slice(0, msgIndex).reverse().find(m => m.role === 'user');
        if (!prevUserMsg) return;
        // Remove the error message and resend
        setMessages(prev => prev.filter(m => m.id !== messageId));
        handleSend(prevUserMsg.content);
    };

    const handlePropertySelect = (property: Property, uiActions?: UIAction[]) => {
        if (onPropertySelect) {
            let wolfScore = property.wolf_score || 75;
            let roi = 12.5;
            let marketTrend = 'Growing 📊';
            let priceVerdict = 'Fair';

            if (uiActions) {
                const scorecard = uiActions.find(a => a.type === 'investment_scorecard');
                if (scorecard?.data?.analysis) {
                    wolfScore = scorecard.data.analysis.match_score || wolfScore;
                    roi = scorecard.data.analysis.roi_projection || roi;
                    marketTrend = scorecard.data.analysis.market_trend || marketTrend;
                    priceVerdict = scorecard.data.analysis.price_verdict || priceVerdict;
                }
            }

            onPropertySelect({
                title: property.title,
                address: property.location,
                price: formatPrice(property.price),
                metrics: {
                    size: property.size_sqm,
                    bedrooms: property.bedrooms,
                    pricePerSqFt: `${Math.round(property.price / property.size_sqm).toLocaleString()}`,
                    wolfScore: wolfScore,
                    roi: roi,
                    marketTrend: marketTrend,
                    priceVerdict: priceVerdict,
                },
                tags: property.developer ? [property.developer] : [],
                aiRecommendation: property.wolf_score && property.wolf_score >= 80
                    ? 'High investment potential based on Osool Score analysis'
                    : undefined,
            });
        }
    };

    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || isTyping) return;

        if (isArabic(messageText)) {
            setDetectedRTL(true);
        }

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: messageText,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
        }

        try {
            // Create abort controller for stop functionality
            const controller = new AbortController();
            abortControllerRef.current = controller;

            // Pass session_id for conversation memory
            const { data } = await api.post('/api/chat', {
                message: messageText,
                session_id: sessionId
            }, { signal: controller.signal });

            const coinvestorMessage: Message = {
                id: `coinvestor-${Date.now()}`,
                role: 'coinvestor',
                content: data.response || data.message || (detectedRTL ? "عذراً، حدثت مشكلة. حاول مرة أخرى." : "Sorry, there was an issue. Please try again."),
                visualizations: data.ui_actions || [],
                properties: data.properties || [],
                timestamp: new Date()
            };

            setMessages(prev => [...prev, coinvestorMessage]);

            if (data.properties && data.properties.length > 0) {
                handlePropertySelect(data.properties[0], data.ui_actions);
            }

            if (onChatContextUpdate) {
                const scorecard = data.ui_actions?.find((a: UIAction) => a.type === 'investment_scorecard');

                let insight = '';
                if (scorecard?.data?.analysis) {
                    const analysis = scorecard.data.analysis;
                    insight = detectedRTL
                        ? `🏢 Osool Score: ${analysis.match_score}/100 | العائد: ${analysis.roi_projection}% | ${analysis.market_trend}`
                        : `🏢 Osool Score: ${analysis.match_score}/100 | ROI: ${analysis.roi_projection}% | ${analysis.market_trend}`;
                }

                onChatContextUpdate({
                    property: data.properties?.[0] ? {
                        title: data.properties[0].title,
                        address: data.properties[0].location,
                        price: formatPrice(data.properties[0].price),
                        metrics: {
                            wolfScore: scorecard?.data?.analysis?.match_score || data.properties[0].wolf_score || 75,
                            roi: scorecard?.data?.analysis?.roi_projection || 12.5,
                            marketTrend: scorecard?.data?.analysis?.market_trend || 'Growing 📊',
                            priceVerdict: scorecard?.data?.analysis?.price_verdict || 'Fair',
                            pricePerSqm: Math.round(data.properties[0].price / data.properties[0].size_sqm),
                            areaAvgPrice: scorecard?.data?.analysis?.area_avg_price_per_sqm || 50000,
                            size: data.properties[0].size_sqm,
                            bedrooms: data.properties[0].bedrooms,
                        },
                        tags: data.properties[0].developer ? [data.properties[0].developer] : [],
                    } : undefined,
                    uiActions: data.ui_actions || [],
                    insight: insight || data.response?.slice(0, 150),
                });
            }
        } catch (error) {
            // Don't show error for user-initiated abort
            if (error instanceof DOMException && error.name === 'AbortError') {
                const abortMessage: Message = {
                    id: `aborted-${Date.now()}`,
                    role: 'coinvestor',
                    content: detectedRTL ? 'تم إيقاف التوليد.' : 'Generation stopped.',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, abortMessage]);
                return;
            }

            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: 'coinvestor',
                content: detectedRTL
                    ? "عذراً، حدثت مشكلة في الاتصال. يرجى المحاولة مرة أخرى."
                    : "Something went wrong. This could be a network issue or the server might be busy.",
                timestamp: new Date(),
                isError: true,
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            abortControllerRef.current = null;
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
    };

    const effectiveRTL = isRTL || detectedRTL;

    return (
        <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-background)] relative" dir={effectiveRTL ? 'rtl' : 'ltr'} role="region" aria-label={effectiveRTL ? 'محادثة AI' : 'AI chat'}>
            {/* Empty State */}
            {!hasMessages ? (
                <div className="flex-1 flex flex-col">
                    <div className="chatgpt-empty-state">
                        <div className="chatgpt-empty-logo">
                            <Sparkles size={24} />
                        </div>
                        <h2 className="chatgpt-empty-title">
                            {getGreeting(effectiveRTL)}
                        </h2>
                        <p className="chatgpt-empty-subtitle">
                            {effectiveRTL ? 'كيف أقدر أساعدك في الاستثمار العقاري اليوم؟' : 'How can I help with your real estate investment today?'}
                        </p>

                        <div className="chatgpt-suggestions">
                            {suggestions.map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleSend(suggestion.query)}
                                    className="chatgpt-suggestion"
                                >
                                    <p className="chatgpt-suggestion-title">
                                        {effectiveRTL ? suggestion.titleAr : suggestion.titleEn}
                                    </p>
                                    <p className="chatgpt-suggestion-desc">
                                        {effectiveRTL ? suggestion.descAr : suggestion.descEn}
                                    </p>
                                </button>
                            ))}
                        </div>

                        {/* WhatsApp handoff CTA */}
                        <button
                            onClick={() => setShowWhatsApp(true)}
                            className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#25D366]/30 bg-[#25D366]/10 px-5 py-2.5 text-sm font-semibold text-[#25D366] transition-colors hover:bg-[#25D366]/20"
                        >
                            <MessageCircle className="h-4 w-4" />
                            {effectiveRTL ? 'تحدث مع مستشار بشري' : 'Talk to a human advisor'}
                        </button>
                    </div>

                    <ChatInput
                        value={input}
                        onChange={handleInputChange}
                        onSend={() => handleSend()}
                        onKeyDown={handleKeyDown}
                        isTyping={isTyping}
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
                                        isStreaming={index === messages.length - 1 && isTyping}
                                        onCopy={() => handleCopy(message.id)}
                                        copied={message.copied}
                                        isRTL={effectiveRTL}
                                        onPropertySelect={handlePropertySelect}
                                        isError={message.isError}
                                        onRetry={message.isError ? () => handleRetry(message.id) : undefined}
                                        onFeedback={!message.isError ? (type) => handleFeedback(message.id, type) : undefined}
                                        feedback={message.feedback}
                                    />
                                )
                            ))}

                            {isTyping && messages[messages.length - 1]?.role === 'user' && (
                                <TypingIndicator isRTL={effectiveRTL} />
                            )}
                        </div>
                        <div className="h-6 sm:h-4" />
                    </div>

                    {/* Scroll to Bottom Button */}
                    <AnimatePresence>
                        {showScrollButton && (
                            <motion.button
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 20 }}
                                onClick={scrollToBottom}
                                className={`absolute bottom-28 ${effectiveRTL ? 'start-4' : 'end-4'} z-20 p-2 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] shadow-md hover:shadow-lg transition-shadow`}
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
                        isTyping={isTyping}
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
