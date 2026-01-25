'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Copy, Check, ChevronDown, Sparkles, Plus, Mic, BarChart3, TrendingUp } from 'lucide-react';
import anime from 'animejs';
import AnimatedBlobs from './AnimatedBlobs';
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

// Typewriter Hook
function useTypewriter(text: string, baseSpeed: number = 12, enabled: boolean = true) {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!enabled) {
            setDisplayedText(text);
            setIsComplete(true);
            return;
        }

        setDisplayedText('');
        setIsComplete(false);
        let index = 0;
        let timeoutId: NodeJS.Timeout;

        const typeNext = () => {
            if (index < text.length) {
                const char = text[index];
                setDisplayedText(text.slice(0, index + 1));
                index++;

                let delay = baseSpeed;
                if (['.', '!', '?', '،', '؟'].includes(char)) {
                    delay = baseSpeed * 6;
                } else if ([',', ':', ';', '-'].includes(char)) {
                    delay = baseSpeed * 3;
                } else if (char === ' ') {
                    delay = baseSpeed * 1.3;
                } else if (/[\u0600-\u06FF]/.test(char)) {
                    delay = baseSpeed * 0.9;
                }

                timeoutId = setTimeout(typeNext, delay);
            } else {
                setIsComplete(true);
            }
        };

        timeoutId = setTimeout(typeNext, 50);
        return () => clearTimeout(timeoutId);
    }, [text, baseSpeed, enabled]);

    return { displayedText, isComplete };
}

// Format price
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M EGP`;
    }
    return `${(price / 1_000).toFixed(0)}K EGP`;
};

// User Message Component with anime.js
function UserMessage({ content, timestamp, isRTL }: { content: string; timestamp?: Date; isRTL: boolean }) {
    const messageIsArabic = isArabic(content);
    const messageRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (messageRef.current) {
            anime({
                targets: messageRef.current,
                opacity: [0, 1],
                translateY: [20, 0],
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, []);

    return (
        <div 
            ref={messageRef}
            className={`flex ${messageIsArabic ? 'justify-start' : 'justify-end'}`}
            style={{ opacity: 0 }}
        >
            <div className={`flex flex-col ${messageIsArabic ? 'items-start' : 'items-end'} gap-1 max-w-[85%] md:max-w-[70%] lg:max-w-[60%]`}>
                <div
                    className="chat-message-user px-6 py-4 shadow-lg shadow-[var(--color-primary)]/10"
                    dir={messageIsArabic ? 'rtl' : 'ltr'}
                >
                    <p className="leading-relaxed text-[15px] font-medium">{content}</p>
                </div>
                <span className={`text-[11px] font-medium text-[var(--color-text-muted)] ${messageIsArabic ? 'ml-2' : 'mr-2'}`}>
                    {isRTL ? 'أنت' : 'You'} {timestamp && `• ${timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                </span>
            </div>
        </div>
    );
}

// AI Message Component with anime.js
function AIMessage({
    content,
    properties,
    visualizations,
    timestamp,
    enableTypewriter = true,
    onCopy,
    copied,
    isRTL,
    onPropertySelect
}: {
    content: string;
    properties?: Property[];
    visualizations?: UIAction[];
    timestamp?: Date;
    enableTypewriter?: boolean;
    onCopy?: () => void;
    copied?: boolean;
    isRTL: boolean;
    onPropertySelect?: (property: Property, uiActions?: UIAction[]) => void;
}) {
    const { displayedText, isComplete } = useTypewriter(content, 12, enableTypewriter);
    const messageIsArabic = isArabic(content);
    const messageRef = useRef<HTMLDivElement>(null);
    const visualsRef = useRef<HTMLDivElement>(null);
    const cardsRef = useRef<HTMLDivElement>(null);

    // Entrance animation for message
    useEffect(() => {
        if (messageRef.current) {
            anime({
                targets: messageRef.current,
                opacity: [0, 1],
                translateY: [30, 0],
                easing: 'easeOutExpo',
                duration: 600,
            });
        }
    }, []);

    // Stagger animation for visualizations
    useEffect(() => {
        if (visualsRef.current && isComplete && visualizations?.length) {
            anime({
                targets: visualsRef.current.querySelectorAll('.viz-card'),
                opacity: [0, 1],
                translateY: [20, 0],
                scale: [0.95, 1],
                delay: anime.stagger(150, { start: 200 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [isComplete, visualizations]);

    // Stagger animation for property cards
    useEffect(() => {
        if (cardsRef.current && isComplete && properties?.length) {
            anime({
                targets: cardsRef.current.querySelectorAll('.property-card'),
                opacity: [0, 1],
                translateX: [30, 0],
                delay: anime.stagger(100, { start: 300 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [isComplete, properties]);

    return (
        <div 
            ref={messageRef}
            className={`flex gap-5 max-w-full md:max-w-[90%] ${messageIsArabic ? 'flex-row-reverse' : ''}`}
            style={{ opacity: 0 }}
        >
            <div className="flex-none flex flex-col items-center gap-2">
                <div className="size-10 rounded-xl bg-gradient-to-br from-[var(--color-teal-accent)] to-[var(--color-primary)] flex items-center justify-center shadow-lg shadow-[var(--color-primary)]/20">
                    <Sparkles size={20} className="text-white" />
                </div>
            </div>
            <div className={`flex flex-col gap-4 flex-1 min-w-0 ${messageIsArabic ? 'items-end' : 'items-start'}`}>
                <div>
                    <div className={`flex items-baseline gap-2 mb-1 ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                        <span className="text-sm font-bold text-[var(--color-text-primary)]">{isRTL ? 'عمرو' : 'AMR AI'}</span>
                        <span className="text-[11px] text-[var(--color-text-muted)]">
                            {timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    <div
                        className="chat-message-ai px-6 py-4 shadow-sm inline-block relative group"
                        dir={messageIsArabic ? 'rtl' : 'ltr'}
                    >
                        <p className="leading-relaxed text-[15px] text-[var(--color-text-primary)]">
                            {enableTypewriter ? displayedText : content}
                            {enableTypewriter && !isComplete && (
                                <span className="inline-block w-0.5 h-4 bg-[var(--color-teal-accent)] ml-1 animate-pulse" />
                            )}
                        </p>
                        {isComplete && onCopy && (
                            <button
                                onClick={onCopy}
                                className={`absolute top-2 ${messageIsArabic ? 'left-2' : 'right-2'} p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-[var(--color-surface-hover)] hover:bg-[var(--color-border)]`}
                            >
                                {copied ? <Check size={14} className="text-[var(--color-teal-accent)]" /> : <Copy size={14} className="text-[var(--color-text-muted)]" />}
                            </button>
                        )}
                    </div>
                </div>

                {/* 📊 VISUALIZATIONS - Show analytics and charts */}
                {visualizations && visualizations.length > 0 && isComplete && (
                    <div 
                        ref={visualsRef}
                        className="w-full space-y-4"
                    >
                        {/* Analytics Header */}
                        <div className={`flex items-center gap-2 text-sm font-semibold text-[var(--color-primary)] ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                            <BarChart3 size={16} />
                            <span>{isRTL ? '📊 التحليلات والرسوم البيانية' : '📊 Analytics & Charts'}</span>
                        </div>
                        
                        {/* Render each visualization */}
                        <div className="grid gap-4">
                            {visualizations.map((viz, index) => (
                                <div
                                    key={`${viz.type}-${index}`}
                                    className="viz-card rounded-2xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)] shadow-lg"
                                    style={{ opacity: 0 }}
                                >
                                    {/* Visualization Header */}
                                    {viz.chart_reference && (
                                        <div className={`px-4 py-2 bg-gradient-to-r from-[var(--color-primary)]/10 to-transparent border-b border-[var(--color-border)] ${messageIsArabic ? 'text-right' : 'text-left'}`}>
                                            <p className="text-xs text-[var(--color-primary)] font-medium flex items-center gap-2">
                                                <TrendingUp size={12} />
                                                {viz.chart_reference}
                                            </p>
                                        </div>
                                    )}
                                    
                                    {/* Visualization Content */}
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

                {/* Property Cards - Only show real data from AI */}
                {properties && properties.length > 0 && isComplete && (
                    <div ref={cardsRef} className="space-y-4 w-full">
                        {properties.map((prop) => (
                            <div 
                                key={prop.id} 
                                onClick={() => onPropertySelect?.(prop, visualizations)} 
                                className="property-card cursor-pointer"
                                style={{ opacity: 0 }}
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
            </div>
        </div>
    );
}

// Typing Indicator with anime.js
function TypingIndicator({ isRTL }: { isRTL: boolean }) {
    const dotsRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (dotsRef.current) {
            const dots = dotsRef.current.querySelectorAll('.typing-dot');
            anime({
                targets: dots,
                translateY: [-6, 0],
                opacity: [0.5, 1],
                delay: anime.stagger(150),
                loop: true,
                direction: 'alternate',
                easing: 'easeInOutSine',
                duration: 400,
            });
        }
    }, []);

    return (
        <div className={`flex gap-5 max-w-full md:max-w-[90%] ${isRTL ? 'flex-row-reverse' : ''}`}>
            <div className="flex-none">
                <div className="size-10 rounded-xl bg-gradient-to-br from-[var(--color-teal-accent)] to-[var(--color-primary)] flex items-center justify-center shadow-lg">
                    <Sparkles size={20} className="text-white animate-pulse" />
                </div>
            </div>
            <div className="chat-message-ai px-6 py-4 shadow-sm">
                <div ref={dotsRef} className="flex items-center gap-1.5">
                    <span className="typing-dot w-2 h-2 bg-[var(--color-teal-accent)] rounded-full" />
                    <span className="typing-dot w-2 h-2 bg-[var(--color-teal-accent)] rounded-full" />
                    <span className="typing-dot w-2 h-2 bg-[var(--color-teal-accent)] rounded-full" />
                </div>
            </div>
        </div>
    );
}

// Chat Input Component
function ChatInput({
    value,
    onChange,
    onSend,
    onKeyDown,
    isTyping,
    inputRef,
    isCentered,
    isRTL
}: {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
    onSend: () => void;
    onKeyDown: (e: React.KeyboardEvent) => void;
    isTyping: boolean;
    inputRef: React.RefObject<HTMLTextAreaElement | null>;
    isCentered: boolean;
    isRTL: boolean;
}) {
    return (
        <div className={`${isCentered ? 'w-full max-w-2xl' : 'max-w-4xl'} mx-auto chat-input-container`}>
            {/* Glow Effect */}
            <div className="chat-input-glow" />

            <div className={`chat-input flex items-center p-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <button
                    className="p-3 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-hover)] transition-colors"
                    title={isRTL ? 'إرفاق ملف' : 'Attach file'}
                >
                    <Plus size={24} />
                </button>
                <textarea
                    ref={inputRef}
                    value={value}
                    onChange={onChange}
                    onKeyDown={onKeyDown}
                    placeholder={isRTL ? 'اسأل عن العقارات، اتجاهات السوق، حسابات العائد...' : 'Ask about properties, market trends, ROI calculations...'}
                    rows={1}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] px-3 py-3 text-base resize-none max-h-[150px] focus:outline-none"
                    dir="auto"
                />
                <div className={`flex items-center gap-1 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <button
                        className="p-3 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-hover)] transition-colors"
                        title={isRTL ? 'إدخال صوتي' : 'Voice Input'}
                    >
                        <Mic size={24} />
                    </button>
                    <button
                        onClick={onSend}
                        disabled={!value.trim() || isTyping}
                        className={`chat-send-button ${isRTL ? 'mr-1' : 'ml-1'} flex items-center justify-center aspect-square disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        {isTyping ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} className={isRTL ? 'rotate-180' : ''} />}
                    </button>
                </div>
            </div>
            <div className="text-center mt-3">
                <p className="text-[10px] font-medium text-[var(--color-text-muted)]">
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
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const hasMessages = messages.length > 0;

    // Auto-detect RTL based on input
    const [detectedRTL, setDetectedRTL] = useState(isRTL);

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
            // Extract additional analytics from UI actions if available
            let wolfScore = property.wolf_score || 75;
            let roi = 12.5;
            let marketTrend = 'Growing 📊';
            let priceVerdict = 'Fair';
            
            // Look for investment scorecard in ui_actions for richer data
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
                    ? 'High investment potential based on Wolf Score analysis'
                    : undefined,
            });
        }
    };

    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || isTyping) return;

        // Detect language direction
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
            const { data } = await api.post('/api/chat', { message: messageText });

            const amrMessage: Message = {
                id: `amr-${Date.now()}`,
                role: 'amr',
                content: data.response || data.message || (detectedRTL ? "عذراً، حدثت مشكلة. حاول مرة أخرى." : "Sorry, there was an issue. Please try again."),
                visualizations: data.ui_actions || [],
                properties: data.properties || [],
                timestamp: new Date()
            };

            setMessages(prev => [...prev, amrMessage]);

            // Auto-select first property for contextual pane with full analytics
            if (data.properties && data.properties.length > 0) {
                handlePropertySelect(data.properties[0], data.ui_actions);
            }
            
            // Also update chat context for real-time pane updates from AI response
            if (onChatContextUpdate) {
                // Extract insights from UI actions
                const scorecard = data.ui_actions?.find((a: UIAction) => a.type === 'investment_scorecard');
                const marketTrend = data.ui_actions?.find((a: UIAction) => a.type === 'market_trend_chart');
                const roiCalc = data.ui_actions?.find((a: UIAction) => a.type === 'roi_calculator');
                
                let insight = '';
                if (scorecard?.data?.analysis) {
                    const analysis = scorecard.data.analysis;
                    insight = detectedRTL 
                        ? `🐺 Wolf Score: ${analysis.match_score}/100 | العائد: ${analysis.roi_projection}% | ${analysis.market_trend}`
                        : `🐺 Wolf Score: ${analysis.match_score}/100 | ROI: ${analysis.roi_projection}% | ${analysis.market_trend}`;
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
        e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
    };

    // Effective RTL state
    const effectiveRTL = isRTL || detectedRTL;

    return (
        <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-surface)]/50 relative" dir={effectiveRTL ? 'rtl' : 'ltr'}>
            {/* Animated Background Blobs */}
            <AnimatedBlobs />

            {/* Empty State with Centered Input */}
            {!hasMessages ? (
                <div className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 z-10 relative">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center mb-8"
                    >
                        <div className="size-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--color-teal-accent)] to-[var(--color-primary)] flex items-center justify-center shadow-2xl">
                            <Sparkles size={40} className="text-white" />
                        </div>
                        <h2 className="text-2xl font-bold text-[var(--color-text-primary)] mb-2">
                            {effectiveRTL ? 'مرحباً بك في عمرو' : 'Welcome to AMR AI'}
                        </h2>
                        <p className="text-[var(--color-text-muted)]">
                            {effectiveRTL ? 'مساعدك العقاري الذكي' : 'Your intelligent real estate assistant'}
                        </p>
                    </motion.div>

                    {/* Centered Input */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="w-full px-4"
                    >
                        <ChatInput
                            value={input}
                            onChange={handleInputChange}
                            onSend={() => handleSend()}
                            onKeyDown={handleKeyDown}
                            isTyping={isTyping}
                            inputRef={inputRef}
                            isCentered={true}
                            isRTL={effectiveRTL}
                        />
                    </motion.div>
                </div>
            ) : (
                <>
                    {/* Chat History */}
                    <div
                        ref={scrollRef}
                        onScroll={handleScroll}
                        className="flex-1 overflow-y-auto p-4 md:p-8 space-y-10 z-10 relative scroll-smooth chat-scrollbar"
                    >
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
                                    enableTypewriter={index === messages.length - 1}
                                    onCopy={() => handleCopy(message.id)}
                                    copied={message.copied}
                                    isRTL={effectiveRTL}
                                    onPropertySelect={handlePropertySelect}
                                />
                            )
                        ))}

                        {isTyping && <TypingIndicator isRTL={effectiveRTL} />}
                        <div className="h-6" /> {/* Spacer */}
                    </div>

                    {/* Scroll to Bottom Button */}
                    <AnimatePresence>
                        {showScrollButton && (
                            <motion.button
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 20 }}
                                onClick={scrollToBottom}
                                className={`absolute bottom-32 ${effectiveRTL ? 'left-8' : 'right-8'} z-20 p-3 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] shadow-lg hover:shadow-xl transition-all`}
                            >
                                <ChevronDown size={20} className="text-[var(--color-text-muted)]" />
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Bottom Input Area */}
                    <div className="p-4 md:p-6 bg-gradient-to-t from-[var(--color-surface)] via-[var(--color-surface)] to-transparent z-20">
                        <ChatInput
                            value={input}
                            onChange={handleInputChange}
                            onSend={() => handleSend()}
                            onKeyDown={handleKeyDown}
                            isTyping={isTyping}
                            inputRef={inputRef}
                            isCentered={false}
                            isRTL={effectiveRTL}
                        />
                    </div>
                </>
            )}
        </main>
    );
}
