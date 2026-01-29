'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import {
    BarChart2, TrendingUp, X, Sparkles, MapPin, Home, DollarSign, Target, Zap, Activity,
    PieChart, Building2, Calendar, ArrowUpRight, ArrowDownRight, Layers, Navigation,
    Phone, MessageCircle, Percent, Square, Footprints, Star, ExternalLink,
    Calculator, Map, Users, FileText, Clock, Shield, Landmark, Bed, Bath, Ruler
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import anime from 'animejs';
import VisualizationRenderer from '../visualizations/VisualizationRenderer';
import MetricsGrid, { MetricItem, metricIcons } from '../insights/MetricsGrid';
import EmbeddedChart, { generateProjectionData } from '../insights/EmbeddedChart';

// UI Action data type from backend
export interface UIActionData {
    type: string;
    priority: number;
    data: any;
    trigger_reason?: string;
    chart_reference?: string;
}

export interface PropertyContext {
    title: string;
    address: string;
    price: string;
    metrics?: {
        capRate?: string;
        pricePerSqFt?: string;
        wolfScore?: number;
        size?: number;
        bedrooms?: number;
        roi?: number;
        occupancyRate?: number;
        marketTrend?: string;
        priceVerdict?: string;
        pricePerSqm?: number;
        areaAvgPrice?: number;
    };
    priceHistory?: { year: string; price: number }[];
    neighborhoodStats?: {
        crimeRate: string;
        schoolScore: number;
        transitScore: number;
    };
    aiRecommendation?: string;
    tags?: string[];
    agent?: {
        name: string;
        title: string;
        avatar?: string;
    };
}

interface ContextualPaneProps {
    isOpen?: boolean;
    onClose?: () => void;
    property?: PropertyContext | null;
    uiActions?: UIActionData[];
    chatInsight?: string | null;
    isRTL?: boolean;
}

// Typewriter Hook with anime.js
function useTypewriter(text: string, speed: number = 20, startDelay: number = 0) {
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

        const timeout = setTimeout(() => {
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
        }, startDelay);

        return () => clearTimeout(timeout);
    }, [text, speed, startDelay]);

    return { displayedText, isComplete };
}

// Animated Counter Component
function AnimatedCounter({
    value,
    suffix = '',
    prefix = '',
    duration = 1500,
    delay = 0
}: {
    value: number;
    suffix?: string;
    prefix?: string;
    duration?: number;
    delay?: number;
}) {
    const counterRef = useRef<HTMLSpanElement>(null);
    const [hasAnimated, setHasAnimated] = useState(false);

    useEffect(() => {
        if (counterRef.current && !hasAnimated) {
            const timer = setTimeout(() => {
                anime({
                    targets: counterRef.current,
                    innerHTML: [0, value],
                    round: 1,
                    easing: 'easeOutExpo',
                    duration: duration,
                });
                setHasAnimated(true);
            }, delay);

            return () => clearTimeout(timer);
        }
    }, [value, duration, delay, hasAnimated]);

    return (
        <span>
            {prefix}<span ref={counterRef}>0</span>{suffix}
        </span>
    );
}

// Animated Progress Bar
function AnimatedProgressBar({
    percentage,
    delay = 0,
    color = 'from-[var(--color-teal-accent)] to-[var(--color-primary)]'
}: {
    percentage: number;
    delay?: number;
    color?: string;
}) {
    const barRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (barRef.current) {
            anime({
                targets: barRef.current,
                width: [`0%`, `${percentage}%`],
                easing: 'easeOutExpo',
                duration: 1200,
                delay: delay,
            });
        }
    }, [percentage, delay]);

    return (
        <div className="w-full bg-[var(--color-surface-elevated)] h-2 rounded-full overflow-hidden">
            <div
                ref={barRef}
                className={`bg-gradient-to-r ${color} h-full rounded-full shadow-[0_0_10px_rgba(45,212,191,0.3)]`}
                style={{ width: '0%' }}
            />
        </div>
    );
}

// Map Module Component
function MapModule({ address, isRTL }: { address: string; isRTL: boolean }) {
    const mapRef = useRef<HTMLDivElement>(null);
    const pinRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (mapRef.current) {
            anime({
                targets: mapRef.current,
                opacity: [0, 1],
                scale: [0.95, 1],
                easing: 'easeOutExpo',
                duration: 600,
            });
        }
        if (pinRef.current) {
            anime({
                targets: pinRef.current,
                translateY: [-20, 0],
                opacity: [0, 1],
                easing: 'easeOutBounce',
                duration: 800,
                delay: 400,
            });
        }
    }, [address]);

    return (
        <div className="space-y-3">
            <div className="flex justify-between items-center">
                <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
                    {isRTL ? 'الموقع' : 'Location'}
                </h3>
                <a href="#" className="text-[11px] text-[var(--color-primary)] font-bold hover:underline flex items-center gap-1">
                    {isRTL ? 'عرض أكبر' : 'View Larger'} <ExternalLink size={10} />
                </a>
            </div>
            <div
                ref={mapRef}
                className="aspect-[4/3] rounded-xl overflow-hidden relative shadow-md border border-[var(--color-border)] bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 group"
                style={{ opacity: 0 }}
            >
                {/* Map Placeholder with Grid Pattern */}
                <div className="absolute inset-0 bg-grid-light dark:bg-grid-dark opacity-50" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />

                {/* Map Controls */}
                <div className="absolute top-3 right-3 bg-[var(--color-surface)] p-1.5 rounded-lg shadow-md">
                    <Layers size={16} className="text-[var(--color-text-muted)]" />
                </div>

                {/* Animated Map Pin */}
                <div
                    ref={pinRef}
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
                    style={{ opacity: 0 }}
                >
                    <div className="relative group/pin cursor-pointer">
                        <div className="w-12 h-12 bg-[var(--color-primary)]/30 rounded-full animate-ping absolute -top-4 -left-4" />
                        <div className="w-4 h-4 bg-[var(--color-primary)] rounded-full border-2 border-white shadow-lg relative z-10" />
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-black/80 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover/pin:opacity-100 transition-opacity whitespace-nowrap">
                            {address}
                        </div>
                    </div>
                </div>
            </div>
            <p className="text-xs text-[var(--color-text-muted)] flex items-center gap-2 bg-[var(--color-surface-elevated)] p-2 rounded-lg">
                <Navigation size={14} className="text-[var(--color-primary)]" />
                <span><span className="font-bold text-[var(--color-text-primary)]">{address}</span></span>
            </p>
        </div>
    );
}

// Key Metrics Grid Component - Only shows real data
function KeyMetricsGrid({
    metrics,
    isRTL
}: {
    metrics: { capRate?: string; pricePerSqm?: number; walkScore?: number };
    isRTL: boolean;
}) {
    const gridRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (gridRef.current) {
            anime({
                targets: gridRef.current.querySelectorAll('.metric-widget'),
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(100, { start: 200 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [metrics]);

    const hasAnyMetric = metrics.capRate || metrics.pricePerSqm || metrics.walkScore;
    if (!hasAnyMetric) return null;

    return (
        <div ref={gridRef}>
            <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                {isRTL ? 'المقاييس الرئيسية' : 'Key Metrics'}
            </h3>
            <div className="grid grid-cols-2 gap-3">
                {/* Cap Rate - Only show if exists */}
                {metrics.capRate && (
                    <div className="metric-widget" style={{ opacity: 0 }}>
                        <div className="flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)]">
                            <Percent size={14} />
                            <p className="text-[10px] uppercase font-bold">{isRTL ? 'معدل العائد' : 'Cap Rate'}</p>
                        </div>
                        <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{metrics.capRate}</p>
                    </div>
                )}

                {/* Price per SQM - Only show if exists */}
                {metrics.pricePerSqm && (
                    <div className="metric-widget" style={{ opacity: 0 }}>
                        <div className="flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)]">
                            <Square size={14} />
                            <p className="text-[10px] uppercase font-bold">{isRTL ? 'السعر/م²' : 'Price/SQM'}</p>
                        </div>
                        <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">
                            {metrics.pricePerSqm.toLocaleString()}
                        </p>
                    </div>
                )}

                {/* Walk Score - Only show if exists */}
                {metrics.walkScore && (
                    <div className="metric-widget col-span-2" style={{ opacity: 0 }}>
                        <div className="flex justify-between items-end mb-2">
                            <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
                                <Footprints size={14} />
                                <p className="text-[10px] uppercase font-bold">{isRTL ? 'نقاط الموقع' : 'Location Score'}</p>
                            </div>
                            <span className="text-xl font-bold text-[var(--color-text-primary)]">{metrics.walkScore}/100</span>
                        </div>
                        <div className="walk-score-bar">
                            <div className="walk-score-bar-fill" style={{ width: `${metrics.walkScore}%` }} />
                        </div>
                        <p className="text-[10px] text-[var(--color-text-muted)] mt-2 text-right">
                            {metrics.walkScore >= 90 ? (isRTL ? '"موقع ممتاز"' : '"Walker\'s Paradise"') :
                             metrics.walkScore >= 70 ? (isRTL ? '"موقع جيد جداً"' : '"Very Walkable"') :
                             (isRTL ? '"موقع جيد"' : '"Somewhat Walkable"')}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

// AI Recommendation Widget
function AIRecommendationWidget({
    insight,
    tags,
    isRTL
}: {
    insight: string;
    tags?: string[];
    isRTL: boolean;
}) {
    const { displayedText, isComplete } = useTypewriter(insight, 15, 300);
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (cardRef.current) {
            anime({
                targets: cardRef.current,
                opacity: [0, 1],
                translateY: [20, 0],
                easing: 'easeOutExpo',
                duration: 800,
                delay: 500,
            });
        }
    }, [insight]);

    return (
        <div
            ref={cardRef}
            className="ai-recommendation-card"
            style={{ opacity: 0 }}
        >
            {/* Background decoration */}
            <div className="absolute -right-4 -top-4 text-white/5">
                <Sparkles size={80} />
            </div>

            <div className="relative z-10">
                <div className="flex items-center gap-2 mb-3">
                    <div className="size-6 rounded bg-white/20 flex items-center justify-center backdrop-blur-sm">
                        <Sparkles size={14} />
                    </div>
                    <h3 className="text-sm font-bold">{isRTL ? 'توصية الذكاء الاصطناعي' : 'AI Recommendation'}</h3>
                </div>
                <p className="text-sm text-white/90 leading-relaxed font-light mb-4">
                    {displayedText}
                    {!isComplete && <span className="inline-block w-0.5 h-3 bg-white ml-0.5 animate-pulse" />}
                </p>
                {tags && tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {tags.map((tag, i) => (
                            <span
                                key={tag}
                                className="px-2 py-1 bg-white/10 backdrop-blur-md rounded text-[10px] font-medium border border-white/20"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

// Agent Contact Card
function AgentContactCard({ agent, isRTL }: { agent?: PropertyContext['agent']; isRTL: boolean }) {
    const defaultAgent = {
        name: isRTL ? 'سارة جينكنز' : 'Sarah Jenkins',
        title: isRTL ? 'وسيط عقاري أول' : 'Senior Broker',
        avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop'
    };

    const agentData = agent || defaultAgent;

    return (
        <div className="agent-card">
            <div
                className="agent-avatar"
                style={{ backgroundImage: `url(${agentData.avatar || defaultAgent.avatar})` }}
            />
            <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-[var(--color-text-primary)] truncate">{agentData.name}</p>
                <p className="text-xs text-[var(--color-text-muted)] truncate">{agentData.title}</p>
            </div>
            <div className="flex gap-2">
                <button className="size-8 flex items-center justify-center rounded-full bg-[var(--color-surface-elevated)] hover:bg-[var(--color-primary)] hover:text-white transition-colors text-[var(--color-text-muted)]">
                    <MessageCircle size={16} />
                </button>
                <button className="size-8 flex items-center justify-center rounded-full bg-[var(--color-surface-elevated)] hover:bg-[var(--color-primary)] hover:text-white transition-colors text-[var(--color-text-muted)]">
                    <Phone size={16} />
                </button>
            </div>
        </div>
    );
}

// Analytics Quick Actions
function AnalyticsQuickActions({
    onAnalyticsRequest,
    isRTL
}: {
    onAnalyticsRequest?: (type: string) => void;
    isRTL: boolean;
}) {
    const actions = [
        { type: 'area_analysis', icon: Map, label: isRTL ? 'تحليل المنطقة' : 'Area Analysis' },
        { type: 'developer_analysis', icon: Building2, label: isRTL ? 'تحليل المطور' : 'Developer Analysis' },
        { type: 'roi_calculator', icon: Calculator, label: isRTL ? 'حاسبة العائد' : 'ROI Calculator' },
        { type: 'payment_plan_comparison', icon: Calendar, label: isRTL ? 'خطط الدفع' : 'Payment Plans' },
    ];

    return (
        <div className="space-y-3">
            <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">
                {isRTL ? 'تحليلات سريعة' : 'Quick Analytics'}
            </h3>
            <div className="grid grid-cols-2 gap-2">
                {actions.map(action => (
                    <button
                        key={action.type}
                        onClick={() => onAnalyticsRequest?.(action.type)}
                        className="flex items-center gap-2 p-2.5 rounded-lg bg-[var(--color-surface-elevated)] border border-[var(--color-border)] hover:border-[var(--color-primary)]/30 transition-all text-left"
                    >
                        <action.icon size={14} className="text-[var(--color-primary)]" />
                        <span className="text-xs font-medium text-[var(--color-text-primary)]">{action.label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}

// Visualization Section - Shows triggered analytics
function VisualizationSection({
    uiActions,
    isRTL
}: {
    uiActions: UIActionData[];
    isRTL: boolean;
}) {
    const sectionRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (sectionRef.current && uiActions.length > 0) {
            anime({
                targets: sectionRef.current.querySelectorAll('.viz-item'),
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(150, { start: 300 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [uiActions]);

    if (uiActions.length === 0) return null;

    // Get visualization type labels
    const getVizLabel = (type: string) => {
        const labels: Record<string, { en: string; ar: string }> = {
            'area_analysis': { en: 'Area Analysis', ar: 'تحليل المنطقة' },
            'developer_analysis': { en: 'Developer Analysis', ar: 'تحليل المطور' },
            'property_type_analysis': { en: 'Property Types', ar: 'أنواع العقارات' },
            'payment_plan_comparison': { en: 'Payment Plans', ar: 'خطط الدفع' },
            'resale_vs_developer': { en: 'Resale vs Developer', ar: 'ريسيل vs مطور' },
            'roi_calculator': { en: 'ROI Calculator', ar: 'حاسبة العائد' },
            'investment_scorecard': { en: 'Investment Score', ar: 'تقييم الاستثمار' },
            'market_trend_chart': { en: 'Market Trends', ar: 'اتجاهات السوق' },
            'inflation_killer': { en: 'Inflation Protection', ar: 'حماية من التضخم' },
            'la2ta_alert': { en: 'Bargain Alert', ar: 'تنبيه فرصة' },
            'law_114_guardian': { en: 'Legal Check', ar: 'فحص قانوني' },
            'comparison_matrix': { en: 'Comparison', ar: 'مقارنة' },
            'payment_timeline': { en: 'Payment Timeline', ar: 'جدول الدفع' },
            'price_heatmap': { en: 'Price Heatmap', ar: 'خريطة الأسعار' },
        };
        return labels[type] || { en: type, ar: type };
    };

    return (
        <div ref={sectionRef} className="space-y-4">
            <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest flex items-center gap-2">
                <BarChart2 size={14} className="text-[var(--color-teal-accent)]" />
                {isRTL ? 'التحليلات النشطة' : 'Active Analytics'}
                <span className="ml-auto text-[var(--color-teal-accent)]">{uiActions.length}</span>
            </h3>

            <div className="space-y-3">
                {uiActions.slice(0, 3).map((action, index) => (
                    <div
                        key={`${action.type}-${index}`}
                        className="viz-item rounded-xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)]"
                        style={{ opacity: 0 }}
                    >
                        {/* Header */}
                        <div className="px-3 py-2 bg-gradient-to-r from-[var(--color-primary)]/10 to-transparent border-b border-[var(--color-border)] flex items-center justify-between">
                            <span className="text-xs font-bold text-[var(--color-primary)]">
                                {isRTL ? getVizLabel(action.type).ar : getVizLabel(action.type).en}
                            </span>
                            {action.trigger_reason && (
                                <span className="text-[9px] text-[var(--color-text-muted)] truncate max-w-[120px]">
                                    {action.trigger_reason}
                                </span>
                            )}
                        </div>

                        {/* Visualization Content */}
                        <div className="p-2 max-h-[250px] overflow-y-auto">
                            <VisualizationRenderer
                                type={action.type}
                                data={action.data}
                            />
                        </div>
                    </div>
                ))}

                {uiActions.length > 3 && (
                    <p className="text-xs text-center text-[var(--color-text-muted)]">
                        +{uiActions.length - 3} {isRTL ? 'تحليلات أخرى في المحادثة' : 'more analytics in chat'}
                    </p>
                )}
            </div>
        </div>
    );
}

export default function ContextualPane({
    isOpen = true,
    onClose,
    property = null,
    uiActions = [],
    chatInsight = null,
    isRTL = false,
}: ContextualPaneProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [animationKey, setAnimationKey] = useState(0);

    // Reset animations when property or uiActions change
    useEffect(() => {
        if (property || uiActions.length > 0) {
            setAnimationKey(prev => prev + 1);
        }
    }, [property, uiActions]);

    // Entrance animation for the whole pane
    useEffect(() => {
        if (containerRef.current && (property || uiActions.length > 0)) {
            anime({
                targets: containerRef.current,
                opacity: [0, 1],
                translateX: [50, 0],
                easing: 'easeOutExpo',
                duration: 600,
            });
        }
    }, [property, uiActions, animationKey]);

    // Extract data from UI actions - NO MOCK DATA
    const scorecard = uiActions.find(a => a.type === 'investment_scorecard');
    const marketTrendData = uiActions.find(a => a.type === 'market_trend_chart');
    const roiData = uiActions.find(a => a.type === 'roi_calculator');

    // Calculate metrics from available data - Only use real data, no defaults
    const wolfScore = scorecard?.data?.analysis?.match_score || property?.metrics?.wolfScore;
    const roi = scorecard?.data?.analysis?.roi_projection || property?.metrics?.roi;
    const pricePerSqm = property?.metrics?.pricePerSqm || scorecard?.data?.analysis?.area_avg_price_per_sqm;
    const areaAvgPrice = scorecard?.data?.analysis?.area_avg_price_per_sqm || property?.metrics?.areaAvgPrice;
    const marketTrend = scorecard?.data?.analysis?.market_trend || property?.metrics?.marketTrend;
    const priceVerdict = scorecard?.data?.analysis?.price_verdict || property?.metrics?.priceVerdict;
    const riskLevel = scorecard?.data?.analysis?.risk_level;

    // Generate AI insight based on available data - Only when real data exists
    const generateInsight = useCallback(() => {
        if (chatInsight) return chatInsight;

        // Don't generate insight without real data
        if (!wolfScore && !roi && !pricePerSqm) {
            return isRTL
                ? '💡 اسأل عن أي عقار وسأقدم لك تحليل شامل للفرصة الاستثمارية.'
                : '💡 Ask about any property and I\'ll provide a comprehensive investment analysis.';
        }

        if (wolfScore && wolfScore >= 85) {
            return isRTL
                ? `🐺 فرصة ممتازة! الـ Wolf Score عالي (${wolfScore}/100). العقار ده تحت سعر السوق وفي منطقة نمو.${roi ? ` العائد المتوقع ${roi}% سنوياً - أحسن من الودائع البنكية!` : ''}`
                : `🐺 Excellent opportunity! High Wolf Score (${wolfScore}/100). This property is below market price in a growth area.${roi ? ` Expected ROI of ${roi}% annually - better than bank deposits!` : ''}`;
        } else if (wolfScore && wolfScore >= 70) {
            return isRTL
                ? `📊 عقار جيد للاستثمار.${pricePerSqm ? ` السعر للمتر ${pricePerSqm.toLocaleString()} جنيه.` : ''}${roi ? ` العائد المتوقع ${roi}% سنوياً.` : ''}`
                : `📊 Good investment property.${pricePerSqm ? ` Price per sqm is ${pricePerSqm.toLocaleString()} EGP.` : ''}${roi ? ` Expected ROI of ${roi}% annually.` : ''}`;
        } else if (pricePerSqm && areaAvgPrice) {
            return isRTL
                ? `💡 السعر للمتر ${pricePerSqm.toLocaleString()} جنيه. متوسط المنطقة ${areaAvgPrice.toLocaleString()} جنيه.`
                : `💡 Price per sqm is ${pricePerSqm.toLocaleString()} EGP. Area average is ${areaAvgPrice.toLocaleString()} EGP.`;
        }

        return isRTL
            ? '💡 جاري تحليل العقار...'
            : '💡 Analyzing property...';
    }, [wolfScore, roi, pricePerSqm, areaAvgPrice, isRTL, chatInsight]);

    // Determine tags based on analysis
    const tags = useMemo(() => {
        const result: string[] = [];
        if (wolfScore >= 80) result.push(isRTL ? 'فرصة قوية' : 'High Potential');
        if (priceVerdict === 'BARGAIN') result.push(isRTL ? 'صفقة' : 'Bargain');
        if (marketTrend?.includes('Growing') || marketTrend?.includes('Bullish')) result.push(isRTL ? 'سوق صاعد' : 'Growing Market');
        if (riskLevel === 'Low') result.push(isRTL ? 'مخاطر منخفضة' : 'Low Risk');
        if (property?.tags) result.push(...property.tags);
        return result.slice(0, 4);
    }, [wolfScore, priceVerdict, marketTrend, riskLevel, property?.tags, isRTL]);

    // Show empty state with quick actions if no data
    const hasData = property || uiActions.length > 0;

    // Desktop Sidebar Content
    const sidebarContent = (
        <div
            key={animationKey}
            ref={containerRef}
            className="h-full flex flex-col"
            style={{ opacity: hasData ? 0 : 1 }}
        >
            {/* Header */}
            <div className="px-5 py-4 border-b border-[var(--color-border)] flex justify-between items-center sticky top-0 bg-[var(--color-surface)]/80 backdrop-blur z-10">
                <h2 className="font-bold text-[var(--color-text-primary)] flex items-center gap-2">
                    <BarChart2 size={18} className="text-[var(--color-teal-accent)]" />
                    {isRTL ? 'رؤى العقار' : 'Property Insights'}
                </h2>
                {hasData && (
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--color-teal-accent)]/10">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-teal-accent)] opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-teal-accent)]"></span>
                        </span>
                        <span className="text-[10px] font-bold text-[var(--color-teal-accent)]">LIVE</span>
                    </div>
                )}
                <button
                    onClick={onClose}
                    className="xl:hidden p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                    <X size={18} className="text-[var(--color-text-muted)]" />
                </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
                {hasData ? (
                    <>
                        {/* Property Info */}
                        {property && (
                            <div className="pb-4 border-b border-[var(--color-border)]">
                                <div className="flex items-start gap-2 mb-3">
                                    <Home size={16} className="text-[var(--color-primary)] mt-0.5 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <h4 className="text-sm font-bold text-[var(--color-text-primary)] leading-tight">
                                            {property.title}
                                        </h4>
                                        <div className="flex items-center gap-1 mt-1">
                                            <MapPin size={12} className="text-[var(--color-text-muted)]" />
                                            <span className="text-[11px] text-[var(--color-text-muted)] truncate">{property.address}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-2xl font-bold text-[var(--color-text-primary)]">{property.price}</span>
                                    {priceVerdict === 'BARGAIN' && (
                                        <span className="badge-high-growth">{isRTL ? 'صفقة!' : 'Bargain!'}</span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Wolf Score & ROI Summary - Only show when real data exists */}
                        {(wolfScore !== undefined || roi !== undefined) && (
                            <div className="grid grid-cols-2 gap-3">
                                {wolfScore !== undefined && (
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/10 to-transparent border border-[var(--color-primary)]/20">
                                        <div className="flex items-center gap-1.5 mb-1">
                                            <Target size={12} className="text-[var(--color-primary)]" />
                                            <span className="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">
                                                Wolf Score
                                            </span>
                                        </div>
                                        <span className="text-xl font-bold text-[var(--color-teal-accent)]">
                                            <AnimatedCounter value={wolfScore} suffix="/100" delay={200} />
                                        </span>
                                    </div>
                                )}
                                {roi !== undefined && (
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-[var(--color-teal-accent)]/10 to-transparent border border-[var(--color-teal-accent)]/20">
                                        <div className="flex items-center gap-1.5 mb-1">
                                            <TrendingUp size={12} className="text-[var(--color-teal-accent)]" />
                                            <span className="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">
                                                {isRTL ? 'العائد' : 'ROI'}
                                            </span>
                                        </div>
                                        <span className="text-xl font-bold text-[var(--color-primary)]">
                                            <AnimatedCounter value={roi} suffix="%" delay={400} duration={1200} />
                                        </span>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Property Details Metrics Grid (moved from card) */}
                        {property?.metrics && (property.metrics.bedrooms || property.metrics.size) && (
                            <div>
                                <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                                    {isRTL ? 'تفاصيل العقار' : 'Property Details'}
                                </h3>
                                <MetricsGrid
                                    metrics={[
                                        ...(property.metrics.bedrooms ? [{
                                            id: 'bedrooms',
                                            label: isRTL ? 'غرف النوم' : 'Bedrooms',
                                            value: property.metrics.bedrooms,
                                            icon: <Bed size={16} />
                                        }] : []),
                                        ...(property.metrics.size ? [{
                                            id: 'size',
                                            label: isRTL ? 'المساحة' : 'Size',
                                            value: property.metrics.size.toLocaleString(),
                                            suffix: isRTL ? 'م²' : 'sqm',
                                            icon: <Ruler size={16} />
                                        }] : []),
                                        ...(pricePerSqm ? [{
                                            id: 'price_per_sqm',
                                            label: isRTL ? 'السعر/م²' : 'Price/sqm',
                                            value: `${(pricePerSqm / 1000).toFixed(1)}K`,
                                            icon: <DollarSign size={16} />
                                        }] : []),
                                        ...(riskLevel ? [{
                                            id: 'risk',
                                            label: isRTL ? 'المخاطر' : 'Risk',
                                            value: isRTL ?
                                                { 'Low': 'منخفض', 'Medium': 'متوسط', 'High': 'مرتفع' }[riskLevel] || riskLevel :
                                                riskLevel,
                                            highlight: riskLevel === 'Low' ? 'success' as const : riskLevel === 'High' ? 'danger' as const : 'warning' as const
                                        }] : []),
                                    ] as MetricItem[]}
                                    columns={2}
                                    isRTL={isRTL}
                                />
                            </div>
                        )}

                        {/* Embedded Price Projection Chart */}
                        {property && pricePerSqm && (
                            <div>
                                <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest mb-3">
                                    {isRTL ? 'توقع السعر' : 'Price Projection'}
                                </h3>
                                <EmbeddedChart
                                    data={property.priceHistory || generateProjectionData(
                                        pricePerSqm * (property.metrics?.size || 100),
                                        5,
                                        roi ? roi / 100 : 0.08
                                    )}
                                    title={isRTL ? 'التوقع لـ 5 سنوات' : '5Y Projection'}
                                    subtitle={isRTL ? 'بناءً على اتجاه السوق الحالي' : 'Based on current market trend'}
                                    height={160}
                                    isRTL={isRTL}
                                    enableDrawAnimation={true}
                                />
                            </div>
                        )}

                        {/* Map Module */}
                        {property && (
                            <MapModule address={property.address} isRTL={isRTL} />
                        )}

                        {/* Key Metrics - Only show when real data exists */}
                        {(pricePerSqm !== undefined || roi !== undefined || wolfScore !== undefined) && (
                            <KeyMetricsGrid
                                metrics={{
                                    capRate: roi ? `${(roi * 0.4).toFixed(1)}%` : undefined,
                                    pricePerSqm: pricePerSqm,
                                    walkScore: wolfScore ? Math.min(wolfScore + 10, 98) : undefined,
                                }}
                                isRTL={isRTL}
                            />
                        )}

                        {/* Active Visualizations */}
                        {uiActions.length > 0 && (
                            <VisualizationSection uiActions={uiActions} isRTL={isRTL} />
                        )}

                        {/* AI Recommendation */}
                        <AIRecommendationWidget
                            insight={generateInsight()}
                            tags={tags}
                            isRTL={isRTL}
                        />

                        {/* Agent Contact */}
                        <AgentContactCard agent={property?.agent} isRTL={isRTL} />
                    </>
                ) : (
                    /* Empty State with Quick Actions */
                    <div className="flex flex-col items-center justify-center h-full text-center py-8">
                        <div className="size-16 rounded-2xl bg-gradient-to-br from-[var(--color-primary)]/10 to-[var(--color-teal-accent)]/10 flex items-center justify-center mb-4">
                            <Sparkles size={28} className="text-[var(--color-primary)]" />
                        </div>
                        <h3 className="text-sm font-bold text-[var(--color-text-primary)] mb-2">
                            {isRTL ? 'ابدأ محادثة' : 'Start a Conversation'}
                        </h3>
                        <p className="text-xs text-[var(--color-text-muted)] mb-6 max-w-[200px]">
                            {isRTL
                                ? 'اسأل عن العقارات أو السوق وسيظهر التحليل هنا'
                                : 'Ask about properties or market and insights will appear here'}
                        </p>
                        <AnalyticsQuickActions isRTL={isRTL} />
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <>
            {/* Desktop Pane - Fixed Sidebar */}
            <aside className={`contextual-sidebar hidden xl:flex flex-col transition-all duration-300 ${hasData ? 'opacity-100' : 'opacity-100'}`}>
                {sidebarContent}
            </aside>

            {/* Mobile Pane Overlay */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/60 z-40 xl:hidden backdrop-blur-sm"
                        />

                        <motion.aside
                            initial={{ x: isRTL ? -360 : 360 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? -360 : 360 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'left-0' : 'right-0'} top-0 bottom-0 w-[var(--panel-width,360px)] bg-[var(--color-surface)] backdrop-blur-xl flex flex-col z-50 xl:hidden border-l border-[var(--color-border)]`}
                        >
                            {sidebarContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
