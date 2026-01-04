"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

const EliteAdvisorChat = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    // Initial greeting
    useEffect(() => {
        // Only add greeting if empty
        if (messages.length === 0) {
            setMessages([{
                role: 'assistant',
                content: `أهلاً بحضرتك في أصول! 🏠\n` +
                    `أنا أسامة، مستشارك العقاري الشخصي.\n\n` +
                    `عشان أقدر أساعدك، ممكن تقولي شوية عن احتياجاتك؟\n` +
                    `مثلاً: بتدور على سكن ولا استثمار؟`
            }]);
        }
    }, []);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        try {
            const response = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [...messages, userMessage].map(m => ({
                        role: m.role,
                        content: m.content
                    }))
                })
            });

            const data = await response.json();

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.message || "عذراً، حدث خطأ."
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'عذراً، حصل مشكلة في الاتصال.'
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-md mx-auto bg-gradient-to-br from-navy to-navy-light rounded-3xl overflow-hidden shadow-2xl border border-glass-border">
            {/* Glass Header */}
            <motion.div
                className="glass-card flex items-center p-4 m-2 !rounded-xl !border-0 bg-white/5"
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
            >
                <div className="relative w-12 h-12 mr-3 border-2 border-gold rounded-full overflow-hidden shrink-0">
                    <img src="/advisor-avatar.png" alt="أسامة" className="w-full h-full object-cover" />
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-teal rounded-full border-2 border-navy"></span>
                </div>
                <div>
                    <h3 className="text-white text-lg font-bold">أسامة - مستشار أصول</h3>
                    <span className="text-teal text-xs">متاح الآن • يرد فوراً</span>
                </div>
            </motion.div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                <AnimatePresence>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            className={`flex items-end gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                        >
                            {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-full overflow-hidden border border-gold/50 shrink-0">
                                    <img src="/advisor-avatar.png" alt="" />
                                </div>
                            )}

                            <div
                                className={`max-w-[80%] p-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'assistant'
                                        ? 'glass-card bg-white/10 text-white rounded-br-sm'
                                        : 'bg-gradient-to-br from-gold to-gold-light text-navy font-medium rounded-bl-sm shadow-md'
                                    }`}
                            >
                                {msg.content}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Typing Indicator */}
                {isTyping && (
                    <motion.div
                        className="flex items-end gap-2"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <div className="w-8 h-8 rounded-full overflow-hidden border border-gold/50 shrink-0">
                            <img src="/advisor-avatar.png" alt="" />
                        </div>
                        <div className="glass-card px-4 py-3 rounded-2xl rounded-br-sm flex gap-1">
                            <span className="w-2 h-2 bg-gold rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                            <span className="w-2 h-2 bg-gold rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                            <span className="w-2 h-2 bg-gold rounded-full animate-bounce"></span>
                        </div>
                    </motion.div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <motion.div
                className="glass-card m-4 p-2 flex gap-2 !rounded-2xl bg-white/5"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
            >
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="اكتب رسالتك هنا..."
                    dir="rtl"
                    className="flex-1 bg-transparent text-white placeholder-white/50 px-3 outline-none"
                />
                <motion.button
                    onClick={sendMessage}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold to-gold-light flex items-center justify-center text-navy shadow-lg"
                >
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 rotate-180">
                        <path d="M2 21l21-9L2 3v7l15 2-15 2v7z" />
                    </svg>
                </motion.button>
            </motion.div>
        </div>
    );
};

export default EliteAdvisorChat;
