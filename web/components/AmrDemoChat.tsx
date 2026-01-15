'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, ShieldCheck, TrendingUp, MapPin, Sparkles } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    type: 'text' | 'chart' | 'location';
};

const data = [
    { year: '2021', value: 100, currency: 100 },
    { year: '2022', value: 115, currency: 85 },
    { year: '2023', value: 145, currency: 60 },
    { year: '2024', value: 185, currency: 40 },
    { year: '2025', value: 240, currency: 30 },
];

export default function AmrDemoChat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'amr',
            content: 'Ahlan! I am Amr. I help you protect your wealth through real estate. How can I assist you today?',
            type: 'text',
        },
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isTyping]);

    // Simulation Sequence
    useEffect(() => {
        const timer = setTimeout(() => {
            handleUserMessage("Ezayak ya Amr? I'm worried about the EGP devaluation.");
        }, 2000); // Auto start after 2s for demo impact

        return () => clearTimeout(timer);
    }, []);

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
        setTimeout(() => {
            const response: Message = {
                id: (Date.now() + 1).toString(),
                role: 'amr',
                content: "Ahlan ya Sadiq! I understand your anxiety. Numbers don't lie. Look at how New Capital properties (Green) have outperformed the EGP (Purple) over the last 4 years. This is your safe haven.",
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

    return (
        <div className="w-full max-w-md mx-auto bg-white dark:bg-slate-900 rounded-2xl shadow-ai border border-gray-100 dark:border-slate-800 overflow-hidden flex flex-col h-[500px]">
            {/* Header */}
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-4 flex items-center gap-3 shadow-md z-10">
                <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center text-green-600 font-bold border-2 border-white/30">
                        A
                    </div>
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-300 border-2 border-green-600 rounded-full animate-pulse"></div>
                </div>
                <div>
                    <h3 className="text-white font-bold text-lg flex items-center gap-2">
                        Amr <ShieldCheck size={16} className="text-green-100" />
                    </h3>
                    <p className="text-green-50 text-xs opacity-90">AI Wealth Consultant</p>
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-950" ref={scrollRef}>
                <AnimatePresence>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-bl-none border border-gray-100 dark:border-slate-700'
                                    }`}
                            >
                                <div className="text-sm leading-relaxed">{msg.content}</div>

                                {msg.type === 'chart' && (
                                    <div className="mt-4 bg-slate-50 dark:bg-slate-900 rounded-xl p-3 border border-slate-100 dark:border-slate-800 h-48 w-full">
                                        <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                                            <TrendingUp size={14} /> Property vs Currency
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
                        className="flex items-center gap-1 text-slate-400 text-xs ml-2"
                    >
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                    </motion.div>
                )}
            </div>

            {/* Input Area (Visual Only) */}
            <div className="p-3 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800">
                <div className="relative">
                    <input
                        type="text"
                        disabled
                        placeholder="Ask Amr about investment..."
                        className="w-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-full py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/20 cursor-not-allowed opacity-70"
                    />
                    <button className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center hover:bg-green-600 transition-colors">
                        <Send size={14} />
                    </button>
                </div>
                <div className="text-[10px] text-center text-slate-400 mt-2 flex items-center justify-center gap-1">
                    <Sparkles size={10} className="text-amber-400" />
                    Powered by Osool Hybrid Brain (GPT-4o + XGBoost)
                </div>
            </div>
        </div>
    );
}
