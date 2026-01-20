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
                {properties && properties.length > 0 && (
                    <div className="grid grid-cols-1 gap-4 max-w-2xl">
                        {properties.map((prop: any, idx: number) => (
                            <div key={idx}
                                className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden shadow-xl shadow-black/5 dark:shadow-black/20 group transition-transform hover:scale-[1.01] duration-300 cursor-pointer"
                                onClick={() => onSelectProperty && onSelectProperty(prop)}
                            >
                                <div className="flex flex-col sm:flex-row">
                                    {/* Image Section */}
                                    <div className="w-full sm:w-2/5 h-56 sm:h-auto bg-cover bg-center relative bg-slate-800">
                                        <div className="absolute inset-0 flex items-center justify-center text-white/10">
                                            <MaterialIcon name="image" size="48px" />
                                        </div>
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent sm:bg-gradient-to-r"></div>
                                        <div className="absolute top-3 left-3 bg-white/90 dark:bg-black/70 backdrop-blur-md text-[var(--color-primary)] dark:text-[var(--color-secondary)] text-[10px] font-bold px-2.5 py-1 rounded-md uppercase tracking-wide border border-white/20">
                                            Top Pick
                                        </div>
                                        <div className="absolute bottom-3 left-3 sm:hidden text-white">
                                            <p className="text-lg font-bold shadow-black drop-shadow-md">{prop.price.toLocaleString()} EGP</p>
                                        </div>
                                    </div>
                                    {/* Content Section - Minimal & Visual */}
                                    <div className="p-4 flex flex-col justify-between flex-1 relative">
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                                                    <span className="text-[10px] font-medium uppercase tracking-wider">{prop.type}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5 bg-[var(--color-primary)]/10 px-2 py-0.5 rounded-full">
                                                    <MaterialIcon name="star" className="text-[var(--color-primary)] text-[12px] fill-current" />
                                                    <span className="text-[11px] font-bold text-[var(--color-primary)]">Wolf Score {prop.wolf_score || 92}</span>
                                                </div>
                                            </div>

                                            <div className="mb-3">
                                                <h3 className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight mt-1">{prop.price.toLocaleString()} EGP</h3>
                                                <p className="text-sm font-medium text-[var(--color-text-muted)] truncate">{prop.compound} • {prop.location}</p>
                                            </div>

                                            <div className="flex items-center gap-4 py-2 text-[var(--color-text-muted)] border-t border-[var(--color-border)]/50">
                                                <div className="flex items-center gap-1.5">
                                                    <MaterialIcon name="bed" className="text-[16px] opacity-70" />
                                                    <span className="text-xs font-semibold">{prop.bedrooms}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <MaterialIcon name="bathtub" className="text-[16px] opacity-70" />
                                                    <span className="text-xs font-semibold">{prop.bathrooms}</span>
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <MaterialIcon name="square_foot" className="text-[16px] opacity-70" />
                                                    <span className="text-xs font-semibold">{prop.size_sqm}m²</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex gap-2 mt-3 pt-3 border-t border-[var(--color-border)]/50">
                                            <button
                                                className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-primary)]/90 text-[var(--color-surface)] py-2 rounded-md text-xs font-bold transition-all shadow-sm hover:shadow-md"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onSelectProperty && onSelectProperty(prop);
                                                }}
                                            >
                                                View Details
                                            </button>
                                            <button className="px-3 py-2 border border-[var(--color-border)] hover:bg-[var(--color-surface-elevated)] rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors">
                                                <MaterialIcon name="bookmark_border" className="text-[18px]" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
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

                {/* Input Area - Dynamic Positioning */}
                <motion.div
                    layout
                    initial={{ top: "60%", transform: "translateY(-50%)" }}
                    animate={
                        messages.length === 0
                            ? { top: "60%", bottom: "auto", transform: "translateY(-50%)" }
                            : { top: "auto", bottom: 0, transform: "translateY(0)" }
                    }
                    transition={{ type: "spring", stiffness: 260, damping: 20 }}
                    className={`absolute left-0 right-0 p-4 md:p-6 z-20 ${messages.length > 0 ? 'bg-gradient-to-t from-[var(--color-background)] via-[var(--color-background)] to-transparent pb-8' : ''}`}
                >
                    <div className="max-w-4xl mx-auto relative group">
                        {/* Glow removed */}
                        <div className="relative bg-[var(--color-surface)] border border-[var(--color-border)] rounded-full flex items-center p-2 pr-2 transition-all duration-300 focus-within:border-[var(--color-primary)]/50 focus-within:ring-1 focus-within:ring-[var(--color-primary)]/20">
                            <button className="p-3 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-primary)] dark:hover:text-white hover:bg-[var(--color-surface-elevated)] transition-colors">
                                <MaterialIcon name="add_circle" />
                            </button>
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className="flex-1 bg-transparent border-none focus:ring-0 text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] px-3 py-3 text-base"
                                placeholder="Ask about properties, market trends..."
                                type="text"
                            />
                            <div className="flex items-center gap-1">
                                <button className="p-3 rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors">
                                    <MaterialIcon name="mic" />
                                </button>
                                <button onClick={handleSend} disabled={!input.trim() || isTyping} className="p-3 rounded-full bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary)]/90 transition-all transform active:scale-95 ml-1 flex items-center justify-center aspect-square disabled:opacity-50">
                                    <MaterialIcon name="arrow_upward" size="20px" />
                                </button>
                            </div>
                        </div>
                        <div className="text-center mt-3">
                            <p className="text-[10px] font-medium text-[var(--color-text-muted)]">AI can generate insights. Verify financial data independently.</p>
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
