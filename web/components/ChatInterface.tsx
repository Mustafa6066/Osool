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
        <div className="w-full max-w-2xl mx-auto flex justify-end animate-in slide-in-from-bottom-2 fade-in duration-500 mb-6">
            <div className="flex flex-col items-end gap-1 max-w-[85%]">
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
        <div className="w-full max-w-2xl mx-auto flex gap-5 animate-in slide-in-from-bottom-4 fade-in duration-700 mb-8">
            {/* Agent Avatar */}
            <div className="flex-none hidden sm:flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/20 to-[var(--color-surface-dark)] border border-[var(--color-primary)]/20 flex items-center justify-center shadow-[0_0_15px_rgba(163,177,138,0.2)]">
                    <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)]" />
                </div>
            </div>

            <div className="flex flex-col gap-6 flex-1 min-w-0">
                {/* Agentic Core Panel */}
                <div className="relative glass-panel bg-white/80 dark:bg-[var(--color-surface-dark)]/40 rounded-2xl p-6 lg:p-8 shadow-soft-glow backdrop-blur-3xl border border-white/10">
                    {/* Decorative Node Glows matching floating cards */}
                    <div className="absolute top-1/2 -left-1 w-1.5 h-1.5 bg-[var(--color-tertiary)]/40 rounded-full blur-[1px]"></div>
                    <div className="absolute top-1/3 -right-1 w-1.5 h-1.5 bg-[var(--color-tertiary)]/40 rounded-full blur-[1px]"></div>
                    <div className="absolute bottom-1/3 -left-1 w-1.5 h-1.5 bg-[var(--color-tertiary)]/40 rounded-full blur-[1px]"></div>

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
                        <div className="flex flex-col items-center justify-center h-full w-full relative">

                            {/* --- Floating Decorative Elements (Desktop Only) --- */}

                            {/* Top Left: Hologram Property */}
                            <motion.div
                                initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2, duration: 0.8 }}
                                className="hidden lg:block absolute left-[-10%] top-[10%] w-80 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
                            >
                                <div className="relative glass-panel rounded-2xl p-5 group hover:border-[var(--color-primary)]/30 transition-colors">
                                    <div className="absolute top-1/2 -right-1 w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full node-glow blur-[1px]"></div>
                                    <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[var(--color-primary)]/60 rounded-tl-lg"></div>
                                    <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-[var(--color-surface-dark)]/50">
                                        <div className="w-full h-full bg-slate-800 relative overflow-hidden">
                                            <div className="absolute inset-0 bg-gradient-to-tr from-[var(--color-primary)]/20 to-transparent"></div>
                                            <MaterialIcon name="apartment" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/20 text-6xl" />
                                        </div>
                                        <div className="absolute top-3 left-3 px-3 py-1 bg-[var(--color-surface-dark)]/40 border border-white/20 text-white text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">
                                            Top Pick
                                        </div>
                                    </div>
                                    <div className="space-y-3">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans">Apartment in El Patio 7</h3>
                                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-display uppercase tracking-wide">New Cairo</p>
                                            </div>
                                            <div className="flex items-center gap-1 text-[var(--color-tertiary)]">
                                                <MaterialIcon name="star" size="14px" className="text-[var(--color-tertiary)]" />
                                                <span className="text-sm font-bold">5.0</span>
                                            </div>
                                        </div>
                                        <div className="text-2xl font-light text-[var(--color-primary)] font-display">18,150,000 <span className="text-base text-slate-500">EGP</span></div>
                                        <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                                            <div className="text-center">
                                                <MaterialIcon name="bed" className="text-slate-400 text-xs mb-1" />
                                                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">3 Bed</p>
                                            </div>
                                            <div className="text-center">
                                                <MaterialIcon name="bathtub" className="text-slate-400 text-xs mb-1" />
                                                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">3 Bath</p>
                                            </div>
                                            <div className="text-center">
                                                <MaterialIcon name="square_foot" className="text-slate-400 text-xs mb-1" />
                                                <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">165m²</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Top Right: Listing Insights */}
                            <motion.div
                                initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4, duration: 0.8 }}
                                className="hidden lg:block absolute right-[-5%] top-[5%] w-72 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
                            >
                                <div className="relative glass-panel rounded-2xl p-6 hover:border-[var(--color-secondary)]/30 transition-colors group">
                                    <div className="absolute top-1/2 -left-1 w-2 h-2 bg-[var(--color-secondary)]/60 rounded-full node-glow blur-[1px]"></div>
                                    <div className="absolute -bottom-[1px] -right-[1px] w-4 h-4 border-b border-r border-[var(--color-secondary)]/60 rounded-br-lg"></div>
                                    <div className="flex justify-between items-center mb-6">
                                        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">Listing Insights</h3>
                                        <MaterialIcon name="analytics" className="text-[var(--color-secondary)]/70 text-lg" />
                                    </div>
                                    <div className="space-y-6">
                                        <div>
                                            <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                                                <span>Cap Rate</span>
                                                <span className="text-[var(--color-primary)]">High</span>
                                            </div>
                                            <div className="text-3xl font-light dark:text-white font-display">8%</div>
                                            <div className="w-full bg-slate-200 dark:bg-white/5 h-1.5 mt-2 rounded-full overflow-hidden">
                                                <div className="bg-gradient-to-r from-[var(--color-secondary)] to-[var(--color-primary)] w-[80%] h-full rounded-full opacity-80"></div>
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-xs text-slate-500 mb-1 font-display uppercase tracking-wider">
                                                <span>Price / SQM</span>
                                            </div>
                                            <div className="text-2xl font-light dark:text-white font-display">110,000 <span className="text-sm text-slate-500">EGP</span></div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-xs text-slate-500 mb-2 font-display uppercase tracking-wider">
                                                <span>Wolf Score</span>
                                                <span className="text-[var(--color-tertiary)] font-bold">85/100</span>
                                            </div>
                                            <div className="h-16 w-full flex items-end gap-1 mt-2">
                                                <div className="w-1/6 bg-[var(--color-secondary)] h-[40%] rounded-t-sm opacity-20"></div>
                                                <div className="w-1/6 bg-[var(--color-secondary)] h-[60%] rounded-t-sm opacity-30"></div>
                                                <div className="w-1/6 bg-[var(--color-secondary)] h-[30%] rounded-t-sm opacity-40"></div>
                                                <div className="w-1/6 bg-[var(--color-primary)] h-[80%] rounded-t-sm opacity-50"></div>
                                                <div className="w-1/6 bg-[var(--color-primary)] h-[90%] rounded-t-sm opacity-70"></div>
                                                <div className="w-1/6 bg-[var(--color-primary)] h-[50%] rounded-t-sm opacity-90"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>

                            {/* Bottom Right: ROI */}
                            <motion.div
                                initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6, duration: 0.8 }}
                                className="hidden lg:block absolute right-[10%] bottom-[10%] w-64 transform transition-transform hover:scale-105 duration-700 z-0 pointer-events-none xl:pointer-events-auto"
                            >
                                <div className="relative glass-panel rounded-2xl p-5 hover:border-[var(--color-primary)]/40 transition-colors">
                                    <div className="absolute top-1/2 -left-1 w-2 h-2 bg-[var(--color-primary)]/60 rounded-full node-glow blur-[1px]"></div>
                                    <div className="flex items-center justify-between mb-3">
                                        <span className="text-[10px] font-bold tracking-widest uppercase text-slate-400">Proj. Annual ROI</span>
                                        <MaterialIcon name="trending_up" className="text-[var(--color-primary)] text-sm" />
                                    </div>
                                    <div className="text-3xl font-light text-[var(--color-primary)] font-display">12.5%</div>
                                    <p className="text-[10px] text-slate-500 mt-2 leading-tight">Based on recent market trends in New Cairo.</p>
                                </div>
                            </motion.div>

                            {/* Bottom Left: FABs */}
                            <motion.div
                                initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.8, duration: 0.8 }}
                                className="hidden lg:flex absolute left-[-5%] bottom-[5%] flex-col gap-3 z-50"
                            >
                                <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
                                    <MaterialIcon name="add" className="text-xl" />
                                </button>
                                <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
                                    <MaterialIcon name="remove" className="text-xl" />
                                </button>
                                <button className="w-11 h-11 rounded-xl bg-white/5 dark:bg-[var(--color-surface-dark)]/50 border border-slate-200 dark:border-white/10 text-slate-500 dark:text-slate-400 backdrop-blur-md flex items-center justify-center hover:bg-[var(--color-primary)]/20 hover:text-[var(--color-primary)] hover:border-[var(--color-primary)]/30 transition-all shadow-lg">
                                    <MaterialIcon name="my_location" className="text-xl" />
                                </button>
                            </motion.div>

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
