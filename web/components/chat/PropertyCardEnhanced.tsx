'use client';

import { useEffect, useRef } from 'react';
import { Bed, Bath, Ruler, Star, TrendingUp, Bookmark, MapPin } from 'lucide-react';
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
}

interface PropertyCardEnhancedProps {
    property: PropertyData;
    showChart?: boolean;
    onViewDetails?: (id: string) => void;
    onBookmark?: (id: string) => void;
    isRTL?: boolean;
}

// SVG Appreciation Chart Component with anime.js
function AppreciationChart({
    projectedPrice,
    projectedGrowth,
    isRTL = false
}: {
    projectedPrice?: string;
    projectedGrowth?: string;
    isRTL?: boolean;
}) {
    const chartRef = useRef<HTMLDivElement>(null);
    const pathRef = useRef<SVGPathElement>(null);

    useEffect(() => {
        // Animate chart path
        if (pathRef.current) {
            const pathLength = pathRef.current.getTotalLength();
            anime({
                targets: pathRef.current,
                strokeDashoffset: [pathLength, 0],
                easing: 'easeOutExpo',
                duration: 1500,
                delay: 300,
            });
            pathRef.current.style.strokeDasharray = `${pathLength}`;
        }

        // Animate data points
        if (chartRef.current) {
            anime({
                targets: chartRef.current.querySelectorAll('.data-point'),
                opacity: [0, 1],
                scale: [0, 1],
                delay: anime.stagger(200, { start: 800 }),
                easing: 'easeOutElastic(1, .8)',
                duration: 600,
            });
        }
    }, []);

    // Don't show chart if no data
    if (!projectedPrice && !projectedGrowth) return null;

    return (
        <div ref={chartRef} className="property-chart-section">
            <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-[var(--color-text-primary)]">
                    {isRTL ? 'توقعات ارتفاع السعر (5 سنوات)' : 'Price Appreciation Forecast (5 Years)'}
                </h4>
                {projectedGrowth && (
                    <span className="text-xs font-bold text-green-600 flex items-center gap-1 bg-green-100 dark:bg-green-900/20 px-2 py-0.5 rounded">
                        <TrendingUp size={12} /> {projectedGrowth} {isRTL ? 'متوقع' : 'Projected'}
                    </span>
                )}
            </div>

            {/* Custom SVG Chart */}
            <div className="h-28 w-full mt-2 relative">
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 400 100">
                    {/* Grid lines */}
                    <line className="chart-grid-line" x1="0" x2="400" y1="20" y2="20" />
                    <line className="chart-grid-line" x1="0" x2="400" y1="50" y2="50" />
                    <line className="chart-grid-line" x1="0" x2="400" y1="80" y2="80" />

                    {/* Area Gradient */}
                    <defs>
                        <linearGradient id="chartGradientEnhanced" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="var(--color-teal-accent)" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="var(--color-teal-accent)" stopOpacity="0" />
                        </linearGradient>
                    </defs>

                    {/* Trend Line Path */}
                    <path
                        ref={pathRef}
                        className="chart-trend-line"
                        d="M0,85 C50,82 80,75 120,70 C180,62 220,50 280,35 C330,22 360,15 400,5"
                    />

                    {/* Fill Area */}
                    <path
                        d="M0,85 C50,82 80,75 120,70 C180,62 220,50 280,35 C330,22 360,15 400,5 V100 H0 Z"
                        fill="url(#chartGradientEnhanced)"
                        style={{ mixBlendMode: 'overlay' }}
                    />

                    {/* Data Points */}
                    <circle className="data-point chart-data-point" cx="0" cy="85" r="3" style={{ opacity: 0 }} />
                    <circle className="data-point chart-data-point" cx="120" cy="70" r="3" style={{ opacity: 0 }} />
                    <circle className="data-point chart-data-point" cx="280" cy="35" r="3" style={{ opacity: 0 }} />

                    {/* Final Point with Tooltip-like label */}
                    <g className="data-point" style={{ opacity: 0 }}>
                        <circle className="fill-[var(--color-primary)] dark:fill-[var(--color-teal-accent)] stroke-white" cx="400" cy="5" r="4" strokeWidth="2" />
                        {projectedPrice && (
                            <>
                                <rect className="fill-[var(--color-primary)] dark:fill-[var(--color-surface-dark)]" height="22" rx="4" width="70" x="325" y="-25" />
                                <text className="fill-white text-[10px] font-bold" fontFamily="system-ui" textAnchor="middle" x="360" y="-10">{projectedPrice}</text>
                            </>
                        )}
                    </g>
                </svg>

                {/* X Axis Labels */}
                <div className="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-2 font-mono">
                    <span>2024</span>
                    <span>2025</span>
                    <span>2026</span>
                    <span>2027</span>
                    <span>2028</span>
                    <span>2029</span>
                </div>
            </div>
        </div>
    );
}

export default function PropertyCardEnhanced({
    property,
    showChart = true,
    onViewDetails,
    onBookmark,
    isRTL = false,
}: PropertyCardEnhancedProps) {
    const cardRef = useRef<HTMLDivElement>(null);

    // Entrance animation
    useEffect(() => {
        if (cardRef.current) {
            anime({
                targets: cardRef.current,
                opacity: [0, 1],
                translateX: [-30, 0],
                easing: 'easeOutExpo',
                duration: 600,
            });
        }
    }, []);

    // Calculate if this is a top pick based on wolf score
    const isTopPick = property.isTopPick || (property.wolfScore && property.wolfScore >= 85);

    return (
        <div
            ref={cardRef}
            className="property-card-enhanced max-w-2xl group"
            style={{ opacity: 0 }}
        >
            <div className={`flex flex-col sm:flex-row ${isRTL ? 'sm:flex-row-reverse' : ''}`}>
                {/* Image Section */}
                <div
                    className="w-full sm:w-2/5 h-56 sm:h-auto bg-cover bg-center relative min-h-[200px]"
                    style={{
                        backgroundImage: property.image
                            ? `url('${property.image}')`
                            : 'linear-gradient(135deg, #1c2b31 0%, #124759 100%)',
                    }}
                >
                    <div className={`absolute inset-0 bg-gradient-to-t from-black/60 to-transparent ${isRTL ? 'sm:bg-gradient-to-l' : 'sm:bg-gradient-to-r'}`} />

                    {/* Top Pick Badge */}
                    {isTopPick && (
                        <div className={`absolute top-3 ${isRTL ? 'right-3' : 'left-3'} badge-top-pick`}>
                            {isRTL ? 'اختيار مميز' : 'Top Pick'}
                        </div>
                    )}

                    {/* Developer Badge */}
                    {property.badge && !isTopPick && (
                        <div className={`absolute top-3 ${isRTL ? 'right-3' : 'left-3'} badge-top-pick`}>
                            {property.badge}
                        </div>
                    )}

                    {/* Mobile Price */}
                    <div className={`absolute bottom-3 ${isRTL ? 'right-3' : 'left-3'} sm:hidden text-white`}>
                        <p className="text-lg font-bold drop-shadow-md">{property.price}</p>
                    </div>
                </div>

                {/* Content Section */}
                <div className={`p-5 flex flex-col justify-between flex-1 relative ${isRTL ? 'text-right' : ''}`}>
                    <div>
                        <div className={`flex justify-between items-start mb-2 ${isRTL ? 'flex-row-reverse' : ''}`}>
                            {property.growthBadge && (
                                <div className="badge-high-growth">
                                    {property.growthBadge}
                                </div>
                            )}
                            {property.rating && (
                                <div className="flex items-center gap-1 bg-[var(--color-surface-elevated)] px-2 py-1 rounded-md border border-[var(--color-border)]">
                                    <Star size={14} className="text-amber-400 fill-amber-400" />
                                    <span className="text-xs font-bold text-[var(--color-text-primary)]">{property.rating.toFixed(1)}</span>
                                </div>
                            )}
                            {property.wolfScore && !property.rating && (
                                <div className="flex items-center gap-1 bg-[var(--color-surface-elevated)] px-2 py-1 rounded-md border border-[var(--color-border)]">
                                    <span className="text-[10px] text-[var(--color-text-muted)]">🐺</span>
                                    <span className="text-xs font-bold text-[var(--color-text-primary)]">{property.wolfScore}</span>
                                </div>
                            )}
                        </div>

                        <h3 className="text-lg font-bold text-[var(--color-text-primary)] leading-tight mb-1 group-hover:text-[var(--color-primary)] transition-colors">
                            {property.title}
                        </h3>

                        <p className={`text-[13px] text-[var(--color-text-muted)] mb-3 flex items-center gap-1 ${isRTL ? 'flex-row-reverse' : ''}`}>
                            <MapPin size={12} />
                            {property.address}
                        </p>

                        {/* Price - Desktop */}
                        <div className="hidden sm:block text-2xl font-extrabold text-[var(--color-text-primary)] mb-4 tracking-tight">
                            {property.price}
                        </div>

                        {/* Property Stats */}
                        <div className={`grid grid-cols-3 gap-2 py-3 border-t border-b border-[var(--color-border)] text-[var(--color-text-muted)]`}>
                            <div className="flex flex-col items-center">
                                <Bed size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.bedrooms} {isRTL ? 'غرف' : 'Bed'}</span>
                            </div>
                            <div className="flex flex-col items-center border-l border-[var(--color-border)]">
                                <Bath size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.bathrooms} {isRTL ? 'حمام' : 'Bath'}</span>
                            </div>
                            <div className="flex flex-col items-center border-l border-[var(--color-border)]">
                                <Ruler size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.sqft.toLocaleString()} {isRTL ? 'م²' : 'sqm'}</span>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className={`flex gap-3 mt-4 ${isRTL ? 'flex-row-reverse' : ''}`}>
                        <button
                            onClick={() => onViewDetails?.(property.id)}
                            className="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-primary-light)] text-white py-2.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-all shadow-lg shadow-[var(--color-primary)]/20 hover:shadow-[var(--color-primary)]/30"
                        >
                            {isRTL ? 'عرض التفاصيل' : 'View Details'}
                        </button>
                        <button
                            onClick={() => onBookmark?.(property.id)}
                            className="px-3 py-2 border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
                        >
                            <Bookmark size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Chart Section - Only show if there's projection data */}
            {showChart && (property.projectedGrowth || property.projectedPrice) && (
                <AppreciationChart
                    projectedPrice={property.projectedPrice}
                    projectedGrowth={property.projectedGrowth}
                    isRTL={isRTL}
                />
            )}
        </div>
    );
}
