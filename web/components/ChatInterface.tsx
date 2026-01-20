'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { streamChat } from '@/lib/api';
import ChartVisualization from './ChartVisualization';
import ContextualPane, { PropertyContext } from './chat/ContextualPane';
import PropertyCardMinimal from '@/components/PropertyCardMinimal';

// Utility for Material Symbols
const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => (
    <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>
        {name}
    </span>
);

/**
 * Sanitize content to prevent XSS attacks.
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
const UserMessage = ({ content, userName }: { content: string; userName?: string }) => {
    const safeContent = useMemo(() => sanitizeContent(content), [content]);

    return (
        <div className="flex justify-end animate-in slide-in-from-bottom-2 fade-in duration-500 mb-6">
            <div className="flex flex-col items-end gap-1 max-w-[85%] md:max-w-[70%] lg:max-w-[60%]">
                <div className="bg-white/10 dark:bg-white/5 backdrop-blur-md border border-white/10 text-[var(--color-text-primary)] px-6 py-4 rounded-3xl rounded-tr-sm shadow-sm">
                    <p className="leading-relaxed text-[15px] font-medium" dir="auto">{safeContent}</p>
                </div>
                <span className="text-[10px] font-medium text-[var(--color-text-muted)] mr-2 uppercase tracking-wider">{userName || 'You'}</span>
            </div>
        </div>
    );
};

// --- AMR Agent Message Component ---
const AgentMessage = ({ content, visualizations, properties, isTyping, onSelectProperty }: any) => {
    const safeContent = useMemo(() => sanitizeContent(content || ''), [content]);

    return (
        <div className="flex gap-5 max-w-full md:max-w-[90%] animate-in slide-in-from-bottom-4 fade-in duration-700 mb-8">
            {/* Agent Avatar */}
            <div className="flex-none hidden sm:flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-surface-dark)] border border-[var(--color-primary)]/20 flex items-center justify-center shadow-[0_0_15px_rgba(163,177,138,0.2)]">
                    <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)]" />
                </div>
            </div>

            <div className="flex flex-col gap-6 flex-1 min-w-0">
                {/* Agentic Core Panel */}
                <div className="relative glass-panel bg-white/80 dark:bg-[var(--color-surface-dark)]/40 rounded-2xl p-6 lg:p-8 shadow-soft-glow backdrop-blur-3xl border border-white/10">
                    {/* Header */}
                    <div className="flex items-center gap-3 mb-4 border-b border-black/5 dark:border-white/5 pb-4">
                        <div className="sm:hidden w-8 h-8 rounded-lg bg-[var(--color-primary)]/10 flex items-center justify-center">
                            <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)] text-sm" />
                        </div>
                        <div>
                            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-0.5">Agentic Core</h2>
                            <span className="text-xs text-[var(--color-primary)] font-display flex items-center gap-2">
                                {isTyping ? 'Processing Market Data' : 'Analysis Complete'}
                                {isTyping && (
                                    <span className="flex space-x-1">
                                        <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                                        <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                        <span className="w-1 h-1 bg-[var(--color-primary)] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                                    </span>
                                )}
                            </span>
                        </div>
                    </div>

                    {/* Content */}
                    <div
                        className="leading-loose text-[15px] prose dark:prose-invert max-w-none text-[var(--color-text-primary)] font-sans"
                        dir="auto"
                    >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {safeContent}
                        </ReactMarkdown>
                    </div>
                </div>

                {/* Properties Grid */}
                {properties && properties.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {properties.map((prop: any, idx: number) => (
                            <PropertyCardMinimal
                                key={idx}
                                property={prop}
                                onClick={() => onSelectProperty && onSelectProperty(prop)}
                            />
                        ))}
                    </div>
                )}

                {/* Visualizations (Charts) */}
                {visualizations && visualizations.length > 0 && (
                    <div className="space-y-4">
                        {visualizations.map((viz: any, idx: number) => {
                            // Adapt backend data logic from original
                            let chartType: any = viz.type || 'bar';
                            let chartData = viz.data;
                            let chartLabels = viz.labels;
                            let chartTitle = viz.title || 'Market Analyis';
                            let chartSubtitle = viz.subtitle;

                            if (viz.type === 'inflation_killer' && viz.data?.projections) {
                                chartType = 'line';
                                chartTitle = 'Inflation Hedge: Property vs Cash';
                                chartData = viz.data.projections;
                                chartLabels = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5'];
                                chartSubtitle = `Projected value after ${viz.data.years} years`;
                            } else if (viz.type === 'market_trend_chart') {
                                chartType = 'line';
                            }

                            if (!Array.isArray(chartData)) chartData = [];
                            if (chartData.length === 0) return null;

                            return (
                                <div key={idx} className="glass-panel rounded-2xl p-4">
                                    <ChartVisualization
                                        type={chartType}
                                        title={chartTitle}
                                        data={chartData}
                                        labels={chartLabels || []}
                                        trend={viz.trend}
                                        subtitle={chartSubtitle}
                                    />
                                </div>
                            );
                        })}
                    </div>
                )}
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
    const [selectedProperty, setSelectedProperty] = useState<PropertyContext | null>(null);
    const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Adapt backend property model to UI Context model
    const handleSelectProperty = (prop: any) => {
        setSelectedProperty({
            title: prop.title,
            address: prop.location,
            price: `${prop.price.toLocaleString()} EGP`,
            metrics: {
                bedrooms: prop.bedrooms,
                size: prop.size_sqm,
                wolfScore: prop.wolf_score || 75,
                capRate: "8%", // Mock
                pricePerSqFt: `${Math.round(prop.price / prop.size_sqm).toLocaleString()}`
            },
            aiRecommendation: prop.aiRecommendation || "This property shows strong appreciation potential based on recent market trends.",
            tags: ["High Growth", "Value Pick"],
            agent: {
                name: "Amr The Agent",
                title: "Senior Consultant"
            }
        });
    };

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, isTyping]);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;
        const userMsg = { role: 'user', content: input, id: Date.now().toString() };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages((prev) => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => {
                    fullResponse += token;
                    setMessages((prev) => prev.map((m) => (m.id === aiMsgId ? { ...m, content: fullResponse } : m)));
                },
                onToolStart: () => { },
                onToolEnd: () => { },
                onComplete: (data) => {
                    setMessages((prev) => prev.map((m) => m.id === aiMsgId ? { ...m, content: fullResponse, properties: data.properties, visualizations: data.ui_actions, isTyping: false } : m));
                    // Auto-select first property
                    if (data.properties && data.properties.length > 0) {
                        handleSelectProperty(data.properties[0]);
                    }
                    setIsTyping(false);
                },
                onError: (err) => {
                    setMessages((prev) => prev.map((m) => m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m));
                    setIsTyping(false);
                }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch (e) { setIsTyping(false); }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const getUserName = (): string => {
        if (user?.full_name) return user.full_name;
        if (user?.email) return user.email.split('@')[0];
        return 'You';
    };

    const handleNewChat = () => {
        setMessages([]);
        setSelectedProperty(null);
        setInput('');
        setIsTyping(false);
        setSessionId(`session-${Date.now()}`);
    };

    return (
        <div className="flex h-screen w-full relative font-display overflow-hidden selection:bg-[var(--color-primary)] selection:text-white">

            {/* Central Chat Area */}
            <main className="flex-1 flex flex-col min-w-0 relative z-10">

                {/* Scrollable Content */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-[15%] space-y-8 z-10 relative scroll-smooth no-scrollbar pt-24 pb-48">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full">
                            {/* Empty State / Initial Greeting Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.8 }}
                                className="relative glass-panel bg-white/80 dark:bg-[var(--color-surface-dark)]/40 rounded-2xl p-6 lg:p-10 shadow-soft-glow backdrop-blur-3xl max-w-2xl w-full border border-white/10"
                            >
                                <div className="absolute top-1/2 -left-1 w-1.5 h-1.5 bg-[var(--color-tertiary)]/40 rounded-full blur-[1px]"></div>
                                <div className="absolute top-1/3 -right-1 w-1.5 h-1.5 bg-[var(--color-tertiary)]/40 rounded-full blur-[1px]"></div>

                                <div className="flex items-center gap-4 mb-8 border-b border-gray-200 dark:border-white/5 pb-6">
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-surface-dark)] border border-[var(--color-primary)]/20 flex items-center justify-center shadow-[0_0_15px_rgba(163,177,138,0.2)]">
                                        <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)] font-light" />
                                    </div>
                                    <div>
                                        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-1">Agentic Core</h2>
                                        <span className="text-sm text-[var(--color-primary)] font-display flex items-center gap-2">
                                            System Online & Ready
                                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                                        </span>
                                    </div>
                                </div>

                                <div className="text-right font-sans text-lg leading-loose text-[var(--color-text-primary)] space-y-6" dir="rtl">
                                    <p className="font-medium">
                                        أهلاً بيك يا {getUserName()}! أنا عمرو، مستشارك العقاري الذكي.
                                    </p>
                                    <p className="font-light text-[var(--color-text-muted)]">
                                        أنا هنا عشان أساعدك تلاقي العقار المثالي ليك في مصر، سواء كان للاستثمار أو السكن. بستخدم بيانات السوق الحقيقية وتحليلات العائد عشان أديك أفضل نصيحة.
                                    </p>
                                    <p className="text-sm text-[var(--color-text-muted)] mt-6 font-display tracking-wide opacity-70">
                                        جرب تسألني: "عايز شقة في التجمع بـ 5 مليون" أو "أيه أفضل استثمار حالياً؟"
                                    </p>
                                </div>
                            </motion.div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg) =>
                                msg.role === 'user' ? (
                                    <UserMessage key={msg.id} content={msg.content} userName={getUserName()} />
                                ) : (
                                    <AgentMessage
                                        key={msg.id}
                                        content={msg.content}
                                        visualizations={msg.visualizations}
                                        properties={msg.properties}
                                        isTyping={msg.isTyping}
                                        onSelectProperty={handleSelectProperty}
                                    />
                                )
                            )}
                        </>
                    )}
                </div>

                {/* Floating Input Area (Pill Design) */}
                <div className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 z-50">
                    <div className="relative group">
                        <div className="absolute -inset-1 bg-gradient-to-r from-[var(--color-primary)]/30 via-[var(--color-tertiary)]/20 to-[var(--color-secondary)]/30 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-700"></div>
                        <div className="relative flex items-center bg-white dark:bg-[#1C212B]/90 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full shadow-2xl overflow-hidden transition-colors hover:border-[var(--color-primary)]/20">

                            {/* Add Button */}
                            <button className="pl-5 pr-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                                <MaterialIcon name="add_circle" />
                            </button>

                            {/* Text Input */}
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className="w-full py-4 bg-transparent border-none focus:ring-0 text-[var(--color-text-primary)] placeholder-slate-400 font-sans text-base tracking-wide"
                                placeholder="Ask about properties, market trends..."
                                type="text"
                                disabled={isTyping}
                            />

                            {/* Mic Button */}
                            <button className="p-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                                <MaterialIcon name="mic" />
                            </button>

                            {/* Send Button */}
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || isTyping}
                                className="mr-2 p-2.5 bg-slate-100 dark:bg-white/10 rounded-full text-slate-500 dark:text-[var(--color-tertiary)] hover:bg-[var(--color-primary)] hover:text-white dark:hover:bg-[var(--color-primary)] dark:hover:text-white transition shadow-inner disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <MaterialIcon name="arrow_upward" className="text-lg" />
                            </button>
                        </div>
                        <div className="text-center mt-3">
                            <p className="text-[10px] text-slate-400 dark:text-slate-500 tracking-widest uppercase font-display opacity-70">AI insights require independent verification</p>
                        </div>
                    </div>
                </div>
            </main>

            {/* Right Contextual Pane (Slide-over) */}
            <ContextualPane
                isOpen={!!selectedProperty}
                onClose={() => setSelectedProperty(null)}
                property={selectedProperty}
                isRTL={language === 'ar'}
            />
        </div>
    );
}
