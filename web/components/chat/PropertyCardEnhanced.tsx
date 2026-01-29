'use client';

import { useEffect, useRef } from 'react';
import { Bed, Bath, Ruler, MapPin, Bookmark, TrendingUp, Star } from 'lucide-react';
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
}

interface PropertyCardEnhancedProps {
    property: PropertyData;
    showChart?: boolean;
    onViewDetails?: (id: string) => void;
    onBookmark?: (id: string) => void;
    onSelect?: (property: PropertyData) => void;
    isRTL?: boolean;
}

// Inline Sparkline Chart Component
function SparklineChart({
    projectedGrowth,
    isRTL = false
}: {
    projectedGrowth?: string;
    isRTL?: boolean;
}) {
    const pathRef = useRef<SVGPathElement>(null);

    useEffect(() => {
        if (pathRef.current) {
            const pathLength = pathRef.current.getTotalLength();
            pathRef.current.style.strokeDasharray = `${pathLength}`;
            pathRef.current.style.strokeDashoffset = `${pathLength}`;
            
            anime({
                targets: pathRef.current,
                strokeDashoffset: [pathLength, 0],
                easing: 'easeOutExpo',
                duration: 1200,
                delay: 400,
            });
        }
    }, []);

    if (!projectedGrowth) return null;

    return (
        <div className="card-chart-inline">
            <div className="flex items-center justify-between mb-2">
                <span className="chart-label">
                    {isRTL ? 'توقع 5 سنوات' : '5Y Projection'}
                </span>
                <span className="chart-value flex items-center gap-1">
                    <TrendingUp size={10} />
                    +{projectedGrowth}
                </span>
            </div>
            <svg viewBox="0 0 200 40" preserveAspectRatio="none" className="overflow-visible">
                {/* Gradient Definition */}
                <defs>
                    <linearGradient id="sparklineGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--chart-line-color)" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="var(--chart-line-color)" stopOpacity="0" />
                    </linearGradient>
                </defs>
                
                {/* Area fill */}
                <path
                    d="M0,35 C20,33 40,30 60,27 C100,20 140,12 180,6 L200,4 V40 H0 Z"
                    className="sparkline-area"
                />
                
                {/* Line */}
                <path
                    ref={pathRef}
                    d="M0,35 C20,33 40,30 60,27 C100,20 140,12 180,6 L200,4"
                    className="sparkline"
                />
                
                {/* End point */}
                <circle cx="200" cy="4" r="3" fill="var(--chart-line-color)" />
            </svg>
        </div>
    );
}

export default function PropertyCardEnhanced({
    property,
    showChart = true,
    onViewDetails,
    onBookmark,
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
    const hasGrowthData = property.projectedGrowth || property.projectedPrice;

    const handleCardClick = () => {
        onSelect?.(property);
    };

    return (
        <div
            ref={cardRef}
            className="premium-card max-w-md cursor-pointer"
            style={{ opacity: 0 }}
            onClick={handleCardClick}
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Image Section */}
            <div className="premium-card-image h-44 sm:h-52">
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

                {/* Title Overlay */}
                <div className={`absolute bottom-0 ${isRTL ? 'right-0' : 'left-0'} p-4 z-10`}>
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
            <div className="data-ribbon">
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

            {/* Property Stats */}
            <div className="property-stats-row">
                <div className="property-stat">
                    <Bed size={14} />
                    <span>{property.bedrooms} {isRTL ? 'غرف' : 'Bed'}</span>
                </div>
                <div className="property-stat">
                    <Bath size={14} />
                    <span>{property.bathrooms} {isRTL ? 'حمام' : 'Bath'}</span>
                </div>
                <div className="property-stat">
                    <Ruler size={14} />
                    <span>{property.sqft.toLocaleString()} {isRTL ? 'م²' : 'sqm'}</span>
                </div>
            </div>

            {/* Inline Sparkline Chart */}
            {showChart && hasGrowthData && (
                <SparklineChart
                    projectedGrowth={property.projectedGrowth}
                    isRTL={isRTL}
                />
            )}

            {/* Action Buttons */}
            <div className="premium-card-actions">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onViewDetails?.(property.id);
                    }}
                    className="premium-card-btn-primary"
                >
                    {isRTL ? 'عرض التفاصيل' : 'View Details'}
                </button>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onBookmark?.(property.id);
                    }}
                    className="premium-card-btn-secondary"
                >
                    <Bookmark size={16} />
                </button>
            </div>
        </div>
    );
}
