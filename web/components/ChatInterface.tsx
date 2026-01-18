'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send,
    ShieldCheck,
    Sparkles,
    Menu,
    Plus,
    PanelLeftClose,
    PanelLeft,
    Copy,
    Check,
    ChevronDown
} from 'lucide-react';
import ConversationHistory from './ConversationHistory';
import VisualizationRenderer from './visualizations/VisualizationRenderer';
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
        <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700 hover:border-green-500/50 transition-colors">
            <div className="flex justify-between items-start mb-2">
                <h4 className="font-semibold text-slate-900 dark:text-white text-sm line-clamp-1">
                    {property.title}
                </h4>
                {property.wolf_score && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        property.wolf_score >= 80
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : property.wolf_score >= 60
                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                            : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                    }`}>
                        {property.wolf_score}/100
                    </span>
                )}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
                {property.location} • {property.size_sqm} sqm • {property.bedrooms} bed
            </p>
            <div className="flex justify-between items-center">
                <span className="text-green-600 dark:text-green-400 font-bold">
                    {formatPrice(property.price)}
                </span>
                {property.valuation_verdict === 'BARGAIN' && (
                    <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">
                        La2ta!
                    </span>
                )}
            </div>
        </div>
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
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`group flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
        >
            {/* AMR Avatar */}
            {!isUser && (
                <div className="flex-shrink-0 mt-1">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-green-500/20">
                        A
                    </div>
                </div>
            )}

            <div className={`flex flex-col max-w-[85%] md:max-w-[75%] space-y-3`}>
                {/* Message Bubble */}
                <div className={`relative rounded-2xl p-4 ${
                    isUser
                        ? 'bg-green-600 text-white rounded-br-sm'
                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-sm border border-slate-100 dark:border-slate-700 shadow-sm'
                }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap" dir="auto">
                        {message.content}
                    </div>

                    {/* Copy Button (AMR messages only) */}
                    {!isUser && (
                        <button
                            onClick={() => onCopy(message.id)}
                            className="absolute -bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white dark:bg-slate-700 rounded-full p-1.5 shadow-md border border-slate-200 dark:border-slate-600"
                        >
                            {message.copied ? (
                                <Check size={12} className="text-green-500" />
                            ) : (
                                <Copy size={12} className="text-slate-400" />
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
                                className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm"
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
                    <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
                        {message.properties.slice(0, 4).map((prop) => (
                            <PropertyCard key={prop.id} property={prop} />
                        ))}
                    </div>
                )}
            </div>

            {/* User Avatar (placeholder space for alignment) */}
            {isUser && <div className="w-8 flex-shrink-0" />}
        </motion.div>
    );
}

// Typing Indicator
function TypingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-4"
        >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex-shrink-0 flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-green-500/20">
                A
            </div>
            <div className="flex items-center gap-1.5 bg-white dark:bg-slate-800 px-4 py-3 rounded-2xl rounded-bl-sm border border-slate-100 dark:border-slate-700 shadow-sm">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" />
            </div>
        </motion.div>
    );
}

// Empty State
function EmptyState() {
    const suggestions = [
        "عايز شقة في التجمع تحت 5 مليون",
        "قارنلي بين زايد والتجمع للاستثمار",
        "إيه أحسن منطقة للعائد الإيجاري؟",
        "Show me properties in New Cairo"
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center px-4 py-12"
        >
            <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-green-500/20">
                <span className="text-4xl font-bold text-white">A</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Ahlan! Ana Amr
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-md">
                Your AI Real Estate Consultant. I help you find verified properties,
                analyze market trends, and protect your investment.
            </p>

            <div className="grid gap-3 w-full max-w-lg">
                <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                    Try asking
                </p>
                {suggestions.map((suggestion, idx) => (
                    <button
                        key={idx}
                        className="text-left px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 text-slate-700 dark:text-slate-300 text-sm hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/10 transition-all"
                    >
                        {suggestion}
                    </button>
                ))}
            </div>
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
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    // Check scroll position for "scroll to bottom" button
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
    const handleSend = async () => {
        const text = input.trim();
        if (!text || isTyping) return;

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: text,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        // Reset textarea height
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
        }

        try {
            const { data } = await api.post('/api/chat', { message: text });

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
        e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
    };

    // New conversation
    const handleNewConversation = () => {
        setMessages([]);
        setInput('');
    };

    return (
        <div className="flex h-[calc(100vh-64px)] bg-slate-100 dark:bg-slate-950 overflow-hidden">
            {/* Desktop Sidebar */}
            <div className={`hidden md:flex flex-col bg-slate-900 dark:bg-black transition-all duration-300 ${
                isSidebarCollapsed ? 'w-0 overflow-hidden' : 'w-64'
            }`}>
                <div className="p-4 border-b border-slate-800">
                    <button
                        onClick={handleNewConversation}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors text-sm font-medium"
                    >
                        <Plus size={18} />
                        New Chat
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2">
                    <ConversationHistory
                        isOpen={true}
                        onClose={() => {}}
                        onSelectConversation={(id) => console.log("Selected:", id)}
                        onNewConversation={handleNewConversation}
                        isDesktopSidebar={true}
                    />
                </div>

                <div className="p-4 border-t border-slate-800">
                    <div className="flex items-center gap-3 text-slate-400 text-xs">
                        <ShieldCheck size={14} className="text-green-500" />
                        <span>Powered by Wolf Brain V5</span>
                    </div>
                </div>
            </div>

            {/* Sidebar Toggle */}
            <button
                onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                className="hidden md:flex absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-slate-800 hover:bg-slate-700 text-white p-2 rounded-r-lg transition-colors"
                style={{ left: isSidebarCollapsed ? 0 : '256px' }}
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
            <div className="flex-1 flex flex-col h-full bg-white dark:bg-slate-900">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="md:hidden p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        >
                            <Menu size={20} />
                        </button>
                        <div className="flex items-center gap-2">
                            <div className="relative">
                                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold shadow-md">
                                    A
                                </div>
                                <div className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-400 border-2 border-white dark:border-slate-900 rounded-full" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-slate-900 dark:text-white text-sm flex items-center gap-1.5">
                                    Amr <ShieldCheck size={14} className="text-green-500" />
                                </h3>
                                <p className="text-xs text-slate-500 dark:text-slate-400">
                                    Wolf of Osool
                                </p>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={handleNewConversation}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <Plus size={16} />
                        <span className="hidden sm:inline">New</span>
                    </button>
                </div>

                {/* Messages Area */}
                <div
                    ref={scrollRef}
                    onScroll={handleScroll}
                    className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
                >
                    {messages.length === 0 ? (
                        <EmptyState />
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
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 10 }}
                            onClick={scrollToBottom}
                            className="absolute bottom-32 left-1/2 -translate-x-1/2 bg-slate-800 dark:bg-slate-700 text-white p-2 rounded-full shadow-lg hover:bg-slate-700 dark:hover:bg-slate-600 transition-colors"
                        >
                            <ChevronDown size={20} />
                        </motion.button>
                    )}
                </AnimatePresence>

                {/* Input Area */}
                <div className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4">
                    <div className="max-w-4xl mx-auto">
                        <div className="relative flex items-end bg-slate-100 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 focus-within:border-green-500 focus-within:ring-2 focus-within:ring-green-500/20 transition-all">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                placeholder="اسأل عمرو عن أي حاجة في العقارات..."
                                rows={1}
                                className="flex-1 bg-transparent text-slate-900 dark:text-white py-4 px-5 text-sm resize-none focus:outline-none max-h-[200px]"
                                dir="auto"
                            />
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || isTyping}
                                className="m-2 w-10 h-10 bg-green-600 hover:bg-green-700 disabled:bg-slate-300 dark:disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-all shadow-lg shadow-green-600/20 disabled:shadow-none"
                            >
                                <Send size={18} />
                            </button>
                        </div>

                        <p className="text-center mt-3 text-[10px] text-slate-400 flex items-center justify-center gap-1.5">
                            <Sparkles size={10} className="text-amber-500" />
                            <span>Powered by Osool Hybrid Brain V5 (Claude + GPT-4o + XGBoost)</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
