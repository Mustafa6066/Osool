"use client";

import { motion } from "framer-motion";
import { TrendingDown, MapPin, Sparkles, ArrowRight, Flame } from "lucide-react";

interface Property {
    id: number;
    title: string;
    location: string;
    price: number;
    size_sqm?: number;
    bedrooms?: number;
    la2ta_score?: number;
    savings?: number;
    valuation?: {
        predicted_price?: number;
        message_ar?: string;
    };
    wolf_score?: number;
}

interface La2taAlertProps {
    properties: Property[];
    message_ar: string;
    message_en: string;
    best_deal?: Property;
    total_found?: number;
    isRTL?: boolean;
}

// Format currency compactly
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(1)}M`;
    }
    return `${(price / 1_000).toFixed(0)}K`;
};

export default function La2taAlert({
    properties = [],
    isRTL = true,
}: La2taAlertProps) {
    if (properties.length === 0) return null;

    const maxSavings = Math.max(...properties.map(p => p.savings || 0));
    const avgDiscount = properties.reduce((sum, p) => sum + (p.la2ta_score || 10), 0) / properties.length;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl overflow-hidden bg-gradient-to-br from-amber-950/90 to-orange-950/90 border border-amber-500/30"
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Compact Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-amber-500/20 to-transparent flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <Flame className="w-5 h-5 text-amber-400" />
                        <motion.div
                            className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full"
                            animate={{ scale: [1, 1.3, 1] }}
                            transition={{ repeat: Infinity, duration: 1 }}
                        />
                    </div>
                    <span className="font-bold text-amber-400 text-sm">
                        {isRTL ? 'لقطة!' : 'Hot Deal!'}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-amber-300/70">
                        {isRTL ? `${properties.length} فرصة` : `${properties.length} found`}
                    </span>
                    {avgDiscount > 0 && (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs font-bold rounded-full flex items-center gap-1">
                            <TrendingDown className="w-3 h-3" />
                            {avgDiscount.toFixed(0)}%
                        </span>
                    )}
                </div>
            </div>

            {/* Main Content - Compact Cards */}
            <div className="p-3 space-y-2">
                {properties.slice(0, 2).map((prop, idx) => (
                    <motion.div
                        key={prop.id || idx}
                        initial={{ opacity: 0, x: isRTL ? 10 : -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={`p-3 rounded-lg border transition-all cursor-pointer ${
                            idx === 0
                                ? 'bg-amber-500/10 border-amber-500/40 hover:border-amber-400'
                                : 'bg-black/20 border-white/10 hover:border-white/20'
                        }`}
                    >
                        <div className="flex items-center justify-between gap-3">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-semibold text-white truncate">
                                        {prop.title}
                                    </span>
                                    {idx === 0 && (
                                        <span className="flex-shrink-0 px-1.5 py-0.5 bg-amber-500 text-black text-[9px] font-bold rounded">
                                            {isRTL ? 'أفضل' : 'BEST'}
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                                    <MapPin className="w-3 h-3 flex-shrink-0" />
                                    <span className="truncate">{prop.location}</span>
                                    {prop.bedrooms && <span>• {prop.bedrooms} {isRTL ? 'غرف' : 'BR'}</span>}
                                </div>
                            </div>

                            <div className="text-end flex-shrink-0">
                                <div className="text-base font-bold text-white">
                                    {formatPrice(prop.price)}
                                </div>
                                {prop.savings && prop.savings > 0 && (
                                    <div className="text-[10px] text-green-400 font-medium">
                                        {isRTL ? `وفّر ${formatPrice(prop.savings)}` : `Save ${formatPrice(prop.savings)}`}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}

                {/* See More Link */}
                {properties.length > 2 && (
                    <button className="w-full py-2 text-xs text-amber-400 hover:text-amber-300 flex items-center justify-center gap-1 transition-colors">
                        <Sparkles className="w-3 h-3" />
                        {isRTL ? `+${properties.length - 2} لقطات أخرى` : `+${properties.length - 2} more deals`}
                        <ArrowRight className={`w-3 h-3 ${isRTL ? 'rotate-180' : ''}`} />
                    </button>
                )}
            </div>

            {/* Persuasive Footer */}
            {maxSavings > 0 && (
                <div className="px-4 py-2 bg-gradient-to-r from-green-500/10 to-transparent border-t border-white/5">
                    <p className="text-[11px] text-center text-green-400/80">
                        {isRTL
                            ? `💰 وفّر حتى ${formatPrice(maxSavings)} عن سعر السوق`
                            : `💰 Save up to ${formatPrice(maxSavings)} below market`
                        }
                    </p>
                </div>
            )}
        </motion.div>
    );
}
