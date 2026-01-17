"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Plus, Copy, Check, ArrowDown, Menu, Paperclip } from "lucide-react";
import DOMPurify from "dompurify";
import PropertyCardMinimal from "./PropertyCardMinimal";
import ConversationHistory from "./ConversationHistory";
import VisualizationRenderer from "./visualizations/VisualizationRenderer";

// UI Action types for V4 Wolf Brain
type UIAction = {
    type: string;
    priority: number;
    data: any;
};

type Message = {
    role: "user" | "assistant";
    content: string;
    timestamp?: Date;
    properties?: any[];
    visualizations?: Record<string, any>;  // V4: Visualization data
    ui_actions?: UIAction[];  // V4: UI action triggers
};

// AMR Greeting based on language detection
const GREETINGS = {
    ar: "أهلاً يا باشا! أنا عمرو، ذئب العقارات في أوصول. بتدور على إيه؟ سكن ولا استثمار؟",
    en: "Welcome, boss! I'm Amr, the Wolf of Real Estate at Osool. What are you looking for? A home or an investment?",
};

// Loading phases
const LOADING_PHASES = [
    { text: "Thinking...", textAr: "بفكر..." },
    { text: "Searching the black book...", textAr: "بدور في الـ black book..." },
    { text: "Running the AI...", textAr: "بشغل الـ AI..." },
];

export default function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: `${GREETINGS.ar}\n\n${GREETINGS.en}`,
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [loadingPhase, setLoadingPhase] = useState(0);
    const [sessionId, setSessionId] = useState<string>("");
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const [showScrollButton, setShowScrollButton] = useState(false);
    const [detectedLanguage, setDetectedLanguage] = useState<"ar" | "en" | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Detect if text contains Arabic characters
    const isArabic = (text: string): boolean => {
        const arabicPattern = /[\u0600-\u06FF]/;
        return arabicPattern.test(text);
    };

    // Sanitize HTML
    const sanitizeHTML = (html: string): string => {
        if (typeof window !== "undefined") {
            return DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ["b", "i", "em", "strong", "br", "p", "ul", "li", "ol", "span"],
                ALLOWED_ATTR: ["class"],
            });
        }
        return html;
    };

    // Format message content
    const formatContent = (content: string): string => {
        return content
            .replace(/\n/g, "<br/>")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`(.*?)`/g, '<span class="bg-amber-100 dark:bg-amber-900/30 px-1 rounded text-amber-800 dark:text-amber-200 text-sm">$1</span>');
    };

    // Copy to clipboard
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

    // Scroll to bottom
    const scrollToBottom = (smooth = true) => {
        messagesEndRef.current?.scrollIntoView({
            behavior: smooth ? "smooth" : "auto"
        });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Handle scroll
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

        if (!detectedLanguage) {
            setDetectedLanguage(isArabic(userMessage) ? "ar" : "en");
        }

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
                        visualizations: data.visualizations,  // V4: Visualization data
                        ui_actions: data.ui_actions,  // V4: UI action triggers
                    },
                ]);
            } else if (data.error) {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content: detectedLanguage === "ar"
                            ? `حصل مشكلة: ${data.error}`
                            : `Error: ${data.error}`,
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
                        ? "حصل مشكلة في الاتصال. جرب تاني."
                        : "Connection error. Please try again.",
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-[var(--color-background)]">
            {/* Sidebar */}
            <ConversationHistory
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                onSelectConversation={(id) => console.log("Selected:", id)}
                onNewConversation={handleNewConversation}
                currentConversationId={sessionId}
            />

            {/* Header - Minimal */}
            <header className="flex-shrink-0 border-b border-[var(--color-border)] bg-[var(--color-background)]/80 backdrop-blur-sm sticky top-0 z-40">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setSidebarOpen(true)}
                            className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors text-[var(--color-text-secondary)]"
                        >
                            <Menu className="w-5 h-5" />
                        </button>

                        <button
                            onClick={handleNewConversation}
                            className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors text-[var(--color-text-secondary)] text-sm font-medium"
                        >
                            <Plus className="w-4 h-4" />
                            <span className="hidden sm:inline">New Chat</span>
                        </button>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-xl">🐺</span>
                        <span className="text-sm font-medium text-[var(--color-text-primary)]">Amr</span>
                    </div>
                </div>
            </header>

            {/* Messages Container */}
            <div
                ref={chatContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto px-4 py-8 scroll-smooth"
            >
                <div className="max-w-2xl mx-auto space-y-8">

                    {/* Welcome State */}
                    {messages.length === 1 && messages[0].role === "assistant" && (
                        <div className="text-center py-20 animate-fade-in">
                            <div className="w-16 h-16 bg-white border border-[var(--color-border)] rounded-2xl mx-auto shadow-sm flex items-center justify-center mb-6">
                                <span className="text-2xl">🐺</span>
                            </div>
                            <h1 className="text-3xl font-serif font-medium text-[var(--color-text-primary)] mb-2">
                                Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}
                            </h1>
                            <p className="text-[var(--color-text-secondary)]">How can I help you close a deal today?</p>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`message-enter ${msg.role === "user" ? "flex justify-end" : ""}`}
                        >
                            {msg.role === "assistant" && idx > 0 ? (
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary)] flex items-center justify-center text-lg flex-shrink-0">🐺</div>
                                    <div className="flex-1 max-w-none">
                                        <div className="group relative">
                                            <div
                                                className="prose text-[var(--color-text-primary)]"
                                                dir={isArabic(msg.content) ? "rtl" : "ltr"}
                                                dangerouslySetInnerHTML={{
                                                    __html: sanitizeHTML(formatContent(msg.content)),
                                                }}
                                            />
                                            <button
                                                onClick={() => copyToClipboard(msg.content, idx)}
                                                className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]"
                                            >
                                                {copiedIndex === idx ? (
                                                    <Check className="w-4 h-4 text-green-500" />
                                                ) : (
                                                    <Copy className="w-4 h-4" />
                                                )}
                                            </button>
                                        </div>

                                        {/* Property Cards */}
                                        {msg.properties && msg.properties.length > 0 && (
                                            <div className="mt-4 space-y-3">
                                                {msg.properties.map((prop: any, pIdx: number) => (
                                                    <PropertyCardMinimal key={pIdx} property={prop} />
                                                ))}
                                            </div>
                                        )}

                                        {/* V4: Visualizations */}
                                        {msg.visualizations && Object.keys(msg.visualizations).length > 0 && (
                                            <div className="mt-4 space-y-4">
                                                {Object.entries(msg.visualizations).map(([type, data], vIdx) => (
                                                    <VisualizationRenderer
                                                        key={`${type}-${vIdx}`}
                                                        type={type}
                                                        data={data}
                                                    />
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : msg.role === "user" ? (
                                <div className="flex justify-end">
                                    <div
                                        className="message-user bg-[var(--color-user-bubble)] border border-[var(--color-border)] rounded-2xl px-4 py-3 max-w-[85%]"
                                        dir={isArabic(msg.content) ? "rtl" : "ltr"}
                                    >
                                        {msg.content}
                                    </div>
                                </div>
                            ) : null}
                        </div>
                    ))}

                    {/* Loading Indicator */}
                    {isLoading && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-full bg-[var(--color-primary)]/20 text-[var(--color-primary)] flex items-center justify-center text-lg flex-shrink-0">🐺</div>
                            <div className="typing-indicator">
                                <div className="loading-dots">
                                    <span className="loading-dot" />
                                    <span className="loading-dot" />
                                    <span className="loading-dot" />
                                </div>
                                <span>
                                    {detectedLanguage === "ar"
                                        ? LOADING_PHASES[loadingPhase].textAr
                                        : LOADING_PHASES[loadingPhase].text}
                                </span>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Scroll to bottom button */}
            {showScrollButton && (
                <button
                    onClick={() => scrollToBottom()}
                    className="fixed bottom-28 right-6 p-2.5 bg-[var(--color-surface)] border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] rounded-full transition-all shadow-md"
                >
                    <ArrowDown className="w-4 h-4 text-[var(--color-text-secondary)]" />
                </button>
            )}

            {/* Input Area - Claude-Style Box */}
            <div className="p-4 bg-[var(--color-background)]/80 backdrop-blur-sm z-10 pb-8">
                <div className="max-w-2xl mx-auto">
                    <div className="relative bg-white rounded-xl border border-[var(--color-border)] shadow-sm focus-within:ring-2 focus-within:ring-[var(--color-primary)]/20 focus-within:border-[var(--color-primary)] transition-all overflow-hidden">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={
                                detectedLanguage === "ar"
                                    ? "اسأل عن العقارات، العائد على الاستثمار، أو اتجاهات السوق..."
                                    : "Ask about properties, ROI, or market trends..."
                            }
                            disabled={isLoading}
                            rows={1}
                            className="w-full max-h-[200px] py-4 px-4 pr-12 bg-transparent border-none focus:ring-0 resize-none text-base outline-none text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]"
                            style={{ minHeight: "60px" }}
                            dir={isArabic(input) ? "rtl" : "ltr"}
                        />

                        {/* Action Buttons */}
                        <div className="flex items-center justify-between px-2 pb-2">
                            <button className="p-2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] rounded-lg transition-colors">
                                <Paperclip className="w-5 h-5" />
                            </button>

                            <button
                                onClick={handleSend}
                                disabled={isLoading || !input.trim()}
                                className={`p-2 rounded-lg transition-all duration-200 ${input.trim() && !isLoading
                                        ? "bg-[var(--color-primary)] text-white shadow-md hover:bg-[var(--color-primary-hover)]"
                                        : "bg-gray-100 text-gray-300 cursor-not-allowed"
                                    }`}
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    <div className="text-center mt-2">
                        <p className="text-xs text-[var(--color-text-muted)]">
                            {detectedLanguage === "ar"
                                ? "عمرو ممكن يغلط. تحقق من بيانات العقارات المهمة."
                                : "Amr can make mistakes. Please verify important real estate data."}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
