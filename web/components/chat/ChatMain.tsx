'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Copy, Check, ChevronDown, Sparkles, Plus, Mic, BarChart3, TrendingUp, RotateCcw, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown'; //
import remarkGfm from 'remark-gfm'; //
import rehypeRaw from 'rehype-raw'; //
import PropertyCardEnhanced from './PropertyCardEnhanced';
import { PropertyContext, UIActionData } from './ContextualPane';
import api from '@/lib/api';
import VisualizationRenderer from '../visualizations/VisualizationRenderer';

// Types
type UIAction = {
    type: string;
    priority: number;
    data: any;
    trigger_reason?: string;
    chart_reference?: string;
};

type Property = {
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

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    visualizations?: UIAction[];
    properties?: Property[];
    timestamp?: Date;
    copied?: boolean;
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
                    <div className="chatgpt-message-content prose dark:prose-invert max-w-none" dir={messageIsArabic ? 'rtl' : 'ltr'}>
                        {/* Markdown Rendering Implementation */}
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                            components={{
                                p: ({ node, ...props }) => <p className="mb-3 last:mb-0 leading-relaxed" {...props} />,
                                ul: ({ node, ...props }) => <ul className={`list-disc mb-3 ${messageIsArabic ? 'mr-5' : 'ml-5'}`} {...props} />,
                                ol: ({ node, ...props }) => <ol className={`list-decimal mb-3 ${messageIsArabic ? 'mr-5' : 'ml-5'}`} {...props} />,
                                li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                                strong: ({ node, ...props }) => <span className="font-bold text-[var(--color-primary)]" {...props} />,
                                h1: ({ node, ...props }) => <h1 className="text-xl font-bold mb-2 mt-4" {...props} />,
                                h2: ({ node, ...props }) => <h2 className="text-lg font-bold mb-2 mt-3" {...props} />,
                                h3: ({ node, ...props }) => <h3 className="text-md font-bold mb-1 mt-2" {...props} />,
                                blockquote: ({ node, ...props }) => (
                                    <blockquote className="border-l-4 border-[var(--color-primary)] pl-4 py-1 my-2 bg-[var(--color-surface-hover)] rounded-r" {...props} />
                                ),
                                a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                            }}
                        >
                            {content}
                        </ReactMarkdown>
                        {isStreaming && <span className="chatgpt-cursor" />}
                    </div>

                    {/* Visualizations */}
                    {visualizations && visualizations.length > 0 && !isStreaming && (
                        <div className="mt-4 space-y-4">
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
                                        showChart={false}
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
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-[var(--color-text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            </div>
        </div>
    );
}

// Chat Input Component - ChatGPT Style (clean, no glow)
function ChatInput({
    value,
    onChange,
    onSend,
    onKeyDown,
    isTyping,
    inputRef,
    isRTL
}: {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
    onSend: () => void;
    onKeyDown: (e: React.KeyboardEvent) => void;
    isTyping: boolean;
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    isRTL: boolean;
}) {
    return (
        <div className="chatgpt-input-area">
            <div className="chatgpt-input-wrapper">
                <div className={`chatgpt-input ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <button
                        className="chatgpt-input-btn"
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
                    />
                    <button
                        className="chatgpt-input-btn"
                        title={isRTL ? 'إدخال صوتي' : 'Voice Input'}
                    >
                        <Mic size={20} />
                    </button>
                    <button
                        onClick={onSend}
                        disabled={!value.trim() || isTyping}
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

// Suggestion Cards
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
            // Pass session_id for conversation memory
            const { data } = await api.post('/api/chat', {
                message: messageText,
                session_id: sessionId
            });

            const amrMessage: Message = {
                id: `amr-${Date.now()}`,
                role: 'amr',
                content: data.response || data.message || (detectedRTL ? "عذراً، حدثت مشكلة. حاول مرة أخرى." : "Sorry, there was an issue. Please try again."),
                visualizations: data.ui_actions || [],
                properties: data.properties || [],
                timestamp: new Date()
            };

            setMessages(prev => [...prev, amrMessage]);

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
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: 'amr',
                content: detectedRTL ? "عذراً، حدثت مشكلة في الاتصال. حاول مرة أخرى لاحقاً." : "Sorry, there was a connection issue. Please try again later.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
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
        <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-background)] relative" dir={effectiveRTL ? 'rtl' : 'ltr'}>
            {/* Empty State */}
            {!hasMessages ? (
                <div className="flex-1 flex flex-col">
                    <div className="chatgpt-empty-state">
                        <div className="chatgpt-empty-logo">
                            <Sparkles size={24} />
                        </div>
                        <h2 className="chatgpt-empty-title">
                            {effectiveRTL ? 'مرحباً بك في عمرو' : 'Welcome to AMR AI'}
                        </h2>
                        <p className="chatgpt-empty-subtitle">
                            {effectiveRTL ? 'مساعدك العقاري الذكي' : 'Your intelligent real estate assistant'}
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
                    </div>

                    <ChatInput
                        value={input}
                        onChange={handleInputChange}
                        onSend={() => handleSend()}
                        onKeyDown={handleKeyDown}
                        isTyping={isTyping}
                        inputRef={inputRef}
                        isRTL={effectiveRTL}
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
                        <div className="chatgpt-thread">
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
                                    />
                                )
                            ))}

                            {isTyping && messages[messages.length - 1]?.role === 'user' && (
                                <TypingIndicator isRTL={effectiveRTL} />
                            )}
                        </div>
                        <div className="h-4" />
                    </div>

                    {/* Scroll to Bottom Button */}
                    <AnimatePresence>
                        {showScrollButton && (
                            <motion.button
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 20 }}
                                onClick={scrollToBottom}
                                className={`absolute bottom-28 ${effectiveRTL ? 'left-4' : 'right-4'} z-20 p-2 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] shadow-md hover:shadow-lg transition-shadow`}
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
                    />
                </>
            )}
        </main>
    );
}
