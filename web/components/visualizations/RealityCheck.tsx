"use client";

import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, Lightbulb, MapPin, Building2, Wallet } from "lucide-react";

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
}

// Map actions to icons
const getActionIcon = (action: string) => {
    if (action.includes("october") || action.includes("nearby")) {
        return <MapPin className="w-4 h-4" />;
    }
    if (action.includes("apt") || action.includes("apartment")) {
        return <Building2 className="w-4 h-4" />;
    }
    if (action.includes("budget")) {
        return <Wallet className="w-4 h-4" />;
    }
    return <ArrowRight className="w-4 h-4" />;
};

export default function RealityCheck({
    detected,
    message_ar,
    message_en,
    alternatives = [],
}: RealityCheckProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="bg-gradient-to-br from-orange-900/30 to-red-900/30 border-2 border-orange-500/50 rounded-2xl p-6 overflow-hidden"
        >
            {/* Header */}
            <div className="flex items-start gap-4 mb-5">
                <motion.div
                    initial={{ rotate: 0 }}
                    animate={{ rotate: [0, -5, 5, -5, 0] }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="bg-orange-500/20 p-2 rounded-xl"
                >
                    <AlertCircle className="w-6 h-6 text-orange-400" />
                </motion.div>
                <div>
                    <h3 className="text-lg font-bold text-orange-400 flex items-center gap-2">
                        Reality Check
                        <span className="text-xs bg-orange-500/30 px-2 py-0.5 rounded-full text-orange-300">
                            Wolf&apos;s Advice
                        </span>
                    </h3>
                    <p className="text-sm text-gray-400 mt-1">{detected}</p>
                </div>
            </div>

            {/* Message */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-black/30 rounded-xl p-4 mb-5 border border-orange-500/20"
            >
                <p className="text-white text-sm leading-relaxed" dir="rtl">
                    {message_ar}
                </p>
                <p className="text-gray-400 text-xs mt-3">{message_en}</p>
            </motion.div>

            {/* Alternatives */}
            {alternatives.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-3 text-sm text-gray-300">
                        <Lightbulb className="w-4 h-4 text-yellow-400" />
                        <span>Smart Alternatives:</span>
                    </div>
                    <div className="space-y-2">
                        {alternatives.map((alt, idx) => (
                            <motion.button
                                key={idx}
                                initial={{ x: -20, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ delay: 0.2 + idx * 0.1 }}
                                whileHover={{ scale: 1.02, x: 5 }}
                                whileTap={{ scale: 0.98 }}
                                className="w-full bg-white/10 hover:bg-white/20 border border-white/20 hover:border-orange-500/50 rounded-xl p-4 text-left transition-all group"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="bg-orange-500/20 p-2 rounded-lg text-orange-400 group-hover:bg-orange-500/30 transition-colors">
                                            {getActionIcon(alt.action)}
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-white" dir="rtl">
                                                {alt.label_ar}
                                            </p>
                                            <p className="text-xs text-gray-500">{alt.label_en}</p>
                                        </div>
                                    </div>
                                    <ArrowRight className="w-5 h-5 text-gray-500 group-hover:text-orange-400 group-hover:translate-x-1 transition-all" />
                                </div>
                            </motion.button>
                        ))}
                    </div>
                </div>
            )}

            {/* Footer */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="mt-5 pt-4 border-t border-white/10 text-center"
            >
                <p className="text-xs text-gray-500">
                    🐺 The Wolf knows the market. These alternatives match your real budget.
                </p>
            </motion.div>
        </motion.div>
    );
}
