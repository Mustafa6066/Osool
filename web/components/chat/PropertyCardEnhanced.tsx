'use client';

import { useEffect, useRef } from 'react';
import { MapPin, TrendingUp, TrendingDown, Star, ArrowUpRight } from 'lucide-react';
import anime from 'animejs';

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
    // Key metric for simplified display
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
}

export default function PropertyCardEnhanced({
    property,
    onViewDetails,
    onSelect,
    isRTL = false,
}: PropertyCardEnhancedProps) {
    const cardRef = useRef<HTMLDivElement>(null);

    // Entrance animation
    useEffect(() => {
        if (cardRef.current) {
            anime({
                targets: cardRef.current,
                opacity: [0, 1],
                translateY: [20, 0],
                easing: 'easeOutExpo',
                duration: 700,
            });
        }
    }, []);

    // Calculate if this is a top pick based on wolf score
    const isTopPick = property.isTopPick || (property.wolfScore && property.wolfScore >= 85);

    // Generate default key metric from projectedGrowth if not provided
    const keyMetric = property.keyMetric || (property.projectedGrowth ? {
        label: isRTL ? 'العائد المتوقع' : 'Projected ROI',
        value: `+${property.projectedGrowth}`,
        trend: 'up' as const
    } : null);

    const handleCardClick = () => {
        onSelect?.(property);
    };

    return (
        <div
            ref={cardRef}
            className="premium-card max-w-md cursor-pointer"
            style={{
                opacity: 0,
                minWidth: 'var(--card-min-width, 280px)',
                maxWidth: 'var(--card-max-width, 400px)'
            }}
            onClick={handleCardClick}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Image Section - 16:9 ratio */}
            <div className="premium-card-image h-44 sm:h-52 relative">
                {property.image ? (
                    <img
                        src={property.image}
                        alt={property.title}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 flex items-center justify-center">
                        <span className="text-4xl opacity-30">🏠</span>
                    </div>
                )}

                {/* Overlay Badges */}
                <div className={`absolute top-3 ${isRTL ? 'right-3' : 'left-3'} z-10 flex flex-col gap-1.5`}>
                    {isTopPick && (
                        <span className="badge-top-pick flex items-center gap-1">
                            <Star size={10} className="fill-current" />
                            {isRTL ? 'اختيار مميز' : 'Top Pick'}
                        </span>
                    )}
                    {property.badge && !isTopPick && (
                        <span className="badge-top-pick">
                            {property.badge}
                        </span>
                    )}
                    {property.growthBadge && (
                        <span className="badge-high-growth">
                            {property.growthBadge}
                        </span>
                    )}
                </div>

                {/* Title Overlay with gradient */}
                <div className={`absolute bottom-0 left-0 right-0 p-4 z-10 bg-gradient-to-t from-black/70 via-black/40 to-transparent`}>
                    <h3 className="text-white font-bold text-base sm:text-lg leading-tight line-clamp-2 drop-shadow-md">
                        {property.title}
                    </h3>
                    <p className="text-white/80 text-xs mt-1 flex items-center gap-1">
                        <MapPin size={10} />
                        {property.address}
                    </p>
                </div>
            </div>

            {/* Data Ribbon - Price & Wolf Score */}
            <div className="data-ribbon" style={{ padding: 'var(--space-4, 16px)' }}>
                <div className="data-ribbon-item">
                    <span className="data-ribbon-value">{property.price}</span>
                    <span className="data-ribbon-label">{isRTL ? 'السعر' : 'Price'}</span>
                </div>

                {property.wolfScore && (
                    <div className="wolf-score-badge">
                        <span>🐺</span>
                        <span>{property.wolfScore}/100</span>
                    </div>
                )}

                {property.rating && !property.wolfScore && (
                    <div className="wolf-score-badge">
                        <Star size={14} className="fill-current" />
                        <span>{property.rating.toFixed(1)}</span>
                    </div>
                )}
            </div>

            {/* Key Metric Highlight (replaces detailed stats) */}
            {keyMetric && (
                <div
                    className="flex items-center justify-between px-4 py-3 bg-[var(--semantic-surface-elevated,#F9FAFB)] dark:bg-[var(--semantic-surface-elevated,#374151)] border-t border-[var(--semantic-border,#E5E7EB)] dark:border-[var(--semantic-border,#374151)]"
                    style={{ padding: 'var(--space-3, 12px) var(--space-4, 16px)' }}
                >
                    <span className="text-xs text-[var(--semantic-text-muted,#6B7280)] dark:text-[var(--semantic-text-muted,#9CA3AF)]">
                        {keyMetric.label}
                    </span>
                    <span className={`text-sm font-semibold flex items-center gap-1 ${
                        keyMetric.trend === 'up'
                            ? 'text-[var(--semantic-success,#059669)] dark:text-[var(--semantic-success,#34D399)]'
                            : keyMetric.trend === 'down'
                            ? 'text-[var(--semantic-danger,#B91C1C)] dark:text-[var(--semantic-danger,#F87171)]'
                            : 'text-[var(--semantic-text-primary,#1F2937)] dark:text-[var(--semantic-text-primary,#F9FAFB)]'
                    }`}>
                        {keyMetric.trend === 'up' && <TrendingUp size={14} />}
                        {keyMetric.trend === 'down' && <TrendingDown size={14} />}
                        {keyMetric.value}
                    </span>
                </div>
            )}

            {/* Full-width View Details Button */}
            <div className="p-4" style={{ padding: 'var(--space-4, 16px)' }}>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onViewDetails?.(property.id);
                    }}
                    className="w-full premium-card-btn-primary flex items-center justify-center gap-2"
                >
                    {isRTL ? 'عرض التفاصيل' : 'View Details'}
                    <ArrowUpRight size={16} />
                </button>
            </div>
        </div>
    );
}
