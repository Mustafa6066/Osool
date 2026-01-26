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
            className="bg-[var(--color-studio-white)] shadow-soft overflow-hidden group transition-all rounded-lg sm:rounded-none"
            style={{ opacity: 0 }}
        >
            <div className="flex flex-col lg:flex-row">
                {/* Image Section - Mobile Optimized */}
                <div className="lg:w-3/5 h-[200px] sm:h-[280px] lg:h-[400px] overflow-hidden relative">
                    {property.image_url ? (
                        <img
                            alt={property.title}
                            className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
                            src={property.image_url}
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                            <MaterialIcon name="apartment" className="text-slate-400" size="48px" />
                        </div>
                    )}
                    <div className="absolute bottom-0 left-0 p-4 sm:p-6 lg:p-10 bg-gradient-to-t from-black/50 to-transparent w-full">
                        <div className="text-white">
                            <p className="text-[8px] sm:text-[10px] font-bold uppercase tracking-[0.2em] sm:tracking-[0.3em] mb-1 sm:mb-2 opacity-80">Featured</p>
                            <h2 className="font-serif text-lg sm:text-2xl lg:text-3xl italic line-clamp-2">{property.title}</h2>
                        </div>
                    </div>
                </div>

                {/* Details Section - Mobile Optimized */}
                <div className="lg:w-2/5 p-4 sm:p-6 lg:p-10 flex flex-col justify-between bg-[var(--color-studio-white)]">
                    <div className="space-y-4 sm:space-y-6">
                        <div>
                            <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] sm:tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1 sm:mb-2">Location</p>
                            <p className="text-xs sm:text-sm font-medium text-[var(--color-text-main)] line-clamp-1">{property.location}</p>
                        </div>
                        <div className="h-px bg-[var(--color-border-subtle)] w-full"></div>
                        <div className="grid grid-cols-2 gap-3 sm:gap-y-6">
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">Price</p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {(property.price / 1000000).toFixed(1)}M <span className="text-xs text-[var(--color-text-muted-studio)]">EGP</span>
                                </p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">Size</p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">{property.size_sqm} m²</p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">Beds/Baths</p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {property.bedrooms}/{property.bathrooms || 2}
                                </p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">ROI</p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-emerald-600">
                                    {projectedGrowth ? `${projectedGrowth}%` : 'N/A'}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="pt-4 sm:pt-6 lg:pt-10 flex gap-2 sm:gap-4">
                        <button
                            onClick={onRequestDetails}
                            className="flex-1 bg-[var(--color-studio-accent)] text-white py-2.5 sm:py-3 lg:py-4 text-[10px] sm:text-[11px] font-bold uppercase tracking-wider sm:tracking-widest hover:opacity-90 transition-opacity active:scale-[0.98] rounded sm:rounded-none"
                        >
                            Details
                        </button>
                        <button
                            onClick={onBookmark}
                            className="size-10 sm:size-12 border border-[var(--color-border-subtle)] flex items-center justify-center hover:bg-[var(--color-studio-gray)] transition-colors rounded sm:rounded-none"
                        >
                            <Bookmark size={18} className="text-[var(--color-text-muted-studio)]" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Appreciation Chart - Hidden on very small screens */}
            {projectedGrowth && (
            <div className="hidden sm:block px-4 sm:px-6 lg:px-10 py-4 sm:py-6 lg:py-10 border-t border-[var(--color-border-subtle)] bg-[var(--color-studio-white)]">
                <div className="flex justify-between items-center mb-4 sm:mb-6 lg:mb-8">
                    <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] sm:tracking-[0.2em] text-[var(--color-text-muted-studio)]">5Y Projection</p>
                    <p className="text-[10px] sm:text-[11px] font-medium text-[var(--color-text-main)]">+{projectedGrowth}%</p>
                </div>
                <div className="h-16 sm:h-24 lg:h-32 w-full relative">
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
                    <div className="flex justify-between mt-2 sm:mt-4 text-[9px] sm:text-[10px] text-[var(--color-text-muted-studio)] font-medium tracking-wider sm:tracking-widest">
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
// CONTEXTUAL INSIGHTS PANE - Minimal & Animated
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
    const contentRef = useRef<HTMLDivElement>(null);
    const { displayedText: typedInsight, isComplete } = useTypewriter(aiInsight || '', 20);
    const [expandedViz, setExpandedViz] = useState<number | null>(null);

    // Animate on content change with smooth stagger
    useEffect(() => {
        if (contentRef.current) {
            const items = contentRef.current.querySelectorAll('.insight-item');
            if (items.length > 0) {
                anime({
                    targets: items,
                    opacity: [0, 1],
                    translateY: [15, 0],
                    scale: [0.98, 1],
                    delay: anime.stagger(80, { start: 100 }),
                    easing: 'easeOutCubic',
                    duration: 400,
                });
            }
        }
    }, [property, aiInsight, visualizations]);

    // Animate visualization expand/collapse
    const toggleViz = (idx: number) => {
        setExpandedViz(expandedViz === idx ? null : idx);
    };

    const hasContent = property || aiInsight || visualizations.length > 0;

    // Get readable visualization name
    const getVizName = (type: string): string => {
        const names: Record<string, string> = {
            'investment_scorecard': isRTL ? 'بطاقة الاستثمار' : 'Investment Score',
            'comparison_matrix': isRTL ? 'مقارنة العقارات' : 'Property Comparison',
            'inflation_killer': isRTL ? 'حماية من التضخم' : 'Inflation Protection',
            'payment_timeline': isRTL ? 'جدول السداد' : 'Payment Schedule',
            'market_trend_chart': isRTL ? 'اتجاه السوق' : 'Market Trend',
            'area_analysis': isRTL ? 'تحليل المنطقة' : 'Area Analysis',
            'developer_analysis': isRTL ? 'تحليل المطور' : 'Developer Profile',
            'roi_calculator': isRTL ? 'حاسبة العائد' : 'ROI Calculator',
            'property_type_analysis': isRTL ? 'أنواع العقارات' : 'Property Types',
            'payment_plan_analysis': isRTL ? 'خطط السداد' : 'Payment Plans',
            'resale_vs_developer': isRTL ? 'ريسيل vs مطور' : 'Resale vs Developer',
        };
        return names[type] || type?.replace(/_/g, ' ');
    };

    // Get visualization icon
    const getVizIcon = (type: string): string => {
        const icons: Record<string, string> = {
            'investment_scorecard': 'analytics',
            'comparison_matrix': 'compare_arrows',
            'inflation_killer': 'shield',
            'payment_timeline': 'event_note',
            'market_trend_chart': 'show_chart',
            'area_analysis': 'pin_drop',
            'developer_analysis': 'domain',
            'roi_calculator': 'calculate',
            'property_type_analysis': 'category',
            'payment_plan_analysis': 'credit_card',
            'resale_vs_developer': 'swap_horiz',
        };
        return icons[type] || 'auto_awesome';
    };

    return (
        <aside className="w-80 flex-none border-l border-[var(--color-border-subtle)] bg-[var(--color-studio-white)] hidden xl:flex flex-col overflow-hidden">
            {/* Header */}
            <div className="p-5 border-b border-[var(--color-border-subtle)] flex items-center gap-2">
                <div className="size-6 rounded-md bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center">
                    <MaterialIcon name="insights" size="14px" className="text-emerald-600" />
                </div>
                <h2 className="text-xs font-semibold text-[var(--color-text-main)]">
                    {isRTL ? 'رؤى ذكية' : 'Smart Insights'}
                </h2>
                {hasContent && (
                    <span className="ml-auto text-[9px] px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded-full font-medium">
                        Live
                    </span>
                )}
            </div>

            {/* Scrollable Content */}
            <div ref={paneRef} className="flex-1 overflow-y-auto scrollbar-hide">
                <div ref={contentRef} className="p-4 space-y-4">
                    {hasContent ? (
                        <>
                            {/* AI Insight - First Priority */}
                            {aiInsight && (
                                <div className="insight-item p-4 rounded-xl bg-gradient-to-br from-[var(--color-studio-gray)] to-[var(--color-studio-gray)]/50 border border-[var(--color-border-subtle)]">
                                    <div className="flex items-center gap-2 mb-3">
                                        <div className="size-5 rounded-full bg-[var(--color-studio-accent)] flex items-center justify-center">
                                            <MaterialIcon name="auto_awesome" size="10px" className="text-white" />
                                        </div>
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-studio-accent)]">
                                            {isRTL ? 'رؤية AMR' : 'AMR Insight'}
                                        </span>
                                    </div>
                                    <p className="text-xs leading-relaxed text-[var(--color-text-main)]" dir={isRTL ? 'rtl' : 'ltr'}>
                                        {typedInsight}
                                        {!isComplete && <span className="inline-block w-0.5 h-3 bg-emerald-500 ml-0.5 animate-pulse" />}
                                    </p>
                                </div>
                            )}

                            {/* Property Quick Stats */}
                            {property && (
                                <div className="insight-item rounded-xl border border-[var(--color-border-subtle)] overflow-hidden">
                                    <div className="p-3 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800/50 dark:to-slate-900/50 border-b border-[var(--color-border-subtle)]">
                                        <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted-studio)]">
                                            {isRTL ? 'ملخص العقار' : 'Property Summary'}
                                        </p>
                                    </div>
                                    <div className="p-3 grid grid-cols-2 gap-3">
                                        <div className="text-center p-2 rounded-lg bg-[var(--color-studio-gray)]/50">
                                            <p className="text-lg font-bold text-[var(--color-text-main)]">
                                                {property.size_sqm > 0 ? Math.round(property.price / property.size_sqm / 1000) : '—'}K
                                            </p>
                                            <p className="text-[9px] text-[var(--color-text-muted-studio)] uppercase tracking-wide">
                                                {isRTL ? 'جنيه/م²' : 'EGP/m²'}
                                            </p>
                                        </div>
                                        <div className="text-center p-2 rounded-lg bg-[var(--color-studio-gray)]/50">
                                            <p className="text-lg font-bold text-emerald-600">
                                                {property.wolf_score || '—'}
                                            </p>
                                            <p className="text-[9px] text-[var(--color-text-muted-studio)] uppercase tracking-wide">
                                                Wolf Score
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Analytics Cards - Expandable */}
                            {visualizations.length > 0 && (
                                <div className="insight-item space-y-2">
                                    <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-text-muted-studio)] px-1">
                                        {isRTL ? 'تحليلات' : 'Analytics'} ({visualizations.length})
                                    </p>

                                    {visualizations.map((viz, idx) => (
                                        <div
                                            key={idx}
                                            className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden transition-all duration-300"
                                        >
                                            {/* Card Header - Clickable */}
                                            <button
                                                onClick={() => toggleViz(idx)}
                                                className="w-full p-3 flex items-center gap-2 hover:bg-[var(--color-studio-gray)]/50 transition-colors"
                                            >
                                                <div className={`size-7 rounded-lg flex items-center justify-center transition-colors ${
                                                    expandedViz === idx
                                                        ? 'bg-emerald-500/20 text-emerald-600'
                                                        : 'bg-[var(--color-studio-gray)] text-[var(--color-text-muted-studio)]'
                                                }`}>
                                                    <MaterialIcon name={getVizIcon(viz.type)} size="14px" />
                                                </div>
                                                <div className="flex-1 text-left">
                                                    <p className="text-xs font-medium text-[var(--color-text-main)]">
                                                        {getVizName(viz.type)}
                                                    </p>
                                                    {viz.priority >= 9 && (
                                                        <span className="text-[8px] text-amber-600 font-medium">
                                                            {isRTL ? 'موصى به' : 'Recommended'}
                                                        </span>
                                                    )}
                                                </div>
                                                <MaterialIcon
                                                    name={expandedViz === idx ? 'expand_less' : 'expand_more'}
                                                    size="18px"
                                                    className="text-[var(--color-text-muted-studio)]"
                                                />
                                            </button>

                                            {/* Expanded Visualization */}
                                            <AnimatePresence>
                                                {expandedViz === idx && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: 'auto', opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        transition={{ duration: 0.2, ease: 'easeInOut' }}
                                                        className="border-t border-[var(--color-border-subtle)] overflow-hidden"
                                                    >
                                                        <div className="max-h-80 overflow-y-auto">
                                                            <VisualizationRenderer type={viz.type} data={viz.data} />
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        /* Empty State */
                        <div className="flex flex-col items-center justify-center h-64 text-center">
                            <div className="size-12 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center mb-3">
                                <Sparkles size={20} className="text-[var(--color-text-muted-studio)]" />
                            </div>
                            <h3 className="text-sm font-medium text-[var(--color-text-main)] mb-1">
                                {isRTL ? 'ابدأ محادثة' : 'Start a Conversation'}
                            </h3>
                            <p className="text-[11px] text-[var(--color-text-muted-studio)] max-w-[160px]">
                                {isRTL
                                    ? 'اسأل AMR وسيظهر التحليل هنا'
                                    : 'Ask AMR and insights appear here'}
                            </p>
                        </div>
                    )}
                </div>
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

                    // ═══════════════════════════════════════════════════════════
                    // SMART ANALYTICS LAYER - Wolf Brain Integration
                    // The backend sends prioritized ui_actions (sorted by priority)
                    // Show the most relevant analytics proactively
                    // ═══════════════════════════════════════════════════════════

                    // Update contextual pane with top property
                    if (data.properties?.length > 0) {
                        setContextProperty(data.properties[0]);
                    }

                    // Proactively show top analytics from Wolf Brain
                    // Replace (not append) to show most relevant for current context
                    if (data.ui_actions?.length > 0) {
                        // Take top 3 highest priority analytics
                        const prioritizedAnalytics = data.ui_actions
                            .sort((a: any, b: any) => (b.priority || 0) - (a.priority || 0))
                            .slice(0, 3);
                        setContextVisualizations(prioritizedAnalytics);
                    }

                    // Extract insight from response for AI summary
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
            {/* Glass Header - Mobile Optimized */}
            <header className="flex-none h-14 sm:h-16 lg:h-20 glass-header border-b border-[var(--color-border-subtle)] flex items-center justify-between px-3 sm:px-6 lg:px-10 z-50">
                <div className="flex items-center gap-2 sm:gap-4 lg:gap-6">
                    <div className="flex items-center gap-1.5 sm:gap-2">
                        <MaterialIcon name="adjust" className="text-xl sm:text-2xl text-[var(--color-studio-accent)] font-light" />
                        <Link href="/" className="text-xs sm:text-sm font-semibold tracking-[0.15em] sm:tracking-[0.2em] uppercase text-[var(--color-text-main)]">
                            Osool <span className="font-light opacity-50">AI</span>
                        </Link>
                    </div>
                    <div className="h-4 w-px bg-[var(--color-border-subtle)] mx-1 sm:mx-2 hidden sm:block"></div>
                    <div className="hidden sm:flex items-center gap-1.5 sm:gap-2">
                        <div className="size-1.5 rounded-full bg-[var(--color-studio-accent)] animate-pulse"></div>
                        <span className="text-[10px] sm:text-[11px] font-medium text-[var(--color-text-muted-studio)] tracking-wide uppercase">
                            {isRTL ? 'نشط' : 'Active'}
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-2 sm:gap-4 lg:gap-8">
                    <nav className="hidden md:flex items-center gap-4 lg:gap-8">
                        <Link href="/dashboard" className="text-[11px] font-semibold uppercase tracking-widest hover:text-[var(--color-studio-accent)] transition-colors text-[var(--color-text-muted-studio)] flex items-center gap-2">
                            <History size={14} />
                            {isRTL ? 'السجل' : 'History'}
                        </Link>
                    </nav>

                    <button
                        onClick={toggleTheme}
                        className="p-1.5 sm:p-2 rounded-full border border-[var(--color-border-subtle)] hover:bg-[var(--color-studio-white)] transition-colors text-[var(--color-text-muted-studio)]"
                    >
                        <MaterialIcon name={theme === 'dark' ? 'light_mode' : 'dark_mode'} size="16px" />
                    </button>

                    <button
                        onClick={handleNewSession}
                        className="p-1.5 sm:px-4 sm:py-2 rounded-full bg-[var(--color-studio-accent)] text-white text-[10px] sm:text-[11px] font-bold uppercase tracking-widest hover:opacity-90 transition-opacity flex items-center gap-1 sm:gap-2"
                    >
                        <PlusCircle size={14} />
                        <span className="hidden sm:inline">{isRTL ? 'جديد' : 'New'}</span>
                    </button>

                    {isAuthenticated && (
                        <div className="relative">
                            <button
                                onClick={() => setUserMenuOpen(!isUserMenuOpen)}
                                className="size-8 sm:size-10 rounded-full bg-cover bg-center border border-[var(--color-border-subtle)] hover:opacity-80 transition-opacity flex items-center justify-center text-[var(--color-text-muted-studio)]"
                            >
                                <User size={16} />
                            </button>
                            <AnimatePresence>
                                {isUserMenuOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 10 }}
                                        className="absolute right-0 mt-2 w-48 sm:w-56 rounded-xl bg-white dark:bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] shadow-xl z-[60]"
                                    >
                                        <div className="p-3 border-b border-[var(--color-border-subtle)]">
                                            <p className="text-sm font-medium text-[var(--color-text-main)]">{user?.full_name || 'User'}</p>
                                            <p className="text-xs text-[var(--color-text-muted-studio)] truncate">{user?.email}</p>
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
                    {/* Empty State - Centered Welcome & Input - Mobile Optimized */}
                    {!hasStartedChat && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center px-3 sm:px-4 py-4 overflow-y-auto">
                            {/* Welcome Section - Animated out on first message */}
                            <div
                                ref={welcomeRef}
                                className={`text-center mb-6 sm:mb-10 transition-opacity ${isTransitioning ? 'pointer-events-none' : ''}`}
                            >
                                <div className="size-14 sm:size-20 rounded-xl sm:rounded-2xl bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] flex items-center justify-center mb-4 sm:mb-6 mx-auto shadow-soft">
                                    <Sparkles size={24} className="sm:hidden text-[var(--color-studio-accent)]" />
                                    <Sparkles size={32} className="hidden sm:block text-[var(--color-studio-accent)]" />
                                </div>
                                <h2 className="text-lg sm:text-xl font-serif italic text-[var(--color-text-main)] mb-2 sm:mb-3">
                                    {isRTL ? 'أهلاً بك في أصول' : 'Welcome to Osool AI'}
                                </h2>
                                <p className="text-xs sm:text-sm text-[var(--color-text-muted-studio)] max-w-xs sm:max-w-md mb-6 sm:mb-8 mx-auto px-2">
                                    {isRTL
                                        ? 'اسأل عن أي منطقة أو مطور وسأقدم لك تحليلات شاملة'
                                        : 'Ask about any area, developer, or property type for analytics'}
                                </p>
                                <div className="flex flex-wrap justify-center gap-2 sm:gap-3 px-2">
                                    {[
                                        { label: isRTL ? 'شقق التجمع' : 'New Cairo', icon: 'apartment' },
                                        { label: isRTL ? 'طلعت مصطفى' : 'TMG', icon: 'business' },
                                        { label: isRTL ? 'أفضل عائد' : 'Best ROI', icon: 'trending_up' },
                                    ].map((suggestion) => (
                                        <button
                                            key={suggestion.label}
                                            onClick={() => setInput(suggestion.label)}
                                            className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] text-xs sm:text-sm text-[var(--color-text-muted-studio)] hover:border-[var(--color-studio-accent)] hover:text-[var(--color-text-main)] transition-all flex items-center gap-1.5 sm:gap-2 shadow-soft active:scale-95"
                                        >
                                            <MaterialIcon name={suggestion.icon} size="14px" />
                                            {suggestion.label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Centered Input - Mobile Optimized */}
                            <div
                                ref={centeredInputRef}
                                className={`w-full max-w-2xl glass-input rounded-xl sm:rounded-2xl p-3 sm:p-4 shadow-soft mx-2 ${isTransitioning ? 'opacity-0' : ''}`}
                            >
                                <div className="relative flex items-center border-b border-[var(--color-studio-accent)]/20 focus-within:border-[var(--color-studio-accent)] transition-all pb-2 px-0.5 sm:px-1">
                                    <button className="p-1.5 sm:p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors flex-shrink-0">
                                        <Plus size={18} />
                                    </button>
                                    <input
                                        value={input}
                                        onChange={e => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        className="flex-1 min-w-0 bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-3 sm:py-4 placeholder:text-[var(--color-text-muted-studio)]/50 text-[var(--color-text-main)]"
                                        placeholder={isRTL ? 'اسأل عن العقارات...' : 'Ask about properties...'}
                                        disabled={isTyping || isTransitioning}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                        autoFocus
                                    />
                                    <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
                                        <button className="hidden sm:block p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                            <Mic size={18} />
                                        </button>
                                        <button
                                            onClick={handleSend}
                                            disabled={!input.trim() || isTyping || isTransitioning}
                                            className="p-1.5 sm:p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors disabled:opacity-50"
                                        >
                                            <Send size={18} />
                                        </button>
                                    </div>
                                </div>
                                <p className="text-[8px] sm:text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.15em] sm:tracking-[0.2em] mt-3 sm:mt-4 opacity-50">
                                    {isRTL ? 'أصول AI • محرك تحليل العقارات' : 'Osool AI • Real Estate Analytics'}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Chat Messages Area - Mobile Optimized */}
                    <div className={`flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-8 md:px-8 lg:px-16 xl:px-20 space-y-6 sm:space-y-8 lg:space-y-12 ${!hasStartedChat ? 'invisible' : ''}`}>
                        {messages.length > 0 && (
                            <>
                                {messages.map((msg, idx) => (
                                    <div key={msg.id || idx}>
                                        {msg.role === 'user' ? (
                                            /* User Message - Mobile Optimized */
                                            <div className="flex justify-end">
                                                <div className="max-w-[90%] sm:max-w-[80%] md:max-w-[70%] lg:max-w-[60%] flex flex-col items-end">
                                                    <div className="bg-[var(--color-studio-white)] px-4 sm:px-6 lg:px-8 py-3 sm:py-4 lg:py-5 rounded-xl sm:rounded-2xl border border-[var(--color-border-subtle)] shadow-soft">
                                                        <p className="text-[13px] sm:text-[14px] leading-relaxed font-normal text-[var(--color-text-main)]" dir={isRTL ? 'rtl' : 'ltr'}>
                                                            {msg.content}
                                                        </p>
                                                    </div>
                                                    <span className="mt-2 sm:mt-3 text-[9px] sm:text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted-studio)] opacity-40">
                                                        {getUserName()} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            </div>
                                        ) : (
                                            /* AI Message - Mobile Optimized */
                                            <div className="space-y-4 sm:space-y-6 max-w-4xl">
                                                <div className="flex gap-2 sm:gap-4 items-start">
                                                    <div className="size-5 sm:size-6 mt-0.5 sm:mt-1 flex-none bg-[var(--color-studio-accent)] flex items-center justify-center rounded-sm">
                                                        <MaterialIcon name="auto_awesome" className="text-white" size="12px" />
                                                    </div>
                                                    <div className="space-y-4 sm:space-y-6 flex-1 min-w-0">
                                                        <div className="prose prose-sm max-w-none">
                                                            {msg.isTyping && !msg.content ? (
                                                                <div className="flex items-center gap-2 text-[var(--color-text-muted-studio)]">
                                                                    <span className="animate-pulse text-sm">{isRTL ? 'جاري التحليل...' : 'Analyzing...'}</span>
                                                                </div>
                                                            ) : (
                                                                <>
                                                                    <div
                                                                        className="text-[13px] sm:text-sm lg:text-base leading-relaxed text-[var(--color-text-main)]"
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

                                                        {/* Inline Visualizations - Mobile Optimized */}
                                                        {msg.visualizations?.length > 0 && (
                                                            <div className="space-y-3 sm:space-y-4 -mx-1 sm:mx-0">
                                                                {msg.visualizations.map((viz: any, vidx: number) => (
                                                                    <div key={vidx} className="bg-[var(--color-studio-white)] rounded-lg sm:rounded-xl border border-[var(--color-border-subtle)] overflow-hidden shadow-soft overflow-x-auto">
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

                    {/* Input Area - Mobile Optimized */}
                    {hasStartedChat && (
                        <div className="p-2 sm:p-4 lg:p-6 glass-input z-30 safe-area-bottom">
                            <div className="max-w-3xl mx-auto">
                                <div className="relative flex items-center border-b border-[var(--color-studio-accent)]/20 focus-within:border-[var(--color-studio-accent)] transition-all pb-1.5 sm:pb-2 px-0.5 sm:px-1">
                                    <button className="p-1.5 sm:p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors flex-shrink-0">
                                        <Plus size={18} />
                                    </button>
                                    <input
                                        value={input}
                                        onChange={e => setInput(e.target.value)}
                                        onKeyDown={handleKeyDown}
                                        className="flex-1 min-w-0 bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-2.5 sm:py-3 lg:py-4 placeholder:text-[var(--color-text-muted-studio)]/50 text-[var(--color-text-main)]"
                                        placeholder={isRTL ? 'اسأل عن العقارات...' : 'Ask about properties...'}
                                        disabled={isTyping}
                                        dir={isRTL ? 'rtl' : 'ltr'}
                                        autoFocus
                                    />
                                    <div className="flex items-center gap-0.5 sm:gap-2 flex-shrink-0">
                                        <button className="hidden sm:block p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors">
                                            <Mic size={18} />
                                        </button>
                                        <button
                                            onClick={handleSend}
                                            disabled={!input.trim() || isTyping}
                                            className="p-1.5 sm:p-2 text-[var(--color-text-muted-studio)] hover:text-[var(--color-studio-accent)] transition-colors disabled:opacity-50 active:scale-95"
                                        >
                                            <Send size={18} />
                                        </button>
                                    </div>
                                </div>
                                <p className="hidden sm:block text-[8px] sm:text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.15em] sm:tracking-[0.2em] mt-2 sm:mt-3 opacity-50">
                                    {isRTL ? 'أصول AI • محرك تحليل العقارات' : 'Osool AI • Real Estate Analytics'}
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
