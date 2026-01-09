"use client";

import { useState, useEffect } from "react";
import { Search, Filter, TrendingUp, Droplet, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import LiquidityPoolCard from "./LiquidityPoolCard";
import SwapInterface from "./SwapInterface";
import AddLiquidityModal from "./AddLiquidityModal";
import UserPositions from "./UserPositions";

interface Pool {
    property_id: number;
    property_title: string;
    token_reserve: number;
    egp_reserve: number;
    current_price: number;
    volume_24h: number;
    apy: number;
    total_lp_tokens: number;
}

export default function LiquidityMarketplace() {
    const [pools, setPools] = useState<Pool[]>([]);
    const [filteredPools, setFilteredPools] = useState<Pool[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedPool, setSelectedPool] = useState<Pool | null>(null);
    const [showSwapModal, setShowSwapModal] = useState(false);
    const [showAddLiquidityModal, setShowAddLiquidityModal] = useState(false);
    const [showPositions, setShowPositions] = useState(false);
    const [sortBy, setSortBy] = useState<"volume" | "apy" | "liquidity">("volume");

    // Fetch pools on mount
    useEffect(() => {
        fetchPools();
    }, []);

    // Filter and sort pools
    useEffect(() => {
        let filtered = [...pools];

        // Search filter
        if (searchQuery) {
            filtered = filtered.filter((pool) =>
                pool.property_title.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        // Sort
        filtered.sort((a, b) => {
            switch (sortBy) {
                case "volume":
                    return b.volume_24h - a.volume_24h;
                case "apy":
                    return b.apy - a.apy;
                case "liquidity":
                    return b.egp_reserve - a.egp_reserve;
                default:
                    return 0;
            }
        });

        setFilteredPools(filtered);
    }, [pools, searchQuery, sortBy]);

    const fetchPools = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/liquidity/pools");
            if (!response.ok) {
                throw new Error("Failed to fetch pools");
            }
            const data = await response.json();
            setPools(data);
        } catch (error) {
            console.error("Error fetching pools:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSelectPool = (propertyId: number) => {
        const pool = pools.find((p) => p.property_id === propertyId);
        if (pool) {
            setSelectedPool(pool);
            setShowSwapModal(true);
        }
    };

    const handleAddLiquidity = (pool: Pool) => {
        setSelectedPool(pool);
        setShowAddLiquidityModal(true);
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-white p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-8"
                >
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
                                Liquidity Marketplace
                            </h1>
                            <p className="text-gray-400">
                                Trade property tokens instantly with automated market makers
                            </p>
                        </div>
                        <button
                            onClick={() => setShowPositions(!showPositions)}
                            className="bg-purple-600/20 hover:bg-purple-600 border border-purple-500/30 text-purple-400 hover:text-white px-6 py-3 rounded-xl transition-all font-medium"
                        >
                            My Positions
                        </button>
                    </div>

                    {/* Stats Bar */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                            <div className="flex items-center gap-3">
                                <div className="bg-blue-500/20 p-3 rounded-lg">
                                    <Droplet size={24} className="text-blue-400" />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm">Total Liquidity</p>
                                    <p className="text-white text-2xl font-bold">
                                        {pools
                                            .reduce((sum, p) => sum + p.egp_reserve, 0)
                                            .toLocaleString()}{" "}
                                        EGP
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                            <div className="flex items-center gap-3">
                                <div className="bg-purple-500/20 p-3 rounded-lg">
                                    <TrendingUp size={24} className="text-purple-400" />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm">24h Volume</p>
                                    <p className="text-white text-2xl font-bold">
                                        {pools
                                            .reduce((sum, p) => sum + p.volume_24h, 0)
                                            .toLocaleString()}{" "}
                                        EGP
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                            <div className="flex items-center gap-3">
                                <div className="bg-green-500/20 p-3 rounded-lg">
                                    <Filter size={24} className="text-green-400" />
                                </div>
                                <div>
                                    <p className="text-gray-400 text-sm">Active Pools</p>
                                    <p className="text-white text-2xl font-bold">
                                        {pools.length}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Search and Filter Bar */}
                <div className="flex flex-col md:flex-row gap-4 mb-6">
                    {/* Search */}
                    <div className="flex-1 relative">
                        <Search
                            size={20}
                            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                        />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search pools by property name..."
                            className="w-full bg-slate-800/50 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white placeholder-gray-500 focus:border-blue-500/50 focus:outline-none transition-all"
                        />
                    </div>

                    {/* Sort Dropdown */}
                    <select
                        value={sortBy}
                        onChange={(e) =>
                            setSortBy(e.target.value as "volume" | "apy" | "liquidity")
                        }
                        className="bg-slate-800/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-blue-500/50 focus:outline-none transition-all cursor-pointer"
                    >
                        <option value="volume">Sort by Volume</option>
                        <option value="apy">Sort by APY</option>
                        <option value="liquidity">Sort by Liquidity</option>
                    </select>
                </div>

                {/* User Positions (Toggleable) */}
                <AnimatePresence>
                    {showPositions && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mb-6"
                        >
                            <UserPositions />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Pools Grid */}
                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                    </div>
                ) : filteredPools.length === 0 ? (
                    <div className="text-center py-16">
                        <p className="text-gray-400 text-lg mb-4">No pools found</p>
                        <p className="text-gray-500 text-sm">
                            Try adjusting your search criteria
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredPools.map((pool, index) => (
                            <motion.div
                                key={pool.property_id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                            >
                                <LiquidityPoolCard
                                    pool={pool}
                                    onSelect={handleSelectPool}
                                />
                            </motion.div>
                        ))}
                    </div>
                )}

                {/* Swap Modal */}
                <AnimatePresence>
                    {showSwapModal && selectedPool && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                            onClick={() => setShowSwapModal(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                onClick={(e) => e.stopPropagation()}
                                className="relative max-w-lg w-full"
                            >
                                <button
                                    onClick={() => setShowSwapModal(false)}
                                    className="absolute -top-12 right-0 bg-white/10 hover:bg-white/20 rounded-full p-2 transition-colors"
                                >
                                    <X size={24} className="text-white" />
                                </button>
                                <SwapInterface
                                    propertyId={selectedPool.property_id}
                                    propertyTitle={selectedPool.property_title}
                                    currentPrice={selectedPool.current_price}
                                    poolReserves={{
                                        tokenReserve: selectedPool.token_reserve,
                                        egpReserve: selectedPool.egp_reserve,
                                    }}
                                />
                                <button
                                    onClick={() => {
                                        setShowSwapModal(false);
                                        handleAddLiquidity(selectedPool);
                                    }}
                                    className="w-full mt-4 bg-slate-700 hover:bg-slate-600 text-white py-3 rounded-xl transition-colors font-medium"
                                >
                                    Add Liquidity Instead
                                </button>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Add Liquidity Modal */}
                <AnimatePresence>
                    {showAddLiquidityModal && selectedPool && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
                            onClick={() => setShowAddLiquidityModal(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                onClick={(e) => e.stopPropagation()}
                                className="relative max-w-lg w-full"
                            >
                                <button
                                    onClick={() => setShowAddLiquidityModal(false)}
                                    className="absolute -top-12 right-0 bg-white/10 hover:bg-white/20 rounded-full p-2 transition-colors"
                                >
                                    <X size={24} className="text-white" />
                                </button>
                                <AddLiquidityModal
                                    propertyId={selectedPool.property_id}
                                    propertyTitle={selectedPool.property_title}
                                    currentPrice={selectedPool.current_price}
                                    poolReserves={{
                                        tokenReserve: selectedPool.token_reserve,
                                        egpReserve: selectedPool.egp_reserve,
                                    }}
                                    onClose={() => setShowAddLiquidityModal(false)}
                                />
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
