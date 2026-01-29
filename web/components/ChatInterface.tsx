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
import {
    emptyChatToActiveTransition,
    messageBubbleEnter,
    sendButtonPress,
    suggestionCardHover,
    suggestionCardUnhover,
    quickActionsEnter
} from '@/lib/animations';
import VisualizationRenderer from './visualizations/VisualizationRenderer';
import UnifiedAnalytics from './visualizations/UnifiedAnalytics';
import InvitationModal from './InvitationModal';
import { User, LogOut, Gift, PlusCircle, History, Send, Mic, Plus, Bookmark, Copy, Check } from 'lucide-react';

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
// AMR AVATAR - Distinctive AI Identity
// ============================================

function AmrAvatar({
    size = 'sm',
    thinking = false,
    showStatus = true,
    isRTL = false
}: {
    size?: 'sm' | 'md' | 'lg';
    thinking?: boolean;
    showStatus?: boolean;
    isRTL?: boolean;
}) {
    return (
        <div className="amr-avatar" data-size={size}>
            {/* Animated pulse ring */}
            <div className={`amr-avatar-ring ${thinking ? 'active' : ''}`} />
            {/* Main surface with gradient and monogram */}
            <div className={`amr-avatar-surface ${thinking ? 'thinking' : ''}`}>
                <span className="amr-avatar-monogram">A</span>
            </div>
            {/* Status dot */}
            {showStatus && (
                <div className={`amr-avatar-status ${isRTL ? 'rtl' : ''}`} />
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
                            className="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
                            src={property.image_url}
                        />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 flex items-center justify-center">
                            <MaterialIcon name="apartment" className="text-slate-400" size="48px" />
                        </div>
                    )}
                    <div className={`absolute bottom-0 p-4 sm:p-6 lg:p-10 bg-gradient-to-t from-black/50 to-transparent w-full ${isRTL ? 'right-0' : 'left-0'}`}>
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
                                    {isRTL ? 'العائد' : 'ROI'}
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
        <aside className={`w-64 flex-none bg-[var(--sidebar-bg)] hidden lg:flex flex-col ${isRTL ? 'border-l' : 'border-r'} border-[var(--color-border-subtle)]`}>
            {/* Brand Header */}
            <div className="p-5 pb-4">
                <div className="flex items-center gap-3 mb-5">
                    <AmrAvatar size="sm" showStatus={false} />
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
                            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[11px] font-medium text-[var(--color-text-muted-studio)] hover:bg-[var(--sidebar-hover)] hover:text-[var(--color-text-main)] transition-all group ${isRTL ? 'text-right' : 'text-left'}`}
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
                        <button className="hover:text-[var(--color-text-main)] transition-colors">
                            <MaterialIcon name="settings" size="18px" />
                        </button>
                        <button className="hover:text-[var(--color-text-main)] transition-colors">
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

    const hasContent = property || aiInsight || visualizations.length > 0;

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

    const getKeyMetric = (viz: any): string => {
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
            className={`w-80 flex-none bg-[var(--sidebar-bg)] hidden xl:flex flex-col overflow-hidden ${isRTL ? 'border-r' : 'border-l'} border-[var(--color-border-subtle)]`}
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
                    <span className={`${isRTL ? 'mr-auto' : 'ml-auto'} text-[8px] px-2 py-0.5 bg-emerald-500/10 text-emerald-600 rounded-full font-bold tracking-wider uppercase`}>
                        Live
                    </span>
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
                                        <AmrAvatar size="sm" showStatus={false} />
                                        <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">
                                            {isRTL ? 'تحليل عمرو' : 'AMR Analysis'}
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
                            <AmrAvatar size="md" thinking={false} showStatus={false} />
                            <p className="text-[11px] text-[var(--color-text-muted-studio)] mt-4 mb-5">
                                {isRTL ? 'اسأل عمرو للبدء' : 'Ask AMR to start analyzing'}
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

function CompactVisualization({ viz, isRTL }: { viz: any; isRTL: boolean }) {
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
        <div className="rounded-xl border border-[var(--color-border-subtle)] overflow-hidden bg-[var(--color-studio-white)]" dir={isRTL ? 'rtl' : 'ltr'}>
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full px-3 sm:px-4 py-2.5 sm:py-3 flex items-center gap-2 bg-gradient-to-r from-slate-50 to-white dark:from-slate-800/50 dark:to-slate-900/50 hover:from-slate-100 hover:to-slate-50 dark:hover:from-slate-700/50 dark:hover:to-slate-800/50 transition-colors"
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
                    <VisualizationRenderer type={viz.type} data={viz.data} isRTL={isRTL} />
                </div>
                {!expanded && (
                    <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[var(--color-studio-white)] to-transparent pointer-events-none" />
                )}
            </motion.div>
        </div>
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
    const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

    // First message state
    const [hasStartedChat, setHasStartedChat] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false);

    // Contextual state
    const [contextProperty, setContextProperty] = useState<Property | null>(null);
    const [contextInsight, setContextInsight] = useState<string | null>(null);
    const [contextVisualizations, setContextVisualizations] = useState<any[]>([]);
    const [, setDetectedAnalytics] = useState<AnalyticsMatch[]>([]);

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const welcomeRef = useRef<HTMLDivElement>(null);
    const centeredInputRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const isRTL = language === 'ar';

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

                    if (data.properties?.length > 0) {
                        setContextProperty(data.properties[0]);
                    }

                    if (data.ui_actions?.length > 0) {
                        const prioritizedAnalytics = data.ui_actions
                            .sort((a: any, b: any) => (b.priority || 0) - (a.priority || 0))
                            .slice(0, 3);
                        setContextVisualizations(prioritizedAnalytics);
                    }

                    const insight = extractInsight(fullResponse);
                    if (insight) {
                        setContextInsight(insight);
                    }

                    setIsTyping(false);
                },
                onFollowUp: (followUp) => {
                    // Create a delayed follow-up AI message
                    const followUpId = (Date.now() + 2).toString();
                    const followUpText = isRTL
                        ? (followUp.message_ar || followUp.message_en || '')
                        : (followUp.message_en || followUp.message_ar || '');
                    if (followUpText) {
                        setMessages(prev => [...prev, {
                            role: 'amr',
                            content: followUpText,
                            id: followUpId,
                            isTyping: false,
                            isFollowUp: true,
                        }]);
                        scrollToBottom();
                    }
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
                                        className={`absolute mt-2 w-48 sm:w-56 rounded-xl bg-white dark:bg-[var(--color-studio-white)] border border-[var(--color-border-subtle)] shadow-xl z-[60] ${isRTL ? 'left-0' : 'right-0'}`}
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
                                {/* AMR Avatar - Large */}
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-avatar flex justify-center mb-5 sm:mb-6"
                                >
                                    <AmrAvatar size="lg" thinking={false} showStatus={true} isRTL={isRTL} />
                                </motion.div>

                                {/* Greeting */}
                                <motion.h2
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.5, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-title text-xl sm:text-2xl lg:text-3xl font-bold text-[var(--color-text-main)] mb-2"
                                >
                                    {isRTL ? (
                                        <span style={{ fontFamily: 'Cairo, sans-serif' }}>مرحبا، أنا عمرو</span>
                                    ) : (
                                        <span className="font-serif italic">Hello, I&apos;m AMR</span>
                                    )}
                                </motion.h2>
                                <motion.p
                                    initial={{ opacity: 0, y: 15 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.4, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                                    className="welcome-subtitle text-sm sm:text-base text-[var(--color-text-muted-studio)] mb-6 sm:mb-8"
                                >
                                    {isRTL ? 'ذكاءك العقاري الشخصي' : 'Your AI Real Estate Intelligence'}
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
                                            <button className="absolute left-2 sm:left-3 p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors z-10">
                                                <Plus size={18} />
                                            </button>

                                            {/* Textarea - full width with padding for buttons */}
                                            <textarea
                                                ref={textareaRef}
                                                value={input}
                                                onChange={e => setInput(e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                rows={1}
                                                className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-3 sm:py-4 px-10 sm:px-12 resize-none placeholder:text-[var(--color-text-muted-studio)]/60 text-[var(--color-text-main)] max-h-[150px] text-center"
                                                placeholder={isRTL ? 'اسأل عمرو عن العقارات...' : 'Ask AMR about properties...'}
                                                disabled={isTyping || isTransitioning}
                                                dir="auto"
                                                autoFocus
                                            />

                                            {/* Right buttons - absolute right */}
                                            <div className="absolute right-2 sm:right-3 flex items-center gap-1 z-10">
                                                <button className="hidden sm:block p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors">
                                                    <Mic size={18} />
                                                </button>
                                                <button
                                                    onClick={handleSend}
                                                    disabled={!input.trim() || isTyping || isTransitioning}
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
                                        {msg.role === 'user' ? (
                                            /* User Message - Deep teal bubble */
                                            <div className="flex justify-end">
                                                <div className="max-w-[85%] sm:max-w-[75%] md:max-w-[65%] lg:max-w-[55%] flex flex-col items-end">
                                                    <div
                                                        className={`px-5 sm:px-6 py-3 sm:py-4 shadow-md ${isRTL
                                                                ? 'rounded-t-[var(--radius-message)] rounded-br-[var(--radius-message)] rounded-bl-[4px]'
                                                                : 'rounded-t-[var(--radius-message)] rounded-bl-[var(--radius-message)] rounded-br-[4px]'
                                                            }`}
                                                        style={{
                                                            background: 'var(--user-surface)',
                                                            color: 'var(--user-surface-text)',
                                                        }}
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
                                            /* AI Message - Tinted surface with accent border */
                                            <div className="max-w-4xl">
                                                {/* AMR header */}
                                                <div className="flex items-center gap-2.5 mb-2">
                                                    <AmrAvatar size="sm" thinking={msg.isTyping} showStatus={false} />
                                                    <span className="text-[12px] font-bold text-[var(--osool-deep-teal)]">
                                                        {isRTL ? 'عمرو' : 'AMR'}
                                                    </span>
                                                    <span className="text-[9px] text-[var(--color-text-muted-studio)] opacity-50">
                                                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>

                                                {/* Message body */}
                                                <div className={`ai-message-body ${msg.isTyping && !msg.content ? 'streaming' : ''} ${isRTL ? 'mr-2 sm:mr-10' : 'ml-2 sm:ml-10'}`}>
                                                    {/* Accent border */}
                                                    <div className="ai-accent-border" />

                                                    <div className={`p-4 sm:p-5 ${isRTL ? 'pr-5 sm:pr-6' : 'pl-5 sm:pl-6'}`}>
                                                        {msg.isTyping && !msg.content ? (
                                                            /* Typing indicator */
                                                            <div className="flex items-center gap-3">
                                                                <div className="flex gap-1">
                                                                    <span className="size-1.5 rounded-full bg-[var(--osool-deep-teal)] animate-bounce" style={{ animationDelay: '0ms' }} />
                                                                    <span className="size-1.5 rounded-full bg-[var(--osool-deep-teal)] animate-bounce" style={{ animationDelay: '150ms' }} />
                                                                    <span className="size-1.5 rounded-full bg-[var(--osool-deep-teal)] animate-bounce" style={{ animationDelay: '300ms' }} />
                                                                </div>
                                                                <span className="text-[12px] text-[var(--color-text-muted-studio)]">
                                                                    {isRTL ? 'جاري التحليل...' : 'Analyzing...'}
                                                                </span>
                                                            </div>
                                                        ) : (
                                                            <>
                                                                <div
                                                                    className="ai-message-content text-[13px] sm:text-sm leading-relaxed text-[var(--color-text-main)] prose prose-sm max-w-none prose-headings:text-[var(--osool-deep-teal)] prose-strong:text-[var(--osool-deep-teal)] prose-code:bg-[var(--osool-deep-teal)]/5 prose-code:text-[var(--osool-deep-teal)] prose-code:rounded prose-code:px-1.5 prose-code:py-0.5"
                                                                    dir="auto"
                                                                >
                                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                                        {sanitizeContent(msg.content)}
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

                                                {/* Featured Property Card */}
                                                <AnimatePresence>
                                                    {msg.properties?.length > 0 && (
                                                        <motion.div
                                                            initial={{ opacity: 0, height: 0 }}
                                                            animate={{ opacity: 1, height: 'auto' }}
                                                            transition={{ duration: 0.4, ease: 'easeOut' }}
                                                            className={`mt-3 overflow-hidden ${isRTL ? 'mr-2 sm:mr-10' : 'ml-2 sm:ml-10'}`}
                                                        >
                                                            <FeaturedPropertyCard
                                                                property={msg.properties[0]}
                                                                onRequestDetails={() => { }}
                                                                onBookmark={() => { }}
                                                                isRTL={isRTL}
                                                            />
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>

                                                {/* Compact Visualizations */}
                                                <AnimatePresence>
                                                    {msg.visualizations?.length > 0 && (
                                                        <motion.div
                                                            initial={{ opacity: 0, height: 0 }}
                                                            animate={{ opacity: 1, height: 'auto' }}
                                                            transition={{ duration: 0.4, ease: 'easeOut', delay: 0.15 }}
                                                            className={`mt-3 space-y-2 sm:space-y-3 overflow-hidden ${isRTL ? 'mr-2 sm:mr-10' : 'ml-2 sm:ml-10'}`}
                                                        >
                                                            <UnifiedAnalytics visualizations={msg.visualizations} isRTL={isRTL} />
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Bottom Input Area - Premium Pill */}
                    {hasStartedChat && (
                        <div className="p-2 sm:p-4 lg:p-6 z-30 safe-area-bottom">
                            <div className="max-w-3xl mx-auto">
                                <div className="osool-input-glow">
                                    <div
                                        className="osool-input-surface cursor-text"
                                        onClick={() => textareaRef.current?.focus()}
                                    >
                                        <div className="relative flex items-center">
                                            {/* Plus button - absolute left */}
                                            <button className="absolute left-2 sm:left-3 p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors z-10">
                                                <Plus size={18} />
                                            </button>

                                            {/* Textarea - full width with padding for buttons */}
                                            <textarea
                                                ref={textareaRef}
                                                value={input}
                                                onChange={e => setInput(e.target.value)}
                                                onKeyDown={handleKeyDown}
                                                rows={1}
                                                className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm py-3 sm:py-3.5 px-10 sm:px-12 resize-none placeholder:text-[var(--color-text-muted-studio)]/60 text-[var(--color-text-main)] max-h-[150px]"
                                                placeholder={isRTL ? 'اسأل عمرو...' : 'Ask AMR...'}
                                                disabled={isTyping}
                                                dir="auto"
                                            />

                                            {/* Right buttons - absolute right */}
                                            <div className="absolute right-2 sm:right-3 flex items-center gap-1 z-10">
                                                <button className="hidden sm:block p-1.5 text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)] transition-colors">
                                                    <Mic size={18} />
                                                </button>
                                                <button
                                                    onClick={handleSend}
                                                    disabled={!input.trim() || isTyping}
                                                    className="osool-send-btn"
                                                >
                                                    <Send size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <p className="hidden sm:block text-[8px] sm:text-[9px] text-center text-[var(--color-text-muted-studio)] uppercase tracking-[0.15em] sm:tracking-[0.2em] mt-2 sm:mt-3 opacity-50">
                                    {isRTL ? 'أصول AI · مدعوم بعقل الذئب' : 'Osool AI · Powered by Wolf Brain'}
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
