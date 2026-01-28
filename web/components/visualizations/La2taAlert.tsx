"use client";

import { motion } from "framer-motion";
import { TrendingDown, MapPin, Bed, Maximize2, Eye } from "lucide-react";

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
}

// Format currency
const formatPrice = (price: number): string => {
    if (price >= 1_000_000) {
        return `${(price / 1_000_000).toFixed(2)}M`;
    }
    return `${(price / 1_000).toFixed(0)}K`;
};

export default function La2taAlert({
    properties = [],
    message_ar,
    message_en,
    total_found,
}: La2taAlertProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 border-2 border-amber-500/50 rounded-2xl p-6 overflow-hidden"
        >
            {/* Alert Header */}
            <div className="flex items-center gap-3 mb-5">
                <motion.div
                    animate={{ rotate: [0, -10, 10, -10, 0] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                    className="text-4xl"
                >
                    🐺
                </motion.div>
                <div>
                    <h3 className="text-lg font-bold text-amber-400 flex items-center gap-2">
                        La2ta Radar Alert!
                        {total_found && total_found > properties.length && (
                            <span className="text-xs bg-amber-500/30 px-2 py-0.5 rounded-full">
                                +{total_found - properties.length} more
                            </span>
                        )}
                    </h3>
                    <p className="text-sm text-gray-400" dir="rtl">{message_ar}</p>
                </div>
            </div>

            {/* Property Cards */}
            <div className="space-y-3">
                {properties.map((prop, idx) => (
                    <motion.div
                        key={prop.id || idx}
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-black/30 rounded-xl p-4 border border-amber-500/30 hover:border-amber-500/50 transition-colors"
                    >
                        <div className="flex justify-between items-start gap-4">
                            {/* Property Info */}
                            <div className="flex-1 min-w-0">
                                <h4 className="font-semibold text-white truncate">
                                    {prop.title}
                                </h4>
                                <div className="flex items-center gap-1 text-xs text-gray-400 mt-1">
                                    <MapPin className="w-3 h-3 flex-shrink-0" />
                                    <span className="truncate">{prop.location}</span>
                                </div>

                                {/* Property Details */}
                                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                    {prop.bedrooms && (
                                        <span className="flex items-center gap-1">
                                            <Bed className="w-3 h-3" />
                                            {prop.bedrooms} BR
                                        </span>
                                    )}
                                    {prop.size_sqm && (
                                        <span className="flex items-center gap-1">
                                            <Maximize2 className="w-3 h-3" />
                                            {prop.size_sqm} sqm
                                        </span>
                                    )}
                                    {prop.wolf_score && (
                                        <span className="flex items-center gap-1 text-amber-400">
                                            🐺 {prop.wolf_score}/100
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Discount Badge */}
                            <div className="flex flex-col items-end gap-2">
                                <div className="bg-green-500/20 border border-green-500/50 rounded-lg px-3 py-1.5">
                                    <div className="flex items-center gap-1 text-green-400 font-bold">
                                        <TrendingDown className="w-4 h-4" />
                                        <span>
                                            -{prop.la2ta_score?.toFixed(0) || "10"}%
                                        </span>
                                    </div>
                                </div>
                                {prop.savings && prop.savings > 0 && (
                                    <span className="text-xs text-green-400">
                                        Save {formatPrice(prop.savings)}
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Price Row */}
                        <div className="flex justify-between items-center mt-4 pt-3 border-t border-white/10">
                            <div>
                                <div className="text-xl font-bold text-blue-400">
                                    {formatPrice(prop.price)} EGP
                                </div>
                                {prop.valuation?.predicted_price && (
                                    <div className="text-xs text-gray-500 line-through">
                                        Market: {formatPrice(prop.valuation.predicted_price)} EGP
                                    </div>
                                )}
                            </div>
                            <button className="bg-amber-500 hover:bg-amber-600 text-black font-semibold px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors">
                                <Eye className="w-4 h-4" />
                                View Deal
                            </button>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Footer Note */}
            <div className="mt-4 text-center">
                <p className="text-xs text-gray-500">
                    {message_en}
                </p>
            </div>
        </motion.div>
    );
}
