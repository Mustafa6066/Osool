'use client';

import { Bed, Bath, Ruler, Star, TrendingUp, Bookmark } from 'lucide-react';
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
}

interface PropertyCardEnhancedProps {
    property: PropertyData;
    showChart?: boolean;
    onViewDetails?: (id: string) => void;
    onBookmark?: (id: string) => void;
}

// SVG Appreciation Chart Component
function AppreciationChart({ projectedPrice = '$2.75M', projectedGrowth = '+12.4%' }: { projectedPrice?: string; projectedGrowth?: string }) {
    return (
        <div className="px-6 py-5 bg-gray-50 dark:bg-black/20 border-t border-gray-200 dark:border-[var(--chat-border-dark)]">
            <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-gray-900 dark:text-white">Price Appreciation Forecast (5 Years)</h4>
                <span className="text-xs font-bold text-green-600 dark:text-green-400 flex items-center gap-1 bg-green-100 dark:bg-green-900/20 px-2 py-0.5 rounded">
                    <TrendingUp size={14} /> {projectedGrowth} Projected
                </span>
            </div>
            {/* Custom SVG Chart */}
            <div className="h-28 w-full mt-2 relative">
                <svg className="w-full h-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 400 100">
                    {/* Grid lines */}
                    <line className="text-gray-200 dark:text-white/5" stroke="currentColor" strokeDasharray="4 4" strokeWidth="1" x1="0" x2="400" y1="20" y2="20" />
                    <line className="text-gray-200 dark:text-white/5" stroke="currentColor" strokeDasharray="4 4" strokeWidth="1" x1="0" x2="400" y1="50" y2="50" />
                    <line className="text-gray-200 dark:text-white/5" stroke="currentColor" strokeDasharray="4 4" strokeWidth="1" x1="0" x2="400" y1="80" y2="80" />

                    {/* Area Gradient */}
                    <defs>
                        <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
                        </linearGradient>
                    </defs>

                    {/* Trend Line Path */}
                    <path
                        className="dark:stroke-[var(--chat-teal-accent)] drop-shadow-md"
                        d="M0,85 C50,82 80,75 120,70 C180,62 220,50 280,35 C330,22 360,15 400,5"
                        fill="none"
                        stroke="var(--chat-primary)"
                        strokeWidth="3"
                    />

                    {/* Fill Area */}
                    <path
                        d="M0,85 C50,82 80,75 120,70 C180,62 220,50 280,35 C330,22 360,15 400,5 V100 H0 Z"
                        fill="url(#chartGradient)"
                        style={{ mixBlendMode: 'overlay' }}
                    />

                    {/* Data Points */}
                    <circle className="fill-white dark:fill-[var(--chat-surface-dark)] stroke-[var(--chat-primary)] dark:stroke-[var(--chat-teal-accent)]" cx="0" cy="85" r="3" strokeWidth="2" />
                    <circle className="fill-white dark:fill-[var(--chat-surface-dark)] stroke-[var(--chat-primary)] dark:stroke-[var(--chat-teal-accent)]" cx="120" cy="70" r="3" strokeWidth="2" />
                    <circle className="fill-white dark:fill-[var(--chat-surface-dark)] stroke-[var(--chat-primary)] dark:stroke-[var(--chat-teal-accent)]" cx="280" cy="35" r="3" strokeWidth="2" />

                    {/* Final Point with Tooltip-like label */}
                    <g>
                        <circle className="fill-[var(--chat-primary)] dark:fill-[var(--chat-teal-accent)] stroke-white dark:stroke-[var(--chat-background-dark)]" cx="400" cy="5" r="4" strokeWidth="2" />
                        <rect className="fill-[var(--chat-primary)] dark:fill-[var(--chat-surface-dark)]" height="22" rx="4" width="70" x="340" y="-25" />
                        <text className="fill-white text-[10px] font-bold" fontFamily="system-ui" textAnchor="middle" x="375" y="-10">{projectedPrice}</text>
                    </g>
                </svg>
                {/* X Axis Labels */}
                <div className="flex justify-between text-[10px] text-gray-400 dark:text-gray-500 mt-2 font-mono">
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
}: PropertyCardEnhancedProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="chat-property-card max-w-2xl group"
        >
            <div className="flex flex-col sm:flex-row">
                {/* Image Section */}
                <div
                    className="w-full sm:w-2/5 h-56 sm:h-auto bg-cover bg-center relative"
                    style={{
                        backgroundImage: property.image
                            ? `url('${property.image}')`
                            : 'linear-gradient(135deg, #1c2b31 0%, #124759 100%)',
                    }}
                >
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent sm:bg-gradient-to-r"></div>
                    {property.badge && (
                        <div className="absolute top-3 left-3 bg-white/90 dark:bg-black/70 backdrop-blur-md text-[var(--chat-primary)] dark:text-[var(--chat-teal-accent)] text-[10px] font-bold px-2.5 py-1 rounded-md uppercase tracking-wide border border-white/20">
                            {property.badge}
                        </div>
                    )}
                    <div className="absolute bottom-3 left-3 sm:hidden text-white">
                        <p className="text-lg font-bold shadow-black drop-shadow-md">{property.price}</p>
                    </div>
                </div>

                {/* Content Section */}
                <div className="p-5 flex flex-col justify-between flex-1 relative">
                    <div>
                        <div className="flex justify-between items-start mb-2">
                            {property.growthBadge && (
                                <div className="px-2 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[10px] font-bold uppercase tracking-wider">
                                    {property.growthBadge}
                                </div>
                            )}
                            {property.rating && (
                                <div className="flex items-center gap-1 bg-gray-100 dark:bg-white/5 px-2 py-1 rounded-md">
                                    <Star size={14} className="text-amber-400 fill-amber-400" />
                                    <span className="text-xs font-bold text-gray-700 dark:text-white">{property.rating}</span>
                                </div>
                            )}
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white leading-tight mb-1 group-hover:text-[var(--chat-primary)] dark:group-hover:text-[var(--chat-teal-accent)] transition-colors">
                            {property.title}
                        </h3>
                        <p className="text-[13px] text-gray-500 dark:text-[var(--chat-text-secondary)] mb-3">{property.address}</p>
                        <div className="hidden sm:block text-2xl font-extrabold text-gray-900 dark:text-white mb-4 tracking-tight">
                            {property.price}
                        </div>
                        <div className="grid grid-cols-3 gap-2 py-3 border-t border-b border-gray-100 dark:border-white/5 text-gray-600 dark:text-gray-300">
                            <div className="flex flex-col items-center">
                                <Bed size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.bedrooms} Bed</span>
                            </div>
                            <div className="flex flex-col items-center border-l border-gray-100 dark:border-white/5">
                                <Bath size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.bathrooms} Bath</span>
                            </div>
                            <div className="flex flex-col items-center border-l border-gray-100 dark:border-white/5">
                                <Ruler size={18} className="mb-1 opacity-70" />
                                <span className="text-xs font-bold">{property.sqft.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-3 mt-4">
                        <button
                            onClick={() => onViewDetails?.(property.id)}
                            className="flex-1 bg-[var(--chat-primary)] hover:bg-[var(--chat-primary)]/90 text-white py-2.5 rounded-lg text-xs font-bold uppercase tracking-wide transition-colors shadow-lg shadow-[var(--chat-primary)]/20 hover:shadow-[var(--chat-primary)]/30"
                        >
                            View Details
                        </button>
                        <button
                            onClick={() => onBookmark?.(property.id)}
                            className="px-3 py-2 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-white/5 rounded-lg text-gray-700 dark:text-white transition-colors"
                        >
                            <Bookmark size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Chart Section */}
            {showChart && (
                <AppreciationChart
                    projectedPrice={property.projectedPrice}
                    projectedGrowth={property.projectedGrowth}
                />
            )}
        </motion.div>
    );
}
