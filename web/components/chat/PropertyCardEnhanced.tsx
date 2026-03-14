'use client';

import { MapPin, TrendingUp, TrendingDown, Star, ArrowUpRight, Bed, Bath, Maximize } from 'lucide-react';
import { motion } from 'framer-motion';

interface PropertyData {
    id: string;
    title: string;
    address: string;
    price: string;
    bedrooms: number;
    bathrooms: number;
    sqft: number;
    rating?: number;
    image?: string;
    badge?: string;
    growthBadge?: string;
    projectedGrowth?: string;
    projectedPrice?: string;
    wolfScore?: number;
    isTopPick?: boolean;
    developer?: string;
    keyMetric?: {
        label: string;
        value: string;
        trend?: 'up' | 'down' | 'stable';
    };
}

interface PropertyCardEnhancedProps {
    property: PropertyData;
    onViewDetails?: (id: string) => void;
    onSelect?: (property: PropertyData) => void;
    isRTL?: boolean;
    variant?: 'default' | 'compact' | 'horizontal';
    index?: number;
}

export default function PropertyCardEnhanced({
    property,
    onViewDetails,
    onSelect,
    isRTL = false,
    variant = 'default',
    index = 0,
}: PropertyCardEnhancedProps) {
    const isTopPick = property.isTopPick || (property.wolfScore && property.wolfScore >= 85);
    const scoreColor = property.wolfScore
        ? property.wolfScore >= 80 ? 'from-emerald-500 to-emerald-400'
            : property.wolfScore >= 60 ? 'from-amber-500 to-yellow-400'
                : 'from-gray-500 to-gray-400'
        : 'from-gray-500 to-gray-400';

    const keyMetric = property.keyMetric || (property.projectedGrowth ? {
        label: isRTL ? 'العائد المتوقع' : 'Projected ROI',
        value: `+${property.projectedGrowth}`,
        trend: 'up' as const
    } : null);

    const handleCardClick = () => {
        onSelect?.(property);
    };

    // Horizontal compact variant for inline chat display
    if (variant === 'horizontal') {
        return (
            <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.08, ease: 'easeOut' }}
                onClick={handleCardClick}
                className="group flex gap-3 p-3 rounded-xl border border-[var(--color-border)] hover:border-emerald-500/30 bg-[var(--color-surface)] cursor-pointer transition-all duration-200 hover:shadow-md"
                dir={isRTL ? 'rtl' : 'ltr'}
            >
                {/* Thumbnail */}
                <div className="w-16 h-16 rounded-lg flex-shrink-0 overflow-hidden bg-[var(--color-surface-elevated)]">
                    {property.image ? (
                        <img src={property.image} alt={property.title} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-xl opacity-30">🏠</div>
                    )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0 flex flex-col justify-center">
                    <h4 className="text-sm font-medium text-[var(--color-text-primary)] truncate">{property.title}</h4>
                    <p className="text-xs text-[var(--color-text-muted)] truncate mt-0.5">{property.address}</p>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-sm font-semibold text-[var(--color-text-primary)]">{property.price}</span>
                        {property.wolfScore && (
                            <span className="text-[9px] font-bold text-emerald-400">{property.wolfScore}/100</span>
                        )}
                    </div>
                </div>

                <ArrowUpRight className="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-emerald-400 transition-colors flex-shrink-0 self-center" />
            </motion.div>
        );
    }

    // Default card variant — minimal vertical design
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1, ease: 'easeOut' }}
            className="group rounded-2xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface)] cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-black/10 hover:border-[var(--color-border-light)]"
            style={{ maxWidth: '400px' }}
            onClick={handleCardClick}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Image Section */}
            <div className="relative h-44 sm:h-48 overflow-hidden">
                {property.image ? (
                    <img
                        src={property.image}
                        alt={property.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-[var(--color-surface-elevated)] to-[var(--color-surface-hover)] flex items-center justify-center">
                        <span className="text-4xl opacity-20">🏠</span>
                    </div>
                )}

                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

                {/* Badges */}
                <div className={`absolute top-3 ${isRTL ? 'right-3' : 'left-3'} flex flex-col gap-1.5`}>
                    {isTopPick && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/90 backdrop-blur-sm text-white text-[10px] font-bold">
                            <Star size={9} className="fill-current" />
                            {isRTL ? 'مميز' : 'Top Pick'}
                        </span>
                    )}
                    {property.badge && !isTopPick && (
                        <span className="px-2 py-0.5 rounded-md bg-emerald-500/90 backdrop-blur-sm text-white text-[10px] font-bold">
                            {property.badge}
                        </span>
                    )}
                    {property.growthBadge && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/90 backdrop-blur-sm text-white text-[10px] font-bold">
                            <TrendingUp size={9} />
                            {property.growthBadge}
                        </span>
                    )}
                </div>

                {/* Title on image */}
                <div className="absolute bottom-0 left-0 right-0 p-4">
                    <h3 className="text-white font-bold text-base leading-tight line-clamp-2 drop-shadow-md">
                        {property.title}
                    </h3>
                    <p className="text-white/70 text-xs mt-1 flex items-center gap-1">
                        <MapPin size={10} />
                        {property.address}
                    </p>
                </div>
            </div>

            {/* Content section */}
            <div className="p-4 space-y-3">
                {/* Price + Wolf Score row */}
                <div className="flex items-center justify-between">
                    <div>
                        <span className="text-lg font-bold text-[var(--color-text-primary)]">{property.price}</span>
                        {property.developer && (
                            <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">{property.developer}</p>
                        )}
                    </div>
                    {property.wolfScore && (
                        <div className="flex flex-col items-end">
                            <span className="text-[9px] text-[var(--color-text-muted)] uppercase tracking-wider">Osool Score</span>
                            <div className="flex items-center gap-2 mt-0.5">
                                <div className="w-16 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full bg-gradient-to-r ${scoreColor}`}
                                        style={{ width: `${Math.min(property.wolfScore, 100)}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold text-emerald-400">{property.wolfScore}</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Property specs */}
                <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                    {property.bedrooms > 0 && (
                        <div className="flex items-center gap-1">
                            <Bed size={12} /> {property.bedrooms}
                        </div>
                    )}
                    {property.bathrooms > 0 && (
                        <div className="flex items-center gap-1">
                            <Bath size={12} /> {property.bathrooms}
                        </div>
                    )}
                    {property.sqft > 0 && (
                        <div className="flex items-center gap-1">
                            <Maximize size={12} /> {property.sqft} m²
                        </div>
                    )}
                </div>

                {/* Key metric highlight */}
                {keyMetric && (
                    <div className="flex items-center justify-between py-2 px-3 rounded-lg bg-[var(--color-surface-elevated)]">
                        <span className="text-[10px] text-[var(--color-text-muted)]">{keyMetric.label}</span>
                        <span className={`text-xs font-bold flex items-center gap-1 ${keyMetric.trend === 'up' ? 'text-emerald-400' : keyMetric.trend === 'down' ? 'text-red-400' : 'text-[var(--color-text-primary)]'
                            }`}>
                            {keyMetric.trend === 'up' && <TrendingUp size={11} />}
                            {keyMetric.trend === 'down' && <TrendingDown size={11} />}
                            {keyMetric.value}
                        </span>
                    </div>
                )}

                {/* View Details button */}
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onViewDetails?.(property.id);
                    }}
                    className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-primary)]/10 text-[var(--color-primary)] hover:bg-[var(--color-primary)] hover:text-white transition-all duration-200 flex items-center justify-center gap-1.5"
                >
                    {isRTL ? 'عرض التفاصيل' : 'View Details'}
                    <ArrowUpRight size={13} />
                </button>
            </div>
        </motion.div>
    );
}
