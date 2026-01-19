'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Copy, Check, ChevronDown, Sparkles, Plus, Mic } from 'lucide-react';
import AnimatedBlobs from './AnimatedBlobs';
import PropertyCardEnhanced from './PropertyCardEnhanced';
import { PropertyContext } from './ContextualPane';
import api from '@/lib/api';

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

// User Message Component
function UserMessage({ content, timestamp, isRTL }: { content: string; timestamp?: Date; isRTL: boolean }) {
    const messageIsArabic = isArabic(content);

    return (
        <div className={`flex ${messageIsArabic ? 'justify-start' : 'justify-end'} animate-in slide-in-from-bottom-2 fade-in duration-500`}>
            <div className={`flex flex-col ${messageIsArabic ? 'items-start' : 'items-end'} gap-1 max-w-[85%] md:max-w-[70%] lg:max-w-[60%]`}>
                <div
                    className="chat-message-user px-6 py-4 shadow-lg shadow-[var(--chat-primary)]/10"
                    dir={messageIsArabic ? 'rtl' : 'ltr'}
                >
                    <p className="leading-relaxed text-[15px] font-medium">{content}</p>
                </div>
                <span className={`text-[11px] font-medium text-gray-400 dark:text-gray-600 ${messageIsArabic ? 'ml-2' : 'mr-2'}`}>
                    {isRTL ? 'أنت' : 'You'} {timestamp && `• ${timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                </span>
            </div>
        </div>
    );
}

// AI Message Component
function AIMessage({
    content,
    properties,
    timestamp,
    enableTypewriter = true,
    onCopy,
    copied,
    isRTL,
    onPropertySelect
}: {
    content: string;
    properties?: Property[];
    timestamp?: Date;
    enableTypewriter?: boolean;
    onCopy?: () => void;
    copied?: boolean;
    isRTL: boolean;
    onPropertySelect?: (property: Property) => void;
}) {
    const { displayedText, isComplete } = useTypewriter(content, 12, enableTypewriter);
    const messageIsArabic = isArabic(content);

    return (
        <div className={`flex gap-5 max-w-full md:max-w-[90%] animate-in slide-in-from-bottom-4 fade-in duration-700 delay-150 ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
            <div className="flex-none flex flex-col items-center gap-2">
                <div className="size-10 rounded-xl bg-gradient-to-br from-[var(--chat-teal-accent)] to-[var(--chat-primary)] flex items-center justify-center shadow-lg shadow-teal-900/20">
                    <Sparkles size={20} className="text-white" />
                </div>
            </div>
            <div className={`flex flex-col gap-4 flex-1 min-w-0 ${messageIsArabic ? 'items-end' : 'items-start'}`}>
                <div>
                    <div className={`flex items-baseline gap-2 mb-1 ${messageIsArabic ? 'flex-row-reverse' : ''}`}>
                        <span className="text-sm font-bold text-gray-900 dark:text-white">{isRTL ? 'عمرو' : 'AMR AI'}</span>
                        <span className="text-[11px] text-gray-400 dark:text-gray-600">
                            {timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                    <div
                        className="chat-message-ai px-6 py-4 shadow-sm inline-block relative group"
                        dir={messageIsArabic ? 'rtl' : 'ltr'}
                    >
                        <p className="leading-relaxed text-[15px] text-gray-700 dark:text-gray-200">
                            {enableTypewriter ? displayedText : content}
                            {enableTypewriter && !isComplete && (
                                <span className="inline-block w-0.5 h-4 bg-[var(--chat-teal-accent)] ml-1 animate-pulse" />
                            )}
                        </p>
                        {isComplete && onCopy && (
                            <button
                                onClick={onCopy}
                                className={`absolute top-2 ${messageIsArabic ? 'left-2' : 'right-2'} p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20`}
                            >
                                {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} className="text-gray-500" />}
                            </button>
                        )}
                    </div>
                </div>

                {/* Property Cards - Only show real data from AI */}
                {properties && properties.length > 0 && isComplete && (
                    <div className="space-y-4 w-full">
                        {properties.map((prop) => (
                            <div key={prop.id} onClick={() => onPropertySelect?.(prop)} className="cursor-pointer">
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

// Typing Indicator
function TypingIndicator({ isRTL }: { isRTL: boolean }) {
    return (
        <div className={`flex gap-5 max-w-full md:max-w-[90%] ${isRTL ? 'flex-row-reverse' : ''}`}>
            <div className="flex-none">
                <div className="size-10 rounded-xl bg-gradient-to-br from-[var(--chat-teal-accent)] to-[var(--chat-primary)] flex items-center justify-center shadow-lg">
                    <Sparkles size={20} className="text-white animate-pulse" />
                </div>
            </div>
            <div className="chat-message-ai px-6 py-4 shadow-sm">
                <div className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
                    className="p-3 rounded-full text-gray-400 hover:text-[var(--chat-primary)] dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
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
                    className="flex-1 bg-transparent border-none focus:ring-0 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 px-3 py-3 text-base resize-none max-h-[150px] focus:outline-none"
                    dir="auto"
                />
                <div className={`flex items-center gap-1 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <button
                        className="p-3 rounded-full text-gray-400 hover:text-[var(--chat-primary)] dark:hover:text-white hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
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
                <p className="text-[10px] font-medium text-gray-400 dark:text-gray-600">
                    {isRTL ? 'الذكاء الاصطناعي يمكنه تقديم رؤى. تحقق من البيانات المالية بشكل مستقل.' : 'AI can generate insights. Verify financial data independently.'}
                </p>
            </div>
        </div>
    );
}

interface ChatMainProps {
    onNewConversation?: () => void;
    onPropertySelect?: (property: PropertyContext) => void;
    isRTL?: boolean;
}

export default function ChatMain({ onNewConversation, onPropertySelect, isRTL = false }: ChatMainProps) {
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

    const handlePropertySelect = (property: Property) => {
        if (onPropertySelect) {
            onPropertySelect({
                title: property.title,
                address: property.location,
                price: formatPrice(property.price),
                metrics: {
                    size: property.size_sqm,
                    bedrooms: property.bedrooms,
                    pricePerSqFt: `${Math.round(property.price / property.size_sqm).toLocaleString()} EGP`,
                },
                tags: property.developer ? [property.developer] : [],
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

            // Auto-select first property for contextual pane
            if (data.properties && data.properties.length > 0) {
                handlePropertySelect(data.properties[0]);
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
        <main className="flex-1 flex flex-col min-w-0 bg-white/50 dark:bg-[var(--chat-background-dark)]/50 relative" dir={effectiveRTL ? 'rtl' : 'ltr'}>
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
                        <div className="size-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[var(--chat-teal-accent)] to-[var(--chat-primary)] flex items-center justify-center shadow-2xl">
                            <Sparkles size={40} className="text-white" />
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                            {effectiveRTL ? 'مرحباً بك في عمرو' : 'Welcome to AMR AI'}
                        </h2>
                        <p className="text-gray-500 dark:text-[var(--chat-text-secondary)]">
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
                                className={`absolute bottom-32 ${effectiveRTL ? 'left-8' : 'right-8'} z-20 p-3 rounded-full bg-white dark:bg-[var(--chat-surface-dark)] border border-gray-200 dark:border-[var(--chat-border-dark)] shadow-lg hover:shadow-xl transition-all`}
                            >
                                <ChevronDown size={20} className="text-gray-600 dark:text-white" />
                            </motion.button>
                        )}
                    </AnimatePresence>

                    {/* Bottom Input Area */}
                    <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent dark:from-[var(--chat-background-dark)] dark:via-[var(--chat-background-dark)] dark:to-transparent z-20">
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
