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
        <div className={`relative flex items-center justify-center w-8 h-8 rounded-full overflow-hidden flex-shrink-0 ${thinking ? 'animate-pulse' : ''}`}>
            <div className="absolute inset-0 bg-gradient-to-tr from-teal-600 to-emerald-600" />
            <span className="relative text-[10px] font-bold text-white font-mono">AMR</span>
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
                        <strong className="font-bold text-teal-400" {...props} />
                    ),
                    em: ({ node, ...props }) => (
                        <em className="italic text-gray-300" {...props} />
                    ),
                    h1: ({ node, ...props }) => (
                        <h1 className="text-xl font-bold mb-3 mt-4 text-white" {...props} />
                    ),
                    h2: ({ node, ...props }) => (
                        <h2 className="text-lg font-bold mb-2 mt-3 text-white" {...props} />
                    ),
                    h3: ({ node, ...props }) => (
                        <h3 className="text-base font-semibold mb-2 mt-2 text-white" {...props} />
                    ),
                    blockquote: ({ node, ...props }) => (
                        <blockquote
                            className={`${msgIsArabic ? 'border-r-4 pr-4' : 'border-l-4 pl-4'} border-teal-500 py-1 my-2 bg-[#252627] rounded`}
                            {...props}
                        />
                    ),
                    a: ({ node, ...props }) => (
                        <a className="text-teal-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />
                    ),
                    code: ({ node, className, children, ...props }) => {
                        const isInline = !className;
                        return isInline ? (
                            <code className="bg-[#252627] text-teal-300 px-1.5 py-0.5 rounded text-sm" {...props}>{children}</code>
                        ) : (
                            <pre className="bg-[#1a1a1b] border border-[#3d3d3d] rounded-lg p-4 my-3 overflow-x-auto">
                                <code className="text-sm text-gray-300" {...props}>{children}</code>
                            </pre>
                        );
                    },
                    hr: ({ node, ...props }) => (
                        <hr className="border-[#3d3d3d] my-4" {...props} />
                    ),
                    table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-3">
                            <table className="w-full border-collapse border border-[#3d3d3d] text-sm" {...props} />
                        </div>
                    ),
                    th: ({ node, ...props }) => (
                        <th className="border border-[#3d3d3d] bg-[#252627] px-3 py-2 text-teal-400 font-semibold" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                        <td className="border border-[#3d3d3d] px-3 py-2" {...props} />
                    ),
                }}
            >
                {content}
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
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
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

        setSidebarOpen(false);

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

            // Extract property artifacts from response
            let artifacts: Artifacts | null = null;
            if (data.properties && data.properties.length > 0) {
                const prop = data.properties[0];
                artifacts = {
                    property: {
                        id: prop.id?.toString() || `prop_${Date.now()}`,
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
                    }
                };
            }

            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'agent',
                content: data.response || data.message || "I'm AMR, your real estate intelligence agent. How can I assist you today?",
                artifacts
            };

            setMessages(prev => [...prev, aiMsg]);

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
        setSidebarOpen(false);
        // New conversation = new session ID
        sessionIdRef.current = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const hasStarted = messages.length > 0;

    return (
        <div className="flex h-screen bg-[#131314] text-[#e3e3e3] font-sans overflow-hidden selection:bg-teal-500/30 relative">

            {/* ---------------------------------------------------------------------------
       * FLOATING HISTORY PANE (SIDEBAR)
       * --------------------------------------------------------------------------- */}
            <aside
                className={`fixed top-4 bottom-4 left-4 w-[300px] bg-[#1e1f20]/95 backdrop-blur-md rounded-3xl z-50 flex flex-col overflow-hidden border border-[#2d2d2d] shadow-2xl transition-transform duration-500 ${sidebarOpen ? 'translate-x-0' : '-translate-x-[calc(100%+24px)]'}`}
                style={{ transitionTimingFunction: 'cubic-bezier(0.2, 0.8, 0.2, 1)' }}
            >
                <div className="p-4 pt-5 flex-1 overflow-y-auto">
                    <div className="flex justify-between items-center mb-6 px-1">
                        <button
                            onClick={() => setSidebarOpen(false)}
                            className="p-2 hover:bg-[#2c2d2e] rounded-full text-gray-400 transition-colors"
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Sessions</span>
                    </div>

                    <button
                        onClick={handleNewChat}
                        className="flex items-center gap-3 px-4 py-3 rounded-full bg-[#2c2d2e] hover:bg-[#353638] text-[#e3e3e3] transition-colors w-full mb-6 border border-[#3d3d3d] group"
                    >
                        <Plus className="w-5 h-5 text-gray-400 group-hover:text-white" />
                        <span className="text-sm font-medium">New Analysis</span>
                    </button>

                    {recentQueries.length > 0 && (
                        <>
                            <div className="text-xs font-medium text-gray-500 mb-3 px-2">Recent Queries</div>
                            <div className="space-y-1">
                                {recentQueries.map((query, i) => (
                                    <button
                                        key={i}
                                        onClick={() => handleSendMessage(query)}
                                        className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-[#e3e3e3] hover:bg-[#2c2d2e] rounded-lg group transition-colors truncate"
                                    >
                                        <History className="w-4 h-4 text-gray-500 flex-shrink-0" />
                                        <span className="truncate flex-1 text-left opacity-80 group-hover:opacity-100" dir="auto">{query}</span>
                                        <MoreHorizontal className="w-4 h-4 text-gray-500 opacity-0 group-hover:opacity-100 flex-shrink-0" />
                                    </button>
                                ))}
                            </div>
                        </>
                    )}
                </div>

                <div className="p-4 bg-[#1e1f20] border-t border-[#2d2d2d]">
                    <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl">
                        <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center text-white font-bold shadow-lg">
                            <Building2 className="w-4 h-4" />
                        </div>
                        <div className="flex-1 text-left">
                            <div className="text-sm font-medium text-white">{userName}</div>
                            <div className="text-[10px] text-teal-400">Elite Investor</div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* ---------------------------------------------------------------------------
       * MAIN CHAT AREA
       * --------------------------------------------------------------------------- */}
            <main className="flex-1 flex flex-col relative min-w-0 bg-[#131314] h-full w-full z-0">

                {/* Top Bar */}
                <div className="absolute top-0 left-0 right-0 h-20 flex items-center justify-between px-6 z-30 pointer-events-none">

                    {/* Menu Trigger */}
                    <div className="flex items-center gap-4 pointer-events-auto">
                        <button
                            onClick={() => setSidebarOpen(true)}
                            className={`p-2.5 hover:bg-[#2c2d2e] rounded-full text-gray-400 transition-all duration-300 ${sidebarOpen ? 'opacity-0 -translate-x-4 pointer-events-none' : 'opacity-100 translate-x-0'}`}
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                        <span className={`text-xl font-medium text-[#e3e3e3] opacity-90 tracking-tight transition-opacity duration-500 ${!hasStarted ? 'opacity-0' : 'opacity-100'}`}>
                            Osool <span className="opacity-50 font-light">AMR</span>
                        </span>
                    </div>

                    <div className="flex items-center gap-3 pointer-events-auto">
                        <button
                            onClick={handleNewChat}
                            className="p-2.5 hover:bg-[#2c2d2e] rounded-full text-gray-400 transition-colors"
                            title="New Chat"
                        >
                            <RefreshCw className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-[800px] mx-auto h-full">

                        {/* GREETING SCREEN */}
                        {!hasStarted && (
                            <div className="flex flex-col h-full relative">

                                {/* Top Half - Title */}
                                <div className="flex-1 flex flex-col justify-end pb-10 px-4">
                                    <div className="text-center w-full max-w-2xl mx-auto">
                                        <h1 className="text-5xl md:text-6xl font-medium tracking-tight mb-4">
                                            <span className="bg-gradient-to-r from-emerald-400 via-teal-500 to-cyan-500 text-transparent bg-clip-text">
                                                Hello, {userName}
                                            </span>
                                        </h1>
                                        <h2 className="text-3xl md:text-4xl text-[#444746] font-normal">Ready to analyze your assets?</h2>
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
                                                className="p-4 bg-[#1e1f20] hover:bg-[#2c2d2e] rounded-2xl text-left transition-all duration-300 h-36 flex flex-col justify-between group border border-transparent hover:border-[#3d3d3d]"
                                            >
                                                <span className="text-sm font-medium text-[#e3e3e3] group-hover:text-white leading-snug" dir="auto">{s.label}</span>
                                                <div className="self-end p-2 bg-[#131314] rounded-full group-hover:bg-[#e3e3e3] group-hover:text-black transition-colors shadow-sm">
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
                            <div className="px-4 pt-28 pb-48">
                                {messages.map((msg) => (
                                    <div key={msg.id} className="mb-8">
                                        <div className="flex gap-5">
                                            <div className="flex-shrink-0 mt-1">
                                                {msg.role === 'user' ? null : <AgentAvatar />}
                                            </div>

                                            <div className={`flex-1 min-w-0 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                                                {msg.role === 'user' ? (
                                                    <div
                                                        className="bg-[#2c2d2e] text-[#e3e3e3] px-6 py-3.5 rounded-[24px] rounded-br-sm max-w-[85%] text-[16px] leading-relaxed tracking-wide"
                                                        dir="auto"
                                                    >
                                                        {msg.content}
                                                    </div>
                                                ) : (
                                                    <div
                                                        className="text-[16px] leading-8 text-[#e3e3e3] font-light tracking-wide"
                                                        dir="auto"
                                                    >
                                                        <MarkdownMessage content={msg.content} />

                                                        {/* Rich Artifacts - Linked to Context Pane */}
                                                        {msg.artifacts?.property && (
                                                            <div className="mt-8" dir="ltr">
                                                                <div
                                                                    onClick={() => { setActiveContext(msg.artifacts!); setContextPaneOpen(true); }}
                                                                    className="group relative border border-[#444746] hover:border-teal-500/50 bg-[#1e1f20] rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 max-w-md shadow-xl hover:shadow-2xl hover:shadow-teal-900/10"
                                                                >
                                                                    <div className="absolute top-0 left-0 w-1.5 h-full bg-teal-500 opacity-0 group-hover:opacity-100 transition-opacity" />

                                                                    <div className="p-5 flex gap-5">
                                                                        <div className="w-28 h-28 bg-gray-800 rounded-xl flex-shrink-0 overflow-hidden shadow-inner">
                                                                            <img src={msg.artifacts.property.image} className="w-full h-full object-cover transform group-hover:scale-110 transition-transform duration-700" alt="Thumb" />
                                                                        </div>
                                                                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                                                                            <div className="flex items-center gap-2 mb-1.5">
                                                                                <Sparkles className="w-3.5 h-3.5 text-teal-400" />
                                                                                <span className="text-[10px] font-bold text-teal-400 uppercase tracking-widest">AMR Insight</span>
                                                                            </div>
                                                                            <h3 className="font-medium text-lg text-[#e3e3e3] truncate mb-1" dir="auto">{msg.artifacts.property.title}</h3>
                                                                            <p className="text-sm text-gray-400 mb-3 truncate" dir="auto">{msg.artifacts.property.location}</p>

                                                                            <div className="flex items-center gap-3">
                                                                                <span className="text-sm font-medium text-white bg-[#2c2d2e] px-2.5 py-1 rounded-md border border-[#3d3d3d]">
                                                                                    {(msg.artifacts.property.price / 1000000).toFixed(1)}M EGP
                                                                                </span>
                                                                                {msg.artifacts.property.metrics.roi > 0 && (
                                                                                    <span className="text-sm font-medium text-emerald-400 bg-emerald-950/30 px-2.5 py-1 rounded-md border border-emerald-900/50">
                                                                                        +{msg.artifacts.property.metrics.roi}% ROI
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        <div className="flex flex-col justify-center items-center text-gray-600 group-hover:text-teal-400 pl-2 border-l border-[#2d2d2d]">
                                                                            <ExternalLink className="w-5 h-5" />
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        )}

                                                        {!isTyping && (
                                                            <div className="flex gap-2 mt-6" dir="ltr">
                                                                <button
                                                                    onClick={() => copyToClipboard(msg.content)}
                                                                    className="p-2 hover:bg-[#2c2d2e] rounded-full text-gray-400 hover:text-[#e3e3e3] transition-colors"
                                                                    title="Copy to clipboard"
                                                                >
                                                                    <Copy className="w-4 h-4" />
                                                                </button>
                                                                <button
                                                                    className="p-2 hover:bg-[#2c2d2e] rounded-full text-gray-400 hover:text-[#e3e3e3] transition-colors"
                                                                    title="Refresh analysis"
                                                                >
                                                                    <RefreshCw className="w-4 h-4" />
                                                                </button>
                                                            </div>
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
                        <div className={`bg-[#1e1f20] rounded-[32px] flex flex-col transition-all duration-200 ${isTyping ? 'opacity-50' : ''} border border-[#3d3d3d] focus-within:border-[#4d4d4d] focus-within:bg-[#1e1f20] shadow-2xl`}>

                            <textarea
                                dir="auto"
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask AMR about liquidity, market data, or properties..."
                                className="w-full bg-transparent border-none text-[#e3e3e3] placeholder-gray-500 focus:ring-0 resize-none py-5 px-6 text-[17px] max-h-[200px] outline-none focus:outline-none ring-0 focus:ring-0"
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
                                        className="p-2.5 bg-white text-black rounded-full hover:bg-gray-200 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className={`text-center mt-3 transition-opacity duration-500 ${!hasStarted ? 'opacity-0' : 'opacity-100'}`}>
                            <p className="text-[12px] text-gray-500">AMR can make mistakes. Verify critical financial data independently.</p>
                        </div>
                    </div>
                </div>

            </main>

            {/* ---------------------------------------------------------------------------
       * RIGHT PANE (WORKSPACE / CANVAS)
       * --------------------------------------------------------------------------- */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-[420px] bg-[#1e1f20] border-l border-[#2d2d2d] flex flex-col shadow-2xl z-40 relative">
                    <div className="h-16 border-b border-[#2d2d2d] flex items-center justify-between px-6 bg-[#1e1f20] flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <span className="text-[#e3e3e3] font-medium text-lg">AMR Workspace</span>
                            <span className="text-[10px] text-teal-400 bg-teal-900/30 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">Live</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setContextPaneOpen(false)}
                                className="p-2 text-gray-400 hover:text-white hover:bg-[#2d2d2e] rounded-full transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-6 space-y-8">

                        {/* Main Visual */}
                        <div className="space-y-4">
                            <div className="aspect-video bg-gray-800 rounded-2xl overflow-hidden relative shadow-2xl ring-1 ring-white/10">
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
                                <h2 className="text-3xl font-medium text-[#e3e3e3] leading-tight mb-2" dir="auto">
                                    {activeContext.property.title}
                                </h2>
                                <p className="text-gray-400 flex items-center gap-1.5 text-sm" dir="auto">
                                    <MapPin className="w-4 h-4 text-teal-500" />
                                    {activeContext.property.location}
                                </p>
                            </div>
                        </div>

                        {/* AI Insight Block */}
                        <div className="bg-[#252627] rounded-2xl p-6 border border-[#3d3d3d] relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                                <Sparkles className="w-24 h-24 text-teal-500" />
                            </div>
                            <div className="flex items-center gap-2 mb-4 relative z-10">
                                <Sparkles className="w-5 h-5 text-teal-400" />
                                <h3 className="font-medium text-[#e3e3e3]">Osool Score Analysis</h3>
                            </div>
                            <div className="space-y-5 relative z-10">
                                <p className="text-[15px] text-[#c4c7c5] leading-relaxed" dir="auto">
                                    Analysis via AMR indicates this asset shows strong investment potential based on market comparables and liquidity metrics.
                                </p>
                                <div className="flex gap-6 pt-2">
                                    <div>
                                        <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold mb-1">Osool Score</div>
                                        <div className="text-3xl font-medium text-teal-400">
                                            {activeContext.property.metrics.wolf_score}
                                            <span className="text-sm text-teal-600/70">/100</span>
                                        </div>
                                    </div>
                                    <div className="w-px bg-[#3d3d3d]" />
                                    <div>
                                        <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold mb-1">Liquidity</div>
                                        <div className="text-3xl font-medium text-emerald-400">
                                            {activeContext.property.metrics.liquidity_rating}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Data Grid */}
                        <div>
                            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-widest pl-1">Specifications</h3>
                            <div className="grid grid-cols-2 gap-px bg-[#3d3d3d] rounded-2xl overflow-hidden border border-[#3d3d3d]">
                                <div className="bg-[#1e1f20] p-5 hover:bg-[#252627] transition-colors">
                                    <div className="text-xs text-gray-500 mb-1.5">Total Area</div>
                                    <div className="text-[#e3e3e3] font-medium text-lg">
                                        {activeContext.property.metrics.size} <span className="text-sm text-gray-600">sqm</span>
                                    </div>
                                </div>
                                <div className="bg-[#1e1f20] p-5 hover:bg-[#252627] transition-colors">
                                    <div className="text-xs text-gray-500 mb-1.5">Bedrooms</div>
                                    <div className="text-[#e3e3e3] font-medium text-lg">
                                        {activeContext.property.metrics.bedrooms} <span className="text-sm text-gray-600">Beds</span>
                                    </div>
                                </div>
                                <div className="bg-[#1e1f20] p-5 hover:bg-[#252627] transition-colors">
                                    <div className="text-xs text-gray-500 mb-1.5">Price / Meter</div>
                                    <div className="text-[#e3e3e3] font-medium text-lg">
                                        {activeContext.property.metrics.price_per_sqm > 0
                                            ? `${(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k`
                                            : 'N/A'
                                        } <span className="text-sm text-gray-600">EGP</span>
                                    </div>
                                </div>
                                <div className="bg-[#1e1f20] p-5 hover:bg-[#252627] transition-colors">
                                    <div className="text-xs text-gray-500 mb-1.5">Total Price</div>
                                    <div className="text-teal-400 font-medium text-lg">
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
                                        className="text-xs bg-teal-900/30 text-teal-400 px-3 py-1.5 rounded-full border border-teal-800/50"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        <button className="w-full py-4 bg-[#e3e3e3] hover:bg-white text-black rounded-full font-bold text-sm tracking-wide transition-all shadow-lg hover:shadow-xl hover:shadow-white/10 transform hover:-translate-y-0.5">
                            Request Viewing
                        </button>

                    </div>
                </aside>
            )}

        </div>
    );
}
