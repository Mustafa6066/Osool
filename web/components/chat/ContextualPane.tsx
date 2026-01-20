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
    if (!property) return null;

    const listingInsightsCard = (
        <div className="relative glass-panel rounded-2xl p-6 group hover:border-[var(--color-secondary)]/30 transition-colors w-full h-full md:h-auto md:aspect-[3/4] flex flex-col">
            <div className="absolute -bottom-[1px] -right-[1px] w-4 h-4 border-b border-r border-[var(--color-secondary)]/60 rounded-br-lg"></div>
            {/* Connector Line (Left) */}
            <div className="absolute top-1/2 -left-16 w-16 h-[1px] bg-gradient-to-l from-white/20 to-transparent"></div>

            <div className="flex justify-between items-center mb-6 flex-none">
                <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">{isRTL ? 'رؤى العقار' : 'Listing Insights'}</h3>
                <BarChart2 size={24} className="text-[var(--color-secondary)]/70" />
            </div>

            <div className="space-y-6 flex-1 overflow-y-auto no-scrollbar">
                {/* Cap Rate */}
                <div>
                    <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-2 font-display uppercase tracking-wider">
                        <span>{isRTL ? 'معدل العائد' : 'Cap Rate'}</span>
                        <span className="text-[var(--color-primary)] font-bold">High</span>
                    </div>
                    <div className="text-3xl font-light text-[var(--color-text-primary)] font-display">{property.metrics?.capRate || '8%'}</div>
                    <div className="w-full bg-[var(--color-surface-elevated)] h-1.5 mt-2 rounded-full overflow-hidden">
                        <div className="bg-gradient-to-r from-[var(--color-secondary)] to-[var(--color-primary)] w-[80%] h-full rounded-full opacity-80"></div>
                    </div>
                </div>

                {/* Price / SQM */}
                <div>
                    <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-1 font-display uppercase tracking-wider">
                        <span>{isRTL ? 'السعر / متر' : 'Price / SQM'}</span>
                    </div>
                    <div className="text-2xl font-light text-[var(--color-text-primary)] font-display">
                        {property.metrics?.pricePerSqFt || '110,000'} <span className="text-sm text-[var(--color-text-muted)]">EGP</span>
                    </div>
                </div>

                {/* Wolf Score */}
                <div>
                    <div className="flex justify-between text-xs text-[var(--color-text-muted)] mb-2 font-display uppercase tracking-wider">
                        <span>{isRTL ? 'تصنيف وولف' : 'Wolf Score'}</span>
                        <span className="text-[var(--color-tertiary)] font-bold">{property.metrics?.wolfScore || 85}/100</span>
                    </div>
                    <div className="h-16 w-full flex items-end gap-1 mt-2">
                        {Array.from({ length: 6 }).map((_, i) => {
                            const score = property.metrics?.wolfScore || 0;
                            const threshold = (i + 1) * 16.6; // ~100/6
                            const opacity = score >= threshold ? 0.3 + (i * 0.1) : 0.1;
                            const height = score >= threshold ? 30 + (i * 10) : 20;
                            const color = i > 3 ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-secondary)]';

                            return (
                                <div
                                    key={i}
                                    className={`w-1/6 ${color} rounded-t-sm transition-all duration-700`}
                                    style={{ height: `${height}%`, opacity }}
                                />
                            );
                        })}
                    </div>
                </div>

                {/* ROI Extra (from design) */}
                <div className="pt-4 border-t border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-bold tracking-widest uppercase text-[var(--color-text-muted)]">{isRTL ? 'العائد السنوي المتوقع' : 'Proj. Annual ROI'}</span>
                        <TrendingUp size={16} className="text-[var(--color-primary)]" />
                    </div>
                    <div className="text-3xl font-light text-[var(--color-primary)] font-display">{property.metrics?.roi || '12.5'}%</div>
                    <p className="text-[10px] text-[var(--color-text-muted)] mt-2 leading-tight">Based on recent market trends.</p>
                </div>
            </div>
        </div>
    );

    return (
        <>
            {/* Desktop Pane - Floating Card (Top Right) */}
            <aside className={`fixed top-[20%] right-[5%] w-72 z-20 hidden xl:block transition-all duration-500 transform ${property ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>
                {property && listingInsightsCard}
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
                            className={`fixed ${isRTL ? 'left-0' : 'right-0'} top-0 bottom-0 w-[300px] bg-[var(--color-surface)]/95 backdrop-blur-xl p-6 flex flex-col z-50 xl:hidden`}
                        >
                            <div className="flex justify-end mb-4">
                                <button onClick={onClose}><X className="text-[var(--color-text-muted)]" /></button>
                            </div>
                            {listingInsightsCard}
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
