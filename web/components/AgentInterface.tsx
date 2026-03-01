'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Sparkles, MapPin,
    X, ChevronRight,
    BarChart2, Shield, Search,
    Copy, RefreshCw, Wallet, ArrowUp
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import dynamic from 'next/dynamic';
import SuggestionChips from '@/components/SuggestionChips';
import FunnelIndicator from '@/components/FunnelIndicator';

const VisualizationRenderer = dynamic(
    () => import('@/components/visualizations/VisualizationRenderer'),
    { ssr: false }
);

/* Types */
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

const SUGGESTIONS: Suggestion[] = [
    { icon: BarChart2, label: "Market Intelligence", prompt: "Analyze current market trends in New Cairo" },
    { icon: Search, label: "Find Opportunities", prompt: "Find high ROI properties under 5M EGP" },
    { icon: Wallet, label: "Liquidity Check", prompt: "Calculate liquidity potential for my unit" },
    { icon: Shield, label: "Developer Audit", prompt: "Audit the delivery history of Palm Hills" },
];

/* Agent Avatar — Minimal monogram */
const AgentAvatar = ({ thinking = false }: { thinking?: boolean }) => (
    <div className={`relative flex items-center justify-center w-8 h-8 rounded-[10px] overflow-hidden flex-shrink-0 shadow-sm ${thinking ? 'animate-pulse' : ''}`}>
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 to-gray-700 dark:from-gray-100 dark:to-gray-300" />
        <span className="relative text-[11px] font-bold text-white dark:text-gray-900 tracking-tight">OA</span>
        <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white dark:border-gray-900" />
    </div>
);

/* RTL Detection */
const isArabic = (text: string): boolean => {
    if (!text) return false;
    const arabicChars = text.match(/[\u0600-\u06FF]/g);
    return !!arabicChars && arabicChars.length > text.length * 0.3;
};

/* Markdown Renderer */
const MarkdownMessage = ({ content }: { content: string }) => {
    const msgIsArabic = isArabic(content);
    const normalized = content
        .replace(/\r\n/g, '\n')
        .replace(/\n{3,}/g, '\n\n')
        .replace(/(?<!\n)\n(?!\n)/g, '\n\n');

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
                    li: ({ node, ...props }) => <li className="mb-1" {...props} />,
                    strong: ({ node, ...props }) => (
                        <strong className="font-semibold text-[var(--color-text-primary)]" {...props} />
                    ),
                    em: ({ node, ...props }) => (
                        <em className="italic text-[var(--color-text-secondary)]" {...props} />
                    ),
                    h1: ({ node, ...props }) => <h1 className="text-xl font-semibold mb-3 mt-4" {...props} />,
                    h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-2 mt-3" {...props} />,
                    h3: ({ node, ...props }) => <h3 className="text-base font-medium mb-2 mt-2" {...props} />,
                    blockquote: ({ node, ...props }) => (
                        <blockquote
                            className={`${msgIsArabic ? 'border-r-2 pr-4' : 'border-l-2 pl-4'} border-emerald-500/40 py-1 my-2 text-[var(--color-text-secondary)]`}
                            {...props}
                        />
                    ),
                    a: ({ node, ...props }) => (
                        <a className="text-emerald-600 dark:text-emerald-400 hover:underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                    code: ({ node, className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                            <code className="bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)] px-1.5 py-0.5 rounded text-[13px] font-mono" {...props}>{children}</code>
                        ) : (
                            <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 my-3 overflow-x-auto">
                                <code className="text-sm text-[var(--color-text-secondary)] font-mono" {...props}>{children}</code>
                            </pre>
                        );
                    },
                    hr: ({ node, ...props }) => <hr className="border-[var(--color-border)] my-4" {...props} />,
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-3 rounded-lg border border-[var(--color-border)]">
                            <table className="w-full border-collapse text-sm" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-left text-[var(--color-text-primary)] font-medium text-xs uppercase tracking-wider" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="border-b border-[var(--color-border)] px-3 py-2.5 text-[var(--color-text-secondary)]" {...props} />
                    ),
                }}
            >
                {normalized}
            </ReactMarkdown>
        </div>
    );
};

/* Main Component */
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
    const sessionIdRef = useRef<string>(`session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`);

    const userName = user?.full_name || user?.email?.split('@')[0] || 'Investor';

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
        }
    }, [inputValue]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    const handleSendMessage = useCallback(async (text?: string) => {
        const content = text || inputValue;
        if (!content.trim() || isTyping) return;

        setRecentQueries(prev => {
            const updated = [content.slice(0, 40), ...prev.filter(q => q !== content.slice(0, 40))];
            return updated.slice(0, 5);
        });

        const userMsg: Message = { id: Date.now(), role: 'user', content };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        try {
            const response = await api.post('/api/chat', {
                message: content,
                session_id: sessionIdRef.current,
                language: 'auto'
            });
            const data = response.data;
            console.log('[AMR] API Response:', data);

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
            triggerXP(5, 'Asked a question');

            if (aiMsg.uiActions && aiMsg.uiActions.length > 0) {
                triggerXP(15, 'Used analysis tool');
            }

            if (aiMsg.artifacts) {
                setActiveContext(aiMsg.artifacts);
            }
        } catch (error: any) {
            console.error('[AMR] API Error:', error?.response?.data || error?.message || error);
            const errorMsg = error?.response?.data?.detail || error?.response?.data?.error ||
                "I'm AMR (Automated Market Researcher). I can access the Osool liquidity engine, analyze market data, and audit real estate assets. How can I assist with your portfolio today?";
            const aiMsg: Message = { id: Date.now() + 1, role: 'agent', content: errorMsg, artifacts: null };
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
        sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const hasStarted = messages.length > 0;

    const generateSuggestions = (msg: Message): string[] => {
        const suggestions: string[] = [];
        const content = msg.content.toLowerCase();
        const hasProperties = msg.allProperties && msg.allProperties.length > 0;
        const hasAnalytics = msg.analyticsContext?.has_analytics;

        if (hasProperties) {
            suggestions.push('Compare these properties');
            suggestions.push('Show ROI analysis');
            suggestions.push('Payment plan options?');
        } else if (hasAnalytics) {
            suggestions.push('Show price trends');
            suggestions.push('Best growth areas?');
            suggestions.push('Compare alternatives');
        } else if (content.includes('developer') || content.includes('مطور')) {
            suggestions.push('Track record');
            suggestions.push('Compare delivery dates');
            suggestions.push('Available units');
        } else if (content.includes('area') || content.includes('location') || content.includes('منطقة')) {
            suggestions.push('Price per sqm');
            suggestions.push('Nearby areas');
            suggestions.push('Infrastructure');
        } else {
            suggestions.push('Top properties');
            suggestions.push('Market overview');
            suggestions.push('Set my budget');
        }

        return suggestions.slice(0, 3);
    };

    return (
        <div className="flex h-full min-h-0 w-full bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-emerald-500/15 relative">

            {/* Main Chat */}
            <main className="flex-1 flex flex-col relative min-w-0 h-full w-full min-h-0 z-0">

                {/* Top bar — only visible in conversation */}
                {hasStarted && (
                    <div className="absolute top-4 left-0 right-0 flex items-center justify-between px-6 z-30 pointer-events-none">
                        <div className="pointer-events-auto bg-[var(--color-surface)]/80 backdrop-blur-xl border border-[var(--color-border)]/50 px-4 py-2 rounded-full shadow-sm">
                            <span className="text-[13px] font-semibold text-[var(--color-text-primary)] tracking-tight">
                                Osool AI <span className="text-[var(--color-text-muted)] font-medium mx-1.5">/</span> <span className="text-[var(--color-text-secondary)] font-medium">Session</span>
                            </span>
                        </div>
                        <button
                            onClick={handleNewChat}
                            className="pointer-events-auto p-2 bg-[var(--color-surface)]/80 backdrop-blur-xl border border-[var(--color-border)]/50 hover:bg-[var(--color-surface)] rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] shadow-sm transition-all hover:scale-105 active:scale-95"
                            title="New Chat"
                        >
                            <RefreshCw className="w-4 h-4" strokeWidth={2} />
                        </button>
                    </div>
                )}

                {/* Funnel */}
                {hasStarted && profile && (
                    <div className="absolute top-12 left-0 right-0 z-20 pointer-events-none">
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
                    <div className="max-w-[980px] mx-auto h-full w-full">

                        {/* Greeting */}
                        {!hasStarted && (
                            <div className="flex flex-col min-h-[calc(100vh-12rem)] justify-center px-4 py-8 relative">
                                {/* Decorative background elements for Figma style */}
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/5 dark:bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none -z-10" />

                                <div className="text-center w-full max-w-3xl mx-auto">
                                    <h1 className="text-[3.5rem] md:text-[4.5rem] font-semibold tracking-tight leading-[1.1] mb-5 text-[var(--color-text-primary)]">
                                        Hello, {userName}
                                    </h1>
                                    <p className="text-[1.25rem] md:text-[1.5rem] text-[var(--color-text-muted)] font-medium max-w-2xl mx-auto leading-relaxed">
                                        What can I help you with<span className="text-emerald-500 font-bold ml-0.5">?</span>
                                    </p>
                                </div>

                                    <div className="w-full max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3 mt-12 px-4">
                                        {SUGGESTIONS.map((s, i) => (
                                            <button
                                                key={i}
                                                onClick={() => handleSendMessage(s.prompt)}
                                                className="p-5 bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)] backdrop-blur-md rounded-3xl text-left transition-all duration-300 h-36 flex flex-col justify-between group border border-[var(--color-border)]/50 hover:border-[var(--color-border)] hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-1"
                                            >
                                                <span className="text-[13px] font-medium text-[var(--color-text-primary)] leading-snug group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" dir="auto">{s.label}</span>
                                                <div className="self-end p-2 bg-[var(--color-background)] rounded-xl text-[var(--color-text-muted)] group-hover:bg-emerald-50 dark:group-hover:bg-emerald-500/10 group-hover:text-emerald-500 transition-colors">
                                                    <s.icon className="w-4 h-4" strokeWidth={1.75} />
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                            </div>
                        )}

                        {/* Messages */}
                        {hasStarted && (
                            <div className="px-4 pt-20 pb-8">
                                {messages.map((msg, index) => (
                                    <div key={msg.id} className="mb-6 animate-fade-in">
                                        <div className="flex gap-4">
                                            <div className="flex-shrink-0 mt-1">
                                                {msg.role === 'user' ? null : <AgentAvatar />}
                                            </div>

                                            <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                                                {msg.role === 'user' ? (
                                                    <div
                                                        className="bg-gray-100 dark:bg-gray-800/80 text-[var(--color-text-primary)] px-5 py-3.5 rounded-3xl rounded-br-[8px] max-w-[85%] text-[15px] leading-relaxed shadow-sm font-medium"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div className="text-[15px] leading-8 text-[var(--color-text-secondary)] tracking-wide pt-1" dir="auto">
                                                        <MarkdownMessage content={msg.content} />

                                                        {/* Visualizations */}
                                                        {msg.uiActions && msg.uiActions.length > 0 && (
                                                            <div className="mt-5 space-y-3" dir="ltr">
                                                                {msg.uiActions
                                                                    .filter((action: any) => {
                                                                        if (action.type === 'property_cards') return false;
                                                                        if (!action.data) return false;
                                                                        const d = action.data;
                                                                        if (action.type === 'area_analysis') {
                                                                            const area = d.area || d.areas?.[0] || d;
                                                                            if (!area?.name || (area?.avg_price_sqm || area?.avg_price_per_sqm || 0) === 0) return false;
                                                                        }
                                                                        if (action.type === 'inflation_killer') {
                                                                            const hasP = d.projections?.length > 0 || d.data_points?.length > 0;
                                                                            const hasS = d.summary?.cash_final > 0 || d.final_values?.cash_real_value > 0;
                                                                            if (!hasP && !hasS) return false;
                                                                        }
                                                                        if (action.type === 'market_benchmark') {
                                                                            if (!d.avg_price_sqm && !d.area_context?.avg_price_sqm) return false;
                                                                        }
                                                                        if (action.type === 'price_growth_chart') {
                                                                            if (!d.data_points?.length || d.data_points.length < 2) return false;
                                                                        }
                                                                        return true;
                                                                    })
                                                                    .map((action: any, idx: number) => (
                                                                        <div key={idx} className="animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
                                                                            <VisualizationRenderer
                                                                                type={action.type}
                                                                                data={action.data || action}
                                                                                isRTL={isArabic(msg.content)}
                                                                            />
                                                                        </div>
                                                                    ))}
                                                            </div>
                                                        )}

                                                        {/* Analytics Panel */}
                                                        {msg.analyticsContext?.has_analytics && (!msg.allProperties || msg.allProperties.length === 0) && (
                                                            <div className="mt-5 p-6 rounded-[20px] border border-[var(--color-border)]/50 bg-[var(--color-surface)] shadow-[0_4px_24px_rgba(0,0,0,0.03)]" dir="ltr">
                                                                <div className="flex items-center gap-2 mb-5">
                                                                    <div className="p-1.5 bg-emerald-50 dark:bg-emerald-500/10 rounded-lg">
                                                                        <BarChart2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" strokeWidth={2.5} />
                                                                    </div>
                                                                    <span className="text-[11px] font-bold text-[var(--color-text-primary)] uppercase tracking-widest pl-1">Market Intelligence</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 md:grid-cols-3 gap-y-6 gap-x-4">
                                                                    {msg.analyticsContext.avg_price_sqm > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Avg Price/m²</div>
                                                                            <div className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                {msg.analyticsContext.avg_price_sqm?.toLocaleString()} <span className="text-[13px] font-medium text-[var(--color-text-muted)] tracking-normal">EGP</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.growth_rate > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Growth Rate</div>
                                                                            <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 tracking-tight">
                                                                                +{(msg.analyticsContext.growth_rate * 100).toFixed(0)}% <span className="text-[13px] font-medium text-[var(--color-text-muted)] tracking-normal">YoY</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.rental_yield > 0 && (
                                                                        <div>
                                                                            <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">Rental Yield</div>
                                                                            <div className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                {(msg.analyticsContext.rental_yield * 100).toFixed(1)}%
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {/* Property Cards */}
                                                        {msg.allProperties && msg.allProperties.length > 0 && (
                                                            <div className="mt-5 space-y-2" dir="ltr">
                                                                {msg.allProperties.map((prop, idx) => (
                                                                    <div
                                                                        key={prop.id}
                                                                        onClick={() => { setActiveContext({ property: prop }); setContextPaneOpen(true); }}
                                                                        className="group relative flex gap-4 p-4 border border-[var(--color-border)]/60 hover:border-emerald-500/40 bg-[var(--color-surface)]/60 backdrop-blur-sm rounded-2xl cursor-pointer transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.04)] hover:-translate-y-0.5"
                                                                        style={{ animationDelay: `${idx * 80}ms` }}
                                                                    >
                                                                        {/* Image */}
                                                                        <div className="w-[84px] h-[84px] md:w-24 md:h-24 bg-[var(--color-surface-hover)] rounded-[14px] flex-shrink-0 overflow-hidden shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)]">
                                                                            <img src={prop.image} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out" alt={prop.title} />
                                                                        </div>

                                                                        {/* Info */}
                                                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                                            <h3 className="font-semibold text-[var(--color-text-primary)] truncate text-[15px]" dir="auto">{prop.title}</h3>
                                                                            <p className="text-[13px] text-[var(--color-text-muted)] truncate mt-0.5" dir="auto">
                                                                                {prop.location} {prop.developer && <span className="mx-1.5 opacity-50">·</span>} {prop.developer}
                                                                            </p>
                                                                            <div className="flex items-center gap-2.5 mt-2.5">
                                                                                <span className="text-[15px] font-bold text-[var(--color-text-primary)] tracking-tight">
                                                                                    {(prop.price / 1000000).toFixed(1)}M <span className="text-[11px] font-medium text-[var(--color-text-muted)]">EGP</span>
                                                                                </span>
                                                                                {prop.metrics.price_per_sqm > 0 && (
                                                                                    <span className="text-[11px] font-medium text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] px-2 py-0.5 rounded-md">
                                                                                        {prop.metrics.price_per_sqm.toLocaleString()}/m²
                                                                                    </span>
                                                                                )}
                                                                                {prop.metrics.roi > 0 && (
                                                                                    <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-md">
                                                                                        +{prop.metrics.roi}% ROI
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            {prop.metrics.wolf_score > 0 && (
                                                                                <div className="mt-2.5 flex items-center gap-2">
                                                                                    <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden max-w-[120px]">
                                                                                        <div
                                                                                            className="h-full rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.4)] transition-all duration-1000 ease-out"
                                                                                            style={{ width: `${Math.min(prop.metrics.wolf_score, 100)}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <span className="text-[10px] text-[var(--color-text-secondary)] font-semibold">{prop.metrics.wolf_score}<span className="text-[8px] text-[var(--color-text-muted)] font-medium">/100</span></span>
                                                                                </div>
                                                                            )}
                                                                        </div>

                                                                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] group-hover:bg-emerald-50 dark:group-hover:bg-emerald-500/10 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors self-center shadow-sm">
                                                                            <ChevronRight className="w-4 h-4" strokeWidth={2.5} />
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}

                                                        {/* Actions + Suggestions */}
                                                        {!isTyping && (
                                                            <>
                                                                <div className="flex gap-1 mt-4" dir="ltr">
                                                                    <button
                                                                        onClick={() => copyToClipboard(msg.content)}
                                                                        className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title="Copy"
                                                                    >
                                                                        <Copy className="w-3.5 h-3.5" />
                                                                    </button>
                                                                    <button
                                                                        className="p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                                                        title="Retry"
                                                                    >
                                                                        <RefreshCw className="w-3.5 h-3.5" />
                                                                    </button>
                                                                </div>

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

                                {/* Typing indicator */}
                                {isTyping && (
                                    <div className="flex gap-4 mb-6">
                                        <AgentAvatar thinking={true} />
                                        <div className="flex items-center gap-1 pt-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '0ms' }} />
                                            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '150ms' }} />
                                            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                )}

                                <div ref={messagesEndRef} />
                            </div>
                        )}
                    </div>
                </div>

                {/* Input Bar - Floating Figma Style */}
                <div className="sticky bottom-0 left-0 right-0 z-40 px-4 md:px-6 pb-6 pt-12 bg-gradient-to-t from-[var(--color-background)] via-[var(--color-background)]/95 to-transparent pointer-events-none">
                    <div className="max-w-[800px] mx-auto relative pointer-events-auto">
                        <div className={`bg-[var(--color-surface)]/95 backdrop-blur-2xl rounded-[24px] flex flex-col transition-all duration-300 ${isTyping ? 'opacity-70 scale-[0.99]' : ''} shadow-[0_8px_30px_rgba(0,0,0,0.04)]`}>

                            <textarea
                                dir="auto"
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask about properties, market data, or investments..."
                                className="w-full bg-transparent border-none text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-0 resize-none py-4 px-6 text-[15px] max-h-[180px] outline-none ring-0 leading-normal font-medium"
                                rows={1}
                                disabled={isTyping}
                            />

                            {(hasStarted || inputValue.trim()) && (
                                <div className="flex items-center justify-between px-4 pb-3">
                                    <div className="flex items-center gap-1.5 text-[11px] font-medium text-[var(--color-text-muted)]/60">
                                        {hasStarted && <span><span className="font-mono bg-[var(--color-background)] px-1 py-0.5 rounded border border-[var(--color-border)] opacity-80">⇧</span> + <span className="font-mono bg-[var(--color-background)] px-1 py-0.5 rounded border border-[var(--color-border)] opacity-80">↵</span> for new line</span>}
                                    </div>

                                    {inputValue.trim() && (
                                        <button
                                            onClick={() => handleSendMessage()}
                                            disabled={isTyping}
                                            title="Send message"
                                            className="p-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl hover:scale-105 active:scale-95 shadow-sm transition-all duration-200 disabled:opacity-30 disabled:pointer-events-none"
                                        >
                                            <ArrowUp className="w-4 h-4" strokeWidth={2.5} />
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>

                        <div className={`text-center mt-3 transition-all duration-300 ${!hasStarted ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}`}>
                            <p className="text-[11px] font-medium text-[var(--color-text-muted)]/60">AMR is an AI agent. Please verify critical investment data independently.</p>
                        </div>
                    </div>
                </div>

            </main>

            {/* Context Pane - Floating Style */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-[400px] bg-[var(--color-surface)]/90 backdrop-blur-2xl border-l border-[var(--color-border)]/50 flex flex-col z-40 relative hidden lg:flex shadow-[-10px_0_40px_rgba(0,0,0,0.04)] m-4 ml-0 rounded-[24px] overflow-hidden">
                    {/* Header */}
                    <div className="h-14 border-b border-[var(--color-border)]/50 flex items-center justify-between px-6 flex-shrink-0 bg-white/50 dark:bg-gray-800/50">
                        <div className="flex items-center gap-2.5">
                            <span className="text-[15px] font-semibold text-[var(--color-text-primary)]">Details</span>
                            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold uppercase tracking-widest shadow-sm">Live Context</span>
                        </div>
                        <button
                            onClick={() => setContextPaneOpen(false)}
                            title="Close details pane"
                            className="w-8 h-8 flex items-center justify-center text-[var(--color-text-muted)] hover:text-gray-900 dark:hover:text-white bg-gray-100/50 dark:bg-gray-800/50 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-all"
                        >
                            <X className="w-4 h-4" strokeWidth={2} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-7 custom-scrollbar">

                        {/* Image */}
                        <div className="space-y-4">
                            <div className="aspect-video bg-[var(--color-surface-hover)] rounded-2xl overflow-hidden relative shadow-[inset_0_0_0_1px_rgba(0,0,0,0.05)] shadow-md">
                                <img
                                    src={activeContext.property.image}
                                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-700 ease-out"
                                    alt="Property"
                                />
                                <div className="absolute top-3 right-3 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md text-[var(--color-text-primary)] px-3 py-1.5 rounded-full text-[11px] font-semibold shadow-sm border border-black/5 dark:border-white/10">
                                    {activeContext.property.status}
                                </div>
                            </div>
                            <div>
                                <h2 className="text-[22px] font-semibold text-[var(--color-text-primary)] leading-tight mb-1.5 tracking-tight" dir="auto">
                                    {activeContext.property.title}
                                </h2>
                                <p className="text-[var(--color-text-muted)] flex items-center gap-1.5 text-[14px] font-medium" dir="auto">
                                    <MapPin className="w-4 h-4 text-emerald-500" strokeWidth={2} />
                                    {activeContext.property.location}
                                </p>
                            </div>
                        </div>

                        {/* Score */}
                        <div className="bg-gradient-to-br from-emerald-500/5 to-transparent rounded-[20px] p-5 border border-emerald-500/10 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 blur-[40px] rounded-full" />
                            <div className="flex items-center gap-2 mb-5 relative z-10">
                                <Sparkles className="w-5 h-5 text-emerald-500" strokeWidth={2} />
                                <h3 className="text-[15px] font-semibold text-[var(--color-text-primary)]">Osool Intelligence Score</h3>
                            </div>
                            <div className="flex gap-8 relative z-10">
                                <div>
                                    <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Index</div>
                                    <div className="text-3xl font-bold text-emerald-500 tracking-tighter">
                                        {activeContext.property.metrics.wolf_score}
                                        <span className="text-lg font-medium text-[var(--color-text-muted)] tracking-normal">/100</span>
                                    </div>
                                </div>
                                <div className="w-px bg-emerald-500/20" />
                                <div>
                                    <div className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Liquidity</div>
                                    <div className="text-3xl font-bold text-[var(--color-text-primary)] tracking-tighter">
                                        {activeContext.property.metrics.liquidity_rating}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Specs Grid */}
                        <div>
                            <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] mb-3.5 uppercase tracking-widest pl-1">Specifications</h3>
                            <div className="grid grid-cols-2 gap-2">
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Total Built Area</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.size} <span className="text-[12px] font-medium text-[var(--color-text-muted)]">m²</span>
                                    </div>
                                </div>
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Bedrooms</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.bedrooms}
                                    </div>
                                </div>
                                <div className="bg-gray-50/50 dark:bg-gray-800/40 p-4 rounded-2xl border border-[var(--color-border)]/50">
                                    <div className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1">Price per m²</div>
                                    <div className="text-[var(--color-text-primary)] font-semibold text-[15px]">
                                        {activeContext.property.metrics.price_per_sqm > 0
                                            ? `${(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                            : 'N/A'
                                        }
                                    </div>
                                </div>
                                <div className="bg-emerald-50/50 dark:bg-emerald-500/5 p-4 rounded-2xl border border-emerald-500/20">
                                    <div className="text-[11px] font-medium text-emerald-600/80 dark:text-emerald-400/80 mb-1">Total Valuation</div>
                                    <div className="text-emerald-600 dark:text-emerald-400 font-bold text-[15px]">
                                        {(activeContext.property.price / 1000000).toFixed(2)}M
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Tags */}
                        {activeContext.property.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-2">
                                {activeContext.property.tags.map((tag, i) => (
                                    <span key={i} className="text-[12px] font-medium bg-gray-100 dark:bg-gray-800 text-[var(--color-text-primary)] px-3.5 py-1.5 rounded-full border border-gray-200 dark:border-gray-700">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        <div className="pt-4 pb-2">
                            <button className="w-full py-4 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-[16px] font-semibold text-[15px] transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-black/10 dark:shadow-white/10 flex items-center justify-center gap-2">
                                Request Private Viewing
                                <ChevronRight className="w-4 h-4 opacity-70" strokeWidth={2.5} />
                            </button>
                        </div>
                    </div>
                </aside>
            )}
        </div>
    );
}
