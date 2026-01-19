'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import {
    Menu, Plus, Mic, ArrowUp, Loader2,
    MessageSquare, Home, BarChart3, Settings, Bell,
    Rocket, Building2, MapPin
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { streamChat } from '@/lib/api';

// --- Sidebar Component ---
const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    return (
        <aside className="hidden md:flex flex-col w-72 h-full border-r border-[#2c3533] bg-[#121615] flex-shrink-0 z-20">
            <div className="p-6 flex flex-col gap-1">
                <h1 className="text-white text-xl font-bold tracking-tight">AMR Advisor</h1>
                <p className="text-[#a2b3af] text-xs">Real Estate Intelligence</p>
            </div>
            <nav className="flex-1 overflow-y-auto px-4 space-y-6 scrollbar-hide">
                <div className="space-y-1">
                    <p className="px-3 text-xs font-semibold text-[#a2b3af] uppercase tracking-wider mb-2">Platform</p>
                    <button className="flex items-center gap-3 px-3 py-2 text-[#a2b3af] hover:text-white hover:bg-[#2c3533] rounded-lg transition-colors group w-full text-left">
                        <Home size={20} className="group-hover:text-[#267360] transition-colors" />
                        <span className="text-sm font-medium">Dashboard</span>
                    </button>
                    <button className="flex items-center gap-3 px-3 py-2 text-white bg-[#2c3533] rounded-lg transition-colors group w-full text-left">
                        <MessageSquare size={20} className="text-[#267360] fill-current" />
                        <span className="text-sm font-medium">Active Chat</span>
                    </button>
                    <button className="flex items-center gap-3 px-3 py-2 text-[#a2b3af] hover:text-white hover:bg-[#2c3533] rounded-lg transition-colors group w-full text-left">
                        <BarChart3 size={20} className="group-hover:text-[#267360] transition-colors" />
                        <span className="text-sm font-medium">Market Analysis</span>
                    </button>
                </div>
            </nav>
            <div className="p-4 border-t border-[#2c3533]">
                <button
                    onClick={onNewChat}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#267360] hover:bg-[#1e5c4d] h-10 px-4 text-white text-sm font-bold transition-all shadow-[0_0_15px_rgba(38,115,96,0.3)]"
                >
                    <Plus size={18} />
                    <span>New Analysis</span>
                </button>
            </div>
        </aside>
    );
};

// --- User Message Component ---
const UserMessage = ({ content }: { content: string }) => (
    <div className="flex flex-col items-end gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="flex items-end gap-3 max-w-[80%] md:max-w-[60%]">
            <div className="flex flex-col gap-1 items-end">
                <div className="bg-[#2c3533] text-white px-5 py-3 rounded-2xl rounded-tr-sm border border-[#3A4542] leading-relaxed text-[15px] shadow-sm" dir="auto">
                    {content}
                </div>
            </div>
            <div className="w-9 h-9 rounded-full bg-slate-700 shrink-0 border border-[#2c3533] flex items-center justify-center text-xs text-white font-bold">
                ME
            </div>
        </div>
    </div>
);

// --- AMR Agent Message Component ---
const AgentMessage = ({ content, visualizations, properties, isTyping }: any) => {
    return (
        <div className="flex flex-col items-start gap-2 w-full animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="flex items-start gap-3 w-full max-w-5xl">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#267360] to-[#0F4C3E] shrink-0 flex items-center justify-center shadow-lg shadow-[#267360]/20">
                    <MessageSquare size={18} className="text-white" />
                </div>
                <div className="flex-1 flex flex-col gap-4">
                    <div className="flex items-baseline justify-between w-full">
                        <span className="text-[#a2b3af] text-xs">AMR Agent • Active now</span>
                    </div>

                    {/* Text Content */}
                    <div
                        className="text-white leading-loose text-[16px] max-w-[680px] whitespace-pre-wrap"
                        dir="auto"
                    >
                        {content}
                        {isTyping && (
                            <span className="inline-block w-1.5 h-4 bg-[#267360] animate-pulse ml-1 align-middle"></span>
                        )}
                    </div>

                    {/* Properties Grid */}
                    {properties && properties.length > 0 && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-2 w-full">
                            {properties.map((prop: any, idx: number) => (
                                <div
                                    key={idx}
                                    className="bg-[#1c2120] border border-[#2c3533] rounded-xl overflow-hidden shadow-xl hover:border-[#267360]/30 transition-all group flex flex-col"
                                >
                                    <div className="relative h-40 bg-slate-800">
                                        <div className="absolute inset-0 flex items-center justify-center text-slate-600">
                                            <Building2 size={48} opacity={0.2} />
                                        </div>
                                        <div className="absolute top-3 right-3 bg-[#267360] text-white text-[10px] font-bold px-2 py-1 rounded uppercase tracking-wider shadow-md">
                                            Verified
                                        </div>
                                    </div>
                                    <div className="p-4 flex flex-col gap-3 flex-1">
                                        <div>
                                            <h4 className="text-white font-bold text-lg leading-tight line-clamp-1">
                                                {prop.title}
                                            </h4>
                                            <p className="text-[#a2b3af] text-xs flex items-center gap-1 mt-1">
                                                <MapPin size={12} />
                                                {prop.location}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-3 text-[#a2b3af] text-xs mt-auto pt-3 border-t border-[#2c3533]">
                                            <span className="font-bold text-white text-base">
                                                {prop.price.toLocaleString()} EGP
                                            </span>
                                            <div className="ml-auto w-8 h-8 rounded-full bg-[#2c3533] hover:bg-white hover:text-black text-white flex items-center justify-center transition-colors cursor-pointer">
                                                <ArrowUp size={16} className="rotate-45" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Visualizations (Charts, etc) */}
                    {visualizations && visualizations.length > 0 && (
                        <div className="space-y-2">
                            {/* Future: Render charts here */}
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
            });
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
        const email = user.email?.toLowerCase();
        if (email === 'mustafa@osool.eg') return 'Mustafa';
        if (email === 'hani@osool.eg') return 'Hani';
        if (email === 'abady@osool.eg') return 'Abady';
        if (email === 'sama@osool.eg') return 'Mrs. Mustafa';
        return user.full_name || user.email?.split('@')[0] || 'Agent';
    };

    return (
        <div className="flex h-[calc(100vh-64px)] w-full relative bg-[#121615] font-display selection:bg-[#267360] selection:text-white overflow-hidden">
            <Sidebar onNewChat={handleNewChat} />

            <main className="flex-1 flex flex-col h-full relative">
                {/* Header */}
                <header className="h-16 border-b border-[#2c3533] flex items-center justify-between px-6 bg-[#121615]/80 backdrop-blur-md z-10 sticky top-0">
                    <div className="flex items-center gap-3">
                        <button className="md:hidden text-[#a2b3af]">
                            <Menu size={24} />
                        </button>
                        <div className="flex items-center gap-2">
                            <Rocket className="text-[#267360]" size={20} />
                            <h2 className="text-lg font-bold tracking-tight text-white">
                                Mission Control: Real Estate Analysis
                            </h2>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[#2c3533] text-[#a2b3af] hover:text-white transition-colors">
                            <Bell size={20} />
                        </button>
                        <button className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-[#2c3533] text-[#a2b3af] hover:text-white transition-colors">
                            <Settings size={20} />
                        </button>
                        <div className="w-8 h-8 rounded-full bg-[#267360]/20 flex items-center justify-center text-[#267360] font-bold text-xs ml-2 border border-[#267360]/30">
                            {getDisplayName()[0]}
                        </div>
                    </div>
                </header>

                {/* Chat Area */}
                <div
                    ref={scrollRef}
                    className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth scrollbar-hide relative"
                    style={{ paddingBottom: messages.length === 0 ? '50vh' : '12rem' }}
                >
                    {messages.length === 0 ? (
                        // Empty State - Centered Welcome
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center space-y-6 w-full max-w-2xl px-4"
                        >
                            <div className="w-20 h-20 rounded-[2rem] bg-gradient-to-br from-[#267360] to-teal-600 flex items-center justify-center shadow-2xl shadow-[#267360]/30 mb-4 mx-auto">
                                <MessageSquare size={40} className="text-white fill-white/20" />
                            </div>
                            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white">
                                Welcome, <span className="text-[#267360]">{getDisplayName()}</span>.
                            </h1>
                            <p className="text-[#a2b3af] text-lg max-w-lg mx-auto">
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
                                        className="flex flex-col items-start gap-2 p-4 rounded-xl bg-[#1c2120] border border-[#2c3533] hover:border-[#267360]/30 transition-all text-left group"
                                    >
                                        <div className="text-[#267360]">{prompt.icon}</div>
                                        <span className="text-sm text-[#a2b3af] group-hover:text-white transition-colors">
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
                            ? { position: 'absolute', top: '60%', bottom: 'auto', left: '50%', x: '-50%', width: '100%', maxWidth: '48rem' }
                            : { position: 'absolute', top: 'auto', bottom: '1.5rem', left: '50%', x: '-50%', width: '100%', maxWidth: '48rem' }
                    }
                    transition={{ type: 'spring', bounce: 0, duration: 0.6 }}
                    className="px-4 md:px-8 z-20"
                >
                    <div className="w-full bg-[#1c2120]/90 backdrop-blur-xl border border-[#2c3533] rounded-2xl shadow-2xl p-2 flex items-end gap-2 transition-all focus-within:border-[#267360]/50 focus-within:ring-1 focus-within:ring-[#267360]/50">
                        <button className="w-10 h-10 flex items-center justify-center rounded-xl text-[#a2b3af] hover:text-white hover:bg-[#2c3533] transition-colors shrink-0">
                            <Plus size={20} />
                        </button>
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="flex-1 bg-transparent border-none text-white placeholder-[#a2b3af]/50 focus:ring-0 text-sm font-medium py-3 px-0 resize-none max-h-[200px] scrollbar-hide"
                            placeholder={
                                language === 'ar'
                                    ? 'اسأل عمرو عن العقارات...'
                                    : 'Ask AMR about real estate...'
                            }
                            rows={1}
                            dir="auto"
                        />
                        <button className="w-10 h-10 flex items-center justify-center rounded-xl text-[#a2b3af] hover:text-white hover:bg-[#2c3533] transition-colors shrink-0">
                            <Mic size={20} />
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="w-10 h-10 flex items-center justify-center rounded-xl bg-[#267360] hover:bg-[#1e5c4d] text-white shadow-lg shadow-[#267360]/20 transition-all shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
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
                        <p className="text-center text-xs text-[#a2b3af]/50 mt-3">
                            AI can make mistakes. Please verify important information.
                        </p>
                    )}
                </motion.div>

                {/* Gradient Fade */}
                <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-[#121615] to-transparent pointer-events-none z-10"></div>
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
