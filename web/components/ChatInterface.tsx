'use client';

import { useState, useMemo, useCallback, useEffect, useRef, type HTMLAttributes, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
// import rehypeRaw from 'rehype-raw'; // DISABLED - kept for reference
import DOMPurify from 'dompurify';
import Link from 'next/link';
import anime from 'animejs';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTheme } from '@/contexts/ThemeContext';
import { streamChat } from '@/lib/api';
import { trackChatMessage, trackChatSessionEnd } from '@/lib/orchestrator';
import { getAnonymousId } from '@/lib/session';
import { getOrchestratorContext } from '@/lib/api-secure';
import { analyticsEngine, type AnalyticsMatch } from '@/lib/AnalyticsRulesEngine';
import {
    emptyChatToActiveTransition,
    messageBubbleEnter,
    sendButtonPress,
    suggestionCardHover,
    suggestionCardUnhover,
    quickActionsEnter
} from '@/lib/animations';
import VisualizationRenderer, { type VisualizationRendererProps } from './visualizations/VisualizationRenderer';
import UnifiedAnalytics from './visualizations/UnifiedAnalytics';
import InvitationModal from './InvitationModal';
import { User, LogOut, Gift, PlusCircle, History, Send, Plus, Bookmark, Copy, Check, ChevronLeft, ChevronRight, Terminal } from 'lucide-react';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import VoiceOrb from '@/components/VoiceOrb';
import { translations } from '@/lib/translations';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// ============================================
// UTILITY COMPONENTS
// ============================================

const MaterialIcon = ({ name, className = '', size = '20px' }: { name: string, className?: string, size?: string }) => {
    if (!name) return null;
    const sizeClassMap: Record<string, string> = {
        '14px': 'text-[14px]',
        '16px': 'text-[16px]',
        '18px': 'text-[18px]',
        '20px': 'text-[20px]',
        '24px': 'text-[24px]',
    };
    const sizeClass = sizeClassMap[size] || 'text-[20px]';
    return (
        <span className={`material-symbols-outlined select-none ${sizeClass} ${className}`}>{name}</span>
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
// CODE BLOCK COMPONENT
// ============================================

const CodeBlock = ({ language, value }: { language: string, value: string }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="code-block-wrapper shadow-lg border border-[var(--color-border-subtle)]">
            <div className="code-header bg-[var(--ai-surface)]">
                <span className="flex items-center gap-2">
                    <Terminal size={14} className="text-[var(--osool-deep-teal)]" />
                    {language || 'text'}
                </span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 hover:text-[var(--osool-deep-teal)] transition-colors"
                >
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>
            </div>
            <SyntaxHighlighter
                language={language}
                style={vscDarkPlus}
                customStyle={{ margin: 0, padding: '1.25rem', fontSize: '0.9rem', background: 'var(--chatgpt-code-bg)' }}
                wrapLines={true}
            >
                {value}
            </SyntaxHighlighter>
        </div>
    );
};

// ============================================
// CoInvestor AVATAR - Distinctive AI Identity
// ============================================

function CoInvestorAvatar({
    size = 'sm',
    thinking = false,
    showStatus = true,
    isRTL = false,
    state = 'default'
}: {
    size?: 'sm' | 'md' | 'lg';
    thinking?: boolean;
    showStatus?: boolean;
    isRTL?: boolean;
    state?: 'default' | 'thinking' | 'searching' | 'success';
}) {
    // Map state to visuals
    const isThinking = thinking || state === 'thinking';
    const isSearching = state === 'searching';
    const isSuccess = state === 'success';

    return (
        <div className="coinvestor-avatar" data-size={size}>
            {/* Animated pulse ring */}
            <div className={`coinvestor-avatar-ring ${isThinking || isSearching ? 'active' : ''} ${isSuccess ? 'bg-emerald-500/20' : ''}`} />
            {/* Main surface with gradient and monogram */}
            <div className={`coinvestor-avatar-surface ${isThinking ? 'thinking' : ''} ${isSearching ? 'animate-pulse' : ''}`}>
                {isSuccess ? (
                    <span className="coinvestor-avatar-monogram text-emerald-400"><Check size={18} /></span>
                ) : (
                    <span className="coinvestor-avatar-monogram">C</span>
                )}
            </div>
            {/* Status dot */}
            {showStatus && (
                <div className={`coinvestor-avatar-status ${isRTL ? 'rtl' : ''}`} />
            )}
        </div>
    );
}

// ============================================
// TYPEWRITER HOOK
// ============================================

function useTypewriter(text: string, speed: number = 25) {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);
    // Keep latest text in a ref so the interval callback always reads current value
    // without needing the effect to re-run (and restart the interval) on every text change
    const textRef = useRef(text);
    const indexRef = useRef(0);
    const speedRef = useRef(speed);

    // Sync refs without causing effect re-runs
    useEffect(() => { textRef.current = text; }, [text]);
    useEffect(() => { speedRef.current = speed; }, [speed]);

    // Reset when text shrinks (new message) — stable dependency
    const prevLenRef = useRef(0);
    useEffect(() => {
        if (text.length < prevLenRef.current) {
            indexRef.current = 0;
            setDisplayedText('');
            setIsComplete(false);
        }
        prevLenRef.current = text.length;
    }, [text]);

    // Single long-lived interval — reads current refs each tick
    useEffect(() => {
        const interval = setInterval(() => {
            const target = textRef.current;
            if (indexRef.current < target.length) {
                // Advance by up to 3 chars per tick for faster catch-up on long bursts
                indexRef.current = Math.min(indexRef.current + 3, target.length);
                setDisplayedText(target.slice(0, indexRef.current));
                setIsComplete(false);
            } else if (indexRef.current >= target.length && target.length > 0) {
                setIsComplete(true);
            }
        }, speedRef.current);

        return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // intentionally empty — interval lives for the lifetime of the component

    return { displayedText, isComplete };
}

// ============================================
// PROPERTY CARD - FEATURED LISTING
// ============================================

interface Property {
    id?: string | number;
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    bathrooms?: number;
    image_url?: string;
    roi?: number;
    annual_return?: number;
    wolf_score?: number;
    developer?: string;
}

interface VisualizationMetricData {
    properties?: Array<Property & { savings?: number }>;
    property?: { wolf_score?: number };
    analysis?: { match_score?: number };
    protection_rate?: number;
    trend?: string;
    data?: { trend?: string };
    area?: { avg_price_per_sqm?: number; yearly_growth?: number; pros?: string[] };
    areas?: Array<{ avg_price_per_sqm?: number; yearly_growth?: number; pros?: string[] }>;
    developer?: { trust_score?: number };
    developers?: Array<{ trust_score?: number }>;
    roi?: { annual_return?: number };
    plans?: unknown[];
    recommendation?: { recommendation?: string };
    alternatives?: Array<{ label_ar?: string; label_en?: string }>;
    [key: string]: unknown;
}

interface VisualizationPayload {
    type: string;
    data?: VisualizationMetricData;
    priority?: number;
    [key: string]: unknown;
}

interface ChatMessage {
    id: string;
    role: string;
    content: string;
    isTyping?: boolean;
    properties?: Property[];
    visualizations?: VisualizationPayload[];
    [key: string]: unknown;
}

type MarkdownCodeProps = HTMLAttributes<HTMLElement> & {
    inline?: boolean;
    className?: string;
    children?: ReactNode;
};

function FeaturedPropertyCard({
    property,
    onBookmark,
    onRequestDetails,
    isRTL = false
}: {
    property: Property;
    onBookmark?: () => void;
    onRequestDetails?: () => void;
    isRTL?: boolean;
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
                {/* Image Section */}
                <div className="lg:w-3/5 h-[200px] sm:h-[280px] lg:h-[400px] overflow-hidden relative">
                    {property.image_url ? (
                        <img
                            alt={property.title}
                            className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105 hologram-img"
                            src={property.image_url}
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                            <MaterialIcon name="apartment" className="text-slate-400" size="48px" />
                        </div>
                    )}
                    <div className={`absolute bottom-0 p-4 sm:p-6 lg:p-10 bg-gradient-to-t from-black/50 to-transparent w-full ${isRTL ? 'end-0' : 'start-0'}`}>
                        <div className="text-white" dir={isRTL ? 'rtl' : 'ltr'}>
                            <p className="text-[8px] sm:text-[10px] font-bold uppercase tracking-[0.2em] sm:tracking-[0.3em] mb-1 sm:mb-2 opacity-80">
                                {isRTL ? 'مميز' : 'Featured'}
                            </p>
                            <h2 className="font-serif text-lg sm:text-2xl lg:text-3xl italic line-clamp-2">{property.title}</h2>
                        </div>
                    </div>
                </div>

                {/* Details Section */}
                <div className="lg:w-2/5 p-4 sm:p-6 lg:p-10 flex flex-col justify-between bg-[var(--color-studio-white)]" dir={isRTL ? 'rtl' : 'ltr'}>
                    <div className="space-y-4 sm:space-y-6">
                        <div>
                            <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] sm:tracking-[0.2em] text-[var(--color-text-muted-studio)] mb-1 sm:mb-2">
                                {isRTL ? 'الموقع' : 'Location'}
                            </p>
                            <p className="text-xs sm:text-sm font-medium text-[var(--color-text-main)] line-clamp-1">{property.location}</p>
                        </div>
                        <div className="h-px bg-[var(--color-border-subtle)] w-full"></div>
                        <div className="grid grid-cols-2 gap-3 sm:gap-y-6">
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">
                                    {isRTL ? 'السعر' : 'Price'}
                                </p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {(property.price / 1000000).toFixed(1)}M <span className="text-xs text-[var(--color-text-muted-studio)]">{isRTL ? 'ج.م' : 'EGP'}</span>
                                </p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">
                                    {isRTL ? 'المساحة' : 'Size'}
                                </p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">{property.size_sqm} {isRTL ? 'م²' : 'm²'}</p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">
                                    {isRTL ? 'غرف/حمام' : 'Beds/Baths'}
                                </p>
                                <p className="text-sm sm:text-lg font-semibold tracking-tight text-[var(--color-text-main)]">
                                    {property.bedrooms}/{property.bathrooms || 2}
                                </p>
                            </div>
                            <div>
                                <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--color-text-muted-studio)] mb-0.5 sm:mb-1">
                                    {isRTL ? 'العائد على الاستثمار' : 'ROI'}
                                </p>
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
                            {isRTL ? 'التفاصيل' : 'Details'}
                        </button>
                        <button
                            onClick={onBookmark}
                            aria-label={isRTL ? 'إضافة للمفضلة' : 'Bookmark property'}
                            className="size-10 sm:size-12 border border-[var(--color-border-subtle)] flex items-center justify-center hover:bg-[var(--color-studio-gray)] transition-colors rounded sm:rounded-none"
                        >
                            <Bookmark size={18} className="text-[var(--color-text-muted-studio)]" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Appreciation Chart */}
            {projectedGrowth && (
                <div className="hidden sm:block px-4 sm:px-6 lg:px-10 py-4 sm:py-6 lg:py-10 border-t border-[var(--color-border-subtle)] bg-[var(--color-studio-white)]" dir={isRTL ? 'rtl' : 'ltr'}>
                    <div className="flex justify-between items-center mb-4 sm:mb-6 lg:mb-8">
                        <p className="text-[9px] sm:text-[10px] font-bold uppercase tracking-[0.15em] sm:tracking-[0.2em] text-[var(--color-text-muted-studio)]">
                            {isRTL ? 'توقعات 5 سنوات' : '5Y Projection'}
                        </p>
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
// SIDEBAR COMPONENT - Enhanced with Quick Tools
// ============================================

function Sidebar({
    onNewSession,
    onInjectQuery,
    isRTL
}: {
    onNewSession: () => void;
    onInjectQuery: (query: string) => void;
    isRTL: boolean;
}) {
    const quickTools = [
        { icon: 'pin_drop', label: isRTL ? 'تحليل منطقة' : 'Area Analysis', query: isRTL ? 'حلل منطقة التجمع الخامس' : 'Analyze New Cairo area' },
        { icon: 'calculate', label: isRTL ? 'حاسبة العائد' : 'ROI Calculator', query: isRTL ? 'احسب العائد الاستثماري' : 'Calculate investment ROI' },
        { icon: 'domain', label: isRTL ? 'تقييم المطورين' : 'Developer Rank', query: isRTL ? 'قارن بين المطورين العقاريين' : 'Compare real estate developers' },
        { icon: 'show_chart', label: isRTL ? 'توقعات السوق' : 'Market Forecast', query: isRTL ? 'توقعات السوق العقاري' : 'Real estate market forecast' },
        { icon: 'credit_card', label: isRTL ? 'خطط السداد' : 'Payment Plans', query: isRTL ? 'أفضل خطط السداد المتاحة' : 'Best available payment plans' },
    ];

    return (
        <aside className={`w-64 flex-none bg-[var(--sidebar-bg)] hidden lg:flex flex-col ${isRTL ? 'border-s' : 'border-e'} border-[var(--color-border-subtle)]`}>
            {/* Brand Header */}
            <div className="p-5 pb-4">
                <div className="flex items-center gap-3 mb-5">
                    <CoInvestorAvatar size="sm" showStatus={false} />
                    <div>
                        <p className="text-[12px] font-bold text-[var(--color-text-main)] tracking-wide">
                            {isRTL ? 'ذكاء أصول' : 'Osool Intelligence'}
                        </p>
                        <p className="text-[9px] text-[var(--color-text-muted-studio)] tracking-wider uppercase">
                            Wolf Brain
                        </p>
                    </div>
                </div>

                {/* New Analysis CTA */}
                <button
                    onClick={onNewSession}
                    className="w-full py-2.5 px-4 bg-[var(--osool-deep-teal)] text-white rounded-xl text-[11px] font-bold uppercase tracking-wider hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-sm active:scale-[0.98]"
                >
                    <MaterialIcon name="add_circle" size="16px" />
                    {isRTL ? 'تحليل جديد' : 'New Analysis'}
                </button>
            </div>

            {/* Quick Tools */}
            <div className="px-4 pb-3">
                <h3 className="text-[9px] font-bold text-[var(--color-text-muted-studio)] uppercase tracking-[0.2em] mb-3 px-1">
                    {isRTL ? 'أدوات سريعة' : 'Quick Tools'}
                </h3>
                <div className="space-y-0.5">
                    {quickTools.map((tool) => (
                        <button
                            key={tool.label}
                            onClick={() => onInjectQuery(tool.query)}
                            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[11px] font-medium text-[var(--color-text-muted-studio)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--color-text-main)] transition-all group ${isRTL ? 'text-end' : 'text-start'}`}
                        >
                            <div className="size-7 rounded-lg bg-[var(--sidebar-active)] flex items-center justify-center flex-shrink-0 group-hover:bg-[var(--osool-deep-teal)]/10 transition-colors">
                                <MaterialIcon name={tool.icon} size="14px" className="group-hover:text-[var(--osool-deep-teal)]" />
                            </div>
                            <span className="truncate">{tool.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* History Section */}
            <div className="flex-1 overflow-y-auto px-4 pb-4">
                <h3 className="text-[9px] font-bold text-[var(--color-text-muted-studio)] uppercase tracking-[0.2em] mb-3 px-1 pt-3 border-t border-[var(--color-border-subtle)]">
                    {isRTL ? 'السجل' : 'History'}
                </h3>
                <div className="flex flex-col items-center justify-center py-6 text-center">
                    <div className="size-10 rounded-xl bg-[var(--sidebar-active)] flex items-center justify-center mb-2">
                        <MaterialIcon name="home_work" size="18px" className="text-[var(--color-text-muted-studio)] opacity-50" />
                    </div>
                    <p className="text-[10px] text-[var(--color-text-muted-studio)] opacity-60">
                        {isRTL ? 'لا توجد محادثات سابقة' : 'No previous sessions'}
                    </p>
                </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-[var(--color-border-subtle)]">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 text-[var(--color-text-muted-studio)]">
                        <button
                            aria-label={isRTL ? 'الإعدادات' : 'Settings'}
                            className="hover:text-[var(--color-text-main)] transition-colors"
                        >
                            <MaterialIcon name="settings" size="18px" />
                        </button>
                        <button
                            aria-label={isRTL ? 'مساعدة' : 'Help'}
                            className="hover:text-[var(--color-text-main)] transition-colors"
                        >
                            <MaterialIcon name="help_outline" size="18px" />
                        </button>
                    </div>
                    <span className="text-[8px] text-[var(--color-text-muted-studio)] opacity-40 tracking-wider">
                        v1.0 Wolf Brain
                    </span>
                </div>
            </div>
        </aside>
    );
}

// ============================================
// CONTEXTUAL INSIGHTS PANE - Enhanced
// ============================================

function ContextualInsights({
    properties,
    currentIndex,
    onPrev,
    onNext,
    aiInsight,
    visualizations,
    isRTL
}: {
    properties: Property[];
    currentIndex: number;
    onPrev: () => void;
    onNext: () => void;
    aiInsight: string | null;
    visualizations: VisualizationPayload[];
    isRTL: boolean;
}) {
    const property = properties[currentIndex] || null;
    const hasMultipleProperties = properties.length > 1;
    const contentRef = useRef<HTMLDivElement>(null);
    const { displayedText: typedInsight, isComplete } = useTypewriter(aiInsight || '', 20);

    useEffect(() => {
        if (contentRef.current) {
            const items = contentRef.current.querySelectorAll('.insight-item');
            if (items.length > 0) {
                anime({
                    targets: items,
                    opacity: [0, 1],
                    translateX: [isRTL ? 10 : -10, 0],
                    delay: anime.stagger(60, { start: 80 }),
                    easing: 'easeOutCubic',
                    duration: 300,
                });
            }
        }
    }, [property, aiInsight, visualizations, isRTL]);

    const hasContent = properties.length > 0 || aiInsight || visualizations.length > 0;

    const getVizName = (type: string): string => {
        const names: Record<string, string> = {
            'investment_scorecard': isRTL ? 'تقييم' : 'Investment',
            'comparison_matrix': isRTL ? 'مقارنة' : 'Compare',
            'inflation_killer': isRTL ? 'حماية' : 'Inflation',
            'payment_timeline': isRTL ? 'السداد' : 'Payment',
            'market_trend_chart': isRTL ? 'السوق' : 'Trend',
            'area_analysis': isRTL ? 'المنطقة' : 'Area',
            'developer_analysis': isRTL ? 'المطور' : 'Developer',
            'roi_calculator': isRTL ? 'العائد' : 'ROI',
            'property_type_analysis': isRTL ? 'أنواع' : 'Types',
            'payment_plan_analysis': isRTL ? 'السداد' : 'Plans',
            'resale_vs_developer': isRTL ? 'ريسيل' : 'Resale',
            'la2ta_alert': isRTL ? 'لقطة' : 'Deal',
            'reality_check': isRTL ? 'تنبيه' : 'Alert',
        };
        return names[type] || type?.replace(/_/g, ' ');
    };

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
            'la2ta_alert': 'local_fire_department',
            'reality_check': 'lightbulb',
        };
        return icons[type] || 'auto_awesome';
    };

    const getKeyMetric = (viz: VisualizationPayload): string => {
        const { type, data } = viz;
        if (!data) return '—';
        switch (type) {
            case 'investment_scorecard':
                return `${data?.analysis?.match_score || data?.property?.wolf_score || '—'}/100`;
            case 'comparison_matrix':
                return `${data?.properties?.length || 0} ${isRTL ? 'عقار' : 'props'}`;
            case 'inflation_killer':
                return data?.protection_rate ? `+${data.protection_rate}%` : '—';
            case 'market_trend_chart':
                return data?.trend || data?.data?.trend || '—';
            case 'area_analysis': {
                const price = data?.area?.avg_price_per_sqm || data?.areas?.[0]?.avg_price_per_sqm;
                return price ? `${Math.round(price / 1000)}K` : '—';
            }
            case 'developer_analysis':
                return `${data?.developer?.trust_score || data?.developers?.[0]?.trust_score || '—'}%`;
            case 'roi_calculator':
                return `${data?.roi?.annual_return || data?.properties?.[0]?.annual_return || '—'}%`;
            case 'payment_plan_analysis':
            case 'payment_plan_comparison':
                return `${data?.plans?.length || 0} ${isRTL ? 'خطة' : 'plans'}`;
            case 'resale_vs_developer':
                return data?.recommendation?.recommendation === 'resale' ? (isRTL ? 'ريسيل' : 'Resale') : (isRTL ? 'مطور' : 'Developer');
            case 'la2ta_alert':
                return `${data?.properties?.length || 0} ${isRTL ? 'فرصة' : 'deals'}`;
            case 'reality_check':
                return `${data?.alternatives?.length || 0} ${isRTL ? 'بديل' : 'options'}`;
            default:
                return '—';
        }
    };

    return (
        <aside
            className={`w-80 flex-none bg-[var(--sidebar-bg)] hidden xl:flex flex-col overflow-hidden ${isRTL ? 'border-e' : 'border-s'} border-[var(--color-border-subtle)]`}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Header */}
            <div className="p-4 border-b border-[var(--color-border-subtle)] flex items-center gap-2.5">
                <div className="size-6 rounded-lg bg-[var(--osool-deep-teal)]/10 flex items-center justify-center">
                    <MaterialIcon name="insights" size="14px" className="text-[var(--osool-deep-teal)]" />
                </div>
                <h2 className="text-[12px] font-bold text-[var(--color-text-main)] tracking-wide">
                    {isRTL ? 'رؤى ذكية' : 'Smart Insights'}
                </h2>
                {hasContent && (
                    <>
                        {hasMultipleProperties && (
                            <div className={`flex items-center gap-1 ${isRTL ? 'me-auto' : 'ms-auto'}`}>
                                <button
                                    onClick={onPrev}
                                    disabled={currentIndex === 0}
                                    aria-label={isRTL ? 'السابق' : 'Previous'}
                                    title={isRTL ? 'السابق' : 'Previous'}
                                    className="p-1 rounded hover:bg-[var(--sidebar-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                >
                                    <ChevronLeft size={14} className="text-[var(--color-text-muted-studio)]" />
                                </button>
                                <span className="text-[10px] font-medium text-[var(--color-text-muted-studio)] min-w-[32px] text-center">
                                    {currentIndex + 1}/{properties.length}
                                </span>
                                <button
                                    onClick={onNext}
                                    disabled={currentIndex === properties.length - 1}
                                    aria-label={isRTL ? 'التالي' : 'Next'}
                                    title={isRTL ? 'التالي' : 'Next'}
                                    className="p-1 rounded hover:bg-[var(--sidebar-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                                >
                                    <ChevronRight size={14} className="text-[var(--color-text-muted-studio)]" />
                                </button>
                            </div>
                        )}
                        <span className="text-[8px] px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded-full font-bold tracking-wider uppercase">
                            Live
                        </span>
                    </>
                )}
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto scrollbar-hide">
                <div ref={contentRef} className="p-3 space-y-2.5">
                    {hasContent ? (
                        <>
                            {/* AI Summary Card */}
                            {aiInsight && (
                                <div className="insight-item p-3.5 rounded-xl bg-gradient-to-br from-[var(--osool-deep-teal)] to-[var(--osool-deep-teal)]/80 text-white">
                                    <div className="flex items-center gap-2 mb-2.5">
                                        <CoInvestorAvatar size="sm" showStatus={false} />
                                        <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">
                                            {isRTL ? 'تحليل CoInvestor' : 'CoInvestor Analysis'}
                                        </span>
                                    </div>
                                    <p className="text-[11px] leading-relaxed opacity-90 line-clamp-4">
                                        {typedInsight}
                                        {!isComplete && <span className="inline-block w-0.5 h-2.5 bg-white/80 mx-0.5 animate-pulse" />}
                                    </p>
                                </div>
                            )}

                            {/* Property Thumbnail + Enhanced Metrics */}
                            {property && (
                                <div className="insight-item space-y-2">
                                    {/* Property Thumbnail Header */}
                                    <div className="insight-property-thumb">
                                        {property.image_url ? (
                                            <img
                                                src={property.image_url}
                                                alt={property.title}
                                            />
                                        ) : (
                                            <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 flex items-center justify-center text-lg">
                                                🏠
                                            </div>
                                        )}
                                        <div className="insight-property-thumb-info">
                                            <p className="insight-property-thumb-title">{property.title}</p>
                                            <p className="insight-property-thumb-price">
                                                {(property.price / 1000000).toFixed(1)}M {isRTL ? 'ج.م' : 'EGP'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* 6-Metric Grid */}
                                    <div className="insight-metrics-grid">
                                        {[
                                            {
                                                label: isRTL ? 'سعر/م²' : 'Price/m²',
                                                value: property.size_sqm > 0 ? `${Math.round(property.price / property.size_sqm / 1000)}K` : '—',
                                                highlight: false
                                            },
                                            {
                                                label: isRTL ? 'تقييم' : 'Wolf',
                                                value: property.wolf_score || '—',
                                                highlight: property.wolf_score && property.wolf_score >= 80
                                            },
                                            {
                                                label: isRTL ? 'العائد' : 'ROI',
                                                value: property.roi ? `${property.roi}%` : '—',
                                                highlight: property.roi && property.roi > 10
                                            },
                                            {
                                                label: isRTL ? 'غرف' : 'Beds',
                                                value: property.bedrooms || '—',
                                                highlight: false
                                            },
                                            {
                                                label: isRTL ? 'المساحة' : 'Size',
                                                value: property.size_sqm ? `${property.size_sqm}m²` : '—',
                                                highlight: false
                                            },
                                            {
                                                label: isRTL ? 'المطور' : 'Dev',
                                                value: property.developer ? property.developer.split(' ')[0] : '—',
                                                highlight: false
                                            },
                                        ].map((metric) => (
                                            <div key={metric.label} className="insight-metric-card">
                                                <p className={`insight-metric-value ${metric.highlight ? 'highlight' : ''}`}>
                                                    {metric.value}
                                                </p>
                                                <p className="insight-metric-label">{metric.label}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Active Analytics */}
                            {visualizations.length > 0 && (
                                <div className="insight-item space-y-1.5">
                                    <p className="text-[9px] font-bold uppercase tracking-wider text-[var(--color-text-muted-studio)] px-1">
                                        {isRTL ? 'التحليلات النشطة' : 'Active Analytics'}
                                    </p>
                                    {visualizations.slice(0, 3).map((viz, idx) => (
                                        <div
                                            key={idx}
                                            className="p-3 rounded-xl border border-[var(--color-border-subtle)] flex items-center gap-2.5 hover:bg-[var(--sidebar-hover)] transition-colors bg-[var(--color-studio-white)]"
                                        >
                                            <div className="size-8 rounded-lg bg-gradient-to-br from-[var(--osool-deep-teal)]/10 to-[var(--osool-bright-teal)]/10 flex items-center justify-center flex-shrink-0">
                                                <MaterialIcon name={getVizIcon(viz.type)} size="14px" className="text-[var(--osool-deep-teal)]" />
                                            </div>
                                            <span className="text-[11px] font-medium text-[var(--color-text-main)] flex-1 truncate">
                                                {getVizName(viz.type)}
                                            </span>
                                            <span className="text-[12px] font-bold text-emerald-600 flex-shrink-0">
                                                {getKeyMetric(viz)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        /* Empty State with Quick Actions */
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                            <CoInvestorAvatar size="md" thinking={false} showStatus={false} />
                            <p className="text-[11px] text-[var(--color-text-muted-studio)] mt-4 mb-5">
                                {isRTL ? 'اسأل CoInvestor للبدء' : 'Ask CoInvestor to start analyzing'}
                            </p>
                            <div className="grid grid-cols-2 gap-2 w-full">
                                {[
                                    { icon: 'trending_up', label: isRTL ? 'عائد' : 'ROI' },
                                    { icon: 'pin_drop', label: isRTL ? 'مناطق' : 'Areas' },
                                    { icon: 'domain', label: isRTL ? 'مطورين' : 'Devs' },
                                    { icon: 'credit_card', label: isRTL ? 'سداد' : 'Plans' },
                                ].map((action) => (
                                    <div key={action.label} className="p-2.5 rounded-lg border border-[var(--color-border-subtle)] text-center hover:bg-[var(--sidebar-hover)] transition-colors cursor-default">
                                        <MaterialIcon name={action.icon} size="16px" className="text-[var(--color-text-muted-studio)] mb-1" />
                                        <p className="text-[9px] font-medium text-[var(--color-text-muted-studio)]">{action.label}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </aside>
    );
}

// ============================================
// COMPACT VISUALIZATION WRAPPER FOR CHAT
// ============================================

function CompactVisualization({ viz, isRTL }: { viz: VisualizationPayload; isRTL: boolean }) {
    const [expanded, setExpanded] = useState(false);

    const getVizName = (type: string): string => {
        const names: Record<string, string> = {
            'investment_scorecard': isRTL ? 'تقييم الاستثمار' : 'Investment Score',
            'comparison_matrix': isRTL ? 'مقارنة' : 'Compare',
            'inflation_killer': isRTL ? 'حماية التضخم' : 'Inflation Shield',
            'payment_timeline': isRTL ? 'جدول السداد' : 'Payment Plan',
            'market_trend_chart': isRTL ? 'اتجاه السوق' : 'Market Trend',
            'area_analysis': isRTL ? 'تحليل المنطقة' : 'Area Analysis',
            'developer_analysis': isRTL ? 'تحليل المطور' : 'Developer',
            'roi_calculator': isRTL ? 'حاسبة العائد' : 'ROI Calculator',
            'property_type_analysis': isRTL ? 'أنواع العقارات' : 'Property Types',
            'payment_plan_analysis': isRTL ? 'خطط السداد' : 'Payment Plans',
            'payment_plan_comparison': isRTL ? 'خطط السداد' : 'Payment Plans',
            'resale_vs_developer': isRTL ? 'ريسيل vs مطور' : 'Resale vs Developer',
            'la2ta_alert': isRTL ? 'لقطة!' : 'Hot Deal!',
            'reality_check': isRTL ? 'تنبيه ذكي' : 'Reality Check',
        };
        return names[type] || type?.replace(/_/g, ' ');
    };

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
            'payment_plan_comparison': 'credit_card',
            'resale_vs_developer': 'swap_horiz',
            'la2ta_alert': 'local_fire_department',
            'reality_check': 'lightbulb',
        };
        return icons[type] || 'auto_awesome';
    };

    return (
        <div className="rounded-xl border border-[var(--color-border-subtle)]/40 overflow-hidden bg-transparent ai-visualization" dir={isRTL ? 'rtl' : 'ltr'}>
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 flex items-center gap-2 bg-transparent hover:bg-[var(--color-border-subtle)]/20 transition-colors"
            >
                <div className="size-6 sm:size-7 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                    <MaterialIcon name={getVizIcon(viz.type)} size="14px" className="text-emerald-600" />
                </div>
                <span className="text-[11px] sm:text-xs font-medium text-[var(--color-text-main)] flex-1 text-start">
                    {getVizName(viz.type)}
                </span>
                <MaterialIcon
                    name={expanded ? 'expand_less' : 'expand_more'}
                    size="18px"
                    className="text-[var(--color-text-muted-studio)] flex-shrink-0"
                />
            </button>

            <motion.div
                initial={false}
                animate={{ height: expanded ? 'auto' : '160px' }}
                transition={{ duration: 0.2, ease: 'easeInOut' }}
                className="overflow-hidden relative"
            >
                <div className={`${expanded ? '' : 'max-h-40'} overflow-y-auto`}>
                    <VisualizationRenderer type={viz.type} data={(viz.data || {}) as VisualizationRendererProps['data']} isRTL={isRTL} />
                </div>
                {!expanded && (
                    <div className="absolute bottom-0 start-0 end-0 h-12 bg-gradient-to-t from-[var(--color-studio-white)] to-transparent pointer-events-none" />
                )}
            </motion.div>
        </div>
    );
}

// Fix malformed markdown tables so remark-gfm can parse them
function fixMarkdownTables(text: string): string {
    const lines = text.split('\n');
    const result: string[] = [];
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        if (/^\s*\|/.test(line)) {
            const tableLines: string[] = [];
            while (i < lines.length && /^\s*\|/.test(lines[i])) { tableLines.push(lines[i]); i++; }
            if (tableLines.length >= 2) {
                const headerCols = (tableLines[0].match(/\|/g) || []).length - 1;
                const isSep = (l: string) => /^\s*\|[\s\-:|]+\|\s*$/.test(l);
                if (isSep(tableLines[1])) {
                    const sepCols = (tableLines[1].match(/\|/g) || []).length - 1;
                    if (sepCols !== headerCols) {
                        tableLines[1] = '| ' + Array(headerCols).fill('---').join(' | ') + ' |';
                    }
                } else if (headerCols >= 2) {
                    tableLines.splice(1, 0, '| ' + Array(headerCols).fill('---').join(' | ') + ' |');
                }
                for (let r = 2; r < tableLines.length; r++) {
                    if (isSep(tableLines[r])) continue;
                    const rowCols = (tableLines[r].match(/\|/g) || []).length - 1;
                    if (rowCols < headerCols) {
                        tableLines[r] = tableLines[r].trimEnd().replace(/\|$/, '') + '| '.repeat(headerCols - rowCols) + '|';
                    }
                }
                result.push(...tableLines);
            } else { result.push(...tableLines); }
        } else { result.push(line); i++; }
    }
    return result.join('\n');
}

// Strip bracketed action annotations from AI responses (e.g. [يفتح حاسبة القوة الشرائية])
function cleanMessageContent(text: string): string {
    return fixMarkdownTables(
        text
            .replace(/\[[\u0600-\u06FF\u0621-\u064A\w\s،,.:()\/\-]+\]/g, '') // Arabic bracket text
            .replace(/\[\s*[a-zA-Z\s_]+\s*\]/g, '')                               // English bracket actions
            .replace(/\n{3,}/g, '\n\n')                                            // Collapse excess blank lines
            .trim()
    );
}

// ============================================
// MAIN CHAT INTERFACE
// ============================================

export default function ChatInterface() {
    const { user, isAuthenticated, logout } = useAuth();
    const { language } = useLanguage();
    const { theme, toggleTheme } = useTheme();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
    const [sessionStartTime] = useState(() => Date.now());
    const [isUserMenuOpen, setUserMenuOpen] = useState(false);
    const [isInvitationModalOpen, setInvitationModalOpen] = useState(false);
    const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

    // First message state
    const [hasStartedChat, setHasStartedChat] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false);

    // Contextual state
    const [contextProperties, setContextProperties] = useState<Property[]>([]);
    const [contextPropertyIndex, setContextPropertyIndex] = useState(0);
    const [contextInsight, setContextInsight] = useState<string | null>(null);
    const [contextVisualizations, setContextVisualizations] = useState<VisualizationPayload[]>([]);
    const [, setDetectedAnalytics] = useState<AnalyticsMatch[]>([]);
    const [leadScore, setLeadScore] = useState<number>(0);

    // Fetch user context from Orchestrator
    useEffect(() => {
        if (isAuthenticated) {
            getOrchestratorContext().then((data) => {
                if (data && typeof data.lead_score === 'number') {
                    setLeadScore(data.lead_score);
                }
            }).catch(() => { /* ignore */ });
        }
    }, [isAuthenticated]);

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const welcomeRef = useRef<HTMLDivElement>(null);
    const centeredInputRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const isRTL = language === 'ar';

    const [transcriptHighlight, setTranscriptHighlight] = useState(false);

    const {
        status: voiceStatus,
        isListening: isVoiceListening,
        amplitude,
        startRecording,
        stopRecording,
    } = useVoiceRecording({
        language: isRTL ? 'ar-EG' : 'auto',
        silenceThresholdMs: 2000,
        onTranscript: (text) => {
            setInput(text);
            textareaRef.current?.focus();
            setTranscriptHighlight(true);
            setTimeout(() => setTranscriptHighlight(false), 600);
        },
        onError: (msg) => {
            console.warn('[Voice]', msg);
        },
    });

    const handleVoiceToggle = useCallback(() => {
        if (isVoiceListening || voiceStatus === 'processing') {
            stopRecording();
        } else {
            startRecording();
        }
    }, [isVoiceListening, voiceStatus, startRecording, stopRecording]);

    // Streaming token buffer — accumulates tokens without triggering renders,
    // flushed to state via requestAnimationFrame for smooth 60fps display
    const streamBufferRef = useRef('');
    const streamMsgIdRef = useRef<string | null>(null);
    const rafIdRef = useRef<number | null>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Auto-resize textarea
    const adjustTextareaHeight = useCallback(() => {
        const el = textareaRef.current;
        if (el) {
            el.style.height = 'auto';
            el.style.height = `${Math.min(el.scrollHeight, 150)}px`;
        }
    }, []);

    useEffect(() => {
        adjustTextareaHeight();
    }, [input, adjustTextareaHeight]);

    const extractInsight = useCallback((content: string): string | null => {
        if (!content) return null;
        const sentences = content.split(/[.!؟]/);
        const insight = sentences.find(s => s.trim().length > 20);
        return insight?.trim() || null;
    }, []);

    const lastContextUpdate = useRef<number>(0);
    const updateContextFromResponse = useCallback((response: string) => {
        const now = Date.now();
        if (now - lastContextUpdate.current < 500) return;
        lastContextUpdate.current = now;

        const areaKeywords = ['التجمع', 'مدينتي', 'الشيخ زايد', 'العاصمة الإدارية', 'الساحل', 'New Cairo', 'Sheikh Zayed', 'Madinaty'];
        const mentionedAreas = areaKeywords.filter(area =>
            response.toLowerCase().includes(area.toLowerCase())
        );

        const developerKeywords = ['طلعت مصطفى', 'بالم هيلز', 'سوديك', 'TMG', 'Palm Hills', 'SODIC', 'Mountain View'];
        const mentionedDevelopers = developerKeywords.filter(dev =>
            response.toLowerCase().includes(dev.toLowerCase())
        );

        if (mentionedAreas.length > 0 || mentionedDevelopers.length > 0) {
            const insight = extractInsight(response);
            if (insight && insight.length > 30) {
                setContextInsight(insight);
            }
        }
    }, [extractInsight]);

    const handleCopyMessage = useCallback(async (msgId: string, content: string) => {
        try {
            await navigator.clipboard.writeText(content);
            setCopiedMsgId(msgId);
            setTimeout(() => setCopiedMsgId(null), 2000);
        } catch { /* ignore */ }
    }, []);

    const handleSend = async () => {
        if (!input.trim() || isTyping || isTransitioning) return;

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

        if (!hasStartedChat) {
            setIsTransitioning(true);
            emptyChatToActiveTransition(
                welcomeRef.current,
                centeredInputRef.current,
                () => {
                    setHasStartedChat(true);
                    setIsTransitioning(false);
                }
            );
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

        // Fire-and-forget to orchestrator — intent classification + lead scoring
        trackChatMessage({
            sessionId,
            anonymousId: getAnonymousId(),
            userId: user?.id?.toString(),
            message: { role: 'user', content: input },
        });

        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();
        setMessages(prev => [...prev, { role: 'coinvestor', content: '', id: aiMsgId, isTyping: true }]);

        let fullResponse = '';
        // Initialize streaming buffer for this response
        streamBufferRef.current = '';
        streamMsgIdRef.current = aiMsgId;
        if (rafIdRef.current !== null) cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;

        const flushStreamBuffer = () => {
            const buffered = streamBufferRef.current;
            if (buffered !== '') {
                setMessages(prev => prev.map(m =>
                    m.id === streamMsgIdRef.current ? { ...m, content: buffered } : m
                ));
            }
            rafIdRef.current = null;
        };

        try {
            await streamChat(userMsg.content, sessionId, {
                onToken: (token) => {
                    fullResponse += token;
                    streamBufferRef.current = fullResponse;
                    updateContextFromResponse(fullResponse);
                    // Schedule a single RAF flush — if one is already pending, skip
                    if (rafIdRef.current === null) {
                        rafIdRef.current = requestAnimationFrame(flushStreamBuffer);
                    }
                },
                onToolStart: () => { },
                onToolEnd: () => { },
                onComplete: (data) => {
                    // Cancel any pending RAF and do final authoritative update
                    if (rafIdRef.current !== null) {
                        cancelAnimationFrame(rafIdRef.current);
                        rafIdRef.current = null;
                    }
                    setMessages(prev => prev.map(m =>
                        m.id === aiMsgId ? {
                            ...m,
                            content: fullResponse,
                            properties: data.properties as unknown as Property[],
                            visualizations: data.ui_actions as unknown as VisualizationPayload[],
                            isTyping: false
                        } : m
                    ));

                    if ((data.properties?.length ?? 0) > 0) {
                        setContextProperties(data.properties as unknown as Property[]);
                        setContextPropertyIndex(0);
                    }

                    if ((data.ui_actions?.length ?? 0) > 0) {
                        const prioritizedAnalytics = data.ui_actions
                            .sort((a, b) => ((b as VisualizationPayload).priority || 0) - ((a as VisualizationPayload).priority || 0))
                            .slice(0, 3);
                        setContextVisualizations(prioritizedAnalytics as unknown as VisualizationPayload[]);
                    }

                    const insight = extractInsight(fullResponse);
                    if (insight) {
                        setContextInsight(insight);
                    }

                    setIsTyping(false);

                    // Notify orchestrator of the AI response
                    trackChatMessage({
                        sessionId,
                        anonymousId: getAnonymousId(),
                        userId: user?.id?.toString(),
                        message: { role: 'assistant', content: fullResponse },
                    });
                },
                onFollowUp: (followUp) => {
                    // Create a delayed follow-up AI message
                    const followUpId = (Date.now() + 2).toString();
                    const followUpMessage = followUp as { message_ar?: string; message_en?: string };
                    const followUpText = isRTL
                        ? (followUpMessage.message_ar || followUpMessage.message_en || '')
                        : (followUpMessage.message_en || followUpMessage.message_ar || '');
                    if (followUpText) {
                        setMessages(prev => [...prev, {
                            role: 'coinvestor',
                            content: followUpText,
                            id: followUpId,
                            isTyping: false,
                            isFollowUp: true,
                        }]);
                        scrollToBottom();
                    }
                },
                onError: () => {
                    if (rafIdRef.current !== null) {
                        cancelAnimationFrame(rafIdRef.current);
                        rafIdRef.current = null;
                    }
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
        // Notify orchestrator that session ended
        if (messages.length > 0) {
            trackChatSessionEnd({
                sessionId,
                anonymousId: getAnonymousId(),
                userId: user?.id?.toString(),
                messageCount: messages.length,
                durationSeconds: Math.floor((Date.now() - sessionStartTime) / 1000),
            });
        }
        setMessages([]);
        setContextProperties([]);
        setContextPropertyIndex(0);
        setContextInsight(null);
        setContextVisualizations([]);
        setDetectedAnalytics([]);
        setInput('');
        setIsTyping(false);
        setHasStartedChat(false);
        setIsTransitioning(false);
        setSessionId(crypto.randomUUID());
    };

    const handleInjectQuery = (query: string) => {
        setInput(query);
        textareaRef.current?.focus();
    };

    const getUserName = (): string => user?.full_name || user?.email?.split('@')[0] || 'User';

    return (
        <div
            className="bg-[var(--color-studio-gray)] text-[var(--color-text-main)] font-sans h-screen flex flex-col overflow-hidden"
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Glass Header */}
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
                        aria-label={theme === 'dark' ? (isRTL ? 'تفعيل الوضع الفاتح' : 'Switch to light mode') : (isRTL ? 'تفعيل الوضع الداكن' : 'Switch to dark mode')}
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
                                aria-label={isRTL ? 'قائمة المستخدم' : 'User menu'}
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
                                        className={`absolute mt-2 w-48 sm:w-56 rounded-xl bg-white dark:bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] shadow-xl z-[60] ${isRTL ? 'start-0' : 'end-0'}`}
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
            <div className={`flex flex-1 overflow-hidden ${isRTL ? 'flex-row-reverse' : ''}`}>
                {/* Left Sidebar */}
                <Sidebar onNewSession={handleNewSession} onInjectQuery={handleInjectQuery} isRTL={isRTL} />

                {/* Main Chat Area */}
                <main className="flex-1 flex flex-col min-w-0 bg-[var(--color-studio-gray)] relative">
                    {/* Empty State - Premium Welcome */}
                    {!hasStartedChat && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center px-3 sm:px-4 py-4 overflow-y-auto">
                            {/* Welcome Section */}
                            <div
                                ref={welcomeRef}
                                className={`text-center mb-6 sm:mb-10 transition-opacity ${isTransitioning ? 'pointer-events-none' : ''}`}
                            >
                                {/* CoInvestor Avatar - Large */}
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-avatar flex justify-center mb-5 sm:mb-6"
                                >
                                    <CoInvestorAvatar size="lg" thinking={false} showStatus={true} isRTL={isRTL} />
                                </motion.div>

                                {/* Greeting */}
                                <motion.h2
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-title text-xl sm:text-2xl lg:text-3xl font-bold text-[var(--color-text-main)] mb-2"
                                >
                                    {isRTL ? (
                                        <span className="font-cairo">{translations.ar.chatInterface.welcomeTitle}</span>
                                    ) : (
                                        <span className="font-serif italic">{translations.en.chatInterface.welcomeTitle}</span>
                                    )}
                                </motion.h2>
                                <motion.p
                                    initial={{ opacity: 0, y: 15 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.4, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-subtitle text-sm sm:text-base text-[var(--color-text-muted-studio)] mb-6 sm:mb-8"
                                >
                                    {isRTL ? translations.ar.chatInterface.welcomeSubtitle : translations.en.chatInterface.welcomeSubtitle}
                                </motion.p>

                                {/* Decorative Divider */}
                                <div className="flex items-center justify-center gap-3 mb-6 sm:mb-8 mx-auto max-w-[200px]">
                                    <div className="flex-1 h-px bg-[var(--color-border-subtle)]" />
                                    <div className="size-1.5 rotate-45 bg-[var(--osool-deep-teal)]" />
                                    <div className="flex-1 h-px bg-[var(--color-border-subtle)]" />
                                </div>

                                {/* Suggestion Cards */}
                                <div className="flex flex-wrap justify-center gap-3 sm:gap-4 px-2 max-w-xl mx-auto">
                                    {[
                                        {
                                            icon: 'pin_drop',
                                            title: isRTL ? 'تحليل المناطق' : 'Area Analysis',
                                            hint: isRTL ? 'قارن أسعار التجمع وزايد' : 'Compare New Cairo vs Zayed',
                                        },
                                        {
                                            icon: 'trending_up',
                                            title: isRTL ? 'أفضل استثمار' : 'Top Investments',
                                            hint: isRTL ? 'أفضل عائد استثماري' : 'Best ROI properties',
                                        },
                                        {
                                            icon: 'domain',
                                            title: isRTL ? 'تقييم المطورين' : 'Developer Insight',
                                            hint: isRTL ? 'طلعت مصطفى مقابل بالم هيلز' : 'TMG vs Palm Hills',
                                        },
                                    ].map((suggestion, idx) => (
                                        <motion.button
                                            key={suggestion.title}
                                            initial={{ opacity: 0, y: 30, scale: 0.9 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            transition={{ duration: 0.5, delay: 0.4 + idx * 0.1, ease: [0.16, 1, 0.3, 1] }}
                                            whileHover={{ scale: 1.05, y: -5, boxShadow: '0 15px 35px rgba(18, 71, 89, 0.12)' }}
                                            whileTap={{ scale: 0.97 }}
                                            onClick={() => setInput(suggestion.hint)}
                                            className="welcome-suggestion group flex flex-col items-center gap-2 p-4 sm:p-5 rounded-2xl bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] hover:border-[var(--osool-deep-teal)]/30 transition-colors w-[140px] sm:w-[160px]"
                                        >
                                            <div className="size-10 sm:size-12 rounded-xl bg-[var(--osool-deep-teal)]/5 group-hover:bg-[var(--osool-deep-teal)]/10 flex items-center justify-center transition-colors">
                                                <MaterialIcon name={suggestion.icon} size="20px" className="text-[var(--osool-deep-teal)]" />
                                            </div>
                                            <span className="text-[11px] sm:text-xs font-bold text-[var(--color-text-main)]">
                                                {suggestion.title}
                                            </span>
                                            <span className="text-[9px] sm:text-[10px] text-[var(--color-text-muted-studio)] leading-tight line-clamp-2">
                                                {suggestion.hint}
                                            </span>
                                        </motion.button>
                                    ))}
                                </div>
                            </div>

                            {/* Centered Input - Full Width Premium Pill */}
                            <motion.div
                                ref={centeredInputRef}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
                                className={`welcome-input w-full px-4 sm:px-8 md:px-12 lg:px-20 ${isTransitioning ? 'opacity-0' : ''}`}
                            >
                                <div className="osool-input-glow">
                                    <div
                                        className="osool-input-surface cursor-text"
                                        onClick={() => textareaRef.current?.focus()}
                                    >
                                        <div className="relative flex items-center">
                                            {/* Plus button - absolute left */}
                                            <button
                                                aria-label={isRTL ? 'إضافة' : 'Add'}
                                                className="absolute start-2 sm:left-3 p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors z-10"
                                            >
                                                <Plus size={18} />
                                            </button>

                                            {/* Textarea - full width with padding for buttons */}
                                            <textarea
                                                ref={textareaRef}
                                                value={input}
                                                onChange={e => setInput(e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                rows={1}
                                                className={`w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-3 sm:py-4 px-10 sm:px-12 resize-none placeholder:text-[var(--color-text-muted-studio)]/60 text-[var(--color-text-main)] max-h-[150px] text-center${transcriptHighlight ? ' ring-2 ring-[var(--osool-deep-teal,#0d9488)]/40 rounded transition-colors duration-300' : ''}`}
                                                placeholder={isRTL ? 'اسأل CoInvestor عن العقارات...' : 'Ask CoInvestor about properties...'}
                                                disabled={isTyping || isTransitioning}
                                                dir="auto"
                                                autoFocus
                                            />

                                            {/* Right buttons - absolute right */}
                                            <div className="absolute end-2 sm:right-3 flex items-center gap-1 z-10">
                                                <VoiceOrb
                                                    status={voiceStatus}
                                                    amplitude={amplitude}
                                                    onClick={handleVoiceToggle}
                                                    isRTL={isRTL}
                                                    size="sm"
                                                />
                                                <button
                                                    onClick={handleSend}
                                                    disabled={!input.trim() || isTyping || isTransitioning}
                                                    aria-label={isRTL ? 'إرسال الرسالة' : 'Send message'}
                                                    className="osool-send-btn"
                                                >
                                                    <Send size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <p className="text-[8px] sm:text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.15em] sm:tracking-[0.2em] mt-3 sm:mt-4 opacity-50">
                                    {isRTL ? 'أصول AI · مدعوم بعقل الذئب' : 'Osool AI · Powered by Wolf Brain'}
                                </p>
                            </motion.div>
                        </div>
                    )}

                    {/* Chat Messages Area */}
                    <div className={`flex-1 overflow-y-auto px-3 sm:px-4 py-4 sm:py-8 md:px-8 lg:px-16 xl:px-20 space-y-4 sm:space-y-6 ${!hasStartedChat ? 'invisible' : ''}`}>
                        {messages.length > 0 && (
                            <>
                                {messages.map((msg, idx) => (
                                    <div key={msg.id || idx} className={msg.role === 'user' ? 'animate-msg-user' : 'animate-msg-ai'}>
                                        {(() => {
                                            // 1. Detect language direction per-message (Basic + Extended + Presentation forms)
                                            const isArabicContent = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/.test(msg.content || '');
                                            // The message is RTL if global app is RTL OR if the content itself is Arabic
                                            const isMsgRtl = isRTL || isArabicContent;

                                            // 2. Formatting constants
                                            const alignClass = isMsgRtl ? 'text-end' : 'text-start';
                                            const dirAttr = isMsgRtl ? 'rtl' : 'ltr';
                                            const marginClass = isMsgRtl ? 'me-0' : 'ms-0';

                                            return (
                                                <>
                                                    {msg.role === 'user' ? (
                                                        /* User Message - Deep teal bubble */
                                                        <div className="flex justify-end">
                                                            <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[65%] lg:max-w-[55%] flex flex-col items-end">
                                                                <div
                                                                    className={`user-message-bubble px-5 sm:px-6 py-3 sm:py-4 shadow-md ${isRTL
                                                                        ? 'rounded-t-[var(--radius-message)] rounded-br-[var(--radius-message)] rounded-bl-[4px]'
                                                                        : 'rounded-t-[var(--radius-message)] rounded-bl-[var(--radius-message)] rounded-br-[4px]'
                                                                        }`}
                                                                >
                                                                    <p className="text-[13px] sm:text-[14px] leading-relaxed font-normal" dir="auto">
                                                                        {msg.content}
                                                                    </p>
                                                                </div>
                                                                <span className="mt-2 text-[9px] sm:text-[10px] font-medium text-[var(--color-text-muted-studio)] opacity-40">
                                                                    {getUserName()} · {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        /* AI Message - Sidebar Layout */
                                                        <div
                                                            className={`max-w-4xl w-full flex items-start gap-3 sm:gap-4 relative z-10 ${isMsgRtl ? 'flex-row-reverse' : 'flex-row'}`}
                                                        >
                                                            {/* 1. Avatar Column (Sidebar) */}
                                                            <div className="flex-shrink-0 mt-1">
                                                                <CoInvestorAvatar size="sm" thinking={msg.isTyping} showStatus={false} />
                                                            </div>

                                                            {/* 2. Content Stack (Name + Bubble) */}
                                                            <div className={`flex flex-col flex-1 min-w-0 ${isMsgRtl ? 'items-end' : 'items-start'}`}>

                                                                {/* Name Row */}
                                                                <div className={`flex items-center gap-2 mb-1 ${isMsgRtl ? 'flex-row-reverse' : 'flex-row'}`}>
                                                                    <span className="text-[12px] font-bold text-[var(--osool-deep-teal)] select-none">
                                                                        {isMsgRtl ? 'CoInvestor' : 'CoInvestor'}
                                                                    </span>
                                                                    <span className="text-[9px] text-[var(--color-text-muted-studio)] opacity-50 select-none">
                                                                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                                    </span>
                                                                </div>

                                                                {/* Message body */}
                                                                <div
                                                                    className={`ai-message-body w-full ${msg.isTyping && !msg.content ? 'streaming' : ''} ${marginClass}`}
                                                                    data-dir={isMsgRtl ? 'rtl' : 'ltr'}
                                                                >
                                                                    {/* Accent border - positioned based on direction */}
                                                                    <div className="ai-accent-border" />

                                                                    <div className={`p-4 sm:p-5 ${isMsgRtl ? 'pe-5 sm:pr-6' : 'ps-5 sm:pl-6'}`}>
                                                                        {msg.isTyping && !msg.content ? (
                                                                            /* Typing Indicator (Bar) */
                                                                            <div className="flex flex-col gap-2">
                                                                                <div className={`flex ${isMsgRtl ? 'justify-end' : 'justify-start'} px-4`}>
                                                                                    <div className="bg-[var(--ai-surface)] p-3 rounded-2xl rounded-ss-none border border-[var(--ai-surface-border)] shadow-sm">
                                                                                        <div className="typing-bar" />
                                                                                    </div>
                                                                                </div>
                                                                                <span className="text-[12px] text-[var(--color-text-muted-studio)] px-4">
                                                                                    {isMsgRtl ? 'جاري التحليل...' : 'Analyzing...'}
                                                                                </span>
                                                                            </div>
                                                                        ) : (
                                                                            <>
                                                                                <div
                                                                                    className={`ai-message-content text-[13px] sm:text-sm leading-relaxed text-[var(--color-text-main)] prose prose-sm dark:prose-invert max-w-none prose-headings:text-[var(--osool-deep-teal)] prose-strong:text-[var(--osool-deep-teal)] prose-code:bg-[var(--osool-deep-teal)]/5 prose-code:text-[var(--osool-deep-teal)] prose-code:rounded prose-code:px-1.5 prose-code:py-0.5 prose-table:border-collapse prose-th:border prose-th:border-[var(--color-border-subtle)] prose-th:p-2 prose-td:border prose-td:border-[var(--color-border-subtle)] prose-td:p-2`}
                                                                                    dir={dirAttr}
                                                                                >
                                                                                    <ReactMarkdown
                                                                                        remarkPlugins={[remarkGfm]}
                                                                                        // rehypePlugins removed - rehypeRaw can cause XSS
                                                                                        components={{
                                                                                            p: ({ node, ...props }) => <p className={`mb-3 last:mb-0 leading-relaxed ${alignClass}`} {...props} />,
                                                                                            strong: ({ node, ...props }) => <strong className="font-bold text-[var(--osool-deep-teal)]" {...props} />,
                                                                                            ul: ({ node, ...props }) => <ul className={`list-disc ${isMsgRtl ? 'me-5' : 'ms-5'} mb-3 ${alignClass}`} {...props} />,
                                                                                            ol: ({ node, ...props }) => <ol className={`list-decimal ${isMsgRtl ? 'me-5' : 'ms-5'} mb-3 ${alignClass}`} {...props} />,
                                                                                            h2: ({ node, ...props }) => <h2 className={`text-lg font-bold text-[var(--osool-deep-teal)] mt-4 mb-2 ${alignClass}`} {...props} />,
                                                                                            h3: ({ node, ...props }) => <h3 className={`text-base font-bold text-[var(--osool-deep-teal)] mt-3 mb-2 ${alignClass}`} {...props} />,
                                                                                            table: ({ node, ...props }) => (
                                                                                                <div className="overflow-x-auto my-4 rounded-lg border border-[var(--color-border-subtle)]">
                                                                                                    <table className={`w-full border-collapse text-sm ${alignClass}`} {...props} />
                                                                                                </div>
                                                                                            ),
                                                                                            th: ({ node, ...props }) => <th className={`border border-[var(--color-border-subtle)] p-2 bg-[var(--ai-surface)] font-bold ${alignClass}`} {...props} />,
                                                                                            td: ({ node, ...props }) => <td className={`border border-[var(--color-border-subtle)] p-2 ${alignClass}`} {...props} />,
                                                                                            code: ({ inline, className, children, ...props }: MarkdownCodeProps) => {
                                                                                                const match = /language-(\w+)/.exec(className || '');
                                                                                                return !inline && match ? (
                                                                                                    <CodeBlock language={match[1]} value={String(children).replace(/\n$/, '')} />
                                                                                                ) : (
                                                                                                    <code className="bg-[var(--osool-deep-teal)]/10 text-[var(--osool-deep-teal)] px-1.5 py-0.5 rounded font-mono text-sm" {...props}>
                                                                                                        {children}
                                                                                                    </code>
                                                                                                );
                                                                                            },
                                                                                            blockquote: ({ node, ...props }) => (
                                                                                                <blockquote className={`border-${isMsgRtl ? 'r' : 'l'}-4 border-[var(--osool-deep-teal)] ${isMsgRtl ? 'pe-4' : 'ps-4'} my-4 italic bg-[var(--ai-surface)] p-3 rounded-${isMsgRtl ? 'l' : 'r'}`} {...props} />
                                                                                            )
                                                                                        }}
                                                                                    >
                                                                                        {cleanMessageContent(msg.content)}
                                                                                    </ReactMarkdown>
                                                                                </div>

                                                                                {/* Action bar */}
                                                                                {!msg.isTyping && msg.content && (
                                                                                    <div className="ai-message-actions mt-3 pt-3 border-t border-[var(--ai-surface-border)]">
                                                                                        <button
                                                                                            onClick={() => handleCopyMessage(msg.id, msg.content)}
                                                                                            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-medium text-[var(--color-text-muted-studio)] hover:bg-[var(--color-studio-gray)] hover:text-[var(--color-text-main)] transition-colors"
                                                                                        >
                                                                                            {copiedMsgId === msg.id ? <Check size={12} /> : <Copy size={12} />}
                                                                                            {copiedMsgId === msg.id ? (isRTL ? 'تم النسخ' : 'Copied') : (isRTL ? 'نسخ' : 'Copy')}
                                                                                        </button>
                                                                                        <button className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-medium text-[var(--color-text-muted-studio)] hover:bg-[var(--color-studio-gray)] hover:text-[var(--color-text-main)] transition-colors">
                                                                                            <Bookmark size={12} />
                                                                                            {isRTL ? 'حفظ' : 'Save'}
                                                                                        </button>
                                                                                    </div>
                                                                                )}
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                </div>

                                                                {/* Featured Property Cards - Show ALL recommended properties */}
                                                                <AnimatePresence>
                                                                    {(msg.properties?.length ?? 0) > 0 && (
                                                                        <motion.div
                                                                            initial={{ opacity: 0, height: 0 }}
                                                                            animate={{ opacity: 1, height: 'auto' }}
                                                                            transition={{ duration: 0.4, ease: 'easeOut' }}
                                                                            className={`mt-3 space-y-3 overflow-hidden ${marginClass}`}
                                                                        >
                                                                            {msg.properties?.map((property, propIdx: number) => (
                                                                                <motion.div
                                                                                    key={property.id || propIdx}
                                                                                    initial={{ opacity: 0, y: 10 }}
                                                                                    animate={{ opacity: 1, y: 0 }}
                                                                                    transition={{ delay: propIdx * 0.1 }}
                                                                                >
                                                                                    <FeaturedPropertyCard
                                                                                        property={property}
                                                                                        onRequestDetails={() => { }}
                                                                                        onBookmark={() => { }}
                                                                                        isRTL={isMsgRtl}
                                                                                    />
                                                                                </motion.div>
                                                                            ))}
                                                                        </motion.div>
                                                                    )}
                                                                </AnimatePresence>

                                                                {/* Compact Visualizations */}
                                                                <AnimatePresence>
                                                                    {(msg.visualizations?.length ?? 0) > 0 && (
                                                                        <motion.div
                                                                            initial={{ opacity: 0, height: 0 }}
                                                                            animate={{ opacity: 1, height: 'auto' }}
                                                                            transition={{ duration: 0.4, ease: 'easeOut', delay: 0.15 }}
                                                                            className={`mt-3 space-y-2 sm:space-y-3 overflow-hidden ${marginClass}`}
                                                                        >
                                                                            <UnifiedAnalytics visualizations={msg.visualizations || []} isRTL={isMsgRtl} />
                                                                        </motion.div>
                                                                    )}
                                                                </AnimatePresence>
                                                            </div>
                                                        </div>
                                                    )}
                                                </>
                                            );
                                        })()}
                                    </div >
                                ))}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Bottom Input Area - Premium Pill or Lead Handoff */}
                    {hasStartedChat && (
                        <div className="p-2 sm:p-4 lg:p-6 z-30 safe-area-bottom">
                            <div className="max-w-3xl mx-auto">
                                {leadScore >= 80 ? (
                                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between shadow-lg">
                                        <div className="flex items-center gap-3 mb-4 md:mb-0">
                                            <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center text-white shrink-0">
                                                <MaterialIcon name="support_agent" />
                                            </div>
                                            <div>
                                                <h4 className="text-[13px] md:text-sm font-bold text-emerald-800 dark:text-emerald-400">
                                                    {isRTL ? 'أنت مستثمر جاد!' : 'Priority Investor Status'}
                                                </h4>
                                                <p className="text-[11px] md:text-xs text-emerald-600 dark:text-emerald-500">
                                                    {isRTL ? 'تحدث مباشرة مع خبير عقاري محترف الآن.' : 'Talk directly to a senior real estate expert now.'}
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => window.open('https://wa.me/201000000000?text=Hello+from+Osool', '_blank')}
                                            className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold py-2.5 px-6 rounded-xl transition shadow-md shadow-emerald-500/20 whitespace-nowrap"
                                        >
                                            {isRTL ? 'تواصل عبر واتساب' : 'Connect on WhatsApp'}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-2">
                                        {/* Warm lead soft CTA — appears above input when score is 60-79 */}
                                        {leadScore >= 60 && leadScore < 80 && (
                                            <div className="bg-blue-500/5 border border-blue-500/15 rounded-xl px-4 py-2.5 flex items-center justify-between">
                                                <p className="text-xs text-blue-600 dark:text-blue-400">
                                                    {isRTL
                                                        ? 'يبدو إنك وصلت لمرحلة متقدمة. محتاج تتكلم مع خبير؟'
                                                        : 'You seem ready for the next step. Want to talk to an expert?'}
                                                </p>
                                                <button
                                                    onClick={() => window.open('https://wa.me/201000000000?text=Hello+from+Osool', '_blank')}
                                                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap ms-3"
                                                >
                                                    {isRTL ? 'تواصل ←' : 'Connect →'}
                                                </button>
                                            </div>
                                        )}
                                    <div className="osool-input-glow">
                                        <div
                                            className="osool-input-surface cursor-text"
                                            onClick={() => textareaRef.current?.focus()}
                                        >
                                            <div className="relative flex items-center">
                                                {/* Plus button - absolute left */}
                                                <button
                                                    aria-label={isRTL ? 'إضافة' : 'Add'}
                                                    className="absolute start-2 sm:left-3 p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors z-10"
                                                >
                                                    <Plus size={18} />
                                                </button>

                                                {/* Textarea - full width with padding for buttons */}
                                                <textarea
                                                    ref={textareaRef}
                                                    value={input}
                                                    onChange={e => setInput(e.target.value)}
                                                    onKeyDown={handleKeyDown}
                                                    rows={1}
                                                    className={`w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-3 sm:py-3.5 px-10 sm:px-12 resize-none placeholder:text-[var(--color-text-muted-studio)]/60 text-[var(--color-text-main)] max-h-[150px]${transcriptHighlight ? ' ring-2 ring-[var(--osool-deep-teal,#0d9488)]/40 rounded transition-colors duration-300' : ''}`}
                                                    placeholder={isRTL ? 'اسأل CoInvestor...' : 'Ask CoInvestor...'}
                                                    disabled={isTyping}
                                                    dir="auto"
                                                />

                                                {/* Right buttons - absolute right */}
                                                <div className="absolute end-2 sm:right-3 flex items-center gap-1 z-10">
                                                    <VoiceOrb
                                                        status={voiceStatus}
                                                        amplitude={amplitude}
                                                        onClick={handleVoiceToggle}
                                                        isRTL={isRTL}
                                                        size="sm"
                                                        className="hidden sm:flex"
                                                    />
                                                    <button
                                                        onClick={handleSend}
                                                        disabled={!input.trim() || isTyping}
                                                        aria-label={isRTL ? 'إرسال الرسالة' : 'Send message'}
                                                        className="osool-send-btn"
                                                    >
                                                        <Send size={16} />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    </div>
                                )}
                                <p className="hidden sm:block text-[8px] sm:text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.15em] sm:tracking-[0.2em] mt-2 sm:mt-3 opacity-50">
                                    {isRTL ? 'أصول AI · مدعوم بعقل الذئب' : 'Osool AI · Powered by Wolf Brain'}
                                </p>
                            </div>
                        </div>
                    )}
                </main>

                {/* Right Contextual Pane */}
                <ContextualInsights
                    properties={contextProperties}
                    currentIndex={contextPropertyIndex}
                    onPrev={() => setContextPropertyIndex(Math.max(0, contextPropertyIndex - 1))}
                    onNext={() => setContextPropertyIndex(Math.min(contextProperties.length - 1, contextPropertyIndex + 1))}
                    aiInsight={contextInsight}
                    visualizations={contextVisualizations}
                    isRTL={isRTL}
                />
            </div >

            <InvitationModal isOpen={isInvitationModalOpen} onClose={() => setInvitationModalOpen(false)} />
        </div >
    );
}
