'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, ShieldCheck, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

type Message = {
    id: string;
    role: 'user' | 'amr';
    content: string;
    type: 'text';
};

export default function AmrDemoChat() {
    const [messages] = useState<Message[]>([
        {
            id: '1',
            role: 'amr',
            content: 'Ahlan! I am Amr. I help you protect your wealth through real estate. How can I assist you today?',
            type: 'text',
        },
    ]);
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);
    const router = useRouter();

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;
        // Redirect to main chat with the message
        router.push(`/chat?initialMessage=${encodeURIComponent(input)}`);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSend();
        }
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
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Input Area (Functional) */}
            <div className="p-3 bg-white dark:bg-slate-900 border-t border-gray-100 dark:border-slate-800">
                <div className="relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask Amr about investment..."
                        className="w-full bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-full py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/20"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
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
