'use client';

import { BarChart2, Percent, Ruler, Footprints, Lightbulb, MessageCircle, Phone, ExternalLink, X, Home, TrendingUp, ShieldCheck, Bus, GraduationCap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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
        roi?: number; // Annual ROI
        occupancyRate?: number; // Estimated Occupancy
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
    isRTL?: boolean;
}

export default function ContextualPane({
    isOpen = true,
    onClose,
    property = null,
    isRTL = false,
}: ContextualPaneProps) {
    // Don't render if no property data
    if (!property) {
        return (
            <>
                {/* Desktop Empty Pane */}
                <aside className={`chat-contextual-pane bg-[var(--color-background)] backdrop-blur-md hidden xl:flex flex-col overflow-y-auto z-20 chat-scrollbar ${isRTL ? 'border-r border-l-0' : ''}`}>
                    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                        <div className="size-16 rounded-2xl bg-[var(--color-surface)] flex items-center justify-center mb-4">
                            <Home size={32} className="text-[var(--color-text-muted)]" />
                        </div>
                        <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-2">
                            {isRTL ? 'لا توجد عقارات محددة' : 'No Property Selected'}
                        </h3>
                        <p className="text-sm text-[var(--color-text-muted)] max-w-[200px]">
                            {isRTL
                                ? 'ابحث عن العقارات وسيظهر التفاصيل هنا'
                                : 'Search for properties and details will appear here'
                            }
                        </p>
                    </div>
                </aside>
            </>
        );
    }

    const paneContent = (
        <>
            {/* Context Header */}
            <div className={`px-5 py-4 border-b border-[var(--color-border)] flex justify-between items-center sticky top-0 bg-[var(--color-background)]/80 backdrop-blur z-10 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <h2 className={`font-bold text-[var(--color-text-primary)] flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <BarChart2 size={20} className="text-[var(--color-primary)] dark:text-[var(--color-secondary)]" />
                    {isRTL ? 'تفاصيل العقار' : 'Listing Insights'}
                </h2>
                <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>
            </div>

            <div className="p-5 space-y-8" dir={isRTL ? 'rtl' : 'ltr'}>
                {/* Property Title */}
                <div className="space-y-2">
                    <h3 className="text-xl font-bold text-[var(--color-text-primary)]">{property.title}</h3>
                    <p className="text-sm text-[var(--color-text-muted)]">{property.address}</p>
                    <p className="text-2xl font-bold text-[var(--color-primary)] dark:text-[var(--color-secondary)]">{property.price}</p>
                </div>

                {/* Stats Grid - Only show if metrics exist */}
                {property.metrics && (
                    <div>
                        <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
                            {isRTL ? 'المقاييس الرئيسية' : 'Key Metrics'}
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                            {property.metrics.capRate && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Percent size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'معدل العائد' : 'Cap Rate'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{property.metrics.capRate}</p>
                                </div>
                            )}
                            {property.metrics.pricePerSqFt && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Ruler size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'السعر/م²' : 'Price / SqM'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{property.metrics.pricePerSqFt}</p>
                                </div>
                            )}
                            {property.metrics.size && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Ruler size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'المساحة' : 'Size'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{property.metrics.size} {isRTL ? 'م²' : 'sqm'}</p>
                                </div>
                            )}
                            {property.metrics.bedrooms && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-[var(--color-text-muted)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Home size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'غرف النوم' : 'Bedrooms'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">{property.metrics.bedrooms}</p>
                                </div>
                            )}
                            {property.metrics.wolfScore && (
                                <div className="metric-card col-span-2">
                                    <div className={`flex justify-between items-end mb-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <div className={`flex items-center gap-1.5 text-[var(--color-text-muted)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                            <ShieldCheck size={16} className="text-amber-500" />
                                            <p className="text-[10px] uppercase font-bold text-amber-500">{isRTL ? 'تصنيف وولف' : 'Wolf Score'}</p>
                                        </div>
                                        <span className="text-xl font-bold text-[var(--color-text-primary)]">{property.metrics.wolfScore}/100</span>
                                    </div>
                                    <div className="h-2 w-full bg-[var(--color-surface)] dark:bg-black/40 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-amber-400 to-amber-600 rounded-full shadow-[0_0_10px_rgba(251,191,36,0.5)]"
                                            style={{ width: `${property.metrics.wolfScore}%` }}
                                        ></div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* AI Insight Widget - Only show if recommendation exists */}
                {property.aiRecommendation && (
                    <div className="ai-recommendation-card p-5">
                        <div className="relative z-10">
                            <div className={`flex items-center gap-2 mb-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                                <div className="size-6 rounded bg-white/20 flex items-center justify-center backdrop-blur-sm">
                                    <Lightbulb size={16} />
                                </div>
                                <h3 className="text-sm font-bold">{isRTL ? 'توصية الذكاء الاصطناعي' : 'AI Recommendation'}</h3>
                            </div>
                            <p className="text-sm text-white/90 leading-relaxed font-light mb-4">
                                {property.aiRecommendation}
                            </p>
                            {property.tags && property.tags.length > 0 && (
                                <div className={`flex flex-wrap gap-2 ${isRTL ? 'justify-end' : ''}`}>
                                    {property.tags.map((tag, index) => (
                                        <span
                                            key={index}
                                            className="px-2 py-1 bg-white/10 backdrop-blur-md rounded text-[10px] font-medium border border-white/20"
                                        >
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Investment Analysis */}
                <div className="space-y-3">
                    <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
                        {isRTL ? 'تحليل الاستثمار' : 'Investment Analysis'}
                    </h3>
                    <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl p-4">
                        <div className="flex justify-between items-center mb-4">
                            <div className="flex items-center gap-2">
                                <div className="p-1.5 rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                                    <TrendingUp size={16} />
                                </div>
                                <span className="text-sm font-bold text-[var(--color-text-primary)]">{isRTL ? 'العائد المتوقع' : 'Proj. Annual ROI'}</span>
                            </div>
                            <span className="text-lg font-bold text-green-600 dark:text-green-400">{property.metrics?.roi || 12.5}%</span>
                        </div>
                        {/* Simple Progress Bar for ROI */}
                        <div className="h-2 w-full bg-[var(--color-surface)] dark:bg-black/40 rounded-full overflow-hidden mb-4">
                            <div
                                className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full"
                                style={{ width: `${(property.metrics?.roi || 12.5) * 4}%` }} // Scale roughly to 25% max visual
                            ></div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[var(--color-border)]">
                            <div className="text-center">
                                <p className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{isRTL ? 'الإشغال المقدر' : 'Est. Occupancy'}</p>
                                <p className="text-sm font-bold text-[var(--color-text-primary)]">{property.metrics?.occupancyRate || 88}%</p>
                            </div>
                            <div className="text-center border-l border-[var(--color-border)]">
                                <p className="text-[10px] text-[var(--color-text-muted)] uppercase mb-1">{isRTL ? 'نمو السعر (سنة)' : '1Y Appreciation'}</p>
                                <p className="text-sm font-bold text-[var(--color-text-primary)]">+15.2%</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Neighborhood Insights */}
                <div className="space-y-3">
                    <h3 className="text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider">
                        {isRTL ? 'إحصائيات الحي' : 'Neighborhood Stats'}
                    </h3>
                    <div className="grid grid-cols-3 gap-2">
                        <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl p-3 flex flex-col items-center justify-center text-center gap-1">
                            <ShieldCheck size={18} className="text-blue-500 dark:text-blue-400 mb-1" />
                            <span className="text-[10px] text-[var(--color-text-muted)] font-medium">{isRTL ? 'أمان' : 'Safety'}</span>
                            <span className="text-xs font-bold text-[var(--color-text-primary)]">{property.neighborhoodStats?.crimeRate || 'High'}</span>
                        </div>
                        <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl p-3 flex flex-col items-center justify-center text-center gap-1">
                            <GraduationCap size={18} className="text-purple-500 dark:text-purple-400 mb-1" />
                            <span className="text-[10px] text-[var(--color-text-muted)] font-medium">{isRTL ? 'تعليم' : 'Schools'}</span>
                            <span className="text-xs font-bold text-[var(--color-text-primary)]">{property.neighborhoodStats?.schoolScore || '9.2'}/10</span>
                        </div>
                        <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl p-3 flex flex-col items-center justify-center text-center gap-1">
                            <Bus size={18} className="text-amber-500 dark:text-amber-400 mb-1" />
                            <span className="text-[10px] text-[var(--color-text-muted)] font-medium">{isRTL ? 'مواصلات' : 'Transit'}</span>
                            <span className="text-xs font-bold text-[var(--color-text-primary)]">{property.neighborhoodStats?.transitScore || '85'}</span>
                        </div>
                    </div>
                </div>

                {/* Agent Contact - Only show if agent exists */}
                {property.agent && (
                    <div className={`bg-[var(--color-surface-elevated)] p-4 rounded-xl border border-[var(--color-border)] shadow-sm flex items-center gap-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                        <div className="size-12 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-teal-600 flex items-center justify-center text-white font-bold border-2 border-[var(--color-surface)] shadow-sm">
                            {property.agent.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className={`flex-1 min-w-0 ${isRTL ? 'text-right' : ''}`}>
                            <p className="text-sm font-bold text-[var(--color-text-primary)] truncate">{property.agent.name}</p>
                            <p className="text-xs text-[var(--color-text-muted)] truncate">{property.agent.title}</p>
                        </div>
                        <div className="flex gap-2">
                            <button className="size-8 flex items-center justify-center rounded-full bg-[var(--color-surface)] hover:bg-[var(--color-primary)] hover:text-white transition-colors text-[var(--color-text-muted)]">
                                <MessageCircle size={18} />
                            </button>
                            <button className="size-8 flex items-center justify-center rounded-full bg-[var(--color-surface)] hover:bg-[var(--color-primary)] hover:text-white transition-colors text-[var(--color-text-muted)]">
                                <Phone size={18} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </>
    );

    return (
        <>
            {/* Desktop Pane */}
            <aside className={`chat-contextual-pane bg-[var(--color-background)] backdrop-blur-md hidden xl:flex flex-col overflow-y-auto z-20 chat-scrollbar ${isRTL ? 'border-r border-l-0' : ''}`}>
                {paneContent}
            </aside>

            {/* Mobile Pane Overlay - Hidden by default, can be shown via prop */}
            <AnimatePresence>
                {isOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onClose}
                            className="fixed inset-0 bg-black/50 z-40 xl:hidden"
                        />

                        <motion.aside
                            initial={{ x: isRTL ? -340 : 340 }}
                            animate={{ x: 0 }}
                            exit={{ x: isRTL ? -340 : 340 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className={`fixed ${isRTL ? 'left-0' : 'right-0'} top-0 h-full w-[340px] bg-[var(--color-background)] backdrop-blur-md flex flex-col z-50 xl:hidden overflow-y-auto chat-scrollbar`}
                        >
                            {paneContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
