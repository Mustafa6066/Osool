'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import {
    Menu, Plus, Mic, ArrowUp, Loader2,
    MessageSquare, Home, BarChart3,
    Rocket, Building2, MapPin, TrendingUp
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { streamChat } from '@/lib/api';
import ChartVisualization from './ChartVisualization';
import Sidebar from '@/components/Sidebar';

/**
 * Sanitize content to prevent XSS attacks.
 * Uses DOMPurify to remove potentially dangerous HTML/JS.
 */
const sanitizeContent = (content: string): string => {
    if (typeof window === 'undefined') return content;
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
        ALLOW_DATA_ATTR: false,
    });
};

// --- User Message Component ---
const UserMessage = ({ content }: { content: string }) => {
    // Sanitize user content to prevent XSS
    const safeContent = useMemo(() => sanitizeContent(content), [content]);

    return (
        <div className="flex flex-col items-end gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-end gap-3 max-w-[80%] md:max-w-[60%]">
                <div className="flex flex-col gap-1 items-end">
                    <div className="bg-[var(--color-surface)] text-[var(--color-text-primary)] px-5 py-3 rounded-2xl rounded-tr-sm border border-[var(--color-border)] leading-relaxed text-[15px] shadow-sm" dir="auto">
                        {safeContent}
                    </div>
                </div>
                <div className="w-9 h-9 rounded-full bg-[var(--color-primary-light)] shrink-0 border border-[var(--color-primary)]/30 flex items-center justify-center text-xs text-[var(--color-primary)] font-bold">
                    ME
                </div>
            </div>
        </div>
    );
};

// --- AMR Agent Message Component ---
const AgentMessage = ({ content, visualizations, properties, isTyping }: any) => {
    // Sanitize AI content to prevent XSS from malicious data
    const safeContent = useMemo(() => sanitizeContent(content || ''), [content]);

    return (
        <div className="flex flex-col items-start gap-2 w-full animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="flex items-start gap-3 w-full max-w-5xl">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] shrink-0 flex items-center justify-center shadow-lg shadow-[var(--color-primary)]/20">
                    <MessageSquare size={18} className="text-white" />
                </div>
                <div className="flex-1 flex flex-col gap-4">
                    <div className="flex items-baseline justify-between w-full">
                        <span className="text-[#a2b3af] text-xs">AMR Agent • Active now</span>
                    </div>

                    {/* Text Content with Markdown Support - XSS Protected */}
                    <div
                        className="text-[var(--color-text-primary)] leading-loose text-[16px] max-w-[680px] prose prose-invert prose-headings:text-[var(--color-text-primary)] prose-p:text-[var(--color-text-primary)] prose-strong:text-[var(--color-primary)] prose-li:text-[var(--color-text-primary)] prose-code:text-[var(--color-secondary)] prose-pre:bg-[var(--color-surface-elevated)] prose-pre:border prose-pre:border-[var(--color-border)]"
                        dir="auto"
                    >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {safeContent}
                        </ReactMarkdown>
                        {isTyping && (
                            <span className="inline-block w-1.5 h-4 bg-[var(--color-primary)] animate-pulse ml-1 align-middle"></span>
                        )}
                    </div>

                    {/* Properties Grid */}
                    {properties && properties.length > 0 && (
                        <div className="space-y-4 mt-2 w-full max-w-3xl">
                            {properties.map((prop: any, idx: number) => (
                                <div
                                    key={idx}
                                    className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-300 group cursor-pointer"
                                >
                                    <div className="flex flex-col sm:flex-row">
                                        {/* Image Section */}
                                        <div className="w-full sm:w-2/5 h-56 sm:h-auto bg-slate-800 relative overflow-hidden">
                                            <div className="absolute inset-0 flex items-center justify-center text-slate-600 bg-gradient-to-br from-slate-800 to-slate-900">
                                                <Building2 size={64} opacity={0.15} />
                                            </div>
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent sm:bg-gradient-to-r"></div>
                                            <div className="absolute top-3 left-3 bg-[var(--color-surface-glass)] backdrop-blur-md text-[var(--color-primary)] text-[10px] font-bold px-2.5 py-1 rounded-md uppercase tracking-wide border border-[var(--color-border-light)] shadow-sm">
                                                Top Pick
                                            </div>
                                            <div className="absolute bottom-3 left-3 sm:hidden text-white">
                                                <p className="text-lg font-bold drop-shadow-md">
                                                    {prop.price.toLocaleString()} EGP
                                                </p>
                                            </div>
                                        </div>

                                        {/* Content Section */}
                                        <div className="p-5 flex flex-col justify-between flex-1">
                                            <div>
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="px-2 py-0.5 rounded bg-[var(--color-primary-light)] text-[var(--color-primary-hover)] text-[10px] font-bold uppercase tracking-wider">
                                                        High Growth
                                                    </div>
                                                    <div className="flex items-center gap-1 bg-[var(--color-surface)] border border-[var(--color-border)] px-2 py-1 rounded-md">
                                                        <span className="text-amber-400 text-xs">★</span>
                                                        <span className="text-xs font-bold text-[var(--color-text-primary)]">
                                                            {prop.wolf_score || '9.2'}
                                                        </span>
                                                    </div>
                                                </div>
                                                <h3 className="text-lg font-bold text-[var(--color-text-primary)] leading-tight mb-1 group-hover:text-[var(--color-primary)] transition-colors">
                                                    {prop.title}
                                                </h3>
                                                <p className="text-[13px] text-[var(--color-text-muted)] mb-3 flex items-center gap-1">
                                                    <MapPin size={14} />
                                                    {prop.location}
                                                </p>
                                                <div className="hidden sm:block text-2xl font-extrabold text-[var(--color-text-primary)] mb-4 tracking-tight">
                                                    {prop.price.toLocaleString()} EGP
                                                </div>

                                                {/* Property Stats */}
                                                <div className="grid grid-cols-3 gap-2 py-3 border-t border-b border-[var(--color-border)] text-[var(--color-text-secondary)]">
                                                    <div className="flex flex-col items-center">
                                                        <span className="text-xs mb-1 opacity-70">🛏️</span>
                                                        <span className="text-xs font-bold">
                                                            {prop.bedrooms || 3} Bed
                                                        </span>
                                                    </div>
                                                    <div className="flex flex-col items-center border-l border-[var(--color-border)]">
                                                        <span className="text-xs mb-1 opacity-70">🚿</span>
                                                        <span className="text-xs font-bold">
                                                            {prop.bathrooms || 2} Bath
                                                        </span>
                                                    </div>
                                                    <div className="flex flex-col items-center border-l border-[var(--color-border)]">
                                                        <span className="text-xs mb-1 opacity-70">📏</span>
                                                        <span className="text-xs font-bold">
                                                            {prop.size_sqm || '180'}m²
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Action Buttons */}
                                            <div className="flex gap-3 mt-4">
                                                <button className="flex-1 bg-[var(--chat-primary)] hover:bg-[var(--chat-primary)]/90 text-white py-2.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-colors shadow-lg shadow-[var(--chat-primary)]/20 hover:shadow-[var(--chat-primary)]/30">
                                                    View Details
                                                </button>
                                                <button className="px-3 py-2 border border-[var(--color-border)] hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-primary)] transition-colors">
                                                    <span className="text-xl">🔖</span>
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Price Appreciation Forecast */}
                                    {prop.show_chart !== false && (
                                        <div className="px-6 py-5 bg-[var(--color-surface)]/50 border-t border-[var(--color-border)]">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="text-xs font-bold text-[var(--color-text-primary)]">
                                                    Price Appreciation Forecast (5 Years)
                                                </h4>
                                                <span className="text-xs font-bold text-green-600 dark:text-green-400 flex items-center gap-1 bg-green-100 dark:bg-green-900/30 px-2 py-0.5 rounded">
                                                    <TrendingUp size={14} /> +12.4% Projected
                                                </span>
                                            </div>
                                            {/* Simple Chart Visualization */}
                                            <div className="h-20 w-full mt-3 flex items-end gap-1">
                                                {[65, 70, 68, 75, 82, 88].map((height, i) => (
                                                    <div
                                                        key={i}
                                                        className="flex-1 bg-gradient-to-t from-[var(--color-primary)] to-[var(--color-secondary)] rounded-t transition-all hover:opacity-80"
                                                        style={{ height: `${height}%` }}
                                                    ></div>
                                                ))}
                                            </div>
                                            <div className="flex justify-between text-[10px] text-gray-500 mt-2">
                                                <span>2024</span>
                                                <span>2025</span>
                                                <span>2026</span>
                                                <span>2027</span>
                                                <span>2028</span>
                                                <span>2029</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Visualizations (Charts, etc) */}
                    {visualizations && visualizations.length > 0 && (
                        <div className="space-y-4 mt-2">
                            {visualizations.map((viz: any, idx: number) => (
                                <ChartVisualization
                                    key={idx}
                                    type={viz.type || 'bar'}
                                    title={viz.title || 'Market Analysis'}
                                    data={viz.data}
                                    labels={viz.labels}
                                    trend={viz.trend}
                                    subtitle={viz.subtitle}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// --- Main Chat Interface ---
export default function ChatInterface() {
    const { user } = useAuth();
    const { language } = useLanguage();
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [input]);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;

        const userMsg = { role: 'user', content: input, id: Date.now().toString() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        // Add placeholder AI message
        const aiMsgId = (Date.now() + 1).toString();
        setMessages((prev) => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';

        try {
            // Pass language context for proper AI response localization
            await streamChat(userMsg.content, 'default-session', {
                onToken: (token) => {
                    fullResponse += token;
                    setMessages((prev) =>
                        prev.map((m) => (m.id === aiMsgId ? { ...m, content: fullResponse } : m))
                    );
                },
                onToolStart: (tool) => {
                    // Could add tool indicator state here
                },
                onToolEnd: (tool) => { },
                onComplete: (data) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === aiMsgId
                                ? {
                                    ...m,
                                    content: fullResponse,
                                    properties: data.properties,
                                    visualizations: data.ui_actions,
                                    isTyping: false,
                                }
                                : m
                        )
                    );
                    setIsTyping(false);
                },
                onError: (err) => {
                    console.error(err);
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === aiMsgId
                                ? {
                                    ...m,
                                    content: fullResponse + '\n\n[System Error: Failed to complete response]',
                                    isTyping: false,
                                }
                                : m
                        )
                    );
                    setIsTyping(false);
                },
            }, language === 'ar' ? 'ar' : language === 'en' ? 'en' : 'auto');
        } catch (e) {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setInput('');
    };

    const getDisplayName = () => {
        if (!user) return 'Agent';
        // Use display_name from JWT token if available (set by backend mapping)
        if ((user as any).display_name) return (user as any).display_name;
        const email = user?.email?.toLowerCase();
        // Fallback: Check admin users first
        if (email === 'mustafa@osool.eg') return 'Mustafa';
        if (email === 'hani@osool.eg') return 'Hani';
        if (email === 'abady@osool.eg') return 'Abady';
        if (email === 'sama@osool.eg') return 'Mrs. Mustafa';
        // Then check full_name
        if (user.full_name && user.full_name !== 'Wallet User') return user.full_name;
        // Fallback to email
        return email?.split('@')[0] || 'Agent';
    };

    const getUserInitials = () => {
        const name = getDisplayName();
        if (name.startsWith('Mrs.')) {
            const actualName = name.substring(4).trim();
            return actualName.substring(0, 2).toUpperCase();
        }
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <div className="flex h-[calc(100vh-64px)] w-full relative bg-[var(--color-background)] font-display selection:bg-[#267360] selection:text-[var(--color-text-primary)] overflow-hidden">
            <Sidebar onNewChat={handleNewChat} />

            <main className="flex-1 flex flex-col h-full relative">
                {/* Header */}
                <header className="h-16 border-b border-[var(--color-border)] flex items-center justify-between px-6 bg-[var(--color-background)]/80 backdrop-blur-md z-10 sticky top-0">
                    <div className="flex items-center gap-3">
                        <button className="md:hidden text-[var(--color-text-muted)]">
                            <Menu size={24} />
                        </button>
                        <div className="flex items-center gap-2">
                            <Rocket className="text-[var(--color-primary)]" size={20} />
                            <h2 className="text-lg font-bold tracking-tight text-[var(--color-text-primary)]">
                                Mission Control: Real Estate Analysis
                            </h2>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <Link
                            href="/"
                            className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                            title="Back to Home"
                        >
                            <Home size={20} />
                        </Link>
                        <div className="w-8 h-8 rounded-full bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)] font-bold text-xs ml-2 border border-[var(--color-primary)]/30">
                            {getUserInitials()}
                        </div>
                    </div>
                </header>

                {/* Chat Area */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth scrollbar-hide relative"
                    style={{ paddingBottom: messages.length === 0 ? '0px' : '180px' }}
                >
                    {messages.length === 0 ? (
                        // Empty State - Centered Welcome
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center space-y-6 w-full max-w-2xl px-4"
                        >
                            <div className="w-20 h-20 rounded-[2rem] bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center shadow-2xl shadow-[var(--color-primary)]/30 mb-4 mx-auto">
                                <MessageSquare size={40} className="text-white fill-white/20" />
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-[var(--color-text-primary)]">
                                Welcome, <span className="text-[var(--color-primary)]">{getDisplayName()}</span>.
                            </h1>
                            <p className="text-[var(--color-text-muted)] text-lg max-w-lg mx-auto">
                                Ready to analyze the market? Ask about price trends, property valuations, or investment
                                opportunities.
                            </p>

                            {/* Starter Prompts */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-8">
                                {[
                                    { icon: <BarChart3 size={20} />, text: 'Show price trends in New Cairo' },
                                    { icon: <Building2 size={20} />, text: 'Compare developers in 5th Settlement' },
                                    { icon: <MapPin size={20} />, text: 'Best ROI in North Coast' },
                                ].map((prompt, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setInput(prompt.text)}
                                        className="flex flex-col items-start gap-2 p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary)]/30 transition-all text-left group"
                                    >
                                        <div className="text-[var(--color-primary)]">{prompt.icon}</div>
                                        <span className="text-sm text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)] transition-colors">
                                            {prompt.text}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    ) : (
                        // Messages
                        messages.map((msg) =>
                            msg.role === 'user' ? (
                                <UserMessage key={msg.id} content={msg.content} />
                            ) : (
                                <AgentMessage
                                    key={msg.id}
                                    content={msg.content}
                                    visualizations={msg.visualizations}
                                    properties={msg.properties}
                                    isTyping={msg.isTyping}
                                />
                            )
                        )
                    )}
                </div>

                {/* Input Area - Dynamically positioned */}
                <motion.div
                    layout
                    initial={false}
                    animate={
                        messages.length === 0
                            ? { position: 'absolute', top: 'auto', bottom: '0', left: '50%', x: '-50%', width: '100%', maxWidth: '48rem' }
                            : { position: 'absolute', top: 'auto', bottom: '1.5rem', left: '50%', x: '-50%', width: '100%', maxWidth: '48rem' }
                    }
                    transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                    className="px-4 md:px-8 z-20"
                >
                    <div className="w-full bg-[var(--color-surface)]/90 backdrop-blur-xl border border-[var(--color-border)] rounded-2xl shadow-2xl p-2 flex items-end gap-2 transition-all focus-within:border-[var(--color-primary)]/50 focus-within:ring-1 focus-within:ring-[var(--color-primary)]/50">
                        <button className="w-10 h-10 flex items-center justify-center rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors shrink-0">
                            <Plus size={20} />
                        </button>
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 bg-transparent border-none text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)]/50 focus:ring-0 text-sm font-medium py-3 px-0 resize-none max-h-[200px] scrollbar-hide"
                            placeholder={
                                language === 'ar'
                                    ? 'اسأل عمرو عن العقارات...'
                                    : 'Ask AMR about real estate...'
                            }
                            rows={1}
                            dir="auto"
                        />
                        <button className="w-10 h-10 flex items-center justify-center rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors shrink-0">
                            <Mic size={20} />
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="w-10 h-10 flex items-center justify-center rounded-xl bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white shadow-lg shadow-[var(--color-primary)]/20 transition-all shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isTyping ? (
                                <Loader2 size={18} className="animate-spin" />
                            ) : (
                                <ArrowUp size={20} />
                            )}
                        </button>
                    </div>

                    {/* Disclaimer */}
                    {messages.length === 0 && (
                        <p className="text-center text-xs text-[#a2b3af]/50 mt-3 pb-4">
                            AI can make mistakes. Please verify important information.
                        </p>
                    )}
                </motion.div>
            </main>

            <style jsx global>{`
                .scrollbar-hide::-webkit-scrollbar {
                    display: none;
                }
                .scrollbar-hide {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
            `}</style>
        </div>
    );
}
