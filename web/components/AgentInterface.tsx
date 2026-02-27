'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Send, Plus, Sparkles, MapPin, TrendingUp,
    Building2, Calculator, X, ChevronRight,
    BarChart2, Shield, Home, Menu,
    Copy, Bookmark, LayoutDashboard,
    History, MoreHorizontal, ArrowUp,
    RefreshCw, Maximize2, ExternalLink, Wallet, Search
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import dynamic from 'next/dynamic';
import SuggestionChips from '@/components/SuggestionChips';
import FunnelIndicator from '@/components/FunnelIndicator';

// Lazy load visualization renderer for smart charts
const VisualizationRenderer = dynamic(
    () => import('@/components/visualizations/VisualizationRenderer'),
    { ssr: false }
);

/**
 * TYPES - Aligned with backend schemas
 */
interface PropertyMetrics {
    size: number;
    bedrooms: number;
    bathrooms: number;
    wolf_score: number;
    roi: number;
    price_per_sqm: number;
    liquidity_rating: string;
}

interface Property {
    id: string;
    title: string;
    location: string;
    price: number;
    currency: string;
    metrics: PropertyMetrics;
    image: string;
    developer: string;
    tags: string[];
    status: string;
}

interface Artifacts {
    property?: Property;
    chart?: { type: string; data: any };
}

interface Message {
    id: number;
    role: 'user' | 'agent';
    content: string;
    artifacts?: Artifacts | null;
    uiActions?: any[];
    analyticsContext?: any;
    showingStrategy?: string;
    allProperties?: Property[];
}

interface Suggestion {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    prompt: string;
}

// Suggestions mapped to backend AI engine capabilities
const SUGGESTIONS: Suggestion[] = [
    { icon: BarChart2, label: "Market Intelligence", prompt: "Analyze current market trends in New Cairo" },
    { icon: Search, label: "Find Opportunities", prompt: "Find high ROI properties under 5M EGP" },
    { icon: Wallet, label: "Liquidity Check", prompt: "Calculate liquidity potential for my unit" },
    { icon: Shield, label: "Developer Audit", prompt: "Audit the delivery history of Palm Hills" },
];

/**
 * COMPONENT: AMR AGENT AVATAR
 */
const AgentAvatar = ({ thinking = false }: { thinking?: boolean }) => {
    return (
        <div className={`relative flex items-center justify-center w-8 h-8 rounded-xl overflow-hidden flex-shrink-0 ${thinking ? 'animate-pulse' : ''}`}>
            <div className="absolute inset-0 bg-[var(--color-text-primary)]" />
            <span className="relative text-[10px] font-bold text-[var(--color-background)] font-mono tracking-tight">A</span>
            {/* Emerald AI dot */}
            <div className="absolute bottom-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-emerald-400" />
        </div>
    );
};

/**
 * Detect if text is primarily Arabic
 */
const isArabic = (text: string): boolean => {
    if (!text) return false;
    const arabicChars = text.match(/[\u0600-\u06FF]/g);
    return !!arabicChars && arabicChars.length > text.length * 0.3;
};

/**
 * COMPONENT: MARKDOWN MESSAGE RENDERER
 * Replaces the old Typewriter — renders AI responses as proper Markdown
 * with Arabic RTL support and styled components.
 */
const MarkdownMessage = ({ content }: { content: string }) => {
    const msgIsArabic = isArabic(content);

    // Normalize newlines: backend sends single \n but Markdown needs \n\n for paragraphs.
    // Convert single newlines to double (but don't quadruple existing double newlines).
    const normalized = content
        .replace(/\r\n/g, '\n')           // Normalize CRLF → LF
        .replace(/\n{3,}/g, '\n\n')       // Collapse 3+ newlines to 2
        .replace(/(?<!\n)\n(?!\n)/g, '\n\n'); // Single \n → double \n\n

    return (
        <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-right' : 'text-left'}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ node, ...props }) => (
                        <p className={`mb-3 last:mb-0 leading-relaxed ${msgIsArabic ? 'text-right' : 'text-left'}`} {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                        <ul className={`list-disc mb-3 space-y-1 ${msgIsArabic ? 'pr-5' : 'pl-5'}`} {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className={`list-decimal mb-3 space-y-1 ${msgIsArabic ? 'pr-5' : 'pl-5'}`} {...props} />
                    ),
                    li: ({ node, ...props }) => (
                        <li className="mb-1" {...props} />
                    ),
                    strong: ({ node, ...props }) => (
                        <strong className="font-bold text-emerald-500 dark:text-emerald-400" {...props} />
                    ),
                    em: ({ node, ...props }) => (
                        <em className="italic text-[var(--color-text-secondary)]" {...props} />
                    ),
                    h1: ({ node, ...props }) => (
                        <h1 className="text-xl font-bold mb-3 mt-4 text-[var(--color-text-primary)]" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                        <h2 className="text-lg font-bold mb-2 mt-3 text-[var(--color-text-primary)]" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className="text-base font-semibold mb-2 mt-2 text-[var(--color-text-primary)]" {...props} />
                    ),
                    blockquote: ({ node, ...props }) => (
                        <blockquote
                            className={`${msgIsArabic ? 'border-r-4 pr-4' : 'border-l-4 pl-4'} border-emerald-500 py-1 my-2 bg-[var(--color-surface-elevated)] rounded`}
                            {...props}
                        />
                    ),
                    a: ({ node, ...props }) => (
                        <a className="text-emerald-500 dark:text-emerald-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                    code: ({ node, className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                            <code className="bg-[var(--color-surface-elevated)] text-emerald-400 px-1.5 py-0.5 rounded text-sm" {...props}>{children}</code>
                        ) : (
                            <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 my-3 overflow-x-auto">
                                <code className="text-sm text-[var(--color-text-secondary)]" {...props}>{children}</code>
                            </pre>
                        );
                    },
                    hr: ({ node, ...props }) => (
                        <hr className="border-[var(--color-border-light)] my-4" {...props} />
                    ),
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-3">
                            <table className="w-full border-collapse border border-[var(--color-border-light)] text-sm" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className="border border-[var(--color-border-light)] bg-[var(--color-surface-elevated)] px-3 py-2 text-emerald-500 dark:text-emerald-400 font-semibold" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="border border-[var(--color-border-light)] px-3 py-2" {...props} />
                    ),
                }}
            >
                {normalized}
            </ReactMarkdown>
        </div>
    );
};

/**
 * MAIN APP: AGENT INTERFACE
 * Clean, content-focused aesthetics with floating panels
 */
export default function AgentInterface() {
    const { user } = useAuth();
    const { profile, triggerXP } = useGamification();
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [contextPaneOpen, setContextPaneOpen] = useState(false);
    const [activeContext, setActiveContext] = useState<Artifacts | null>(null);
    const [recentQueries, setRecentQueries] = useState<string[]>([]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    // Stable session ID per conversation — so backend can load history
    const sessionIdRef = useRef<string>(`session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`);

    // Get user's display name
    const userName = user?.full_name || user?.email?.split('@')[0] || 'Investor';

    // Auto-resize input
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
        }
    }, [inputValue]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    const handleSendMessage = useCallback(async (text?: string) => {
        const content = text || inputValue;
        if (!content.trim() || isTyping) return;

        // SmartNav handles navigation

        // Add to recent queries
        setRecentQueries(prev => {
            const updated = [content.slice(0, 40), ...prev.filter(q => q !== content.slice(0, 40))];
            return updated.slice(0, 5);
        });

        // Add User Message
        const userMsg: Message = { id: Date.now(), role: 'user', content };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        try {
            // Call the real API (session_id required by backend)
            const response = await api.post('/api/chat', {
                message: content,
                session_id: sessionIdRef.current,
                language: 'auto'
            });
            const data = response.data;
            console.log('[AMR] API Response:', data);

            // Extract ALL property artifacts from response
            let artifacts: Artifacts | null = null;
            const allProps: Property[] = [];

            if (data.properties && data.properties.length > 0) {
                data.properties.forEach((prop: any) => {
                    allProps.push({
                        id: prop.id?.toString() || `prop_${Date.now()}_${Math.random()}`,
                        title: prop.title || prop.name || 'Property',
                        location: prop.location || prop.address || 'Location',
                        price: prop.price || 0,
                        currency: 'EGP',
                        metrics: {
                            size: prop.size_sqm || prop.size || 0,
                            bedrooms: prop.bedrooms || 0,
                            bathrooms: prop.bathrooms || 0,
                            wolf_score: prop.wolf_score || 0,
                            roi: prop.projected_roi || prop.roi || 0,
                            price_per_sqm: prop.price_per_sqm || 0,
                            liquidity_rating: prop.liquidity_rating || 'Medium'
                        },
                        image: prop.image_url || prop.image || "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=800",
                        developer: prop.developer || 'Developer',
                        tags: prop.tags || [],
                        status: prop.status || 'Available'
                    });
                });
                // First property as artifact for context pane
                if (allProps.length > 0) {
                    artifacts = { property: allProps[0] };
                }
            }

            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'agent',
                content: data.response || data.message || "I'm AMR, your real estate intelligence agent. How can I assist you today?",
                artifacts,
                uiActions: data.ui_actions || [],
                analyticsContext: data.analytics_context || null,
                showingStrategy: data.showing_strategy || 'NONE',
                allProperties: allProps,
            };

            setMessages(prev => [...prev, aiMsg]);

            // Award XP for asking a question
            triggerXP(5, 'Asked a question');

            // Award bonus XP for analysis tools used
            if (aiMsg.uiActions && aiMsg.uiActions.length > 0) {
                triggerXP(15, 'Used analysis tool');
            }

            if (aiMsg.artifacts) {
                setActiveContext(aiMsg.artifacts);
                setContextPaneOpen(true);
            }
        } catch (error: any) {
            // Log real error for debugging
            console.error('[AMR] API Error:', error?.response?.data || error?.message || error);

            // Try to extract error message from backend
            const errorMsg = error?.response?.data?.detail || error?.response?.data?.error ||
                "I'm AMR (Automated Market Researcher). I can access the Osool liquidity engine, analyze market data, and audit real estate assets. How can I assist with your portfolio today?";

            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'agent',
                content: errorMsg,
                artifacts: null
            };
            setMessages(prev => [...prev, aiMsg]);
        } finally {
            setIsTyping(false);
        }
    }, [inputValue, isTyping]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setContextPaneOpen(false);
        setActiveContext(null);
        setInputValue('');
        // SmartNav handles navigation
        // New conversation = new session ID
        sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const hasStarted = messages.length > 0;

    // Generate contextual follow-up suggestions based on the AI response
    const generateSuggestions = (msg: Message): string[] => {
        const suggestions: string[] = [];
        const content = msg.content.toLowerCase();
        const hasProperties = msg.allProperties && msg.allProperties.length > 0;
        const hasAnalytics = msg.analyticsContext?.has_analytics;
        const hasVisualizations = msg.uiActions && msg.uiActions.length > 0;

        if (hasProperties) {
            suggestions.push('Compare these properties side by side');
            suggestions.push('Show ROI analysis');
            suggestions.push('What are the payment plans?');
        } else if (hasAnalytics) {
            suggestions.push('Show price trends over time');
            suggestions.push('Which area has best growth?');
            suggestions.push('Compare with alternative investments');
        } else if (content.includes('developer') || content.includes('مطور')) {
            suggestions.push('Show their track record');
            suggestions.push('Compare delivery dates');
            suggestions.push('Show available units');
        } else if (content.includes('area') || content.includes('location') || content.includes('منطقة')) {
            suggestions.push('Show price per sqm breakdown');
            suggestions.push('What about nearby areas?');
            suggestions.push('Show infrastructure developments');
        } else {
            suggestions.push('Show me top properties');
            suggestions.push('Market overview');
            suggestions.push('Help me set a budget');
        }

        return suggestions.slice(0, 3);
    };

    return (
        <div className="flex h-full w-full bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden selection:bg-emerald-500/20 relative">

            {/* ---------------------------------------------------------------------------
       * MAIN CHAT AREA
       * --------------------------------------------------------------------------- */}
            <main className="flex-1 flex flex-col relative min-w-0 bg-[var(--color-background)] h-full w-full z-0">

                {/* Top Bar */}
                <div className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6 z-30 pointer-events-none">

                    {/* Title */}
                    <div className="flex items-center gap-4 pointer-events-auto">
                        <span className={`text-xl font-medium text-[var(--color-text-primary)] opacity-90 tracking-tight transition-opacity duration-500 ${!hasStarted ? 'opacity-0' : 'opacity-100'}`}>
                            Osool <span className="opacity-50 font-light">AMR</span>
                        </span>
                    </div>

                    <div className="flex items-center gap-3 pointer-events-auto">
                        <button
                            onClick={handleNewChat}
                            className="p-2.5 hover:bg-[var(--color-surface-hover)] rounded-full text-[var(--color-text-muted)] transition-colors"
                            title="New Chat"
                        >
                            <RefreshCw className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Funnel Indicator — buying journey progress */}
                {hasStarted && profile && (
                    <div className="absolute top-14 left-0 right-0 z-20 pointer-events-none">
                        <div className="max-w-[600px] mx-auto">
                            <FunnelIndicator
                                leadScore={profile.investment_readiness_score || 0}
                                readinessScore={profile.investment_readiness_score}
                            />
                        </div>
                    </div>
                )}

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-[800px] mx-auto h-full">

                        {/* GREETING SCREEN */}
                        {!hasStarted && (
                            <div className="flex flex-col h-full relative">

                                {/* Top Half - Title */}
                                <div className="flex-1 flex flex-col justify-end pb-10 px-4">
                                    <div className="text-center w-full max-w-2xl mx-auto">
                                        <h1 className="text-5xl md:text-6xl font-semibold tracking-tight mb-4">
                                            <span className="text-[var(--color-text-primary)]">
                                                Hello, {userName}
                                            </span>
                                        </h1>
                                        <h2 className="text-2xl md:text-3xl text-[var(--color-text-muted)] font-light tracking-tight">What would you like to explore<span className="text-emerald-500">?</span></h2>
                                    </div>
                                </div>

                                {/* Middle Spacer for Input Bar */}
                                <div className="h-[140px] flex-shrink-0 w-full" aria-hidden="true" />

                                {/* Bottom Half - Cards */}
                                <div className="flex-1 flex flex-col justify-start pt-2 px-4">
                                    <div className="w-full max-w-3xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {SUGGESTIONS.map((s, i) => (
                                            <button
                                                key={i}
                                                onClick={() => handleSendMessage(s.prompt)}
                                                className="p-4 bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] rounded-2xl text-left transition-all duration-300 h-36 flex flex-col justify-between group border border-[var(--color-border)] hover:border-emerald-500/20 hover:shadow-sm"
                                            >
                                                <span className="text-sm font-medium text-[var(--color-text-primary)] leading-snug" dir="auto">{s.label}</span>
                                                <div className="self-end p-2 bg-[var(--color-background)] rounded-xl text-[var(--color-text-muted)] group-hover:text-emerald-500 transition-colors">
                                                    <s.icon className="w-4 h-4" />
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* CHAT MESSAGES */}
                        {hasStarted && (
                            <div className="px-4 pt-20 pb-48">
                                {messages.map((msg, index) => (
                                    <div key={msg.id} className="mb-8">
                                        <div className="flex gap-5">
                                            <div className="flex-shrink-0 mt-1">
                                                {msg.role === 'user' ? null : <AgentAvatar />}
                                            </div>

                                            <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                                                {msg.role === 'user' ? (
                                                    <div
                                                        className="bg-[var(--color-surface-hover)] text-[var(--color-text-primary)] px-6 py-3.5 rounded-[24px] rounded-br-sm max-w-[85%] text-[16px] leading-relaxed tracking-wide"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div
                                                        className="text-[16px] leading-8 text-[var(--color-text-primary)] font-light tracking-wide"
                                                        dir="auto"
                                                    >
                                                        <MarkdownMessage content={msg.content} />

                                                        {/* Smart Visualizations — Charts triggered by AI brain */}
                                                        {msg.uiActions && msg.uiActions.length > 0 && (
                                                            <div className="mt-6 space-y-4" dir="ltr">
                                                                {msg.uiActions
                                                                    .filter((action: any) => {
                                                                        // Skip property cards (rendered separately)
                                                                        if (action.type === 'property_cards') return false;
                                                                        // Skip visualizations with no data
                                                                        if (!action.data) return false;
                                                                        const d = action.data;
                                                                        // Skip area_analysis with no real numbers
                                                                        if (action.type === 'area_analysis') {
                                                                            const area = d.area || d.areas?.[0] || d;
                                                                            const price = area?.avg_price_sqm || area?.avg_price_per_sqm || 0;
                                                                            if (!area?.name || price === 0) return false;
                                                                        }
                                                                        // Skip inflation_killer with no projections
                                                                        if (action.type === 'inflation_killer') {
                                                                            const hasProjections = d.projections?.length > 0 || d.data_points?.length > 0;
                                                                            const hasSummary = d.summary?.cash_final > 0 || d.final_values?.cash_real_value > 0;
                                                                            if (!hasProjections && !hasSummary) return false;
                                                                        }
                                                                        // Skip market_benchmark with no price data
                                                                        if (action.type === 'market_benchmark') {
                                                                            if (!d.avg_price_sqm && !d.area_context?.avg_price_sqm) return false;
                                                                        }
                                                                        // Skip price_growth_chart with no data points
                                                                        if (action.type === 'price_growth_chart') {
                                                                            if (!d.data_points?.length || d.data_points.length < 2) return false;
                                                                        }
                                                                        return true;
                                                                    })
                                                                    .map((action: any, idx: number) => (
                                                                    <div key={idx} className="animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: `${idx * 150}ms` }}>
                                                                        <VisualizationRenderer
                                                                            type={action.type}
                                                                            data={action.data || action}
                                                                            isRTL={isArabic(msg.content)}
                                                                        />
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}

                                                        {/* Analytics Insight Panel — shown when ANALYTICS_ONLY mode */}
                                                        {msg.analyticsContext?.has_analytics && (!msg.allProperties || msg.allProperties.length === 0) && (
                                                            <div className="mt-6 p-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 backdrop-blur-sm" dir="ltr">
                                                                <div className="flex items-center gap-2 mb-4">
                                                                    <BarChart2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                                                                    <span className="text-xs font-bold text-emerald-500 dark:text-emerald-400 uppercase tracking-widest">Market Intelligence</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                                                    {msg.analyticsContext.avg_price_sqm > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Avg Price/m²</div>
                                                                            <div className="text-lg font-semibold text-[var(--color-text-primary)]">
                                                                                {msg.analyticsContext.avg_price_sqm?.toLocaleString()} <span className="text-xs opacity-50">EGP</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.growth_rate > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Growth Rate</div>
                                                                            <div className="text-lg font-semibold text-emerald-400">
                                                                                +{(msg.analyticsContext.growth_rate * 100).toFixed(0)}% <span className="text-xs opacity-50">YoY</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.rental_yield > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Rental Yield</div>
                                                                            <div className="text-lg font-semibold text-cyan-400">
                                                                                {(msg.analyticsContext.rental_yield * 100).toFixed(1)}%
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Property Cards — All properties, not just first */}
                                                        {msg.allProperties && msg.allProperties.length > 0 && (
                                                            <div className="mt-6 space-y-3" dir="ltr">
                                                                {msg.allProperties.map((prop, idx) => (
                                                                    <div
                                                                        key={prop.id}
                                                                        onClick={() => { setActiveContext({ property: prop }); setContextPaneOpen(true); }}
                                                                        className="group relative flex gap-4 p-4 border border-[var(--color-border)] hover:border-emerald-500/40 bg-[var(--color-surface)] rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-lg hover:shadow-black/5"
                                                                        style={{ animationDelay: `${idx * 100}ms` }}
                                                                    >
                                                                        {/* Accent bar */}
                                                                        <div className="absolute top-0 left-0 w-1 h-full rounded-l-2xl bg-gradient-to-b from-emerald-500 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />

                                                                        {/* Image */}
                                                                        <div className="w-20 h-20 md:w-24 md:h-24 bg-[var(--color-surface-hover)] rounded-xl flex-shrink-0 overflow-hidden">
                                                                            <img src={prop.image} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" alt={prop.title} />
                                                                        </div>

                                                                        {/* Info */}
                                                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                                            <h3 className="font-medium text-[var(--color-text-primary)] truncate text-sm md:text-base" dir="auto">{prop.title}</h3>
                                                                            <p className="text-xs text-[var(--color-text-muted)] truncate mt-0.5" dir="auto">
                                                                                {prop.location} {prop.developer && `• ${prop.developer}`}
                                                                            </p>
                                                                            <div className="flex items-center gap-2 mt-2">
                                                                                <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                                                                                    {(prop.price / 1000000).toFixed(1)}M EGP
                                                                                </span>
                                                                                {prop.metrics.price_per_sqm > 0 && (
                                                                                    <span className="text-[10px] text-[var(--color-text-muted)]">
                                                                                        {prop.metrics.price_per_sqm.toLocaleString()}/m²
                                                                                    </span>
                                                                                )}
                                                                                {prop.metrics.roi > 0 && (
                                                                                    <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                                                                                        +{prop.metrics.roi}% ROI
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            {/* Mini Osool score bar */}
                                                                            {prop.metrics.wolf_score > 0 && (
                                                                                <div className="mt-2 flex items-center gap-2">
                                                                                    <div className="flex-1 h-1 bg-[var(--color-border)] rounded-full overflow-hidden max-w-[120px]">
                                                                                        <div
                                                                                            className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-700"
                                                                                            style={{ width: `${Math.min(prop.metrics.wolf_score, 100)}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <span className="text-[9px] text-emerald-500 dark:text-emerald-400 font-bold">{prop.metrics.wolf_score}</span>
                                                                                </div>
                                                                            )}
                                                                        </div>

                                                                        {/* Arrow */}
                                                                        <div className="flex items-center text-[var(--color-text-muted)] group-hover:text-emerald-500 dark:text-emerald-400 transition-colors">
                                                                            <ChevronRight className="w-4 h-4" />
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}

                                                        {!isTyping && (
                                                            <>
                                                                <div className="flex gap-2 mt-6" dir="ltr">
                                                                    <button
                                                                        onClick={() => copyToClipboard(msg.content)}
                                                                        className="p-2 hover:bg-[var(--color-surface-hover)] rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title="Copy to clipboard"
                                                                    >
                                                                        <Copy className="w-4 h-4" />
                                                                    </button>
                                                                    <button
                                                                        className="p-2 hover:bg-[var(--color-surface-hover)] rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title="Refresh analysis"
                                                                    >
                                                                        <RefreshCw className="w-4 h-4" />
                                                                    </button>
                                                                </div>

                                                                {/* Smart Suggestion Chips */}
                                                                {index === messages.length - 1 && (
                                                                    <SuggestionChips
                                                                        suggestions={generateSuggestions(msg)}
                                                                        onSelect={(suggestion) => handleSendMessage(suggestion)}
                                                                        isRTL={isArabic(msg.content)}
                                                                    />
                                                                )}
                                                            </>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                {isTyping && (
                                    <div className="flex gap-5 mb-8 pl-1">
                                        <AgentAvatar thinking={true} />
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>
                </div>

                {/* BOTTOM INPUT BAR (OMNIBAR) - Centered when empty, bottom when chatting */}
                <div className={`absolute left-0 right-0 z-40 transition-all duration-700 ${!hasStarted
                    ? 'top-[50%] -translate-y-1/2 p-4'
                    : 'bottom-0 p-6'
                    }`}
                    style={{ transitionTimingFunction: 'cubic-bezier(0.25, 1, 0.5, 1)' }}
                >
                    <div className="max-w-[800px] mx-auto relative">
                        <div className={`bg-[var(--color-surface)] rounded-[28px] flex flex-col transition-all duration-200 ${isTyping ? 'opacity-50' : ''} border border-[var(--color-border)] focus-within:border-emerald-500/25 focus-within:shadow-[0_0_0_3px_rgba(16,185,129,0.06)] shadow-xl`}>

                            <textarea
                                dir="auto"
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask AMR about liquidity, market data, or properties..."
                                className="w-full bg-transparent border-none text-[var(--color-text-primary)] placeholder-gray-500 focus:ring-0 resize-none py-5 px-6 text-[17px] max-h-[200px] outline-none focus:outline-none ring-0 focus:ring-0"
                                rows={1}
                                disabled={isTyping}
                            />

                            <div className="flex items-center justify-between px-4 pb-4">
                                <div className="flex items-center gap-2">
                                    {/* Placeholder for additional icons */}
                                </div>

                                {inputValue.trim() && (
                                    <button
                                        onClick={() => handleSendMessage()}
                                        disabled={isTyping}
                                        className="p-2.5 bg-[var(--color-text-primary)] text-[var(--color-background)] rounded-full hover:opacity-80 transition-opacity shadow-md disabled:opacity-30 disabled:cursor-not-allowed"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className={`text-center mt-3 transition-opacity duration-500 ${!hasStarted ? 'opacity-0' : 'opacity-100'}`}>
                            <p className="text-[12px] text-[var(--color-text-muted)]">AMR can make mistakes. Verify critical financial data independently.</p>
                        </div>
                    </div>
                </div>

            </main>

            {/* ---------------------------------------------------------------------------
       * RIGHT PANE (WORKSPACE / CANVAS)
       * --------------------------------------------------------------------------- */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-[420px] bg-[var(--color-surface)] border-l border-[var(--color-border)] flex flex-col shadow-2xl z-40 relative">
                    <div className="h-16 border-b border-[var(--color-border)] flex items-center justify-between px-6 bg-[var(--color-surface)] flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <span className="text-[var(--color-text-primary)] font-medium text-lg">AMR Workspace</span>
                            <span className="text-[10px] text-emerald-500 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Live</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setContextPaneOpen(false)}
                                className="p-2 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)] rounded-full transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-8">

                        {/* Main Visual */}
                        <div className="space-y-4">
                            <div className="aspect-video bg-[var(--color-surface-hover)] rounded-2xl overflow-hidden relative shadow-2xl ring-1 ring-white/10">
                                <img
                                    src={activeContext.property.image}
                                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
                                    alt="Property Detail"
                                />
                                <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-md text-black px-3 py-1.5 rounded-full text-xs font-bold shadow-lg tracking-wide">
                                    {activeContext.property.status}
                                </div>
                            </div>
                            <div>
                                <h2 className="text-3xl font-medium text-[var(--color-text-primary)] leading-tight mb-2" dir="auto">
                                    {activeContext.property.title}
                                </h2>
                                <p className="text-[var(--color-text-muted)] flex items-center gap-1.5 text-sm" dir="auto">
                                    <MapPin className="w-4 h-4 text-emerald-500" />
                                    {activeContext.property.location}
                                </p>
                            </div>
                        </div>

                        {/* AI Insight Block */}
                        <div className="bg-[var(--color-surface-elevated)] rounded-2xl p-6 border border-[var(--color-border-light)] relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                                <Sparkles className="w-24 h-24 text-emerald-500" />
                            </div>
                            <div className="flex items-center gap-2 mb-4 relative z-10">
                                <Sparkles className="w-5 h-5 text-emerald-500 dark:text-emerald-400" />
                                <h3 className="font-medium text-[var(--color-text-primary)]">Osool Score Analysis</h3>
                            </div>
                            <div className="space-y-5 relative z-10">
                                <p className="text-[15px] text-[var(--color-text-secondary)] leading-relaxed" dir="auto">
                                    Analysis via AMR indicates this asset shows strong investment potential based on market comparables and liquidity metrics.
                                </p>
                                <div className="flex gap-6 pt-2">
                                    <div>
                                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider font-bold mb-1">Osool Score</div>
                                        <div className="text-3xl font-medium text-emerald-500 dark:text-emerald-400">
                                            {activeContext.property.metrics.wolf_score}
                                            <span className="text-sm text-emerald-600/50">/100</span>
                                        </div>
                                    </div>
                                    <div className="w-px bg-[var(--color-border)]" />
                                    <div>
                                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider font-bold mb-1">Liquidity</div>
                                        <div className="text-3xl font-medium text-emerald-400">
                                            {activeContext.property.metrics.liquidity_rating}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Data Grid */}
                        <div>
                            <h3 className="text-xs font-bold text-[var(--color-text-muted)] mb-4 uppercase tracking-widest pl-1">Specifications</h3>
                            <div className="grid grid-cols-2 gap-px bg-[var(--color-border)] rounded-2xl overflow-hidden border border-[var(--color-border-light)]">
                                <div className="bg-[var(--color-surface)] p-5 hover:bg-[var(--color-surface-elevated)] transition-colors">
                                    <div className="text-xs text-[var(--color-text-muted)] mb-1.5">Total Area</div>
                                    <div className="text-[var(--color-text-primary)] font-medium text-lg">
                                        {activeContext.property.metrics.size} <span className="text-sm text-[var(--color-text-muted)]">sqm</span>
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-5 hover:bg-[var(--color-surface-elevated)] transition-colors">
                                    <div className="text-xs text-[var(--color-text-muted)] mb-1.5">Bedrooms</div>
                                    <div className="text-[var(--color-text-primary)] font-medium text-lg">
                                        {activeContext.property.metrics.bedrooms} <span className="text-sm text-[var(--color-text-muted)]">Beds</span>
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-5 hover:bg-[var(--color-surface-elevated)] transition-colors">
                                    <div className="text-xs text-[var(--color-text-muted)] mb-1.5">Price / Meter</div>
                                    <div className="text-[var(--color-text-primary)] font-medium text-lg">
                                        {activeContext.property.metrics.price_per_sqm > 0
                                            ? `${(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                            : 'N/A'
                                        } <span className="text-sm text-[var(--color-text-muted)]">EGP</span>
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-5 hover:bg-[var(--color-surface-elevated)] transition-colors">
                                    <div className="text-xs text-[var(--color-text-muted)] mb-1.5">Total Price</div>
                                    <div className="text-emerald-500 dark:text-emerald-400 font-medium text-lg">
                                        {(activeContext.property.price / 1000000).toFixed(2)}M
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Tags */}
                        {activeContext.property.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                                {activeContext.property.tags.map((tag, i) => (
                                    <span
                                        key={i}
                                        className="text-xs bg-emerald-500/10 text-emerald-500 dark:text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/20/50"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        <button className="w-full py-4 bg-[var(--color-text-primary)] hover:opacity-90 text-[var(--color-background)] rounded-full font-bold text-sm tracking-wide transition-all shadow-lg transform hover:-translate-y-0.5">
                            Request Viewing
                        </button>

                    </div>
                </aside>
            )}

        </div>
    );
}
