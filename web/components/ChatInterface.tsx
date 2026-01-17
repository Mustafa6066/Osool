'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Menu, Plus, User, Bot, Sparkles } from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: 'Hello Mustafa. I am Amr, your Osool Real Estate advisor. How can I help you find the perfect property today?',
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [input]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        // Simulate AI response (Replace with your actual API call)
        setTimeout(() => {
            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'I can certainly help with that. Are you looking for a residential unit in New Cairo or an investment opportunity in the Administrative Capital?',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMessage]);
            setIsLoading(false);
        }, 1500);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="flex h-screen overflow-hidden bg-white text-gray-800 font-sans">

            {/* Sidebar - ChatGPT Style */}
            <div
                className={`${isSidebarOpen ? 'w-[260px]' : 'w-0'
                    } bg-gray-900 text-gray-100 flex-shrink-0 transition-all duration-300 ease-in-out flex flex-col overflow-hidden relative`}
            >
                <div className="p-3 flex-1 overflow-y-auto no-scrollbar">
                    <button
                        onClick={() => setMessages([])} // Reset logic
                        className="flex items-center gap-3 w-full px-3 py-3 rounded-md border border-gray-700 hover:bg-gray-800 transition-colors text-sm text-left mb-4"
                    >
                        <Plus size={16} />
                        New chat
                    </button>

                    <div className="flex flex-col gap-2">
                        <div className="text-xs font-medium text-gray-500 px-3 py-2">Today</div>
                        <button className="text-sm truncate px-3 py-2 rounded hover:bg-gray-800 text-left">
                            Real Estate Investment...
                        </button>
                        <button className="text-sm truncate px-3 py-2 rounded hover:bg-gray-800 text-left">
                            New Cairo Compounds
                        </button>
                    </div>
                </div>

                {/* User Profile in Sidebar */}
                <div className="p-3 border-t border-gray-700">
                    <button className="flex items-center gap-3 w-full px-3 py-3 rounded hover:bg-gray-800 transition-colors">
                        <div className="w-8 h-8 rounded bg-green-600 flex items-center justify-center text-white font-medium text-sm">
                            M
                        </div>
                        <div className="text-sm font-medium">Mustafa</div>
                    </button>
                </div>
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full relative">

                {/* Top Navigation (Mobile/Toggle) */}
                <div className="sticky top-0 z-10 p-2 flex items-center gap-2 text-gray-500 bg-white/80 backdrop-blur-sm sm:hidden">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 hover:bg-gray-100 rounded-md"
                    >
                        <Menu size={20} />
                    </button>
                    <span className="font-medium text-gray-700">Amr • Osool</span>
                </div>

                {/* Toggle Button for Desktop */}
                <div className="absolute top-4 left-4 z-20 hidden sm:block">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className={`p-2 rounded-md hover:bg-gray-100 text-gray-500 transition-opacity ${isSidebarOpen ? 'opacity-0 hover:opacity-100' : 'opacity-100'}`}
                        title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
                    >
                        <Menu size={20} />
                    </button>
                </div>

                {/* Chat Scroll Area */}
                <div className="flex-1 overflow-y-auto no-scrollbar">
                    <div className="flex flex-col pb-48 pt-10"> {/* Large padding bottom for input area */}

                        {messages.length === 0 ? (
                            /* Empty State / Welcome */
                            <div className="flex flex-col items-center justify-center h-full mt-20 px-4 text-center">
                                <div className="w-16 h-16 bg-white rounded-full shadow-sm border flex items-center justify-center mb-6">
                                    <Sparkles className="w-8 h-8 text-blue-600" />
                                </div>
                                <h2 className="text-2xl font-semibold text-gray-800 mb-2">How can Amr help you today?</h2>
                            </div>
                        ) : (
                            /* Message List */
                            messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`w-full border-b border-black/5 ${message.role === 'assistant' ? 'bg-gray-50/50' : 'bg-white'
                                        }`}
                                >
                                    <div className="max-w-3xl mx-auto flex gap-6 p-4 md:py-8 text-base leading-7">
                                        {/* Avatar */}
                                        <div className="flex-shrink-0 flex flex-col relative items-end">
                                            {message.role === 'user' ? (
                                                <div className="w-8 h-8 bg-gray-200 rounded-sm flex items-center justify-center">
                                                    <User size={18} className="text-gray-500" />
                                                </div>
                                            ) : (
                                                <div className="w-8 h-8 bg-blue-600 rounded-sm flex items-center justify-center shadow-sm">
                                                    <Bot size={18} className="text-white" />
                                                </div>
                                            )}
                                        </div>

                                        {/* Content */}
                                        <div className="relative flex-1 overflow-hidden">
                                            <div className="font-semibold text-sm mb-1 opacity-90">
                                                {message.role === 'user' ? 'Mustafa' : 'Amr'}
                                            </div>
                                            <div className="prose prose-slate max-w-none text-gray-800 whitespace-pre-wrap">
                                                {message.content}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                        {/* Loading Indicator */}
                        {isLoading && (
                            <div className="w-full bg-gray-50/50 border-b border-black/5">
                                <div className="max-w-3xl mx-auto flex gap-6 p-4 md:py-8">
                                    <div className="w-8 h-8 bg-blue-600 rounded-sm flex items-center justify-center">
                                        <Bot size={18} className="text-white" />
                                    </div>
                                    <div className="flex items-center gap-1 mt-2">
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75"></span>
                                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150"></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area - Fixed Bottom */}
                <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4">
                    <div className="max-w-3xl mx-auto">
                        <div className="relative flex items-end w-full p-3 bg-white border border-gray-300 rounded-xl shadow-lg ring-offset-2 focus-within:ring-2 focus-within:ring-blue-500/20 overflow-hidden">
                            <textarea
                                ref={textareaRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Message Amr..."
                                className="w-full max-h-[200px] py-2 px-2 bg-transparent border-none outline-none text-gray-800 placeholder-gray-400 resize-none overflow-y-auto no-scrollbar"
                                rows={1}
                                style={{ minHeight: '44px' }}
                            />
                            <button
                                onClick={() => handleSubmit()}
                                disabled={!input.trim() || isLoading}
                                className={`p-2 mb-1 rounded-lg transition-all duration-200 ${input.trim()
                                        ? 'bg-blue-600 text-white shadow-sm'
                                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                <Send size={18} />
                            </button>
                        </div>
                        <div className="text-center mt-2">
                            <p className="text-xs text-gray-400">
                                Amr can make mistakes. Consider checking important real estate information.
                            </p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
