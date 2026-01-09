"use client";

import { TrendingUp, Droplet, Activity, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

interface LiquidityPoolCardProps {
    pool: {
        property_id: number;
        property_title: string;
        token_reserve: number;
        egp_reserve: number;
        current_price: number;
        volume_24h: number;
        apy: number;
        total_lp_tokens: number;
    };
    onSelect: (propertyId: number) => void;
}

export default function LiquidityPoolCard({
    pool,
    onSelect,
}: LiquidityPoolCardProps) {
    const formatCurrency = (amount: number) => {
        if (amount >= 1000000) {
            return `${(amount / 1000000).toFixed(2)}M`;
        } else if (amount >= 1000) {
            return `${(amount / 1000).toFixed(1)}K`;
        }
        return amount.toFixed(0);
    };

    const getAPYColor = (apy: number) => {
        if (apy >= 20) return "text-green-400";
        if (apy >= 10) return "text-blue-400";
        return "text-yellow-400";
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            className="bg-gradient-to-br from-slate-900 to-slate-800 border border-white/10 rounded-xl overflow-hidden hover:border-blue-500/50 transition-all group cursor-pointer shadow-lg"
            onClick={() => onSelect(pool.property_id)}
        >
            <div className="p-5">
                {/* Header */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                        <h4 className="text-white font-bold text-lg mb-1 line-clamp-1">
                            {pool.property_title}
                        </h4>
                        <p className="text-gray-400 text-xs">
                            Pool #{pool.property_id}
                        </p>
                    </div>
                    <div className="bg-blue-500/10 border border-blue-500/30 px-3 py-1.5 rounded-full">
                        <span className="text-blue-400 text-sm font-mono font-bold">
                            {pool.current_price.toFixed(2)} EGP
                        </span>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                    {/* Liquidity */}
                    <div className="bg-slate-800/50 border border-white/5 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                            <Droplet size={14} className="text-blue-400" />
                            <span className="text-gray-400 text-xs">Liquidity</span>
                        </div>
                        <p className="text-white font-bold text-lg">
                            {formatCurrency(pool.egp_reserve)} EGP
                        </p>
                    </div>

                    {/* Volume 24h */}
                    <div className="bg-slate-800/50 border border-white/5 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                            <Activity size={14} className="text-purple-400" />
                            <span className="text-gray-400 text-xs">24h Volume</span>
                        </div>
                        <p className="text-white font-bold text-lg">
                            {formatCurrency(pool.volume_24h)} EGP
                        </p>
                    </div>
                </div>

                {/* APY Banner */}
                <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-3 mb-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <TrendingUp size={16} className="text-green-400" />
                            <span className="text-gray-300 text-sm font-medium">
                                APY
                            </span>
                        </div>
                        <span className={`${getAPYColor(pool.apy)} text-2xl font-bold`}>
                            {pool.apy.toFixed(2)}%
                        </span>
                    </div>
                </div>

                {/* Token Reserves Info */}
                <div className="flex items-center justify-between text-xs text-gray-400 mb-4 pb-4 border-b border-white/5">
                    <span>Token Reserve</span>
                    <span className="text-white font-mono">
                        {formatCurrency(pool.token_reserve)} tokens
                    </span>
                </div>

                {/* Action Button */}
                <button
                    className="w-full bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white py-3 rounded-lg transition-all flex items-center justify-center gap-2 group-hover:bg-blue-600 group-hover:text-white font-medium"
                    onClick={(e) => {
                        e.stopPropagation();
                        onSelect(pool.property_id);
                    }}
                >
                    Trade Now
                    <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                </button>
            </div>

            {/* Hot Pool Indicator */}
            {pool.volume_24h > 100000 && (
                <div className="absolute top-3 right-3">
                    <div className="bg-red-500/90 text-white text-xs px-2 py-1 rounded-full font-bold animate-pulse">
                        🔥 HOT
                    </div>
                </div>
            )}
        </motion.div>
    );
}
