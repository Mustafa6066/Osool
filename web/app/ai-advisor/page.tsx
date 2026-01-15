"use client";

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import AuthModal from '@/components/AuthModal';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Send, Sparkles, Home, FileText, TrendingUp, HelpCircle,
    Bot, User as UserIcon, Loader2
} from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

const quickActions = [
    { icon: <Home className="w-5 h-5" />, labelKey: 'chat.quickActions.analyzeProperty', prompt: 'Analyze property prices in New Cairo' },
    { icon: <FileText className="w-5 h-5" />, labelKey: 'chat.quickActions.checkContract', prompt: 'What should I look for in a property contract?' },
    { icon: <TrendingUp className="w-5 h-5" />, labelKey: 'chat.quickActions.marketInsights', prompt: 'What are the current market trends in Egypt?' },
    { icon: <HelpCircle className="w-5 h-5" />, labelKey: 'chat.quickActions.investmentAdvice', prompt: 'Give me investment advice for Egyptian real estate' },
];

export default function AIAdvisorPage() {
    const { t, language } = useLanguage();
    const { isAuthenticated } = useAuth();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: language === 'ar'
                ? 'مرحباً! أنا عمرو، مستشارك العقاري الذكي. كيف يمكنني مساعدتك اليوم؟ يمكنني تحليل العقارات، مراجعة العقود، وتقديم رؤى السوق.'
                : "Hello! I'm Amr, your AI real estate advisor. How can I help you today? I can analyze properties, review contracts, and provide market insights.",
            timestamp: new Date(),
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText) return;

        if (!isAuthenticated) {
            setShowAuthModal(true);
            return;
        }

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: messageText,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        // Simulate AI response (in production, call API)
        setTimeout(() => {
            const aiResponse: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: getAIResponse(messageText, language),
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, aiResponse]);
            setIsLoading(false);
        }, 1500);
    };

    const getAIResponse = (query: string, lang: string): string => {
        // Simulated responses - in production, this would call the backend
        const responses: Record<string, { en: string; ar: string }> = {
            default: {
                en: "I understand you're asking about real estate in Egypt. Based on current market data, I can provide you with AI-powered insights on property valuations, legal verification, and investment opportunities. Would you like me to elaborate on any specific aspect?",
                ar: "أفهم أنك تسأل عن العقارات في مصر. استناداً إلى بيانات السوق الحالية، يمكنني تقديم رؤى مدعومة بالذكاء الاصطناعي حول تقييمات العقارات والتحقق القانوني وفرص الاستثمار. هل تريد مني التوضيح أكثر؟",
            },
        };

        return lang === 'ar' ? responses.default.ar : responses.default.en;
    };

    return (
        <main className="min-h-screen bg-[var(--color-background)] flex flex-col">
            <Navigation />

            <AuthModal
                isOpen={showAuthModal}
                onClose={() => setShowAuthModal(false)}
                onSuccess={() => setShowAuthModal(false)}
            />

            <div className="flex-1 flex flex-col lg:flex-row max-w-7xl mx-auto w-full">
                {/* Quick Actions Sidebar - Desktop */}
                <aside className="hidden lg:block w-72 border-r border-[var(--color-border)] p-6">
                    <div className="sticky top-24">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center">
                                <Sparkles className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h2 className="font-bold text-[var(--color-text-primary)]">
                                    {language === 'ar' ? 'عمرو' : 'Amr'}
                                </h2>
                                <p className="text-xs text-[var(--color-text-muted)]">AI Advisor</p>
                            </div>
                        </div>

                        <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-4">
                            {language === 'ar' ? 'إجراءات سريعة' : 'Quick Actions'}
                        </h3>

                        <div className="space-y-2">
                            {quickActions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSend(action.prompt)}
                                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left
                             bg-[var(--color-surface)] border border-[var(--color-border)]
                             hover:border-[var(--color-primary)] transition-colors
                             text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
                                >
                                    <span className="text-[var(--color-primary)]">{action.icon}</span>
                                    <span className="text-sm font-medium">{t(action.labelKey)}</span>
                                </button>
                            ))}
                        </div>

                        <div className="mt-8 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                            <p className="text-xs text-purple-300 leading-relaxed">
                                {language === 'ar'
                                    ? 'مدعوم بتقنية Claude 3.5 Sonnet ونماذج XGBoost المدربة على بيانات السوق المصري.'
                                    : 'Powered by Claude 3.5 Sonnet and XGBoost models trained on Egyptian market data.'
                                }
                            </p>
                        </div>
                    </div>
                </aside>

                {/* Chat Area */}
                <div className="flex-1 flex flex-col">
                    {/* Header */}
                    <div className="border-b border-[var(--color-border)] p-4 lg:p-6">
                        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">
                            {t('chat.title')}
                        </h1>
                        <p className="text-sm text-[var(--color-text-muted)]">
                            {t('chat.subtitle')}
                        </p>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-6">
                        <AnimatePresence>
                            {messages.map((message) => (
                                <motion.div
                                    key={message.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                    className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                                >
                                    {/* Avatar */}
                                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                    ${message.role === 'assistant'
                                            ? 'bg-gradient-to-r from-purple-500 to-indigo-500'
                                            : 'bg-[var(--color-primary)]'
                                        }`}
                                    >
                                        {message.role === 'assistant'
                                            ? <Bot className="w-5 h-5 text-white" />
                                            : <UserIcon className="w-5 h-5 text-white" />
                                        }
                                    </div>

                                    {/* Message Bubble */}
                                    <div className={`max-w-[80%] lg:max-w-[60%] rounded-2xl p-4
                    ${message.role === 'assistant'
                                            ? 'bg-[var(--color-surface)] border border-[var(--color-border)]'
                                            : 'bg-[var(--color-primary)] text-white'
                                        }`}
                                    >
                                        <p className={message.role === 'assistant' ? 'text-[var(--color-text-primary)]' : ''}>
                                            {message.content}
                                        </p>
                                        <p className={`text-xs mt-2 ${message.role === 'assistant' ? 'text-[var(--color-text-muted)]' : 'text-white/70'
                                            }`}>
                                            {message.timestamp.toLocaleTimeString(language === 'ar' ? 'ar-EG' : 'en-US', {
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>

                        {/* Loading Indicator */}
                        {isLoading && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex gap-4"
                            >
                                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 flex items-center justify-center">
                                    <Bot className="w-5 h-5 text-white" />
                                </div>
                                <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-4">
                                    <Loader2 className="w-5 h-5 text-[var(--color-primary)] animate-spin" />
                                </div>
                            </motion.div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Mobile Quick Actions */}
                    <div className="lg:hidden border-t border-[var(--color-border)] p-4 overflow-x-auto">
                        <div className="flex gap-2">
                            {quickActions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSend(action.prompt)}
                                    className="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-full
                             bg-[var(--color-surface)] border border-[var(--color-border)]
                             text-sm text-[var(--color-text-secondary)]"
                                >
                                    <span className="text-[var(--color-primary)]">{action.icon}</span>
                                    {t(action.labelKey)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Input Area */}
                    <div className="border-t border-[var(--color-border)] p-4 lg:p-6">
                        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-3">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={t('chat.placeholder')}
                                className="flex-1 px-4 py-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]
                           text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)]
                           focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="px-6 py-3 rounded-xl bg-[var(--color-primary)] text-white font-semibold
                           hover:bg-[var(--color-primary-hover)] transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed
                           flex items-center gap-2"
                            >
                                <Send className="w-5 h-5" />
                                <span className="hidden sm:inline">{language === 'ar' ? 'إرسال' : 'Send'}</span>
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
