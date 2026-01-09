"use client";

import { useState, useEffect } from "react";
import { TrendingUp, Droplet, DollarSign, MinusCircle } from "lucide-react";
import { motion } from "framer-motion";

interface Position {
    pool_id: number;
    property_title: string;
    lp_tokens: number;
    initial_token_amount: number;
    initial_egp_amount: number;
    current_token_amount: number;
    current_egp_amount: number;
    pnl_egp: number;
    pnl_percent: number;
    fees_earned_egp: number;
    share_of_pool: number;
}

export default function UserPositions() {
    const [positions, setPositions] = useState<Position[]>([]);
    const [loading, setLoading] = useState(true);
    const [removingPosition, setRemovingPosition] = useState<number | null>(null);

    useEffect(() => {
        fetchPositions();
    }, []);

    const fetchPositions = async () => {
        setLoading(true);
        try {
            const response = await fetch("/api/liquidity/positions", {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
            });

            if (!response.ok) {
                throw new Error("Failed to fetch positions");
            }

            const data = await response.json();
            setPositions(data);
        } catch (error) {
            console.error("Error fetching positions:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleRemoveLiquidity = async (poolId: number, lpTokens: number) => {
        const confirmed = window.confirm(
            `Are you sure you want to remove all liquidity from this pool?\n\nYou will receive:\n- ${lpTokens.toFixed(2)} LP tokens worth of tokens and EGP`
        );

        if (!confirmed) return;

        setRemovingPosition(poolId);

        try {
            const response = await fetch("/api/liquidity/remove", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    pool_id: poolId,
                    lp_token_amount: lpTokens,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Failed to remove liquidity");
            }

            const result = await response.json();
            alert(
                `Liquidity removed successfully!\n\nReceived:\n- ${result.token_amount_received} tokens\n- ${result.egp_amount_received} EGP\n\nTX Hash: ${result.tx_hash}`
            );

            // Refresh positions
            fetchPositions();
        } catch (error: any) {
            alert(`Error: ${error.message}`);
        } finally {
            setRemovingPosition(null);
        }
    };

    const totalValue = positions.reduce(
        (sum, pos) => sum + pos.current_token_amount * 7.5 + pos.current_egp_amount,
        0
    );

    const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl_egp, 0);

    const totalFeesEarned = positions.reduce(
        (sum, pos) => sum + pos.fees_earned_egp,
        0
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (positions.length === 0) {
        return (
            <div className="bg-slate-800/50 border border-white/10 rounded-xl p-8 text-center">
                <Droplet size={48} className="text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400 text-lg mb-2">No liquidity positions</p>
                <p className="text-gray-500 text-sm">
                    Add liquidity to a pool to start earning fees
                </p>
            </div>
        );
    }

    return (
        <div>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-500/20 p-3 rounded-lg">
                            <DollarSign size={20} className="text-blue-400" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-xs">Total Value</p>
                            <p className="text-white text-xl font-bold">
                                {totalValue.toLocaleString()} EGP
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                        <div
                            className={`p-3 rounded-lg ${
                                totalPnL >= 0
                                    ? "bg-green-500/20"
                                    : "bg-red-500/20"
                            }`}
                        >
                            <TrendingUp
                                size={20}
                                className={
                                    totalPnL >= 0 ? "text-green-400" : "text-red-400"
                                }
                            />
                        </div>
                        <div>
                            <p className="text-gray-400 text-xs">Total PnL</p>
                            <p
                                className={`text-xl font-bold ${
                                    totalPnL >= 0 ? "text-green-400" : "text-red-400"
                                }`}
                            >
                                {totalPnL >= 0 ? "+" : ""}
                                {totalPnL.toLocaleString()} EGP
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-slate-800/50 border border-white/10 rounded-xl p-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-purple-500/20 p-3 rounded-lg">
                            <Droplet size={20} className="text-purple-400" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-xs">Fees Earned</p>
                            <p className="text-white text-xl font-bold">
                                {totalFeesEarned.toLocaleString()} EGP
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Positions List */}
            <div className="space-y-4">
                {positions.map((position, index) => (
                    <motion.div
                        key={position.pool_id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="bg-slate-800/50 border border-white/10 rounded-xl p-5 hover:border-purple-500/50 transition-all"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h4 className="text-white font-bold text-lg">
                                    {position.property_title}
                                </h4>
                                <p className="text-gray-400 text-xs">
                                    Pool #{position.pool_id} • {position.share_of_pool.toFixed(2)}% of pool
                                </p>
                            </div>
                            <button
                                onClick={() =>
                                    handleRemoveLiquidity(
                                        position.pool_id,
                                        position.lp_tokens
                                    )
                                }
                                disabled={removingPosition === position.pool_id}
                                className="bg-red-600/20 hover:bg-red-600 border border-red-500/30 text-red-400 hover:text-white px-4 py-2 rounded-lg transition-all text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <MinusCircle size={16} />
                                {removingPosition === position.pool_id
                                    ? "Removing..."
                                    : "Remove"}
                            </button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-slate-900/50 rounded-lg p-3">
                                <p className="text-gray-400 text-xs mb-1">LP Tokens</p>
                                <p className="text-white font-mono font-bold">
                                    {position.lp_tokens.toFixed(2)}
                                </p>
                            </div>

                            <div className="bg-slate-900/50 rounded-lg p-3">
                                <p className="text-gray-400 text-xs mb-1">Current Value</p>
                                <p className="text-white font-mono font-bold">
                                    {(
                                        position.current_token_amount * 7.5 +
                                        position.current_egp_amount
                                    ).toLocaleString()}{" "}
                                    EGP
                                </p>
                            </div>

                            <div className="bg-slate-900/50 rounded-lg p-3">
                                <p className="text-gray-400 text-xs mb-1">PnL</p>
                                <p
                                    className={`font-mono font-bold ${
                                        position.pnl_egp >= 0
                                            ? "text-green-400"
                                            : "text-red-400"
                                    }`}
                                >
                                    {position.pnl_egp >= 0 ? "+" : ""}
                                    {position.pnl_egp.toFixed(2)} EGP
                                    <span className="text-xs ml-1">
                                        ({position.pnl_percent >= 0 ? "+" : ""}
                                        {position.pnl_percent.toFixed(2)}%)
                                    </span>
                                </p>
                            </div>

                            <div className="bg-slate-900/50 rounded-lg p-3">
                                <p className="text-gray-400 text-xs mb-1">Fees Earned</p>
                                <p className="text-purple-400 font-mono font-bold">
                                    {position.fees_earned_egp.toFixed(2)} EGP
                                </p>
                            </div>
                        </div>

                        {/* Position Details */}
                        <div className="mt-4 pt-4 border-t border-white/5 grid grid-cols-2 gap-4 text-xs">
                            <div>
                                <p className="text-gray-500 mb-1">Initial Deposit</p>
                                <p className="text-gray-300">
                                    {position.initial_token_amount.toFixed(2)} tokens +{" "}
                                    {position.initial_egp_amount.toFixed(2)} EGP
                                </p>
                            </div>
                            <div>
                                <p className="text-gray-500 mb-1">Current Holdings</p>
                                <p className="text-gray-300">
                                    {position.current_token_amount.toFixed(2)} tokens +{" "}
                                    {position.current_egp_amount.toFixed(2)} EGP
                                </p>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
