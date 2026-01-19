'use client';

import { BarChart2, Percent, Ruler, Footprints, Lightbulb, MessageCircle, Phone, ExternalLink, X, Home } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface PropertyContext {
    title: string;
    address: string;
    price: string;
    metrics?: {
        capRate?: string;
        pricePerSqFt?: string;
        walkScore?: number;
        size?: number;
        bedrooms?: number;
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
                <aside className={`chat-contextual-pane bg-white/60 dark:bg-[#131d20] backdrop-blur-md hidden xl:flex flex-col overflow-y-auto z-20 chat-scrollbar ${isRTL ? 'border-r border-l-0' : ''}`}>
                    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                        <div className="size-16 rounded-2xl bg-gray-100 dark:bg-[var(--chat-surface-dark)] flex items-center justify-center mb-4">
                            <Home size={32} className="text-gray-400 dark:text-gray-500" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                            {isRTL ? 'لا توجد عقارات محددة' : 'No Property Selected'}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-[200px]">
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
            <div className={`px-5 py-4 border-b border-gray-200 dark:border-[var(--chat-border-dark)] flex justify-between items-center sticky top-0 bg-white/80 dark:bg-[#131d20]/80 backdrop-blur z-10 ${isRTL ? 'flex-row-reverse' : ''}`}>
                <h2 className={`font-bold text-gray-900 dark:text-white flex items-center gap-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                    <BarChart2 size={20} className="text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]" />
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
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">{property.title}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{property.address}</p>
                    <p className="text-2xl font-bold text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)]">{property.price}</p>
                </div>

                {/* Stats Grid - Only show if metrics exist */}
                {property.metrics && (
                    <div>
                        <h3 className="text-[11px] font-bold text-gray-500 dark:text-[var(--chat-text-secondary)] uppercase tracking-wider mb-3">
                            {isRTL ? 'المقاييس الرئيسية' : 'Key Metrics'}
                        </h3>
                        <div className="grid grid-cols-2 gap-3">
                            {property.metrics.capRate && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Percent size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'معدل العائد' : 'Cap Rate'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.capRate}</p>
                                </div>
                            )}
                            {property.metrics.pricePerSqFt && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Ruler size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'السعر/م²' : 'Price / SqM'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.pricePerSqFt}</p>
                                </div>
                            )}
                            {property.metrics.size && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Ruler size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'المساحة' : 'Size'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.size} {isRTL ? 'م²' : 'sqm'}</p>
                                </div>
                            )}
                            {property.metrics.bedrooms && (
                                <div className="metric-card">
                                    <div className={`flex items-center gap-1.5 mb-1 text-gray-500 dark:text-[var(--chat-text-secondary)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <Home size={16} />
                                        <p className="text-[10px] uppercase font-bold">{isRTL ? 'غرف النوم' : 'Bedrooms'}</p>
                                    </div>
                                    <p className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">{property.metrics.bedrooms}</p>
                                </div>
                            )}
                            {property.metrics.walkScore && (
                                <div className="metric-card col-span-2">
                                    <div className={`flex justify-between items-end mb-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                                        <div className={`flex items-center gap-1.5 text-gray-500 dark:text-[var(--chat-text-secondary)] ${isRTL ? 'flex-row-reverse' : ''}`}>
                                            <Footprints size={16} />
                                            <p className="text-[10px] uppercase font-bold">{isRTL ? 'نقاط المشي' : 'Walk Score'}</p>
                                        </div>
                                        <span className="text-xl font-bold text-gray-900 dark:text-white">{property.metrics.walkScore}/100</span>
                                    </div>
                                    <div className="h-2 w-full bg-gray-100 dark:bg-black/40 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)]"
                                            style={{ width: `${property.metrics.walkScore}%` }}
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

                {/* Agent Contact - Only show if agent exists */}
                {property.agent && (
                    <div className={`bg-white dark:bg-[var(--chat-surface-dark)] p-4 rounded-xl border border-gray-200 dark:border-[var(--chat-border-dark)] shadow-sm flex items-center gap-3 ${isRTL ? 'flex-row-reverse' : ''}`}>
                        <div className="size-12 rounded-full bg-gradient-to-br from-[var(--chat-primary)] to-teal-600 flex items-center justify-center text-white font-bold border-2 border-white dark:border-[var(--chat-background-dark)] shadow-sm">
                            {property.agent.name.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div className={`flex-1 min-w-0 ${isRTL ? 'text-right' : ''}`}>
                            <p className="text-sm font-bold text-gray-900 dark:text-white truncate">{property.agent.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{property.agent.title}</p>
                        </div>
                        <div className="flex gap-2">
                            <button className="size-8 flex items-center justify-center rounded-full bg-gray-100 dark:bg-white/5 hover:bg-[var(--chat-primary)] hover:text-white dark:hover:bg-[var(--chat-primary)] transition-colors text-gray-600 dark:text-white">
                                <MessageCircle size={18} />
                            </button>
                            <button className="size-8 flex items-center justify-center rounded-full bg-gray-100 dark:bg-white/5 hover:bg-[var(--chat-primary)] hover:text-white dark:hover:bg-[var(--chat-primary)] transition-colors text-gray-600 dark:text-white">
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
            <aside className={`chat-contextual-pane bg-white/60 dark:bg-[#131d20] backdrop-blur-md hidden xl:flex flex-col overflow-y-auto z-20 chat-scrollbar ${isRTL ? 'border-r border-l-0' : ''}`}>
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
                            className={`fixed ${isRTL ? 'left-0' : 'right-0'} top-0 h-full w-[340px] bg-white/95 dark:bg-[#131d20] backdrop-blur-md flex flex-col z-50 xl:hidden overflow-y-auto chat-scrollbar`}
                        >
                            {paneContent}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
