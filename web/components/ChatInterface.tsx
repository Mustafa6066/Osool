'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    Sparkles,
    Menu,
    Plus,
    PanelLeftClose,
    PanelLeft,
    Copy,
    Check,
    ChevronDown,
    MessageSquare
} from 'lucide-react';
import ConversationHistory from './ConversationHistory';
import VisualizationRenderer from './visualizations/VisualizationRenderer';
import ThemeToggle from './ThemeToggle';
import api from '../lib/api';

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
    valuation_verdict?: string;
    la2ta_score?: number;
    [key: string]: any;
};

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    visualizations?: UIAction[];
    properties?: Property[];
    psychology?: any;
    timestamp?: Date;
    copied?: boolean;
};

// Format price in Egyptian style
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M EGP`;
    }
    return `${(price / 1_000).toFixed(0)}K EGP`;
};

// Property Card Component
function PropertyCard({ property }: { property: Property }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="group relative bg-[var(--color-surface)] rounded-2xl p-4 
                       border border-[var(--color-border)] hover:border-[var(--color-primary)]/50
                       shadow-sm hover:shadow-md transition-all duration-300"
        >
            <div className="flex justify-between items-start mb-3">
                <h4 className="font-semibold text-[var(--color-text-primary)] text-sm line-clamp-1 flex-1 pr-2">
                    {property.title}
                </h4>
                {property.wolf_score && (
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full flex-shrink-0 ${property.wolf_score >= 80
                            ? 'bg-emerald-500/10 text-emerald-500 ring-1 ring-emerald-500/20'
                            : property.wolf_score >= 60
                                ? 'bg-amber-500/10 text-amber-500 ring-1 ring-amber-500/20'
                                : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                        }`}>
                        {property.wolf_score}/100
                    </span>
                )}
            </div>
            <p className="text-xs text-[var(--color-text-muted)] mb-3 flex items-center gap-2">
                <span>{property.location}</span>
                <span className="w-1 h-1 rounded-full bg-[var(--color-border)]"></span>
                <span>{property.size_sqm} sqm</span>
                <span className="w-1 h-1 rounded-full bg-[var(--color-border)]"></span>
                <span>{property.bedrooms} bed</span>
            </p>
            <div className="flex justify-between items-center">
                <span className="text-[var(--color-primary)] font-bold text-lg">
                    {formatPrice(property.price)}
                </span>
                {property.valuation_verdict === 'BARGAIN' && (
                    <span className="text-xs bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-3 py-1 rounded-full font-medium">
                        🐺 La2ta!
                    </span>
                )}
            </div>
        </motion.div>
    );
}

// Message Component
function ChatMessage({
    message,
    onCopy
}: {
    message: Message;
    onCopy: (id: string) => void;
}) {
    const isUser = message.role === 'user';

    return (
        <motion.div
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
            className={`group flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            {/* AMR Avatar */}
            {!isUser && (
                <div className="flex-shrink-0 mt-1">
                    <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 
                                  flex items-center justify-center text-white text-sm font-bold 
                                  shadow-lg shadow-emerald-500/25">
                        A
                    </div>
                </div>
            )}

            <div className={`flex flex-col max-w-[85%] md:max-w-[70%] space-y-3`}>
                {/* Message Bubble */}
                <div className={`relative rounded-2xl px-4 py-3 message-bubble ${isUser
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-br-md'
                        : 'glass border border-[var(--color-border)] text-[var(--color-text-primary)] rounded-bl-md'
                    }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap" dir="auto">
                        {message.content}
                    </div>

                    {/* Copy Button (AMR messages only) */}
                    {!isUser && (
                        <button
                            onClick={() => onCopy(message.id)}
                            className="absolute -bottom-2 right-2 opacity-0 group-hover:opacity-100 
                                     transition-all duration-200 bg-[var(--color-surface)] rounded-full p-1.5 
                                     shadow-md border border-[var(--color-border)] hover:border-[var(--color-primary)]"
                        >
                            {message.copied ? (
                                <Check size={12} className="text-emerald-500" />
                            ) : (
                                <Copy size={12} className="text-[var(--color-text-muted)]" />
                            )}
                        </button>
                    )}
                </div>

                {/* Inline Visualizations */}
                {message.visualizations && message.visualizations.length > 0 && (
                    <div className="space-y-3">
                        {message.visualizations.map((viz, idx) => (
                            <motion.div
                                key={`${message.id}-viz-${idx}`}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className="rounded-2xl overflow-hidden border border-[var(--color-border)] 
                                          bg-[var(--color-surface)] shadow-lg"
                            >
                                <VisualizationRenderer
                                    type={viz.type}
                                    data={viz.data}
                                />
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Property Cards */}
                {message.properties && message.properties.length > 0 && (
                    <div className="mt-2 grid gap-3 grid-cols-1 lg:grid-cols-2">
                        {message.properties.slice(0, 4).map((prop) => (
                            <PropertyCard key={prop.id} property={prop} />
                        ))}
                    </div>
                )}
            </div>

            {/* User Avatar space */}
            {isUser && <div className="w-9 flex-shrink-0" />}
        </motion.div>
    );
}

// Typing Indicator
function TypingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-3"
        >
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 
                          flex-shrink-0 flex items-center justify-center text-white text-sm font-bold 
                          shadow-lg shadow-emerald-500/25">
                A
            </div>
            <div className="flex items-center gap-1.5 glass px-5 py-3 rounded-2xl rounded-bl-md border border-[var(--color-border)]">
                <motion.span
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 bg-emerald-500 rounded-full"
                />
                <motion.span
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.15 }}
                    className="w-2 h-2 bg-emerald-500 rounded-full"
                />
                <motion.span
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.3 }}
                    className="w-2 h-2 bg-emerald-500 rounded-full"
                />
            </div>
        </motion.div>
    );
}

// Empty State
function EmptyState({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) {
    const suggestions = [
        { text: "عايز شقة في التجمع تحت 5 مليون", icon: "🏠" },
        { text: "قارنلي بين زايد والتجمع للاستثمار", icon: "📊" },
        { text: "إيه أحسن منطقة للعائد الإيجاري؟", icon: "💰" },
        { text: "Show me properties in New Cairo", icon: "🔍" }
    ];

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center h-full text-center px-4 py-12"
        >
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 20 }}
                className="w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-500 
                          flex items-center justify-center mb-8 shadow-2xl shadow-emerald-500/30"
            >
                <span className="text-4xl font-bold text-white">A</span>
            </motion.div>

            <motion.h2
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="text-3xl font-bold text-[var(--color-text-primary)] mb-3"
            >
                Ahlan! Ana Amr 👋
            </motion.h2>

            <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-[var(--color-text-secondary)] mb-10 max-w-md text-lg"
            >
                Your AI Real Estate Consultant. I help you find verified properties
                and protect your investment.
            </motion.p>

            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="grid gap-3 w-full max-w-lg"
            >
                <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mb-2 font-medium">
                    Try asking
                </p>
                {suggestions.map((suggestion, idx) => (
                    <motion.button
                        key={idx}
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 0.4 + idx * 0.1 }}
                        onClick={() => onSuggestionClick(suggestion.text)}
                        className="group text-left px-5 py-4 rounded-2xl border border-[var(--color-border)] 
                                 bg-[var(--color-surface)] text-[var(--color-text-secondary)] text-sm 
                                 hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)]
                                 transition-all duration-300 flex items-center gap-3"
                    >
                        <span className="text-xl">{suggestion.icon}</span>
                        <span className="group-hover:text-[var(--color-text-primary)] transition-colors">
                            {suggestion.text}
                        </span>
                    </motion.button>
                ))}
            </motion.div>
        </motion.div>
    );
}

// Main Chat Interface
export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [messages, isTyping]);

    // Check scroll position
    const handleScroll = useCallback(() => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
        }
    }, []);

    const scrollToBottom = () => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    };

    // Copy message content
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

    // Send message
    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || isTyping) return;

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
                content: data.response || data.message || "عذراً، حصل مشكلة. جرب تاني يا باشا.",
                visualizations: data.ui_actions || [],
                properties: data.properties || [],
                psychology: data.psychology,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, amrMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: 'amr',
                content: "عذراً، فيه مشكلة في الاتصال. جرب تاني بعد شوية يا باشا.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    // Handle keyboard
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    // Auto-resize textarea
    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
    };

    // New conversation
    const handleNewConversation = () => {
        setMessages([]);
        setInput('');
    };

    return (
        <div className="flex h-screen bg-[var(--color-background)] overflow-hidden">
            {/* Desktop Sidebar */}
            <motion.div
                initial={false}
                animate={{ width: isSidebarCollapsed ? 0 : 280 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="hidden md:flex flex-col bg-[var(--color-surface)] border-r border-[var(--color-border)] overflow-hidden"
            >
                <div className="p-4 border-b border-[var(--color-border)]">
                    <button
                        onClick={handleNewConversation}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 
                                 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl 
                                 font-medium shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30
                                 transition-all duration-300 hover:-translate-y-0.5"
                    >
                        <Plus size={18} />
                        New Chat
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-3 custom-scrollbar">
                    <ConversationHistory
                        isOpen={true}
                        onClose={() => { }}
                        onSelectConversation={(id) => console.log("Selected:", id)}
                        onNewConversation={handleNewConversation}
                        isDesktopSidebar={true}
                    />
                </div>

                <div className="p-4 border-t border-[var(--color-border)]">
                    <div className="flex items-center gap-3 text-[var(--color-text-muted)] text-xs">
                        <Sparkles size={14} className="text-emerald-500" />
                        <span>Powered by Wolf Brain V5</span>
                    </div>
                </div>
            </motion.div>

            {/* Sidebar Toggle */}
            <button
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="hidden md:flex absolute top-1/2 -translate-y-1/2 z-20 
                         bg-[var(--color-surface)] border border-[var(--color-border)] 
                         hover:border-[var(--color-primary)] text-[var(--color-text-secondary)] 
                         p-2 rounded-r-lg transition-all duration-300 shadow-md"
                style={{ left: isSidebarCollapsed ? 0 : 280 }}
            >
                {isSidebarCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
            </button>

            {/* Mobile Sidebar Overlay */}
            <ConversationHistory
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                onSelectConversation={(id) => {
                    console.log("Selected:", id);
                    setIsSidebarOpen(false);
                }}
                onNewConversation={() => {
                    handleNewConversation();
                    setIsSidebarOpen(false);
                }}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full">
                {/* Header */}
                <header className="flex items-center justify-between px-4 md:px-6 py-3 
                               border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 
                               backdrop-blur-xl sticky top-0 z-10">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="md:hidden p-2 text-[var(--color-text-secondary)] 
                                     hover:bg-[var(--color-surface-elevated)] rounded-xl transition-colors"
                        >
                            <Menu size={20} />
                        </button>
                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 
                                              flex items-center justify-center text-white font-bold shadow-lg shadow-emerald-500/20">
                                    A
                                </div>
                                <div className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 
                                              border-2 border-[var(--color-surface)] rounded-full" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-[var(--color-text-primary)] flex items-center gap-2">
                                    Amr
                                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                                        Online
                                    </span>
                                </h3>
                                <p className="text-xs text-[var(--color-text-muted)]">
                                    Wolf of Osool
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <button
                            onClick={handleNewConversation}
                            className="flex items-center gap-2 px-3 py-2 text-sm font-medium 
                                     text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] 
                                     rounded-xl transition-colors"
                        >
                            <Plus size={16} />
                            <span className="hidden sm:inline">New</span>
                        </button>
                    </div>
                </header>

                {/* Messages Area */}
                <div
                    ref={scrollRef}
                    onScroll={handleScroll}
                    className="flex-1 overflow-y-auto px-4 md:px-6 py-6 space-y-5 custom-scrollbar"
                >
                    {messages.length === 0 ? (
                        <EmptyState onSuggestionClick={(text) => handleSend(text)} />
                    ) : (
                        <AnimatePresence mode="popLayout">
                            {messages.map((msg) => (
                                <ChatMessage
                                    key={msg.id}
                                    message={msg}
                                    onCopy={handleCopy}
                                />
                            ))}
                            {isTyping && <TypingIndicator />}
                        </AnimatePresence>
                    )}
                </div>

                {/* Scroll to Bottom Button */}
                <AnimatePresence>
                    {showScrollButton && (
                        <motion.button
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            onClick={scrollToBottom}
                            className="absolute bottom-28 left-1/2 -translate-x-1/2 
                                     bg-[var(--color-surface)] border border-[var(--color-border)]
                                     text-[var(--color-text-secondary)] p-2 rounded-full shadow-lg 
                                     hover:border-[var(--color-primary)] transition-all"
                        >
                            <ChevronDown size={20} />
                        </motion.button>
                    )}
                </AnimatePresence>

                {/* Input Area */}
                <div className="border-t border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-xl p-4">
                    <div className="max-w-4xl mx-auto">
                        <div className="relative flex items-end bg-[var(--color-surface-elevated)] 
                                      rounded-2xl border border-[var(--color-border)] input-focus
                                      shadow-sm hover:shadow-md transition-all duration-300">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                placeholder="اسأل عمرو عن أي حاجة في العقارات..."
                                rows={1}
                                className="flex-1 bg-transparent text-[var(--color-text-primary)] py-4 px-5 
                                         text-sm resize-none focus:outline-none max-h-[150px] 
                                         placeholder:text-[var(--color-text-muted)]"
                                dir="auto"
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={!input.trim() || isTyping}
                                className="m-2 w-11 h-11 bg-gradient-to-r from-emerald-500 to-teal-500
                                         disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed 
                                         text-white rounded-xl flex items-center justify-center 
                                         transition-all duration-300 shadow-lg shadow-emerald-500/20 
                                         disabled:shadow-none hover:shadow-emerald-500/40 hover:-translate-y-0.5
                                         active:translate-y-0"
                            >
                                <Send size={18} />
                            </button>
                        </div>

                        <p className="text-center mt-3 text-[10px] text-[var(--color-text-muted)] 
                                    flex items-center justify-center gap-2">
                            <Sparkles size={10} className="text-amber-500" />
                            <span>Powered by Osool Hybrid Brain V5</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
