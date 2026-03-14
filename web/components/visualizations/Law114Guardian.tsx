"use client";

import { motion } from "framer-motion";
import { Shield, Check, Upload, FileText, AlertTriangle, Award } from "lucide-react";
import { useState } from "react";

interface Law114GuardianProps {
    status: "ready" | "scanning" | "scanned";
    capabilities?: string[];
    trust_badges?: string[];
    cta?: {
        text_ar: string;
        text_en: string;
    };
    result?: {
        score: number;
        red_flags: number;
        warnings: number;
        verdict: "SAFE" | "CAUTION" | "DANGER";
        issues?: string[];
    };
}

export default function Law114Guardian({
    status,
    capabilities = [],
    trust_badges = [],
    cta,
    result,
}: Law114GuardianProps) {
    const [isHovered, setIsHovered] = useState(false);

    // Ready state - show CTA to upload contract
    if (status === "ready") {
        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-500/30 rounded-2xl p-6 overflow-hidden"
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                {/* Header */}
                <div className="flex items-center gap-4 mb-5">
                    <motion.div
                        animate={{ rotate: isHovered ? [0, -5, 5, 0] : 0 }}
                        transition={{ duration: 0.5 }}
                        className="bg-blue-500/20 p-3 rounded-xl"
                    >
                        <Shield className="w-8 h-8 text-blue-400" />
                    </motion.div>
                    <div>
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            Law 114 Guardian
                            <span className="text-xs bg-blue-500/30 px-2 py-0.5 rounded-full text-blue-300">
                                AI-Powered
                            </span>
                        </h3>
                        <p className="text-xs text-gray-400">Contract Scanner & Legal Protector</p>
                    </div>
                </div>

                {/* Capabilities */}
                <div className="space-y-2 mb-5">
                    {capabilities.map((cap, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ x: -10, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: idx * 0.1 }}
                            className="flex items-center gap-2 text-sm text-gray-300"
                        >
                            <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
                            <span>{cap}</span>
                        </motion.div>
                    ))}
                </div>

                {/* Trust Badges */}
                {trust_badges.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-5">
                        {trust_badges.map((badge, idx) => (
                            <span
                                key={idx}
                                className="text-xs bg-white/5 border border-white/10 px-2 py-1 rounded-full text-gray-400"
                            >
                                {badge}
                            </span>
                        ))}
                    </div>
                )}

                {/* Upload CTA */}
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors"
                >
                    <Upload className="w-5 h-5" />
                    <span dir="rtl">{cta?.text_ar || "ارفع العقد وأنا أفحصه"}</span>
                </motion.button>

                <p className="text-xs text-center text-gray-500 mt-3">
                    Based on Egyptian Civil Code & Law 114/1946
                </p>
            </motion.div>
        );
    }

    // Scanning state
    if (status === "scanning") {
        return (
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border border-blue-500/30 rounded-2xl p-6"
            >
                <div className="flex flex-col items-center justify-center py-8">
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="mb-4"
                    >
                        <FileText className="w-12 h-12 text-blue-400" />
                    </motion.div>
                    <h3 className="text-lg font-semibold text-white mb-2">Scanning Contract...</h3>
                    <p className="text-sm text-gray-400">Analyzing clauses against Egyptian law</p>
                    <div className="w-full max-w-xs mt-4">
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: "0%" }}
                                animate={{ width: "100%" }}
                                transition={{ duration: 3, ease: "easeInOut" }}
                                className="h-full bg-blue-500"
                            />
                        </div>
                    </div>
                </div>
            </motion.div>
        );
    }

    // Scanned state - show results
    if (status === "scanned" && result) {
        const getVerdictConfig = () => {
            switch (result.verdict) {
                case "SAFE":
                    return {
                        color: "green",
                        icon: <Check className="w-6 h-6" />,
                        label: "Contract is Safe",
                        labelAr: "العقد آمن",
                    };
                case "CAUTION":
                    return {
                        color: "yellow",
                        icon: <AlertTriangle className="w-6 h-6" />,
                        label: "Review Recommended",
                        labelAr: "يحتاج مراجعة",
                    };
                case "DANGER":
                    return {
                        color: "red",
                        icon: <AlertTriangle className="w-6 h-6" />,
                        label: "Issues Found",
                        labelAr: "فيه مشاكل",
                    };
                default:
                    return {
                        color: "gray",
                        icon: <FileText className="w-6 h-6" />,
                        label: "Unknown",
                        labelAr: "غير معروف",
                    };
            }
        };

        const verdictConfig = getVerdictConfig();

        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`bg-gradient-to-br from-${verdictConfig.color}-900/30 to-${verdictConfig.color}-800/20 border border-${verdictConfig.color}-500/30 rounded-2xl p-6`}
            >
                {/* Header with Score */}
                <div className="flex items-center justify-between mb-5">
                    <div className="flex items-center gap-3">
                        <div className={`bg-${verdictConfig.color}-500/20 p-2 rounded-lg text-${verdictConfig.color}-400`}>
                            {verdictConfig.icon}
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white">{verdictConfig.label}</h3>
                            <p className="text-sm text-gray-400" dir="rtl">{verdictConfig.labelAr}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={`text-3xl font-bold text-${verdictConfig.color}-400`}>
                            {result.score}/100
                        </div>
                        <p className="text-xs text-gray-500">Safety Score</p>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-red-400">{result.red_flags}</div>
                        <div className="text-xs text-gray-400">Red Flags</div>
                    </div>
                    <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 text-center">
                        <div className="text-2xl font-bold text-yellow-400">{result.warnings}</div>
                        <div className="text-xs text-gray-400">Warnings</div>
                    </div>
                </div>

                {/* Issues List */}
                {result.issues && result.issues.length > 0 && (
                    <div className="bg-black/20 rounded-lg p-3 mb-4">
                        <h4 className="text-sm font-semibold text-gray-300 mb-2">Issues Found:</h4>
                        <ul className="space-y-1">
                            {result.issues.map((issue, idx) => (
                                <li key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                                    <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                    {issue}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Action Button */}
                <button className="w-full bg-white/10 hover:bg-white/20 text-white font-semibold py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors">
                    <Award className="w-5 h-5" />
                    Request Full Legal Review
                </button>
            </motion.div>
        );
    }

    return null;
}
