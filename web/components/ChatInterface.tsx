"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Sparkles } from "lucide-react";
import PropertyCard from "./PropertyCard";

type Message = {
    role: "user" | "assistant";
    content: string;
    properties?: any[];
};

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: "Ahlan! I am Amr, your Senior Property Consultant at Osool. I can help you find your dream home, calculate payments, or check legal safety. How can I help you today?"
        }
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string>("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Generate Session ID on mount
        if (typeof window !== "undefined") {
            const existing = sessionStorage.getItem("osool_chat_session");
            if (existing) {
                setSessionId(existing);
            } else {
                const newId = crypto.randomUUID();
                sessionStorage.setItem("osool_chat_session", newId);
                setSessionId(newId);
            }
        }
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = input;
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setIsLoading(true);

        try {
            const token = localStorage.getItem("osool_jwt");

            // Direct call to Backend API
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(token ? { "Authorization": `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    message: userMessage,  // CHANGED: 'text' -> 'message' to match backend model
                    session_id: sessionId  // Added Session ID
                }),
            });

            const data = await response.json();

            if (data.response) {
                setMessages((prev) => [...prev, {
                    role: "assistant",
                    content: data.response,
                    properties: data.properties // Store properties
                }]);
            } else if (data.error) {
                setMessages((prev) => [...prev, { role: "assistant", content: "⚠️ System Error: " + data.error }]);
            }

        } catch (error) {
            console.error("Chat Error:", error);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "⚠️ Connection Error. Please ensure backend is running." }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto bg-white/10 backdrop-blur-md rounded-xl border border-white/20 shadow-2xl overflow-hidden">

            {/* Header */}
            <div className="bg-gradient-to-r from-[#1a1c2e] to-[#2d3748] p-4 flex items-center gap-3 border-b border-white/10">
                <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center border-2 border-green-400">
                        <Bot className="text-white w-6 h-6" />
                    </div>
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-[#1a1c2e] rounded-full"></span>
                </div>
                <div>
                    <h3 className="text-white font-bold text-lg flex items-center gap-2">
                        Amr <span className="text-xs font-normal text-green-400 bg-green-400/10 px-2 py-0.5 rounded-full">Online</span>
                    </h3>
                    <p className="text-gray-400 text-xs">Senior Consultant @ Osool {sessionId.slice(0, 4)}</p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0f111a]/80">
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex items-start gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"
                            }`}
                    >
                        <div
                            className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${msg.role === "user" ? "bg-purple-600" : "bg-blue-600"
                                }`}
                        >
                            {msg.role === "user" ? <User size={16} /> : <Sparkles size={16} />}
                        </div>

                        <div className="flex flex-col max-w-[80%]">
                            <div
                                className={`rounded-2xl p-4 text-sm leading-relaxed ${msg.role === "user"
                                    ? "bg-purple-600 text-white rounded-tr-none shadow-lg shadow-purple-900/20"
                                    : "bg-[#1e293b] text-gray-100 rounded-tl-none border border-white/5 shadow-lg"
                                    }`}
                            >
                                <div dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') }} />
                            </div>

                            {/* Property Cards */}
                            {msg.properties && msg.properties.length > 0 && (
                                <div className="mt-2 space-y-2">
                                    {msg.properties.map((prop: any, pIdx: number) => (
                                        <PropertyCard key={pIdx} property={prop} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center animate-pulse">
                            <Sparkles size={16} />
                        </div>
                        <div className="bg-[#1e293b] p-3 rounded-2xl rounded-tl-none border border-white/5">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 bg-[#1a1c2e] border-t border-white/10">
                <div className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 bg-[#0f111a] border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        placeholder="Ask about properties, investments, or legal checks..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="bg-blue-600 hover:bg-blue-500 text-white p-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-600/30"
                    >
                        <Send size={20} />
                    </button>
                </div>
                <p className="text-gray-500 text-[10px] mt-2 text-center">
                    Osool AI can make mistakes. Please check important info.
                </p>
            </div>
        </div>
    );
}
