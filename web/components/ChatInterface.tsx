'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, ShieldCheck, TrendingUp, Sparkles, Menu, Plus } from 'lucide-react';
import { AreaChart, Area, Tooltip, ResponsiveContainer } from 'recharts';
import ConversationHistory from './ConversationHistory';

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    type: 'text' | 'chart' | 'location';
};

// Demo data for the chart
const data = [
    { year: '2021', value: 100, currency: 100 },
    { year: '2022', value: 115, currency: 85 },
    { year: '2023', value: 145, currency: 60 },
    { year: '2024', value: 185, currency: 40 },
    { year: '2025', value: 240, currency: 30 },
];

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'amr',
            content: 'Ahlan! I am Amr, your AI real estate wealth partner. I can help you find verified properties, analyze market trends, and calculate ROI based on real inflation data. How can I protect your wealth today?',
            type: 'text',
        },
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    const handleUserMessage = async (text: string) => {
        const newMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: text,
            type: 'text',
        };
        setMessages((prev) => [...prev, newMessage]);
        setInput('');
        setIsTyping(true);

        // Simulate Amr thinking and responding
        // In a real app, this would call the /api/chat endpoint
        setTimeout(() => {
            const response: Message = {
                id: (Date.now() + 1).toString(),
                role: 'amr',
                content: "I'm analyzing the market data for you. Based on current inflation rates, New Capital properties have shown a 24% increase in value against the EGP over the last 12 months.",
                type: 'chart',
            };
            setMessages((prev) => [...prev, response]);
            setIsTyping(false);
        }, 1500);
    };

    const handleSend = () => {
        if (!input.trim()) return;
        handleUserMessage(input);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex h-[calc(100vh-64px)] bg-slate-50 dark:bg-slate-950 overflow-hidden relative">

            {/* Sidebar (Conversation History) */}
            <ConversationHistory
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
                onSelectConversation={(id) => console.log("Selected conversation:", id)}
                onNewConversation={() => setMessages([])}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full w-full max-w-5xl mx-auto border-x border-slate-200 dark:border-slate-800/50 bg-white dark:bg-slate-900 shadow-2xl">

                {/* Header */}
                <div className="bg-white dark:bg-slate-900 p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsSidebarOpen(true)}
                            className="md:hidden p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        >
                            <Menu size={20} />
                        </button>
                        <div className="relative">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold shadow-lg shadow-green-500/20">
                                A
                            </div>
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white dark:border-slate-900 rounded-full animate-pulse"></div>
                        </div>
                        <div>
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                Amr <ShieldCheck size={16} className="text-green-500" />
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-slate-400">AI Wealth Consultant</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setMessages([])}
                        className="hidden md:flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    >
                        <Plus size={16} />
                        New Chat
                    </button>
                </div>

                {/* Messages List */}
                <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" ref={scrollRef}>
                    <AnimatePresence>
                        {messages.length === 0 && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex flex-col items-center justify-center h-full text-center text-slate-400 p-8"
                            >
                                <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                                    <Sparkles className="w-8 h-8 text-amber-500" />
                                </div>
                                <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-300 mb-2">Start a new conversation</h3>
                                <p className="max-w-xs mx-auto text-sm">Ask Amr about property investments, market trends, or legal advice.</p>
                            </motion.div>
                        )}

                        {messages.map((msg) => (
                            <motion.div
                                key={msg.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                {msg.role === 'amr' && (
                                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex-shrink-0 flex items-center justify-center text-white text-xs font-bold mt-1 shadow-md">
                                        A
                                    </div>
                                )}

                                <div className={`flex flex-col max-w-[85%] md:max-w-[70%] space-y-2`}>
                                    <div
                                        className={`rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                                                ? 'bg-blue-600 text-white rounded-br-none'
                                                : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-none border border-slate-100 dark:border-slate-700'
                                            }`}
                                    >
                                        <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                                    </div>

                                    {msg.type === 'chart' && (
                                        <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm h-64 w-full md:w-[400px]">
                                            <div className="flex items-center gap-2 mb-4 text-xs font-semibold text-slate-500 dark:text-slate-400">
                                                <TrendingUp size={14} /> Property vs Currency Performance
                                            </div>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <AreaChart data={data}>
                                                    <defs>
                                                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                                                        </linearGradient>
                                                        <linearGradient id="colorCurrency" x1="0" y1="0" x2="0" y2="1">
                                                            <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                                            <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                                        </linearGradient>
                                                    </defs>
                                                    <Tooltip
                                                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', fontSize: '12px', color: '#fff' }}
                                                    />
                                                    <Area type="monotone" dataKey="value" stroke="#22c55e" fillOpacity={1} fill="url(#colorValue)" name="Property Value" strokeWidth={2} />
                                                    <Area type="monotone" dataKey="currency" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorCurrency)" name="EGP Value" strokeWidth={2} />
                                                </AreaChart>
                                            </ResponsiveContainer>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {isTyping && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex items-center gap-4"
                        >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex-shrink-0 flex items-center justify-center text-white text-xs font-bold shadow-md">
                                A
                            </div>
                            <div className="flex items-center gap-1 bg-white dark:bg-slate-800 px-4 py-3 rounded-2xl rounded-bl-none border border-slate-100 dark:border-slate-700">
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                            </div>
                        </motion.div>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800">
                    <div className="max-w-4xl mx-auto relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask Amr about real estate investments..."
                            className="w-full bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-full py-4 pl-6 pr-14 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-shadow"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:hover:bg-green-600 text-white rounded-full flex items-center justify-center transition-all shadow-lg shadow-green-600/20"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <div className="text-center mt-3">
                        <p className="text-[10px] text-slate-400 flex items-center justify-center gap-1.5">
                            <Sparkles size={10} className="text-amber-500" />
                            <span>Powered by Osool Hybrid Brain (GPT-4o + XGBoost). Not financial advice.</span>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
