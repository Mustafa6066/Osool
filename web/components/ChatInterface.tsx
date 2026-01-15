"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Bot, User, Sparkles, Plus, Copy, Check, ArrowDown, Loader2 } from "lucide-react";
import DOMPurify from "dompurify";
import PropertyCard from "./PropertyCard";
import InvestmentScorecard from "./visualizations/InvestmentScorecard";
import ComparisonMatrix from "./visualizations/ComparisonMatrix";
import PaymentTimeline from "./visualizations/PaymentTimeline";
import MarketTrendChart from "./visualizations/MarketTrendChart";

type Message = {
    role: "user" | "assistant";
    content: string;
    timestamp?: Date;
    properties?: any[];
    visualizations?: {
        investment_scorecard?: any;
        comparison_matrix?: any;
        payment_timeline?: any;
        market_trend_chart?: any;
    };
};

// AMR Greeting based on language detection
const GREETINGS = {
    ar: "أهلاً وسهلاً! أنا عمرو، مستشارك العقاري الذكي. أقدر أساعدك تلاقي بيت أحلامك، أحلل الأسعار والاستثمارات، وأحسب الأقساط. إزاي أقدر أخدمك النهارده؟",
    en: "Hello! I'm Amr, your AI real estate advisor. I can help you find your dream property, analyze prices and investments, and calculate payment plans. How can I help you today?",
};

// Loading phases for better UX
const LOADING_PHASES = [
    { text: "Thinking...", textAr: "بفكر..." },
    { text: "Searching properties...", textAr: "بدور على العقارات..." },
    { text: "Analyzing data...", textAr: "بحلل البيانات..." },
    { text: "Preparing response...", textAr: "بجهز الرد..." },
];

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: `${GREETINGS.ar}\n\n${GREETINGS.en}`,
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [loadingPhase, setLoadingPhase] = useState(0);
    const [sessionId, setSessionId] = useState<string>("");
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [detectedLanguage, setDetectedLanguage] = useState<"ar" | "en" | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Detect if text contains Arabic characters
    const isArabic = (text: string): boolean => {
        const arabicPattern = /[\u0600-\u06FF]/;
        return arabicPattern.test(text);
    };

    // Sanitize HTML to prevent XSS attacks
    const sanitizeHTML = (html: string): string => {
        if (typeof window !== "undefined") {
            return DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ["b", "i", "em", "strong", "br", "p", "ul", "li", "ol", "span"],
                ALLOWED_ATTR: ["class"],
            });
        }
        return html;
    };

    // Format message content with markdown-like styling
    const formatContent = (content: string): string => {
        return content
            .replace(/\n/g, "<br/>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`(.*?)`/g, '<span class="bg-white/10 px-1 rounded text-purple-300">$1</span>');
    };

    // Copy message to clipboard
    const copyToClipboard = async (text: string, index: number) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (err) {
            console.error("Failed to copy:", err);
        }
    };

    // Generate session ID on mount
    useEffect(() => {
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

    // Scroll to bottom smoothly
    const scrollToBottom = (smooth = true) => {
        messagesEndRef.current?.scrollIntoView({
            behavior: smooth ? "smooth" : "auto"
        });
    };

    // Auto-scroll on new messages
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Handle scroll for showing scroll-to-bottom button
    const handleScroll = () => {
        if (!chatContainerRef.current) return;
        const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
        setShowScrollButton(!isNearBottom);
    };

    // Loading phase animation
    useEffect(() => {
        if (!isLoading) {
            setLoadingPhase(0);
            return;
        }

        const interval = setInterval(() => {
            setLoadingPhase((prev) => (prev + 1) % LOADING_PHASES.length);
        }, 1500);

        return () => clearInterval(interval);
    }, [isLoading]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + "px";
        }
    }, [input]);

    // Handle new conversation
    const handleNewConversation = () => {
        setMessages([
            {
                role: "assistant",
                content: `${GREETINGS.ar}\n\n${GREETINGS.en}`,
                timestamp: new Date(),
            },
        ]);
        const newId = crypto.randomUUID();
        sessionStorage.setItem("osool_chat_session", newId);
        setSessionId(newId);
        setDetectedLanguage(null);
    };

    // Handle send message
    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput("");

        // Detect language from first real user message
        if (!detectedLanguage) {
            setDetectedLanguage(isArabic(userMessage) ? "ar" : "en");
        }

        // Add user message
        setMessages((prev) => [
            ...prev,
            { role: "user", content: userMessage, timestamp: new Date() },
        ]);
        setIsLoading(true);

        try {
            const token = localStorage.getItem("access_token");
            const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
            const response = await fetch(
                `${apiUrl}/api/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                    body: JSON.stringify({
                        message: userMessage,
                        session_id: sessionId,
                    }),
                }
            );

            const data = await response.json();

            if (data.response) {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content: data.response,
                        timestamp: new Date(),
                        properties: data.properties,
                        visualizations: data.visualizations,
                    },
                ]);
            } else if (data.error) {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content: `⚠️ ${data.error}`,
                        timestamp: new Date(),
                    },
                ]);
            }
        } catch (error) {
            console.error("Chat Error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: detectedLanguage === "ar"
                        ? "⚠️ حصل مشكلة في الاتصال. جرب تاني."
                        : "⚠️ Connection error. Please try again.",
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-[#0a0a0a]">
            {/* Header */}
            <header className="flex-shrink-0 border-b border-white/10 bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-50">
                <div className="container mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleNewConversation}
                            className="p-2 rounded-lg hover:bg-white/5 transition-colors text-gray-400 hover:text-white"
                            title="New conversation"
                        >
                            <Plus className="w-5 h-5" />
                        </button>

                        <div className="flex items-center gap-3">
                            <div className="relative">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                                    <Bot className="w-5 h-5 text-white" />
                                </div>
                                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-[#0a0a0a]" />
                            </div>
                            <div>
                                <h1 className="text-white font-semibold">Amr • عمرو</h1>
                                <p className="text-xs text-gray-500">AI Real Estate Advisor</p>
                            </div>
                        </div>
                    </div>

                    <div className="text-xs text-gray-600">
                        Session: {sessionId.slice(0, 8)}
                    </div>
                </div>
            </header>

            {/* Messages Container */}
            <div
                ref={chatContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto"
            >
                <div className="container mx-auto max-w-3xl px-4 py-6">
                    <div className="space-y-6">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                            >
                                {/* Avatar */}
                                <div className="flex-shrink-0">
                                    <div
                                        className={`w-8 h-8 rounded-full flex items-center justify-center ${msg.role === "user"
                                            ? "bg-purple-600"
                                            : "bg-gradient-to-br from-purple-600 to-blue-600"
                                            }`}
                                    >
                                        {msg.role === "user" ? (
                                            <User className="w-4 h-4 text-white" />
                                        ) : (
                                            <Sparkles className="w-4 h-4 text-white" />
                                        )}
                                    </div>
                                </div>

                                {/* Message Content */}
                                <div className={`flex-1 max-w-[85%] ${msg.role === "user" ? "text-right" : ""}`}>
                                    <div className="group relative">
                                        <div
                                            className={`inline-block px-4 py-3 rounded-2xl text-[15px] leading-relaxed ${msg.role === "user"
                                                ? "bg-purple-600 text-white rounded-tr-md"
                                                : "bg-white/5 text-gray-200 rounded-tl-md border border-white/5"
                                                }`}
                                            dir={isArabic(msg.content) ? "rtl" : "ltr"}
                                        >
                                            <div
                                                dangerouslySetInnerHTML={{
                                                    __html: sanitizeHTML(formatContent(msg.content)),
                                                }}
                                            />
                                        </div>

                                        {/* Copy Button */}
                                        <button
                                            onClick={() => copyToClipboard(msg.content, idx)}
                                            className={`absolute top-2 ${msg.role === "user" ? "left-2" : "right-2"
                                                } opacity-0 group-hover:opacity-100 transition-all p-1.5 rounded-lg bg-black/50 hover:bg-black/70 text-gray-400 hover:text-white`}
                                        >
                                            {copiedIndex === idx ? (
                                                <Check className="w-3.5 h-3.5 text-green-400" />
                                            ) : (
                                                <Copy className="w-3.5 h-3.5" />
                                            )}
                                        </button>
                                    </div>

                                    {/* Timestamp */}
                                    {msg.timestamp && (
                                        <p className="text-[10px] text-gray-600 mt-1">
                                            {msg.timestamp.toLocaleTimeString([], {
                                                hour: "2-digit",
                                                minute: "2-digit",
                                            })}
                                        </p>
                                    )}

                                    {/* Property Cards */}
                                    {msg.properties && msg.properties.length > 0 && (
                                        <div className="mt-4 space-y-3">
                                            {msg.properties.map((prop: any, pIdx: number) => (
                                                <PropertyCard key={pIdx} property={prop} />
                                            ))}
                                        </div>
                                    )}

                                    {/* Visualizations */}
                                    {msg.visualizations?.investment_scorecard && (
                                        <div className="mt-4">
                                            <InvestmentScorecard
                                                property={msg.visualizations.investment_scorecard.property}
                                                analysis={msg.visualizations.investment_scorecard.analysis}
                                            />
                                        </div>
                                    )}

                                    {msg.visualizations?.comparison_matrix && (
                                        <div className="mt-4">
                                            <ComparisonMatrix
                                                properties={msg.visualizations.comparison_matrix.properties}
                                                bestValueId={msg.visualizations.comparison_matrix.best_value_id}
                                                recommendedId={msg.visualizations.comparison_matrix.recommended_id}
                                            />
                                        </div>
                                    )}

                                    {msg.visualizations?.payment_timeline && (
                                        <div className="mt-4">
                                            <PaymentTimeline
                                                property={msg.visualizations.payment_timeline.property}
                                                payment={msg.visualizations.payment_timeline.payment}
                                            />
                                        </div>
                                    )}

                                    {msg.visualizations?.market_trend_chart && (
                                        <div className="mt-4">
                                            <MarketTrendChart
                                                location={msg.visualizations.market_trend_chart.location}
                                                data={msg.visualizations.market_trend_chart.data}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading Indicator */}
                        {isLoading && (
                            <div className="flex gap-4">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center animate-pulse">
                                    <Loader2 className="w-4 h-4 text-white animate-spin" />
                                </div>
                                <div className="bg-white/5 border border-white/5 rounded-2xl rounded-tl-md px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <span className="flex gap-1">
                                            <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                                            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                            <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                                        </span>
                                        <span className="text-sm text-gray-400">
                                            {detectedLanguage === "ar"
                                                ? LOADING_PHASES[loadingPhase].textAr
                                                : LOADING_PHASES[loadingPhase].text}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>
            </div>

            {/* Scroll to bottom button */}
            {showScrollButton && (
                <button
                    onClick={() => scrollToBottom()}
                    className="fixed bottom-28 right-6 p-2 bg-white/10 hover:bg-white/20 rounded-full border border-white/10 transition-all shadow-lg"
                >
                    <ArrowDown className="w-5 h-5 text-white" />
                </button>
            )}

            {/* Input Area */}
            <div className="flex-shrink-0 border-t border-white/10 bg-[#0a0a0a]/80 backdrop-blur-xl">
                <div className="container mx-auto max-w-3xl px-4 py-4">
                    <div className="relative">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={
                                detectedLanguage === "ar"
                                    ? "اكتب رسالتك هنا..."
                                    : "Message Amr..."
                            }
                            disabled={isLoading}
                            rows={1}
                            className="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3.5 pr-12 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all resize-none max-h-[200px]"
                            dir={isArabic(input) ? "rtl" : "ltr"}
                        />
                        <button
                            onClick={handleSend}
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 bottom-2 p-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-xl transition-all"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                    <p className="text-center text-gray-600 text-[10px] mt-2">
                        Amr can make mistakes. Please verify important information.
                    </p>
                </div>
            </div>
        </div>
    );
}
