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
    <div className={`relative flex items-center justify-center w-7 h-7 rounded-lg overflow-hidden flex-shrink-0 ${thinking ? 'animate-pulse' : ''}`}>
        <div className="absolute inset-0 bg-[var(--color-text-primary)]" />
        <span className="relative text-[10px] font-bold text-[var(--color-background)] tracking-tight">A</span>
        <div className="absolute bottom-0 right-0 w-1.5 h-1.5 rounded-full bg-emerald-400" />
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
                    <div className="absolute top-0 left-0 right-0 h-12 flex items-center justify-between px-6 z-30 pointer-events-none">
                        <div className="pointer-events-auto">
                            <span className="text-sm font-medium text-[var(--color-text-muted)] tracking-tight">
                                AMR <span className="text-[var(--color-text-muted)]/50">·</span> Session
                            </span>
                        </div>
                        <button
                            onClick={handleNewChat}
                            className="pointer-events-auto p-2 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                            title="New Chat"
                        >
                            <RefreshCw className="w-4 h-4" />
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
                            <div className="flex flex-col min-h-[calc(100vh-12rem)] justify-center px-4 py-10">
                                <div className="text-center w-full max-w-2xl mx-auto">
                                        <h1 className="text-5xl md:text-6xl font-medium tracking-tight mb-4 text-[var(--color-text-primary)]">
                                            Hello, {userName}
                                        </h1>
                                        <p className="text-xl md:text-2xl text-[var(--color-text-muted)] font-light max-w-xl mx-auto">
                                            What can I help you with<span className="text-emerald-500">?</span>
                                        </p>
                                    </div>

                                    <div className="w-full max-w-3xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-2.5 mt-10">
                                        {SUGGESTIONS.map((s, i) => (
                                            <button
                                                key={i}
                                                onClick={() => handleSendMessage(s.prompt)}
                                                className="p-4 bg-[var(--color-surface)] hover:bg-[var(--color-surface-hover)] rounded-2xl text-left transition-all duration-200 h-32 flex flex-col justify-between group border border-[var(--color-border)] hover:border-[var(--color-text-muted)]/20"
                                            >
                                                <span className="text-[13px] font-medium text-[var(--color-text-primary)] leading-snug" dir="auto">{s.label}</span>
                                                <div className="self-end p-1.5 bg-[var(--color-background)] rounded-lg text-[var(--color-text-muted)] group-hover:text-emerald-500 transition-colors">
                                                    <s.icon className="w-4 h-4" />
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
                                                        className="bg-[var(--color-surface)] text-[var(--color-text-primary)] px-5 py-3 rounded-2xl rounded-br-md max-w-[80%] text-[15px] leading-relaxed border border-[var(--color-border)]"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div className="text-[15px] leading-7 text-[var(--color-text-secondary)] tracking-wide" dir="auto">
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
                                                            <div className="mt-5 p-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]" dir="ltr">
                                                                <div className="flex items-center gap-2 mb-4">
                                                                    <BarChart2 className="w-4 h-4 text-emerald-500" />
                                                                    <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">Market Intelligence</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                                                    {msg.analyticsContext.avg_price_sqm > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Avg Price/m²</div>
                                                                            <div className="text-lg font-semibold text-[var(--color-text-primary)]">
                                                                                {msg.analyticsContext.avg_price_sqm?.toLocaleString()} <span className="text-xs text-[var(--color-text-muted)]">EGP</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.growth_rate > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Growth Rate</div>
                                                                            <div className="text-lg font-semibold text-emerald-500">
                                                                                +{(msg.analyticsContext.growth_rate * 100).toFixed(0)}% <span className="text-xs text-[var(--color-text-muted)]">YoY</span>
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                    {msg.analyticsContext.rental_yield > 0 && (
                                                                        <div>
                                                                            <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Rental Yield</div>
                                                                            <div className="text-lg font-semibold text-[var(--color-text-primary)]">
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
                                                                        className="group relative flex gap-4 p-3.5 border border-[var(--color-border)] hover:border-emerald-500/30 bg-[var(--color-surface)] rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md hover:shadow-black/5"
                                                                        style={{ animationDelay: `${idx * 80}ms` }}
                                                                    >
                                                                        {/* Image */}
                                                                        <div className="w-[72px] h-[72px] md:w-20 md:h-20 bg-[var(--color-surface-hover)] rounded-lg flex-shrink-0 overflow-hidden">
                                                                            <img src={prop.image} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt={prop.title} />
                                                                        </div>

                                                                        {/* Info */}
                                                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                                            <h3 className="font-medium text-[var(--color-text-primary)] truncate text-sm" dir="auto">{prop.title}</h3>
                                                                            <p className="text-xs text-[var(--color-text-muted)] truncate mt-0.5" dir="auto">
                                                                                {prop.location} {prop.developer && `· ${prop.developer}`}
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
                                                                                    <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/8 px-1.5 py-0.5 rounded">
                                                                                        +{prop.metrics.roi}% ROI
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            {prop.metrics.wolf_score > 0 && (
                                                                                <div className="mt-1.5 flex items-center gap-2">
                                                                                    <div className="flex-1 h-1 bg-[var(--color-border)] rounded-full overflow-hidden max-w-[100px]">
                                                                                        <div
                                                                                            className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                                                                                            style={{ width: `${Math.min(prop.metrics.wolf_score, 100)}%` }}
                                                                                        />
                                                                                    </div>
                                                                                    <span className="text-[9px] text-emerald-600 dark:text-emerald-400 font-semibold">{prop.metrics.wolf_score}</span>
                                                                                </div>
                                                                            )}
                                                                        </div>

                                                                        <div className="flex items-center text-[var(--color-text-muted)] group-hover:text-emerald-500 transition-colors">
                                                                            <ChevronRight className="w-4 h-4" />
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

                {/* Input Bar */}
                <div className="sticky bottom-0 left-0 right-0 z-40 px-4 md:px-6 pb-4 pt-3 border-t border-[var(--color-border)] bg-[var(--color-background)]/92 backdrop-blur-xl">
                    <div className="max-w-[980px] mx-auto relative">
                        <div className={`bg-[var(--color-surface)] rounded-2xl flex flex-col transition-all duration-150 ${isTyping ? 'opacity-60' : ''} border border-[var(--color-border)] focus-within:border-[var(--color-text-muted)]/30 shadow-lg shadow-black/5 dark:shadow-black/20`}>

                            <textarea
                                dir="auto"
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask about properties, market data, or investments..."
                                className="w-full bg-transparent border-none text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-0 resize-none py-4 px-5 text-[15px] max-h-[180px] outline-none ring-0"
                                rows={1}
                                disabled={isTyping}
                            />

                            <div className="flex items-center justify-between px-3 pb-3">
                                <div className="flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]/60">
                                    {hasStarted && <span>Shift + Enter for new line</span>}
                                </div>

                                {inputValue.trim() && (
                                    <button
                                        onClick={() => handleSendMessage()}
                                        disabled={isTyping}
                                        title="Send message"
                                        className="p-2 bg-[var(--color-text-primary)] text-[var(--color-background)] rounded-lg hover:opacity-85 transition-opacity disabled:opacity-30 disabled:cursor-not-allowed"
                                    >
                                        <ArrowUp className="w-4 h-4" strokeWidth={2.5} />
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className={`text-center mt-2 transition-opacity duration-300 ${!hasStarted ? 'opacity-0' : 'opacity-100'}`}>
                            <p className="text-[11px] text-[var(--color-text-muted)]/50">AMR may make mistakes. Verify critical data independently.</p>
                        </div>
                    </div>
                </div>

            </main>

            {/* Context Pane */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-[380px] bg-[var(--color-surface)] border-l border-[var(--color-border)] flex flex-col z-40 relative hidden lg:flex">
                    {/* Header */}
                    <div className="h-12 border-b border-[var(--color-border)] flex items-center justify-between px-5 flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-[var(--color-text-primary)]">Details</span>
                            <span className="text-[9px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/8 px-1.5 py-0.5 rounded font-medium uppercase tracking-wider">Live</span>
                        </div>
                        <button
                            onClick={() => setContextPaneOpen(false)}
                            title="Close details pane"
                            className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)] rounded-lg transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-5 space-y-6">

                        {/* Image */}
                        <div className="space-y-3">
                            <div className="aspect-video bg-[var(--color-surface-hover)] rounded-xl overflow-hidden relative">
                                <img
                                    src={activeContext.property.image}
                                    className="w-full h-full object-cover hover:scale-[1.02] transition-transform duration-500"
                                    alt="Property"
                                />
                                <div className="absolute top-3 right-3 bg-[var(--color-background)]/90 backdrop-blur-sm text-[var(--color-text-primary)] px-2.5 py-1 rounded-lg text-[10px] font-medium border border-[var(--color-border)]">
                                    {activeContext.property.status}
                                </div>
                            </div>
                            <div>
                                <h2 className="text-xl font-medium text-[var(--color-text-primary)] leading-tight mb-1" dir="auto">
                                    {activeContext.property.title}
                                </h2>
                                <p className="text-[var(--color-text-muted)] flex items-center gap-1 text-sm" dir="auto">
                                    <MapPin className="w-3.5 h-3.5 text-emerald-500" />
                                    {activeContext.property.location}
                                </p>
                            </div>
                        </div>

                        {/* Score */}
                        <div className="bg-[var(--color-surface-elevated)] rounded-xl p-5 border border-[var(--color-border)]">
                            <div className="flex items-center gap-2 mb-4">
                                <Sparkles className="w-4 h-4 text-emerald-500" />
                                <h3 className="text-sm font-medium text-[var(--color-text-primary)]">Osool Score</h3>
                            </div>
                            <div className="flex gap-6">
                                <div>
                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Score</div>
                                    <div className="text-2xl font-medium text-emerald-500">
                                        {activeContext.property.metrics.wolf_score}
                                        <span className="text-sm text-[var(--color-text-muted)]">/100</span>
                                    </div>
                                </div>
                                <div className="w-px bg-[var(--color-border)]" />
                                <div>
                                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Liquidity</div>
                                    <div className="text-2xl font-medium text-[var(--color-text-primary)]">
                                        {activeContext.property.metrics.liquidity_rating}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Specs Grid */}
                        <div>
                            <h3 className="text-[10px] font-medium text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">Specifications</h3>
                            <div className="grid grid-cols-2 gap-px bg-[var(--color-border)] rounded-xl overflow-hidden">
                                <div className="bg-[var(--color-surface)] p-4">
                                    <div className="text-[10px] text-[var(--color-text-muted)] mb-1">Area</div>
                                    <div className="text-[var(--color-text-primary)] font-medium">
                                        {activeContext.property.metrics.size} <span className="text-xs text-[var(--color-text-muted)]">m²</span>
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-4">
                                    <div className="text-[10px] text-[var(--color-text-muted)] mb-1">Bedrooms</div>
                                    <div className="text-[var(--color-text-primary)] font-medium">
                                        {activeContext.property.metrics.bedrooms}
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-4">
                                    <div className="text-[10px] text-[var(--color-text-muted)] mb-1">Price/m²</div>
                                    <div className="text-[var(--color-text-primary)] font-medium">
                                        {activeContext.property.metrics.price_per_sqm > 0
                                            ? `${(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                            : 'N/A'
                                        }
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] p-4">
                                    <div className="text-[10px] text-[var(--color-text-muted)] mb-1">Total</div>
                                    <div className="text-emerald-500 font-medium">
                                        {(activeContext.property.price / 1000000).toFixed(2)}M
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Tags */}
                        {activeContext.property.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                                {activeContext.property.tags.map((tag, i) => (
                                    <span key={i} className="text-[11px] bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)] px-2.5 py-1 rounded-lg border border-[var(--color-border)]">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        <button className="w-full py-3 bg-[var(--color-text-primary)] text-[var(--color-background)] rounded-xl font-medium text-sm transition-opacity hover:opacity-90">
                            Request Viewing
                        </button>
                    </div>
                </aside>
            )}
        </div>
    );
}
