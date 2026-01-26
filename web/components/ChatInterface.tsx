'use client';

import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DOMPurify from 'dompurify';
import Link from 'next/link';
import anime from 'animejs';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { streamChat } from '@/lib/api';
import { analyticsEngine, type AnalyticsMatch } from '@/lib/AnalyticsRulesEngine';
import { emptyChatToActiveTransition } from '@/lib/animations';
import VisualizationRenderer from './visualizations/VisualizationRenderer';
import InvitationModal from './InvitationModal';
import { User, LogOut, Gift, PlusCircle, History, Sparkles, Send, Mic, Plus, Bookmark } from 'lucide-react';

// ============================================
// UTILITY COMPONENTS
// ============================================

const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => {
    if (!name) return null;
    return (
        <span className={`material-symbols-outlined select-none ${className}`} style={{ fontSize: size }}>{name}</span>
    );
};

const sanitizeContent = (content: string): string => {
    if (typeof window === 'undefined') return content;
    return DOMPurify.sanitize(content, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    });
};

// ============================================
// TYPEWRITER HOOK
// ============================================

function useTypewriter(text: string, speed: number = 25) {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!text) {
            setDisplayedText('');
            setIsComplete(true);
            return;
        }

        setDisplayedText('');
        setIsComplete(false);

        let index = 0;
        const interval = setInterval(() => {
            if (index < text.length) {
                setDisplayedText(text.slice(0, index + 1));
                index++;
            } else {
                setIsComplete(true);
                clearInterval(interval);
            }
        }, speed);

        return () => clearInterval(interval);
    }, [text, speed]);

    return { displayedText, isComplete };
}

// ============================================
// PROPERTY CARD - FEATURED LISTING
// ============================================

interface Property {
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    bathrooms?: number;
    image_url?: string;
    roi?: number;
    wolf_score?: number;
    developer?: string;
}

function FeaturedPropertyCard({
    property,
    onBookmark,
    onRequestDetails
}: {
    property: Property;
    onBookmark?: () => void;
    onRequestDetails?: () => void;
}) {
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (cardRef.current) {
            anime({
                targets: cardRef.current,
                opacity: [0, 1],
                translateY: [30, 0],
                easing: 'easeOutExpo',
                duration: 800,
            });
        }
    }, [property]);

    const projectedGrowth = property.roi;

    return (
        <motion.div
            ref={cardRef}
            className="bg-[var(--color-studio-white)] shadow-soft overflow-hidden group transition-all"
            style={{ opacity: 0 }}
        >
            <div className="flex flex-col lg:flex-row">
                {/* Image Section */}
                <div className="lg:w-3/5 h-[350px] lg:h-[450px] overflow-hidden relative">
                    {property.image_url ? (
                        <img
                            alt={property.title}
                            className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
                            src={property.image_url}
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                            <MaterialIcon name="apartment" className="text-slate-400" size="64px" />
                        </div>
                    )}
                    <div className="absolute bottom-0 left-0 p-8 lg:p-10 bg-gradient-to-t from-black/40 to-transparent w-full">
                        <div className="text-white">
                            <p className="text-[10px] font-bold uppercase tracking-[0.3em] mb-2 opacity-80">Featured Listing</p>
                            <h2 className="font-serif text-2xl lg:text-3xl italic">{property.title}</h2>
                        </div>
                    </div>
                </div>

                {/* Details Section */}
                <div className="lg:w-2/5 p-8 lg:p-10 flex flex-col justify-between bg-[var(--color-studio-white)]">
                    <div className="space-y-6">
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-2">Location</p>
                            <p className="text-sm font-medium text-[var(--color-text-main)]">{property.location}</p>
                        </div>
                        <div className="h-px bg-[var(--color-border-subtle)] w-full"></div>
                        <div className="grid grid-cols-2 gap-y-6">
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1">Asking Price</p>
                                <p className="text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {property.price.toLocaleString()} <span className="text-sm text-[var(--color-text-muted-studio)]">EGP</span>
                                </p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1">Sq. Footage</p>
                                <p className="text-lg font-semibold tracking-tight text-[var(--color-text-main)]">{property.size_sqm}</p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1">Beds / Baths</p>
                                <p className="text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {property.bedrooms} / {property.bathrooms || 2}
                                </p>
                            </div>
                            <div>
                                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1">ROI Est.</p>
                                <p className="text-lg font-semibold tracking-tight text-emerald-600">
                                    {projectedGrowth ? `${projectedGrowth}%` : 'N/A'}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="pt-8 lg:pt-10 flex gap-4">
                        <button
                            onClick={onRequestDetails}
                            className="flex-1 bg-[var(--color-studio-accent)] text-white py-4 text-[11px] font-bold uppercase tracking-widest hover:opacity-90 transition-opacity"
                        >
                            Request Prospectus
                        </button>
                        <button
                            onClick={onBookmark}
                            className="size-12 border border-[var(--color-border-subtle)] flex items-center justify-center hover:bg-[var(--color-studio-gray)] transition-colors"
                        >
                            <Bookmark size={20} className="text-[var(--color-text-muted-studio)]" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Appreciation Chart */}
            {projectedGrowth && (
            <div className="px-8 lg:px-10 py-8 lg:py-10 border-t border-[var(--color-border-subtle)] bg-[var(--color-studio-white)]">
                <div className="flex justify-between items-center mb-6 lg:mb-8">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)]">Appreciation Projection (5Y)</p>
                    <p className="text-[11px] font-medium text-[var(--color-text-main)]">+{projectedGrowth}% Compound Growth</p>
                </div>
                <div className="h-24 lg:h-32 w-full relative">
                    <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 800 100">
                        <line stroke="#E9ECEF" strokeWidth="1" x1="0" x2="800" y1="100" y2="100"></line>
                        <path
                            d="M0,90 C150,85 250,70 400,60 C550,50 650,20 800,10"
                            fill="none"
                            stroke="#2D3436"
                            strokeLinecap="round"
                            strokeWidth="1.5"
                        ></path>
                        <circle cx="0" cy="90" fill="#2D3436" r="2.5"></circle>
                        <circle cx="400" cy="60" fill="#2D3436" r="2.5"></circle>
                        <circle cx="800" cy="10" fill="#2D3436" r="3.5"></circle>
                    </svg>
                    <div className="flex justify-between mt-4 text-[10px] text-[var(--color-text-muted-studio)] font-medium tracking-widest">
                        <span>2024</span>
                        <span>2026</span>
                        <span>2028</span>
                    </div>
                </div>
            </div>
            )}
        </motion.div>
    );
}

// ============================================
// SIDEBAR COMPONENT
// ============================================

function Sidebar({
    onNewSession,
    isRTL
}: {
    onNewSession: () => void;
    isRTL: boolean;
}) {
    return (
        <aside className="w-64 flex-none bg-[var(--color-studio-white)] border-r border-[var(--color-border-subtle)] hidden lg:flex flex-col">
            <div className="p-8">
                <button
                    onClick={onNewSession}
                    className="w-full text-left py-2 px-0 border-b border-[var(--color-studio-accent)]/10 hover:border-[var(--color-studio-accent)] transition-all flex items-center justify-between group"
                >
                    <span className="text-[11px] font-bold uppercase tracking-widest text-[var(--color-text-main)]">
                        {isRTL ? 'محادثة جديدة' : 'New Session'}
                    </span>
                    <MaterialIcon name="east" className="text-sm group-hover:translate-x-1 transition-transform text-[var(--color-text-main)]" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-8 space-y-10 pb-8">
                <div>
                    <h3 className="text-[10px] font-bold text-[var(--color-text-muted-studio)] uppercase tracking-[0.2em] mb-6">
                        {isRTL ? 'السجل الأخير' : 'Recent History'}
                    </h3>
                    <div className="flex flex-col gap-5">
                        <p className="text-xs text-[var(--color-text-muted-studio)] italic">
                            {isRTL ? 'لا توجد محادثات سابقة' : 'No previous conversations'}
                        </p>
                    </div>
                </div>
            </div>

            <div className="p-8 border-t border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-4 text-[var(--color-text-muted-studio)]">
                    <button className="hover:text-[var(--color-text-main)] transition-colors">
                        <MaterialIcon name="settings" size="20px" />
                    </button>
                    <button className="hover:text-[var(--color-text-main)] transition-colors">
                        <MaterialIcon name="help_outline" size="20px" />
                    </button>
                </div>
            </div>
        </aside>
    );
}

// ============================================
// CONTEXTUAL INSIGHTS PANE
// ============================================

function ContextualInsights({
    property,
    aiInsight,
    visualizations,
    isRTL
}: {
    property: Property | null;
    aiInsight: string | null;
    visualizations: any[];
    isRTL: boolean;
}) {
    const paneRef = useRef<HTMLDivElement>(null);
    const { displayedText: typedInsight, isComplete } = useTypewriter(aiInsight || '', 15);

    useEffect(() => {
        if (paneRef.current && (property || aiInsight || visualizations.length > 0)) {
            anime({
                targets: paneRef.current.querySelectorAll('.insight-item'),
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(100, { start: 200 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [property, aiInsight, visualizations]);

    const hasContent = property || aiInsight || visualizations.length > 0;

    return (
        <aside className="w-80 flex-none border-l border-[var(--color-border-subtle)] bg-[var(--color-studio-white)] hidden xl:flex flex-col">
            <div className="p-6 lg:p-8 border-b border-[var(--color-border-subtle)]">
                <h2 className="text-[11px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-main)] flex items-center gap-2">
                    <MaterialIcon name="location_searching" size="18px" />
                    {isRTL ? 'رؤى السياق' : 'Contextual Insights'}
                </h2>
            </div>

            <div ref={paneRef} className="flex-1 overflow-y-auto p-6 lg:p-8 space-y-8">
                {hasContent ? (
                    <>
                        {/* Property Location Map Placeholder */}
                        {property && (
                            <div className="insight-item space-y-4" style={{ opacity: 0 }}>
                                <div className="aspect-square bg-[var(--color-studio-gray)] rounded-sm overflow-hidden relative border border-[var(--color-border-subtle)]">
                                    <div className="w-full h-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                                        <div className="text-center">
                                            <MaterialIcon name="map" className="text-slate-300" size="48px" />
                                            <p className="text-xs text-slate-400 mt-2">{property.location}</p>
                                        </div>
                                    </div>
                                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                                        <div className="size-3 bg-[var(--color-studio-accent)] rounded-full border-2 border-white shadow-sm"></div>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted-studio)]">
                                        {property.location?.split(',')[0] || 'Location'}
                                    </span>
                                    <a className="text-[10px] underline uppercase tracking-widest text-[var(--color-text-main)]" href="#">
                                        {isRTL ? 'عرض الخريطة' : 'Map View'}
                                    </a>
                                </div>
                            </div>
                        )}

                        {/* Market Indicators */}
                        {property && (
                            <div className="insight-item space-y-6" style={{ opacity: 0 }}>
                                <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)]">
                                    {isRTL ? 'مؤشرات السوق' : 'Market Indicators'}
                                </h3>
                                <div className="space-y-4">
                                    <div className="flex justify-between items-baseline">
                                        <span className="text-xs text-[var(--color-text-muted-studio)]">
                                            {isRTL ? 'السعر / م²' : 'Price / SQM'}
                                        </span>
                                        <span className="text-sm font-semibold tracking-tight text-[var(--color-text-main)]">
                                            {property.size_sqm > 0 ? Math.round(property.price / property.size_sqm).toLocaleString() : '—'}
                                        </span>
                                    </div>
                                    {property.roi && (
                                        <div className="flex justify-between items-baseline">
                                            <span className="text-xs text-[var(--color-text-muted-studio)]">
                                                {isRTL ? 'العائد المتوقع' : 'Expected ROI'}
                                            </span>
                                            <span className="text-sm font-semibold tracking-tight text-[var(--color-text-main)]">
                                                {property.roi}%
                                            </span>
                                        </div>
                                    )}
                                    {property.wolf_score && (
                                        <div className="flex justify-between items-baseline">
                                            <span className="text-xs text-[var(--color-text-muted-studio)]">Wolf Score</span>
                                            <span className="text-sm font-semibold tracking-tight text-[var(--color-text-main)]">
                                                {property.wolf_score}/100
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Visualizations from AI */}
                        {visualizations.length > 0 && (
                            <div className="insight-item space-y-4" style={{ opacity: 0 }}>
                                <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-text-muted-studio)]">
                                    {isRTL ? 'التحليلات' : 'Analytics'}
                                </h3>
                                {visualizations.slice(0, 2).map((viz, idx) => (
                                    <div key={idx} className="rounded-lg border border-[var(--color-border-subtle)] overflow-hidden">
                                        <VisualizationRenderer type={viz.type} data={viz.data} />
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* AI Insight */}
                        {aiInsight && (
                            <div className="insight-item p-6 bg-[var(--color-studio-gray)] border border-[var(--color-border-subtle)] space-y-4" style={{ opacity: 0 }}>
                                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--color-studio-accent)]">
                                    {isRTL ? 'رؤية الذكاء الاصطناعي' : 'AI Insight'}
                                </p>
                                <p className="text-xs leading-relaxed text-[var(--color-text-muted-studio)] font-medium">
                                    {typedInsight}
                                    {!isComplete && <span className="inline-block w-0.5 h-3 bg-[var(--color-studio-accent)] ml-0.5 animate-pulse" />}
                                </p>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12">
                        <div className="size-16 rounded-2xl bg-[var(--color-studio-gray)] flex items-center justify-center mb-4">
                            <Sparkles size={28} className="text-[var(--color-text-muted-studio)]" />
                        </div>
                        <h3 className="text-sm font-medium text-[var(--color-text-main)] mb-2">
                            {isRTL ? 'ابدأ محادثة' : 'Start Chatting'}
                        </h3>
                        <p className="text-xs text-[var(--color-text-muted-studio)] max-w-[180px]">
                            {isRTL
                                ? 'اسأل عن العقارات وسيظهر التحليل هنا'
                                : 'Ask about properties and insights will appear here'}
                        </p>
                    </div>
                )}
            </div>
        </aside>
    );
}

// ============================================
// MAIN CHAT INTERFACE
// ============================================

export default function ChatInterface() {
    const { user, isAuthenticated, logout } = useAuth();
    const { language } = useLanguage();
    const { theme, toggleTheme } = useTheme();

    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`);
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);

    // First message state - for centered input animation
    const [hasStartedChat, setHasStartedChat] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false);

    // Contextual state - updated from AI responses
    const [contextProperty, setContextProperty] = useState<Property | null>(null);
    const [contextInsight, setContextInsight] = useState<string | null>(null);
    const [contextVisualizations, setContextVisualizations] = useState<any[]>([]);
    const [detectedAnalytics, setDetectedAnalytics] = useState<AnalyticsMatch[]>([]);

    // Refs for animations
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const welcomeRef = useRef<HTMLDivElement>(null);
    const centeredInputRef = useRef<HTMLDivElement>(null);
    const isRTL = language === 'ar';

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Extract insight from AI message
    const extractInsight = useCallback((content: string): string | null => {
        if (!content) return null;
        // Get first meaningful sentence as insight
        const sentences = content.split(/[.!؟]/);
        const insight = sentences.find(s => s.trim().length > 20);
        return insight?.trim() || null;
    }, []);

    // Real-time context extraction from AI response (debounced)
    const lastContextUpdate = useRef<number>(0);
    const updateContextFromResponse = useCallback((response: string) => {
        const now = Date.now();
        // Debounce to avoid too frequent updates (every 500ms)
        if (now - lastContextUpdate.current < 500) return;
        lastContextUpdate.current = now;

        // Extract areas mentioned
        const areaKeywords = ['التجمع', 'مدينتي', 'الشيخ زايد', 'العاصمة الإدارية', 'الساحل', 'New Cairo', 'Sheikh Zayed', 'Madinaty'];
        const mentionedAreas = areaKeywords.filter(area =>
            response.toLowerCase().includes(area.toLowerCase())
        );

        // Extract developers mentioned
        const developerKeywords = ['طلعت مصطفى', 'بالم هيلز', 'سوديك', 'TMG', 'Palm Hills', 'SODIC', 'Mountain View'];
        const mentionedDevelopers = developerKeywords.filter(dev =>
            response.toLowerCase().includes(dev.toLowerCase())
        );

        // If AI mentions specific context, update insight
        if (mentionedAreas.length > 0 || mentionedDevelopers.length > 0) {
            const insight = extractInsight(response);
            if (insight && insight.length > 30) {
                setContextInsight(insight);
            }
        }
    }, [extractInsight]);

    const handleSend = async () => {
        if (!input.trim() || isTyping || isTransitioning) return;

        // Detect analytics from user input (with defensive check)
        let analyticsMatches: AnalyticsMatch[] = [];
        try {
            if (analyticsEngine && typeof analyticsEngine.detectAnalytics === 'function') {
                analyticsMatches = analyticsEngine.detectAnalytics(input) || [];
            }
        } catch (e) {
            console.warn('Analytics detection failed:', e);
        }
        if (analyticsMatches.length > 0) {
            setDetectedAnalytics(analyticsMatches);
        }

        // Trigger animation on first message
        if (!hasStartedChat) {
            setIsTransitioning(true);

            // Animate the transition
            emptyChatToActiveTransition(
                welcomeRef.current,
                centeredInputRef.current,
                () => {
                    setHasStartedChat(true);
                    setIsTransitioning(false);
                }
            );

            // Small delay to let animation start
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        let analyticsContext = null;
        try {
            if (analyticsMatches.length > 0 && analyticsEngine && typeof analyticsEngine.buildAnalyticsContext === 'function') {
                analyticsContext = analyticsEngine.buildAnalyticsContext(analyticsMatches);
            }
        } catch (e) {
            console.warn('Analytics context build failed:', e);
        }

        const userMsg = {
            role: 'user',
            content: input,
            id: Date.now().toString(),
            analytics: analyticsContext
        };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, { role: 'amr', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => {
                    fullResponse += token;
                    setMessages(prev => prev.map(m =>
                        m.id === aiMsgId ? { ...m, content: fullResponse } : m
                    ));

                    // Real-time context extraction during streaming
                    updateContextFromResponse(fullResponse);
                },
                onToolStart: () => { },
                onToolEnd: () => { },
                onComplete: (data) => {
                    setMessages(prev => prev.map(m =>
                        m.id === aiMsgId ? {
                            ...m,
                            content: fullResponse,
                            properties: data.properties,
                            visualizations: data.ui_actions,
                            isTyping: false
                        } : m
                    ));

                    // Update contextual pane with AI response data
                    if (data.properties?.length > 0) {
                        setContextProperty(data.properties[0]);
                    }
                    if (data.ui_actions?.length > 0) {
                        setContextVisualizations(prev => [...prev, ...data.ui_actions]);
                    }
                    // Extract insight from response
                    const insight = extractInsight(fullResponse);
                    if (insight) {
                        setContextInsight(insight);
                    }

                    setIsTyping(false);
                },
                onError: () => {
                    setMessages(prev => prev.map(m =>
                        m.id === aiMsgId ? { ...m, content: fullResponse + '\n\n[Error]', isTyping: false } : m
                    ));
                    setIsTyping(false);
                }
            }, language === 'ar' ? 'ar' : 'auto');
        } catch {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleNewSession = () => {
        setMessages([]);
        setContextProperty(null);
        setContextInsight(null);
        setContextVisualizations([]);
        setDetectedAnalytics([]);
        setInput('');
        setIsTyping(false);
        setHasStartedChat(false);
        setIsTransitioning(false);
        setSessionId(`session-${Date.now()}`);
    };

    const getUserName = (): string => user?.full_name || user?.email?.split('@')[0] || 'User';

    // Get latest AI message for featured property
    const latestAiMessage = useMemo(() => {
        const aiMessages = messages.filter(m => m.role === 'amr' && !m.isTyping);
        return aiMessages.length > 0 ? aiMessages[aiMessages.length - 1] : null;
    }, [messages]);

    const featuredProperty = latestAiMessage?.properties?.[0] || null;

    return (
        <div className="bg-[var(--color-studio-gray)] text-[var(--color-text-main)] font-sans h-screen flex flex-col overflow-hidden">
            {/* Glass Header */}
            <header className="flex-none h-20 glass-header border-b border-[var(--color-border-subtle)] flex items-center justify-between px-6 lg:px-10 z-50">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                        <MaterialIcon name="adjust" className="text-2xl text-[var(--color-studio-accent)] font-light" />
                        <Link href="/" className="text-sm font-semibold tracking-[0.2em] uppercase text-[var(--color-text-main)]">
                            Osool <span className="font-light opacity-50">AI</span>
                        </Link>
                    </div>
                    <div className="h-4 w-px bg-[var(--color-border-subtle)] mx-2 hidden md:block"></div>
                    <div className="hidden md:flex items-center gap-2">
                        <div className="size-1.5 rounded-full bg-[var(--color-studio-accent)] animate-pulse"></div>
                        <span className="text-[11px] font-medium text-[var(--color-text-muted-studio)] tracking-wide uppercase">
                            {isRTL ? 'محرك الذكاء نشط' : 'AI Engine Active'}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-4 lg:gap-8">
                    <nav className="hidden md:flex items-center gap-6 lg:gap-8">
                        <Link href="/dashboard" className="text-[11px] font-semibold uppercase tracking-widest hover:text-[var(--color-studio-accent)] transition-colors text-[var(--color-text-muted-studio)] flex items-center gap-2">
                            <History size={14} />
                            {isRTL ? 'السجل' : 'History'}
                        </Link>
                    </nav>

                    <button
                        onClick={toggleTheme}
                        className="p-2 rounded-full border border-[var(--color-border-subtle)] hover:bg-[var(--color-studio-white)] transition-colors text-[var(--color-text-muted-studio)]"
                    >
                        <MaterialIcon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} size="18px" />
                    </button>

                    <button
                        onClick={handleNewSession}
                        className="hidden sm:flex px-4 py-2 rounded-full bg-[var(--color-studio-accent)] text-white text-[11px] font-bold uppercase tracking-widest hover:opacity-90 transition-opacity items-center gap-2"
                    >
                        <PlusCircle size={14} />
                        {isRTL ? 'جديد' : 'New'}
                    </button>

                    {isAuthenticated && (
                        <div className="relative">
                            <button
                                onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                className="size-10 rounded-full bg-cover bg-center border border-[var(--color-border-subtle)] hover:opacity-80 transition-opacity flex items-center justify-center text-[var(--color-text-muted-studio)]"
                            >
                                <User size={18} />
                            </button>
                            <AnimatePresence>
                                {isUserMenuOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className="absolute right-0 mt-2 w-56 rounded-xl bg-white border border-[var(--color-border-subtle)] shadow-xl z-[60]"
                                    >
                                        <div className="p-3 border-b border-[var(--color-border-subtle)]">
                                            <p className="text-sm font-medium text-[var(--color-text-main)]">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-[var(--color-text-muted-studio)]">{user?.email}</p>
                                        </div>
                                        <div className="p-2">
                                            <button
                                                onClick={() => setInvitationModalOpen(true)}
                                                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-[var(--color-studio-gray)] text-emerald-600"
                                            >
                                                <Gift size={16} /> {isRTL ? 'دعوة' : 'Invite'}
                                            </button>
                                            <button
                                                onClick={() => logout()}
                                                className="flex items-center gap-2 w-full px-3 py-2 text-sm rounded-lg hover:bg-red-50 text-red-500"
                                            >
                                                <LogOut size={16} /> {isRTL ? 'خروج' : 'Sign Out'}
                                            </button>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content Area */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left Sidebar */}
                <Sidebar onNewSession={handleNewSession} isRTL={isRTL} />

                {/* Main Chat Area */}
                <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-studio-gray)] relative">
                    {/* Empty State - Centered Welcome & Input */}
                    {!hasStartedChat && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
                            {/* Welcome Section - Animated out on first message */}
                            <div
                                ref={welcomeRef}
                                className={`text-center mb-10 transition-opacity ${isTransitioning ? 'pointer-events-none' : ''}`}
                            >
                                <div className="size-20 rounded-2xl bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] flex items-center justify-center mb-6 mx-auto shadow-soft">
                                    <Sparkles size={32} className="text-[var(--color-studio-accent)]" />
                                </div>
                                <h2 className="text-xl font-serif italic text-[var(--color-text-main)] mb-3">
                                    {isRTL ? 'أهلاً بك في أصول' : 'Welcome to Osool AI'}
                                </h2>
                                <p className="text-sm text-[var(--color-text-muted-studio)] max-w-md mb-8 mx-auto">
                                    {isRTL
                                        ? 'اسأل عن أي منطقة، مطور، أو نوع عقار وسأقدم لك تحليلات شاملة'
                                        : 'Ask about any area, developer, or property type and I\'ll provide comprehensive analytics'}
                                </p>
                                <div className="flex flex-wrap justify-center gap-3">
                                    {[
                                        { label: isRTL ? 'شقق في التجمع الخامس' : 'Apartments in New Cairo', icon: 'apartment' },
                                        { label: isRTL ? 'مشاريع طلعت مصطفى' : 'TMG Projects', icon: 'business' },
                                        { label: isRTL ? 'أفضل عائد استثماري' : 'Best ROI', icon: 'trending_up' },
                                    ].map((suggestion) => (
                                        <button
                                            key={suggestion.label}
                                            onClick={() => setInput(suggestion.label)}
                                            className="px-4 py-2 rounded-full bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] text-sm text-[var(--color-text-muted-studio)] hover:border-[var(--color-studio-accent)] hover:text-[var(--color-text-main)] transition-all flex items-center gap-2 shadow-soft"
                                        >
                                            <MaterialIcon name={suggestion.icon} size="16px" />
                                            {suggestion.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Centered Input */}
                            <div
                                ref={centeredInputRef}
                                className={`w-full max-w-2xl glass-input rounded-2xl p-4 shadow-soft ${isTransitioning ? 'opacity-0' : ''}`}
                            >
                                <div className="relative flex items-center border-b border-[var(--color-studio-accent)]/20 focus-within:border-[var(--color-studio-accent)] transition-all pb-2 px-1">
                                    <button className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                        <Plus size={20} />
                                    </button>
                                    <input
                                        value={input}
                                        onChange={e => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-4 placeholder:text-[var(--color-text-muted-studio)]/50 text-[var(--color-text-main)]"
                                        placeholder={isRTL ? 'اسأل عن العقارات أو السوق...' : 'Ask about properties, market trends...'}
                                        disabled={isTyping || isTransitioning}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                        autoFocus
                                    />
                                    <div className="flex items-center gap-2">
                                        <button className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                            <Mic size={20} />
                                        </button>
                                        <button
                                            onClick={handleSend}
                                            disabled={!input.trim() || isTyping || isTransitioning}
                                            className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors disabled:opacity-50"
                                        >
                                            <Send size={20} />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.2em] mt-4 opacity-50">
                                    {isRTL ? 'أصول AI • محرك تحليل العقارات المتقدم' : 'Osool AI • Advanced Real Estate Analytics Engine'}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Chat Messages Area - Shown after first message */}
                    <div className={`flex-1 overflow-y-auto px-4 py-8 md:px-12 lg:px-20 space-y-12 ${!hasStartedChat ? 'invisible' : ''}`}>
                        {messages.length > 0 && (
                            <>
                                {messages.map((msg, idx) => (
                                    <div key={msg.id || idx}>
                                        {msg.role === 'user' ? (
                                            /* User Message */
                                            <div className="flex justify-end">
                                                <div className="max-w-[80%] md:max-w-[60%] flex flex-col items-end">
                                                    <div className="bg-[var(--color-studio-white)] px-6 lg:px-8 py-4 lg:py-5 rounded-2xl border border-[var(--color-border-subtle)] shadow-soft">
                                                        <p className="text-[14px] leading-relaxed font-normal text-[var(--color-text-main)]" dir={isRTL ? 'rtl' : 'ltr'}>
                                                            {msg.content}
                                                        </p>
                                                    </div>
                                                    <span className="mt-3 text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted-studio)] opacity-40">
                                                        {getUserName()} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            </div>
                                        ) : (
                                            /* AI Message */
                                            <div className="space-y-6 max-w-4xl">
                                                <div className="flex gap-4 items-start">
                                                    <div className="size-6 mt-1 flex-none bg-[var(--color-studio-accent)] flex items-center justify-center rounded-sm">
                                                        <MaterialIcon name="auto_awesome" className="text-white" size="14px" />
                                                    </div>
                                                    <div className="space-y-6 flex-1">
                                                        <div className="prose prose-sm max-w-none">
                                                            {msg.isTyping && !msg.content ? (
                                                                <div className="flex items-center gap-2 text-[var(--color-text-muted-studio)]">
                                                                    <span className="animate-pulse">{isRTL ? 'جاري التحليل...' : 'Analyzing...'}</span>
                                                                </div>
                                                            ) : (
                                                                <>
                                                                    <div
                                                                        className="text-sm lg:text-base leading-relaxed text-[var(--color-text-main)]"
                                                                        dir={isRTL ? 'rtl' : 'ltr'}
                                                                    >
                                                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                                            {sanitizeContent(msg.content)}
                                                                        </ReactMarkdown>
                                                                    </div>
                                                                </>
                                                            )}
                                                        </div>

                                                        {/* Featured Property Card */}
                                                        {msg.properties?.length > 0 && (
                                                            <FeaturedPropertyCard
                                                                property={msg.properties[0]}
                                                                onRequestDetails={() => { }}
                                                                onBookmark={() => { }}
                                                            />
                                                        )}

                                                        {/* Inline Visualizations */}
                                                        {msg.visualizations?.length > 0 && (
                                                            <div className="space-y-4">
                                                                {msg.visualizations.map((viz: any, vidx: number) => (
                                                                    <div key={vidx} className="bg-[var(--color-studio-white)] rounded-xl border border-[var(--color-border-subtle)] overflow-hidden shadow-soft">
                                                                        <VisualizationRenderer type={viz.type} data={viz.data} />
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Input Area - Shown at bottom after first message */}
                    {hasStartedChat && (
                        <div className="p-4 lg:p-8 glass-input z-30">
                            <div className="max-w-3xl mx-auto">
                                <div className="relative flex items-center border-b border-[var(--color-studio-accent)]/20 focus-within:border-[var(--color-studio-accent)] transition-all pb-2 px-1">
                                    <button className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                        <Plus size={20} />
                                    </button>
                                    <input
                                        value={input}
                                        onChange={e => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-4 placeholder:text-[var(--color-text-muted-studio)]/50 text-[var(--color-text-main)]"
                                        placeholder={isRTL ? 'اسأل عن العقارات أو السوق...' : 'Ask about properties, market trends...'}
                                        disabled={isTyping}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                        autoFocus
                                    />
                                    <div className="flex items-center gap-2">
                                        <button className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                            <Mic size={20} />
                                        </button>
                                        <button
                                            onClick={handleSend}
                                            disabled={!input.trim() || isTyping}
                                            className="p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors disabled:opacity-50"
                                        >
                                            <Send size={20} />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.2em] mt-4 opacity-50">
                                    {isRTL ? 'أصول AI • محرك تحليل العقارات المتقدم' : 'Osool AI • Advanced Real Estate Analytics Engine'}
                                </p>
                            </div>
                        </div>
                    )}
                </main>

                {/* Right Contextual Pane */}
                <ContextualInsights
                    property={contextProperty}
                    aiInsight={contextInsight}
                    visualizations={contextVisualizations}
                    isRTL={isRTL}
                />
            </div>

            <InvitationModal isOpen={isInvitationModalOpen} onClose={() => setInvitationModalOpen(false)} />
        </div>
    );
}
