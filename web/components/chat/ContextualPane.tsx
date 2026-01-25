'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { BarChart2, TrendingUp, X, Sparkles, MapPin, Home, DollarSign, Target, Zap, Activity, PieChart, Building2, Calendar, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import anime from 'animejs';

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
function useTypewriter(text: string, speed: number = 30, startDelay: number = 0) {
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
                className={`bg-gradient-to-r ${color} h-full rounded-full`}
                style={{ width: '0%' }}
            />
        </div>
    );
}

// Animated Bar Chart
function AnimatedBarChart({ score, delay = 0 }: { score: number; delay?: number }) {
    const barsRef = useRef<(HTMLDivElement | null)[]>([]);

    useEffect(() => {
        barsRef.current.forEach((bar, i) => {
            if (bar) {
                const threshold = (i + 1) * 16.6;
                const targetHeight = score >= threshold ? 30 + (i * 12) : 15;
                const targetOpacity = score >= threshold ? 0.5 + (i * 0.1) : 0.15;

                anime({
                    targets: bar,
                    height: [`0%`, `${targetHeight}%`],
                    opacity: [0, targetOpacity],
                    easing: 'easeOutElastic(1, .8)',
                    duration: 1000,
                    delay: delay + (i * 100),
                });
            }
        });
    }, [score, delay]);

    return (
        <div className="h-20 w-full flex items-end gap-1.5">
            {Array.from({ length: 6 }).map((_, i) => (
                <div
                    key={i}
                    ref={el => { barsRef.current[i] = el; }}
                    className={`flex-1 rounded-t-md transition-colors ${
                        i > 3 ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-teal-accent)]'
                    }`}
                    style={{ height: '0%', opacity: 0 }}
                />
            ))}
        </div>
    );
}

// AI Insight Card with Typewriter
function AIInsightCard({ 
    insight, 
    isRTL,
    delay = 0 
}: { 
    insight: string; 
    isRTL: boolean;
    delay?: number;
}) {
    const { displayedText, isComplete } = useTypewriter(insight, 25, delay);
    const cardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (cardRef.current) {
            anime({
                targets: cardRef.current,
                opacity: [0, 1],
                translateY: [20, 0],
                easing: 'easeOutExpo',
                duration: 800,
                delay: delay,
            });
        }
    }, [delay]);

    return (
        <div 
            ref={cardRef}
            className="mt-4 p-4 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/10 to-[var(--color-teal-accent)]/5 border border-[var(--color-primary)]/20"
            style={{ opacity: 0 }}
        >
            <div className="flex items-center gap-2 mb-2">
                <Sparkles size={14} className="text-[var(--color-teal-accent)]" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--color-primary)]">
                    {isRTL ? 'رؤية الذكاء الاصطناعي' : 'AI Insight'}
                </span>
            </div>
            <p className="text-xs text-[var(--color-text-primary)] leading-relaxed">
                {displayedText}
                {!isComplete && <span className="inline-block w-0.5 h-3 bg-[var(--color-teal-accent)] ml-0.5 animate-pulse" />}
            </p>
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
    const metricsRef = useRef<HTMLDivElement>(null);
    const [animationKey, setAnimationKey] = useState(0);
    const [activeTab, setActiveTab] = useState<'analysis' | 'market' | 'roi'>('analysis');

    // Reset animations when property or uiActions change
    useEffect(() => {
        if (property || uiActions.length > 0) {
            setAnimationKey(prev => prev + 1);
        }
    }, [property, uiActions]);

    // Entrance animation for the whole card
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

    // Stagger animation for metrics
    useEffect(() => {
        if (metricsRef.current && property) {
            anime({
                targets: metricsRef.current.querySelectorAll('.metric-item'),
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(100, { start: 300 }),
                easing: 'easeOutExpo',
                duration: 500,
            });
        }
    }, [property, animationKey]);

    // Extract data from UI actions
    const scorecard = uiActions.find(a => a.type === 'investment_scorecard');
    const marketTrendData = uiActions.find(a => a.type === 'market_trend_chart');
    const roiData = uiActions.find(a => a.type === 'roi_calculator');
    const inflationData = uiActions.find(a => a.type === 'inflation_killer');
    const comparisonData = uiActions.find(a => a.type === 'comparison_matrix');

    // Don't render if no property data AND no ui actions
    if (!property && uiActions.length === 0) return null;

    const wolfScore = scorecard?.data?.analysis?.match_score || property?.metrics?.wolfScore || 75;
    const roi = scorecard?.data?.analysis?.roi_projection || property?.metrics?.roi || 12.5;
    const pricePerSqm = property?.metrics?.pricePerSqm || property?.metrics?.pricePerSqFt || '—';
    const areaAvgPrice = scorecard?.data?.analysis?.area_avg_price_per_sqm || property?.metrics?.areaAvgPrice || 50000;
    const marketTrend = scorecard?.data?.analysis?.market_trend || property?.metrics?.marketTrend || 'Growing 📊';
    const priceVerdict = scorecard?.data?.analysis?.price_verdict || property?.metrics?.priceVerdict || 'Fair';
    const riskLevel = scorecard?.data?.analysis?.risk_level || 'Medium';

    // Generate AI insight based on property data
    const generateInsight = useCallback(() => {
        if (chatInsight) return chatInsight;
        
        if (wolfScore >= 85) {
            return isRTL 
                ? `🐺 فرصة ممتازة! الـ Wolf Score عالي (${wolfScore}/100) - العقار ده تحت سعر السوق وفي منطقة نمو.`
                : `🐺 Excellent opportunity! High Wolf Score (${wolfScore}/100) - This property is below market price in a growth area.`;
        } else if (wolfScore >= 70) {
            return isRTL
                ? `📊 عقار جيد للاستثمار. العائد المتوقع ${roi}% سنوياً - أعلى من البنك!`
                : `📊 Good investment property. Expected ROI of ${roi}% annually - better than bank deposits!`;
        }
        return isRTL
            ? `💡 راجع التفاصيل بعناية. السعر للمتر ${pricePerSqm} جنيه - قارن مع المنطقة.`
            : `💡 Review details carefully. Price per sqm is ${pricePerSqm} EGP - compare with the area.`;
    }, [wolfScore, roi, pricePerSqm, isRTL, chatInsight]);

    // Tab content components
    const AnalysisTab = () => (
        <div ref={metricsRef} className="space-y-4">
            {/* Wolf Score */}
            <div className="metric-item">
                <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                        <Target size={14} className="text-[var(--color-primary)]" />
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                            {isRTL ? 'تصنيف وولف' : 'Wolf Score'}
                        </span>
                    </div>
                    <span className="text-lg font-bold text-[var(--color-teal-accent)]">
                        <AnimatedCounter value={wolfScore} suffix="/100" delay={200} />
                    </span>
                </div>
                <AnimatedBarChart score={wolfScore} delay={300} />
            </div>

            {/* ROI */}
            <div className="metric-item">
                <div className="flex justify-between items-center mb-2">
                    <div className="flex items-center gap-2">
                        <TrendingUp size={14} className="text-[var(--color-teal-accent)]" />
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                            {isRTL ? 'العائد السنوي' : 'Annual ROI'}
                        </span>
                    </div>
                    <span className="text-lg font-bold text-[var(--color-primary)]">
                        <AnimatedCounter value={roi} suffix="%" delay={500} duration={1200} />
                    </span>
                </div>
                <AnimatedProgressBar percentage={Math.min(roi * 4, 100)} delay={600} />
            </div>

            {/* Price per SQM vs Area Average */}
            <div className="metric-item p-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)]">
                <div className="flex items-center gap-2 mb-3">
                    <Zap size={14} className="text-yellow-500" />
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--color-text-muted)]">
                        {isRTL ? 'السعر/متر' : 'Price/SQM'}
                    </span>
                </div>
                <div className="flex justify-between items-end">
                    <div>
                        <div className="text-xl font-bold text-[var(--color-text-primary)]">
                            {typeof pricePerSqm === 'number' ? pricePerSqm.toLocaleString() : pricePerSqm}
                        </div>
                        <div className="text-[10px] text-[var(--color-text-muted)]">{isRTL ? 'هذا العقار' : 'This Property'}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-lg font-medium text-[var(--color-text-muted)]">
                            {areaAvgPrice.toLocaleString()}
                        </div>
                        <div className="text-[10px] text-[var(--color-text-muted)]">{isRTL ? 'متوسط المنطقة' : 'Area Average'}</div>
                    </div>
                </div>
                {typeof pricePerSqm === 'number' && pricePerSqm < areaAvgPrice && (
                    <div className="mt-2 flex items-center gap-1 text-green-500 text-xs font-bold">
                        <ArrowDownRight size={12} />
                        {Math.round(((areaAvgPrice - pricePerSqm) / areaAvgPrice) * 100)}% {isRTL ? 'تحت السوق!' : 'below market!'}
                    </div>
                )}
            </div>

            {/* Risk Level & Price Verdict */}
            <div className="metric-item grid grid-cols-2 gap-2">
                <div className={`p-2 rounded-lg text-center ${
                    riskLevel === 'Low' ? 'bg-green-500/10 border border-green-500/20' :
                    riskLevel === 'Medium' ? 'bg-yellow-500/10 border border-yellow-500/20' :
                    'bg-red-500/10 border border-red-500/20'
                }`}>
                    <div className="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">{isRTL ? 'المخاطر' : 'Risk'}</div>
                    <div className={`text-sm font-bold ${
                        riskLevel === 'Low' ? 'text-green-500' :
                        riskLevel === 'Medium' ? 'text-yellow-500' :
                        'text-red-500'
                    }`}>{riskLevel}</div>
                </div>
                <div className={`p-2 rounded-lg text-center ${
                    priceVerdict === 'BARGAIN' ? 'bg-green-500/10 border border-green-500/20' :
                    priceVerdict === 'Fair' ? 'bg-blue-500/10 border border-blue-500/20' :
                    'bg-orange-500/10 border border-orange-500/20'
                }`}>
                    <div className="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">{isRTL ? 'السعر' : 'Price'}</div>
                    <div className={`text-sm font-bold ${
                        priceVerdict === 'BARGAIN' ? 'text-green-500' :
                        priceVerdict === 'Fair' ? 'text-blue-500' :
                        'text-orange-500'
                    }`}>{priceVerdict}</div>
                </div>
            </div>
        </div>
    );

    const MarketTab = () => (
        <div className="space-y-4">
            {/* Market Trend Badge */}
            <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-green-500/10 to-transparent border border-green-500/20">
                <div className="p-2 rounded-lg bg-green-500/20">
                    <Activity size={18} className="text-green-500" />
                </div>
                <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-green-600">
                        {isRTL ? 'اتجاه السوق' : 'Market Trend'}
                    </span>
                    <p className="text-lg font-bold text-green-500">{marketTrend}</p>
                </div>
            </div>

            {/* Market Stats from UI Actions */}
            {marketTrendData?.data && (
                <div className="space-y-3">
                    <div className="flex justify-between items-center p-2 rounded-lg bg-[var(--color-surface-elevated)]">
                        <span className="text-xs text-[var(--color-text-muted)]">{isRTL ? 'نمو السعر (سنوي)' : 'Price Growth (YTD)'}</span>
                        <span className="text-sm font-bold text-green-500">
                            +{marketTrendData.data.price_growth_ytd || 15}%
                        </span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded-lg bg-[var(--color-surface-elevated)]">
                        <span className="text-xs text-[var(--color-text-muted)]">{isRTL ? 'مؤشر الطلب' : 'Demand Index'}</span>
                        <span className="text-sm font-bold text-[var(--color-teal-accent)]">
                            {marketTrendData.data.demand_index || 'High 🔥'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center p-2 rounded-lg bg-[var(--color-surface-elevated)]">
                        <span className="text-xs text-[var(--color-text-muted)]">{isRTL ? 'مستوى العرض' : 'Supply Level'}</span>
                        <span className="text-sm font-bold text-[var(--color-primary)]">
                            {marketTrendData.data.supply_level || 'Moderate 📦'}
                        </span>
                    </div>
                </div>
            )}

            {/* Comparison Badge if available */}
            {comparisonData && (
                <div className="p-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
                    <div className="flex items-center gap-2 mb-2">
                        <PieChart size={14} className="text-[var(--color-primary)]" />
                        <span className="text-[10px] font-bold uppercase text-[var(--color-text-muted)]">
                            {isRTL ? 'مقارنة' : 'Comparison'}
                        </span>
                    </div>
                    <p className="text-xs text-[var(--color-text-primary)]">
                        {isRTL 
                            ? `تم مقارنة ${comparisonData.data.properties?.length || 0} عقارات` 
                            : `Compared ${comparisonData.data.properties?.length || 0} properties`}
                    </p>
                </div>
            )}
        </div>
    );

    const ROITab = () => (
        <div className="space-y-4">
            {/* ROI Summary */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-[var(--color-primary)]/10 to-[var(--color-teal-accent)]/5 border border-[var(--color-primary)]/20">
                <div className="flex items-center gap-2 mb-3">
                    <DollarSign size={16} className="text-[var(--color-teal-accent)]" />
                    <span className="text-xs font-bold uppercase text-[var(--color-primary)]">
                        {isRTL ? 'ملخص العائد' : 'ROI Summary'}
                    </span>
                </div>
                <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">
                    <AnimatedCounter value={roi} suffix="%" delay={100} />
                </div>
                <p className="text-xs text-[var(--color-text-muted)]">
                    {isRTL ? 'العائد السنوي المتوقع' : 'Expected Annual Return'}
                </p>
            </div>

            {/* ROI Comparison from UI Actions */}
            {roiData?.data?.comparison && (
                <div className="space-y-2">
                    <div className="text-[10px] font-bold uppercase text-[var(--color-text-muted)] mb-2">
                        {isRTL ? 'مقارنة الاستثمار' : 'Investment Comparison'}
                    </div>
                    
                    {roiData.data.comparison.vs_bank && (
                        <div className="flex justify-between items-center p-2 rounded-lg bg-[var(--color-surface-elevated)]">
                            <span className="text-xs">{isRTL ? '🏦 ودائع البنك' : '🏦 Bank Deposit'}</span>
                            <span className={`text-sm font-bold ${
                                roiData.data.comparison.vs_bank.winner === 'property' ? 'text-green-500' : 'text-red-500'
                            }`}>
                                {roiData.data.comparison.vs_bank.winner === 'property' ? '✓' : '✗'}
                            </span>
                        </div>
                    )}
                    
                    {roiData.data.comparison.vs_gold && (
                        <div className="flex justify-between items-center p-2 rounded-lg bg-[var(--color-surface-elevated)]">
                            <span className="text-xs">{isRTL ? '🥇 الذهب' : '🥇 Gold'}</span>
                            <span className={`text-sm font-bold ${
                                roiData.data.comparison.vs_gold.winner === 'property' ? 'text-green-500' : 'text-red-500'
                            }`}>
                                {roiData.data.comparison.vs_gold.winner === 'property' ? '✓' : '✗'}
                            </span>
                        </div>
                    )}
                </div>
            )}

            {/* Inflation Protection */}
            {inflationData && (
                <div className="p-3 rounded-xl border border-orange-500/20 bg-orange-500/5">
                    <div className="flex items-center gap-2 mb-2">
                        <ArrowUpRight size={14} className="text-orange-500" />
                        <span className="text-[10px] font-bold uppercase text-orange-600">
                            {isRTL ? 'حماية من التضخم' : 'Inflation Protection'}
                        </span>
                    </div>
                    <p className="text-xs text-[var(--color-text-primary)]">
                        {isRTL 
                            ? `العقار يحميك من التضخم (${inflationData.data.egypt_inflation_rate || 33.7}%)`
                            : `Property protects against inflation (${inflationData.data.egypt_inflation_rate || 33.7}%)`}
                    </p>
                </div>
            )}
        </div>
    );

    const listingInsightsCard = (
        <div 
            key={animationKey}
            ref={containerRef}
            className="relative bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-5 shadow-xl w-full overflow-hidden"
            style={{ opacity: 0 }}
        >
            {/* Decorative Corners */}
            <div className="absolute -bottom-[1px] -right-[1px] w-5 h-5 border-b-2 border-r-2 border-[var(--color-teal-accent)] rounded-br-xl" />
            <div className="absolute -top-[1px] -left-[1px] w-5 h-5 border-t-2 border-l-2 border-[var(--color-primary)]/30 rounded-tl-xl" />

            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-[var(--color-teal-accent)]/10">
                        <BarChart2 size={18} className="text-[var(--color-teal-accent)]" />
                    </div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
                        {isRTL ? 'تحليل ذكي' : 'AI Analysis'}
                    </h3>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[var(--color-teal-accent)]/10">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-teal-accent)] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--color-teal-accent)]"></span>
                    </span>
                    <span className="text-[10px] font-bold text-[var(--color-teal-accent)]">LIVE</span>
                </div>
            </div>

            {/* Property Title (if available) */}
            {property && (
                <div className="mb-4 pb-3 border-b border-[var(--color-border)]">
                    <div className="flex items-start gap-2">
                        <Home size={16} className="text-[var(--color-primary)] mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-bold text-[var(--color-text-primary)] leading-tight truncate">
                                {property.title}
                            </h4>
                            <div className="flex items-center gap-1 mt-1">
                                <MapPin size={12} className="text-[var(--color-text-muted)]" />
                                <span className="text-[11px] text-[var(--color-text-muted)] truncate">{property.address}</span>
                            </div>
                        </div>
                    </div>
                    <div className="mt-2 flex items-baseline gap-1">
                        <DollarSign size={14} className="text-[var(--color-teal-accent)]" />
                        <span className="text-xl font-bold text-[var(--color-text-primary)]">{property.price}</span>
                    </div>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="flex gap-1 mb-4 p-1 rounded-lg bg-[var(--color-surface-elevated)]">
                {(['analysis', 'market', 'roi'] as const).map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`flex-1 py-1.5 px-2 text-[10px] font-bold uppercase rounded-md transition-all ${
                            activeTab === tab 
                                ? 'bg-[var(--color-primary)] text-white shadow-md' 
                                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                        }`}
                    >
                        {tab === 'analysis' ? (isRTL ? 'تحليل' : 'Analysis') :
                         tab === 'market' ? (isRTL ? 'السوق' : 'Market') :
                         (isRTL ? 'العائد' : 'ROI')}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                >
                    {activeTab === 'analysis' && <AnalysisTab />}
                    {activeTab === 'market' && <MarketTab />}
                    {activeTab === 'roi' && <ROITab />}
                </motion.div>
            </AnimatePresence>

            {/* AI Insight with Typewriter */}
            <AIInsightCard 
                insight={generateInsight()} 
                isRTL={isRTL}
                delay={800}
            />

            {/* Tags */}
            {property?.tags && property.tags.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[var(--color-border)]">
                    <div className="flex flex-wrap gap-2">
                        {property.tags.map((tag, i) => (
                            <motion.span
                                key={tag}
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 1.0 + (i * 0.1) }}
                                className="px-2 py-1 text-[10px] font-bold rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                            >
                                {tag}
                            </motion.span>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );

    return (
        <>
            {/* Desktop Pane - Floating Card (Top Right) */}
            <aside className={`fixed top-[12%] right-[2%] w-80 z-20 hidden xl:block transition-all duration-500 transform ${(property || uiActions.length > 0) ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>
                {listingInsightsCard}
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
                            initial={{ x: isRTL ? -340 : 340 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? -340 : 340 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'left-0' : 'right-0'} top-0 bottom-0 w-[320px] bg-[var(--color-surface)] backdrop-blur-xl p-5 flex flex-col z-50 xl:hidden border-l border-[var(--color-border)] overflow-y-auto`}
                        >
                            <div className="flex justify-end mb-4">
                                <button 
                                    onClick={onClose} 
                                    title={isRTL ? 'إغلاق' : 'Close'}
                                    className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
                                >
                                    <X size={20} className="text-[var(--color-text-muted)]" />
                                </button>
                            </div>
                            {listingInsightsCard}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
