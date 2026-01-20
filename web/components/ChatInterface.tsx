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
import Sidebar from '@/components/Sidebar';
import ContextualPane, { PropertyContext } from './chat/ContextualPane';
import HologramCard from '@/components/HologramCard';

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
    const displayName = userName || 'You';

    return (
        <div className="flex justify-end animate-in slide-in-from-bottom-2 fade-in duration-500">
            <div className="flex flex-col items-end gap-1 max-w-[85%] md:max-w-[70%] lg:max-w-[60%]">
                <div className="bg-[var(--color-primary)] text-white px-6 py-4 rounded-3xl rounded-tr-sm shadow-lg shadow-[var(--color-primary)]/10">
                    <p className="leading-relaxed text-[15px] font-medium" dir="auto">{safeContent}</p>
                </div>
                <span className="text-[11px] font-medium text-[var(--color-text-muted)] mr-2">{displayName} • Just now</span>
            </div>
        </div>
    );
};

// --- AMR Agent Message Component ---
const AgentMessage = ({ content, visualizations, properties, isTyping, onSelectProperty }: any) => {
    const safeContent = useMemo(() => sanitizeContent(content || ''), [content]);

    return (
        <div className="flex gap-5 max-w-full md:max-w-[90%] animate-in slide-in-from-bottom-4 fade-in duration-700">
            <div className="flex-none flex flex-col items-center gap-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-secondary)] to-[var(--color-primary)] flex items-center justify-center shadow-lg shadow-[var(--color-primary)]/20">
                    <MaterialIcon name="auto_awesome" className="text-white" />
                </div>
            </div>
            <div className="flex flex-col gap-4 flex-1 min-w-0">
                {/* Text Response */}
                <div>
                    <div className="flex items-baseline gap-2 mb-1">
                        <span className="text-sm font-bold text-[var(--color-text-primary)]">Agentic AI</span>
                        <span className="text-[11px] text-[var(--color-text-muted)]">Just now</span>
                    </div>
                    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] px-6 py-4 rounded-3xl rounded-tl-sm shadow-sm inline-block">
                        <div
                            className="leading-relaxed text-[15px] prose dark:prose-invert max-w-none prose-p:leading-7 prose-p:mb-4 prose-ul:my-4 prose-li:my-1 text-[var(--color-text-primary)]"
                            dir="auto"
                        >
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {safeContent}
                            </ReactMarkdown>
                            {isTyping && (
                                <span className="inline-block w-2 h-2 bg-[var(--color-secondary)] rounded-full animate-pulse ml-1 align-middle"></span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Properties Grid */}
                {/* Properties Carousel (Holographic) */}
                {properties && properties.length > 0 && (
                    <div className="mt-4 flex gap-4 overflow-x-auto pb-4 px-1 no-scrollbar snap-x w-full">
                        {properties.map((prop: any, idx: number) => (
                            <div key={idx} className="snap-center shrink-0 w-[300px]">
                                <HologramCard
                                    property={prop}
                                    onSelect={() => {
                                        if (onSelectProperty) onSelectProperty(prop);
                                    }}
                                />
                            </div>
                        ))}
                    </div>
                )}

                {/* Visualizations (Charts) */}
                {visualizations && visualizations.length > 0 && (
                    <div className="space-y-4 mt-2">
                        {visualizations.map((viz: any, idx: number) => {
                            // Adapt backend data
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
                                <ChartVisualization
                                    key={idx}
                                    type={chartType}
                                    title={chartTitle}
                                    data={chartData}
                                    labels={chartLabels || []}
                                    trend={viz.trend}
                                    subtitle={chartSubtitle}
                                />
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
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Adapt backend property model to UI Context model
    const handleSelectProperty = (prop: any) => {
        setSelectedProperty({
            title: prop.title,
            address: prop.location,
            price: `${prop.price.toLocaleString()} EGP`,
            metrics: {
                bedrooms: prop.bedrooms,
                size: prop.size_sqm,
                wolfScore: prop.wolf_score || 75, // Fallback to 75 if missing
                capRate: "8%", // Mock
                pricePerSqFt: `${Math.round(prop.price / prop.size_sqm).toLocaleString()}`
            },
            aiRecommendation: "This property shows strong appreciation potential based on recent market trends in the area.",
            tags: ["High Growth", "Great Location", "Value Pick"],
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

                    // Auto-select the first property if available
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
        // Priority: full_name > email prefix > 'You'
        if (user?.full_name) {
            return user.full_name;
        }
        if (user?.email) {
            return user.email.split('@')[0];
        }
        return 'You';
    };

    // Clear conversation memory and reset state
    const handleNewChat = () => {
        setMessages([]);
        setSelectedProperty(null);
        setInput('');
        setIsTyping(false);
        // Generate a new session ID to ensure backend starts fresh conversation
        setSessionId(`session-${Date.now()}`);
    };

    return (
        <div className="flex h-screen w-full relative bg-[var(--color-background)] font-display selection:bg-[var(--color-secondary)] selection:text-black overflow-hidden">
            <Sidebar onNewChat={handleNewChat} />

            {/* Central Chat Area */}
            <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-background)] relative">
                {/* Decorative Background - Removed for deep black theme */}
                {/* <div className="absolute inset-0 overflow-hidden pointer-events-none z-0"> ... </div> */}

                {/* Header Removed as per request */}

                {/* Chat History */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 md:p-8 space-y-10 z-10 relative scroll-smooth no-scrollbar pt-12">
                    {messages.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-center space-y-6 opacity-80 pb-32">
                            <div className="w-20 h-20 rounded-2xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] flex items-center justify-center shadow-lg transition-colors">
                                <MaterialIcon name="auto_awesome" className="text-[var(--color-primary)] dark:text-[var(--color-secondary)] text-[40px]" />
                            </div>
                            <h2 className="text-2xl font-bold text-[var(--color-text-primary)]">Ready to analyze the market?</h2>
                        </div>
                    ) : (
                        <>
                            {/* Clear Memory Button - shown when there are messages */}
                            <div className="flex justify-end mb-4">
                                <button
                                    onClick={handleNewChat}
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] rounded-lg border border-[var(--color-border)] transition-colors"
                                >
                                    <MaterialIcon name="delete_sweep" size="18px" />
                                    Clear Chat
                                </button>
                            </div>

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
                    {/* Spacer for bottom input area */}
                    <div className="h-32"></div>
                </div>

                {/* Input Area - Floating Glass Pill */}
                <motion.div
                    layout
                    initial={{ top: "60%", transform: "translateY(-50%)" }}
                    animate={
                        messages.length === 0
                            ? { top: "60%", bottom: "auto", transform: "translateY(-50%)" }
                            : { top: "auto", bottom: 0, transform: "translateY(0)" }
                    }
                    transition={{ type: "spring", stiffness: 260, damping: 20 }}
                    className={`absolute left-0 right-0 p-6 z-20 pointer-events-none ${messages.length > 0 ? '' : ''}`}
                >
                    <div className="max-w-2xl mx-auto relative group pointer-events-auto">
                        <div className="absolute -inset-1 bg-gradient-to-r from-[var(--color-primary)]/30 via-[var(--color-tertiary)]/20 to-[var(--color-secondary)]/30 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-700"></div>
                        <div className="relative flex items-center bg-white dark:bg-[var(--color-surface-dark)]/80 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-full shadow-2xl overflow-hidden transition-colors hover:border-[var(--color-primary)]/20">
                            <button className="pl-5 pr-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                                <MaterialIcon name="add_circle" />
                            </button>
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className="w-full py-4 bg-transparent border-none focus:ring-0 text-slate-700 dark:text-gray-200 placeholder-slate-400 font-sans text-base tracking-wide"
                                placeholder="Ask about properties, market trends..."
                                type="text"
                            />
                            <button className="p-3 text-slate-400 hover:text-[var(--color-primary)] transition">
                                <MaterialIcon name="mic" />
                            </button>
                            <button
                                onClick={handleSend}
                                disabled={!input.trim() || isTyping}
                                className="mr-2 p-2.5 bg-slate-100 dark:bg-white/10 rounded-full text-slate-500 dark:text-[var(--color-tertiary)] hover:bg-[var(--color-primary)] hover:text-white dark:hover:bg-[var(--color-primary)] dark:hover:text-white transition shadow-inner flex items-center justify-center disabled:opacity-50"
                            >
                                <MaterialIcon name="arrow_upward" size="20px" />
                            </button>
                        </div>
                        <div className="text-center mt-3">
                            <p className="text-[10px] text-slate-400 dark:text-slate-500 tracking-widest uppercase font-display opacity-70">AI insights require independent verification</p>
                        </div>
                    </div>
                </motion.div>
            </main>

            {/* Right Contextual Pane */}
            <ContextualPane
                isOpen={!!selectedProperty}
                onClose={() => setSelectedProperty(null)}
                property={selectedProperty}
                isRTL={language === 'ar'}
            />
        </div>
    );
}
