"use client";

import { motion } from "framer-motion";
import { AlertTriangle, ArrowRight, MapPin, Building2, Wallet, TrendingUp } from "lucide-react";

interface Alternative {
    label_ar: string;
    label_en: string;
    action: string;
}

interface RealityCheckProps {
    detected: string;
    message_ar: string;
    message_en: string;
    alternatives: Alternative[];
    pivot_action?: string;
    isRTL?: boolean;
}

// Map actions to icons
const getActionIcon = (action: string) => {
    if (action.includes("october") || action.includes("nearby") || action.includes("area")) {
        return MapPin;
    }
    if (action.includes("apt") || action.includes("apartment") || action.includes("type")) {
        return Building2;
    }
    if (action.includes("budget") || action.includes("price")) {
        return Wallet;
    }
    return TrendingUp;
};

export default function RealityCheck({
    detected,
    message_ar,
    message_en,
    alternatives = [],
    isRTL = true,
}: RealityCheckProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl overflow-hidden bg-gradient-to-br from-orange-950/80 to-red-950/60 border border-orange-500/30"
            dir={isRTL ? 'rtl' : 'ltr'}
        >
            {/* Compact Header */}
            <div className="px-4 py-3 bg-gradient-to-r from-orange-500/20 to-transparent flex items-center gap-3">
                <div className="p-1.5 bg-orange-500/20 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-orange-400" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-bold text-orange-400 text-sm">
                            {isRTL ? 'تنبيه ذكي' : 'Reality Check'}
                        </span>
                        <span className="px-1.5 py-0.5 bg-orange-500/20 text-orange-300 text-[9px] font-medium rounded">
                            {isRTL ? 'نصيحة' : 'Advice'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Message - Compact */}
            <div className="px-4 py-3">
                <p className="text-sm text-white/90 leading-relaxed">
                    {isRTL ? message_ar : message_en}
                </p>
                {detected && (
                    <p className="text-xs text-orange-300/70 mt-2">
                        {detected}
                    </p>
                )}
            </div>

            {/* Alternatives - Compact Pills */}
            {alternatives.length > 0 && (
                <div className="px-4 pb-3">
                    <div className="flex flex-wrap gap-2">
                        {alternatives.slice(0, 3).map((alt, idx) => {
                            const Icon = getActionIcon(alt.action);
                            return (
                                <motion.button
                                    key={idx}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: idx * 0.1 }}
                                    whileHover={{ scale: 1.03 }}
                                    whileTap={{ scale: 0.97 }}
                                    className="flex items-center gap-2 px-3 py-2 bg-white/10 hover:bg-white/15 border border-white/10 hover:border-orange-500/40 rounded-lg text-xs transition-all group"
                                >
                                    <Icon className="w-3.5 h-3.5 text-orange-400" />
                                    <span className="text-white/90 font-medium">
                                        {isRTL ? alt.label_ar : alt.label_en}
                                    </span>
                                    <ArrowRight className={`w-3 h-3 text-orange-400/50 group-hover:text-orange-400 transition-colors ${isRTL ? 'rotate-180' : ''}`} />
                                </motion.button>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Persuasive Footer */}
            <div className="px-4 py-2 bg-gradient-to-r from-white/5 to-transparent border-t border-white/5">
                <p className="text-[10px] text-center text-white/50">
                    {isRTL
                        ? '💡 بدائل ذكية تناسب ميزانيتك الحقيقية'
                        : '💡 Smart alternatives that match your real budget'
                    }
                </p>
            </div>
        </motion.div>
    );
}
