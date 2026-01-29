'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    Send, Mic, Plus, Sparkles, MapPin, TrendingUp,
    Building2, Calculator, X, ChevronRight,
    BarChart2, Shield, Home, Menu, User,
    Copy, Bookmark, LayoutDashboard, PanelRightClose,
    PanelRightOpen, History, Edit, MoreHorizontal, ArrowUp
} from 'lucide-react';
import api from '@/lib/api';

/**
 * TYPES
 */
interface PropertyMetrics {
    size: number;
    bedrooms: number;
    bathrooms: number;
    wolf_score: number;
    roi: number;
    price_per_sqm: number;
}

interface Property {
    id: number;
    title: string;
    location: string;
    price: number;
    metrics: PropertyMetrics;
    image: string;
    developer: string;
    tags: string[];
    agent: { name: string; role: string };
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

/**
 * MOCK DATA
 */
const SAMPLE_PROPERTIES: Property[] = [
    {
        id: 1,
        title: "The Marq - Water Villa",
        location: "New Cairo, Golden Square",
        price: 12500000,
        metrics: {
            size: 280,
            bedrooms: 4,
            bathrooms: 3,
            wolf_score: 92,
            roi: 18.5,
            price_per_sqm: 44600
        },
        image: "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=2670",
        developer: "The Address",
        tags: ["High Growth", "Under Market Price"],
        agent: { name: "Sarah J.", role: "Senior Advisor" }
    }
];

const SUGGESTIONS: Suggestion[] = [
    { icon: MapPin, label: "Area Analysis", prompt: "Compare prices in New Cairo vs Zayed" },
    { icon: TrendingUp, label: "Find Opportunities", prompt: "Find high ROI properties under 5M" },
    { icon: Shield, label: "Developer Audit", prompt: "Audit the reputation of Palm Hills" },
    { icon: Calculator, label: "ROI Calculator", prompt: "Calculate ROI for a 3M EGP apartment" },
];

/**
 * COMPONENT: AMR AVATAR
 */
const AmrAvatar = ({ size = 'md', thinking = false }: { size?: 'sm' | 'md' | 'lg'; thinking?: boolean }) => {
    const sizeClasses = { sm: 'w-6 h-6 text-xs', md: 'w-8 h-8 text-sm', lg: 'w-12 h-12 text-lg' };

    return (
        <div className={`relative flex items-center justify-center rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 text-white font-bold font-mono shadow-md ${sizeClasses[size]}`}>
            {thinking && <div className="absolute inset-0 rounded-full bg-teal-400/30 animate-ping" />}
            <span>A</span>
        </div>
    );
};

/**
 * COMPONENT: TYPEWRITER EFFECT
 */
const Typewriter = ({ text, onComplete }: { text: string; onComplete?: () => void }) => {
    const [displayed, setDisplayed] = useState('');

    useEffect(() => {
        setDisplayed('');
        let i = 0;
        const timer = setInterval(() => {
            if (i < text.length) {
                setDisplayed(prev => prev + text.charAt(i));
                i++;
            } else {
                clearInterval(timer);
                if (onComplete) onComplete();
            }
        }, 10);
        return () => clearInterval(timer);
    }, [text, onComplete]);

    return <span>{displayed}</span>;
};

/**
 * MAIN APP: AGENT INTERFACE
 * Clean, content-focused aesthetics inspired by ChatGPT and Gemini
 */
export default function AgentInterface() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [contextPaneOpen, setContextPaneOpen] = useState(false);
    const [activeContext, setActiveContext] = useState<Artifacts | null>(null);
    const [recentChats] = useState(['New Cairo Analysis', 'Zayed vs October', 'Investment ROI']);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isTyping]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 128)}px`;
        }
    }, [inputValue]);

    const handleSendMessage = useCallback(async (text?: string) => {
        const content = text || inputValue;
        if (!content.trim() || isTyping) return;

        // Add User Message
        const userMsg: Message = { id: Date.now(), role: 'user', content };
        setMessages(prev => [...prev, userMsg]);
        setInputValue('');
        setIsTyping(true);

        try {
            // Call the real API
            const response = await api.post('/api/chat', { message: content });
            const data = response.data;

            // Extract properties from response if available
            let artifacts: Artifacts | null = null;
            if (data.properties && data.properties.length > 0) {
                const prop = data.properties[0];
                artifacts = {
                    property: {
                        id: prop.id,
                        title: prop.title,
                        location: prop.location,
                        price: prop.price,
                        metrics: {
                            size: prop.size_sqm || 0,
                            bedrooms: prop.bedrooms || 0,
                            bathrooms: prop.bathrooms || 0,
                            wolf_score: prop.wolf_score || 0,
                            roi: prop.projected_roi || 0,
                            price_per_sqm: prop.price_per_sqm || 0
                        },
                        image: prop.image_url || "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=2670",
                        developer: prop.developer || "Unknown",
                        tags: prop.tags || [],
                        agent: { name: "AMR", role: "AI Agent" }
                    }
                };
            }

            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'agent',
                content: data.response || data.message || "I'm here to help with your real estate questions.",
                artifacts
            };

            setMessages(prev => [...prev, aiMsg]);

            if (aiMsg.artifacts) {
                setActiveContext(aiMsg.artifacts);
                setContextPaneOpen(true);
            }
        } catch (error) {
            // Fallback simulation for demo
            const isAnalysis = content.toLowerCase().includes('analyze') ||
                content.toLowerCase().includes('marq') ||
                content.toLowerCase().includes('opportunity') ||
                content.toLowerCase().includes('find');

            const aiMsg: Message = {
                id: Date.now() + 1,
                role: 'agent',
                content: isAnalysis
                    ? "I've analyzed the current market listings. Based on your criteria, 'The Marq' in New Cairo stands out. It currently has a Wolf Score of 92/100, indicating a strong buy signal relative to the area average."
                    : "I'm AMR, your real estate intelligence agent. I can help you analyze markets, calculate ROI, or find specific properties. How can I assist you today?",
                artifacts: isAnalysis ? { property: SAMPLE_PROPERTIES[0] } : null
            };

            setMessages(prev => [...prev, aiMsg]);

            if (aiMsg.artifacts) {
                setActiveContext(aiMsg.artifacts);
                setContextPaneOpen(true);
            }
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
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    return (
        <div className="flex h-screen bg-[#131314] text-gray-200 font-sans overflow-hidden">

            {/* ---------------------------------------------------------------------------
       * SIDEBAR (History Panel)
       * --------------------------------------------------------------------------- */}
            <aside className={`${sidebarOpen ? 'w-[260px]' : 'w-0'} bg-[#1e1f20] flex-shrink-0 transition-all duration-300 ease-in-out flex flex-col overflow-hidden border-r border-[#2d2d2d]`}>
                <div className="p-3 flex-shrink-0">
                    <button
                        onClick={handleNewChat}
                        className="w-full flex items-center gap-3 px-3 py-3 rounded-lg bg-[#28292a] hover:bg-[#2d2e2f] text-sm text-gray-200 transition-colors text-left group"
                    >
                        <Plus className="w-4 h-4" />
                        <span className="font-medium">New chat</span>
                        <Edit className="w-4 h-4 ml-auto text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto px-2 py-2">
                    <div className="mb-4">
                        <h3 className="px-3 text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Recent</h3>
                        {recentChats.map((chat, i) => (
                            <button
                                key={i}
                                className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-[#28292a] rounded-lg group transition-colors"
                            >
                                <History className="w-4 h-4 text-gray-500 group-hover:text-gray-400" />
                                <span className="truncate flex-1 text-left">{chat}</span>
                                <MoreHorizontal className="w-4 h-4 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </button>
                        ))}
                    </div>
                </div>

                <div className="p-3 border-t border-[#2d2d2d]">
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-[#28292a] rounded-lg transition-colors">
                        <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                            M
                        </div>
                        <div className="flex-1 text-left">
                            <div className="font-medium text-gray-200">Mustafa</div>
                            <div className="text-xs text-gray-500">Pro Plan</div>
                        </div>
                        <div className="text-[10px] bg-teal-500/10 text-teal-400 px-1.5 py-0.5 rounded font-medium">NEW</div>
                    </button>
                </div>
            </aside>

            {/* ---------------------------------------------------------------------------
       * MAIN CHAT AREA
       * --------------------------------------------------------------------------- */}
            <main className="flex-1 flex flex-col relative min-w-0">

                {/* Header / Top Bar */}
                <div className="absolute top-0 left-0 right-0 h-14 flex items-center justify-between px-4 z-10 bg-[#131314]/80 backdrop-blur-sm">
                    <div className="flex items-center gap-2">
                        {!sidebarOpen && (
                            <button
                                onClick={() => setSidebarOpen(true)}
                                className="p-2 text-gray-400 hover:bg-[#28292a] rounded-lg transition-colors"
                            >
                                <Menu className="w-5 h-5" />
                            </button>
                        )}
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="p-2 text-gray-400 hover:bg-[#28292a] rounded-lg transition-colors"
                        >
                            {sidebarOpen ? <PanelRightClose className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                        <span className="text-lg font-medium text-gray-300 flex items-center gap-2">
                            Osool <span className="text-gray-500 text-sm">v1.0</span>
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        {activeContext && !contextPaneOpen && (
                            <button
                                onClick={() => setContextPaneOpen(true)}
                                className="p-2 text-gray-400 hover:bg-[#28292a] rounded-lg transition-colors"
                                title="Open Canvas"
                            >
                                <PanelRightOpen className="w-5 h-5" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Messages Stream */}
                <div className="flex-1 overflow-y-auto scroll-smooth">
                    <div className="max-w-3xl mx-auto px-4 pt-20 pb-44">

                        {/* Empty State / Welcome */}
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
                                <div className="w-16 h-16 bg-gradient-to-br from-[#1e1f20] to-[#28292a] rounded-2xl flex items-center justify-center mb-6 shadow-xl ring-1 ring-white/5">
                                    <TrendingUp className="w-8 h-8 text-teal-500" />
                                </div>
                                <h1 className="text-2xl md:text-3xl font-medium text-white mb-2">Welcome to Osool Intelligence</h1>
                                <p className="text-gray-500 mb-10 max-w-md text-sm md:text-base">
                                    Your autonomous real estate agent. Analyze markets, calculate risks, and find opportunities.
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                                    {SUGGESTIONS.map((s, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleSendMessage(s.prompt)}
                                            className="p-4 bg-[#1e1f20] hover:bg-[#28292a] border border-[#2d2d2d] hover:border-teal-500/30 rounded-xl text-left transition-all group"
                                        >
                                            <div className="flex items-center gap-3 mb-1">
                                                <s.icon className="w-4 h-4 text-teal-500" />
                                                <span className="font-medium text-gray-200 text-sm">{s.label}</span>
                                            </div>
                                            <span className="text-xs text-gray-500 group-hover:text-gray-400 transition-colors">{s.prompt}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Conversation Messages */}
                        {messages.map((msg) => (
                            <div key={msg.id} className="mb-8 group">
                                <div className="flex gap-4">
                                    {/* Avatar */}
                                    <div className="flex-shrink-0 mt-1">
                                        {msg.role === 'user' ? (
                                            <div className="w-8 h-8 bg-[#2d2d2d] rounded-full flex items-center justify-center text-gray-300">
                                                <User className="w-5 h-5" />
                                            </div>
                                        ) : (
                                            <AmrAvatar size="md" />
                                        )}
                                    </div>

                                    {/* Message Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium text-sm text-gray-400 mb-1.5">
                                            {msg.role === 'user' ? 'You' : 'Osool Agent'}
                                        </div>
                                        <div className="prose prose-invert prose-sm max-w-none text-gray-200 leading-7">
                                            {msg.role === 'agent' ? <Typewriter text={msg.content} /> : msg.content}
                                        </div>

                                        {/* Artifacts / Property Cards */}
                                        {msg.artifacts?.property && (
                                            <div className="mt-4">
                                                <div
                                                    onClick={() => { setActiveContext(msg.artifacts!); setContextPaneOpen(true); }}
                                                    className="inline-flex flex-col bg-[#1e1f20] border border-[#2d2d2d] hover:border-teal-500/50 rounded-xl overflow-hidden cursor-pointer transition-all hover:shadow-lg hover:shadow-teal-900/10 max-w-sm w-full group/card"
                                                >
                                                    <div className="h-32 bg-gray-800 relative overflow-hidden">
                                                        <img
                                                            src={msg.artifacts.property.image}
                                                            className="w-full h-full object-cover opacity-80 group-hover/card:opacity-100 group-hover/card:scale-105 transition-all duration-300"
                                                            alt="Property"
                                                        />
                                                        <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-0.5 rounded-full text-xs font-medium text-white flex items-center gap-1">
                                                            <Sparkles className="w-3 h-3 text-teal-400" />
                                                            {msg.artifacts.property.metrics.wolf_score} Match
                                                        </div>
                                                    </div>
                                                    <div className="p-3">
                                                        <div className="font-medium text-white mb-1">{msg.artifacts.property.title}</div>
                                                        <div className="text-xs text-gray-500 mb-3 flex items-center gap-1">
                                                            <MapPin className="w-3 h-3" />
                                                            {msg.artifacts.property.location}
                                                        </div>
                                                        <div className="flex items-center justify-between text-xs">
                                                            <span className="text-teal-400 font-mono font-medium">
                                                                {(msg.artifacts.property.price / 1000000).toFixed(2)}M EGP
                                                            </span>
                                                            <span className="text-green-400 font-mono">
                                                                +{msg.artifacts.property.metrics.roi}% ROI
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="px-3 py-2 bg-[#252627] border-t border-[#2d2d2d] text-xs text-gray-500 flex items-center justify-between group-hover/card:text-gray-300 transition-colors">
                                                        <span>Click to view analysis</span>
                                                        <ChevronRight className="w-3 h-3" />
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Action Buttons (Hover) */}
                                        {msg.role === 'agent' && !isTyping && (
                                            <div className="flex gap-1 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => copyToClipboard(msg.content)}
                                                    className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-[#28292a] rounded transition-colors"
                                                    title="Copy"
                                                >
                                                    <Copy className="w-4 h-4" />
                                                </button>
                                                <button
                                                    className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-[#28292a] rounded transition-colors"
                                                    title="Bookmark"
                                                >
                                                    <Bookmark className="w-4 h-4" />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* Typing Indicator */}
                        {isTyping && (
                            <div className="flex gap-4 mb-8">
                                <AmrAvatar size="md" thinking={true} />
                                <div className="flex items-center gap-1.5 mt-3">
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Floating Input Area (Omnibar) */}
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[#131314] via-[#131314]/95 to-transparent z-20 pointer-events-none">
                    <div className="max-w-3xl mx-auto pointer-events-auto">
                        <div className="bg-[#1e1f20] rounded-[26px] p-1.5 pr-2 pl-4 flex items-end gap-2 border border-[#2d2d2d] focus-within:border-gray-600 focus-within:bg-[#232425] transition-all shadow-2xl shadow-black/50">
                            <button className="p-2 mb-0.5 text-gray-400 hover:text-white bg-[#2d2d2d] hover:bg-[#3d3d3d] rounded-full transition-colors">
                                <Plus className="w-4 h-4" />
                            </button>

                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Message Osool..."
                                className="flex-1 bg-transparent border-none text-gray-200 placeholder-gray-500 focus:ring-0 focus:outline-none resize-none max-h-32 py-3 text-base leading-6"
                                rows={1}
                            />

                            <div className="flex items-center gap-1 mb-1">
                                {!inputValue.trim() && (
                                    <button className="p-2 text-gray-400 hover:text-white transition-colors">
                                        <Mic className="w-5 h-5" />
                                    </button>
                                )}
                                <button
                                    onClick={() => handleSendMessage()}
                                    disabled={!inputValue.trim() || isTyping}
                                    className={`p-2.5 rounded-full transition-all ${inputValue.trim() && !isTyping
                                            ? 'bg-white text-black hover:bg-gray-200 shadow-lg'
                                            : 'bg-[#2d2d2d] text-gray-500 cursor-not-allowed'
                                        }`}
                                >
                                    <ArrowUp className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                        <div className="text-center mt-2">
                            <p className="text-[10px] text-gray-600">Osool can make mistakes. Consider checking important information.</p>
                        </div>
                    </div>
                </div>
            </main>

            {/* ---------------------------------------------------------------------------
       * RIGHT PANE (Context Canvas)
       * --------------------------------------------------------------------------- */}
            {contextPaneOpen && activeContext?.property && (
                <aside className="w-[400px] bg-[#1e1f20] border-l border-[#2d2d2d] flex flex-col shadow-2xl z-30">
                    {/* Canvas Header */}
                    <div className="h-14 border-b border-[#2d2d2d] flex items-center justify-between px-4 bg-[#1e1f20] flex-shrink-0">
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-200">
                            <LayoutDashboard className="w-4 h-4 text-teal-500" />
                            <span>Canvas</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <button className="p-2 text-gray-400 hover:text-white hover:bg-[#2d2d2d] rounded transition-colors">
                                <MoreHorizontal className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setContextPaneOpen(false)}
                                className="p-2 text-gray-400 hover:text-white hover:bg-[#2d2d2d] rounded transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* Canvas Content */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-6">

                        {/* Property Hero */}
                        <div className="space-y-3">
                            <div className="aspect-video bg-gray-800 rounded-xl overflow-hidden relative group">
                                <img
                                    src={activeContext.property.image}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                    alt="Property Detail"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                                <div className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-sm px-2.5 py-1 rounded-full text-white text-xs font-medium flex items-center gap-1">
                                    <MapPin className="w-3 h-3" />
                                    {activeContext.property.location}
                                </div>
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-white leading-tight">{activeContext.property.title}</h2>
                                <p className="text-teal-400 font-mono mt-1 text-lg font-medium">
                                    {(activeContext.property.price / 1000000).toFixed(2)}M EGP
                                </p>
                            </div>
                        </div>

                        {/* Key Metrics Grid */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-[#28292a] p-4 rounded-xl border border-[#2d2d2d]">
                                <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                                    <Sparkles className="w-3 h-3" />
                                    Wolf Score
                                </div>
                                <div className="text-2xl font-semibold text-white flex items-center gap-2">
                                    {activeContext.property.metrics.wolf_score}
                                    <span className="text-[10px] font-medium text-teal-400 bg-teal-500/10 px-1.5 py-0.5 rounded-full">High</span>
                                </div>
                            </div>
                            <div className="bg-[#28292a] p-4 rounded-xl border border-[#2d2d2d]">
                                <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                                    <TrendingUp className="w-3 h-3" />
                                    Proj. ROI
                                </div>
                                <div className="text-2xl font-semibold text-green-400">
                                    +{activeContext.property.metrics.roi}%
                                </div>
                            </div>
                        </div>

                        {/* Property Details */}
                        <div className="space-y-4 pt-4 border-t border-[#2d2d2d]">
                            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                                <Home className="w-4 h-4 text-gray-500" />
                                Property Details
                            </h3>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between items-center py-1">
                                    <span className="text-gray-500">Size</span>
                                    <span className="text-gray-200 font-medium">{activeContext.property.metrics.size} sqm</span>
                                </div>
                                <div className="flex justify-between items-center py-1">
                                    <span className="text-gray-500">Bedrooms</span>
                                    <span className="text-gray-200 font-medium">{activeContext.property.metrics.bedrooms}</span>
                                </div>
                                <div className="flex justify-between items-center py-1">
                                    <span className="text-gray-500">Bathrooms</span>
                                    <span className="text-gray-200 font-medium">{activeContext.property.metrics.bathrooms}</span>
                                </div>
                                <div className="flex justify-between items-center py-1">
                                    <span className="text-gray-500">Price/sqm</span>
                                    <span className="text-gray-200 font-medium">{(activeContext.property.metrics.price_per_sqm / 1000).toFixed(1)}k EGP</span>
                                </div>
                                <div className="flex justify-between items-center py-1">
                                    <span className="text-gray-500">Developer</span>
                                    <span className="text-gray-200 font-medium">{activeContext.property.developer}</span>
                                </div>
                            </div>
                        </div>

                        {/* Tags */}
                        {activeContext.property.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                                {activeContext.property.tags.map((tag, i) => (
                                    <span
                                        key={i}
                                        className="text-xs bg-teal-500/10 text-teal-400 px-2.5 py-1 rounded-full border border-teal-500/20"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        {/* CTA Button */}
                        <button className="w-full py-3 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white rounded-xl font-medium transition-all text-sm shadow-lg shadow-teal-900/20">
                            Schedule Viewing
                        </button>

                    </div>
                </aside>
            )}

        </div>
    );
}
