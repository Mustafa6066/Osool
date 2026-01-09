"use client";

import { useState, useEffect } from "react";
import { Plus, Info, TrendingUp, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

interface AddLiquidityModalProps {
    propertyId: number;
    propertyTitle: string;
    currentPrice: number;
    poolReserves: {
        tokenReserve: number;
        egpReserve: number;
    };
    onClose: () => void;
}

export default function AddLiquidityModal({
    propertyId,
    propertyTitle,
    currentPrice,
    poolReserves,
    onClose,
}: AddLiquidityModalProps) {
    const [tokenAmount, setTokenAmount] = useState<string>("");
    const [egpAmount, setEgpAmount] = useState<string>("");
    const [lpTokensToReceive, setLpTokensToReceive] = useState<number>(0);
    const [estimatedAPY, setEstimatedAPY] = useState<number>(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Auto-calculate the other amount to maintain pool ratio
    useEffect(() => {
        if (!tokenAmount || parseFloat(tokenAmount) <= 0) {
            setEgpAmount("");
            setLpTokensToReceive(0);
            return;
        }

        const tokens = parseFloat(tokenAmount);
        const ratio = poolReserves.egpReserve / poolReserves.tokenReserve;
        const calculatedEGP = tokens * ratio;
        setEgpAmount(calculatedEGP.toFixed(2));

        // Estimate LP tokens (simplified: sqrt(tokenAmount * egpAmount))
        const estimatedLP = Math.sqrt(tokens * calculatedEGP);
        setLpTokensToReceive(estimatedLP);

        // Estimate APY (placeholder - should come from backend)
        setEstimatedAPY(12.5);
    }, [tokenAmount, poolReserves]);

    const handleAddLiquidity = async () => {
        if (!tokenAmount || !egpAmount) {
            setError("Please enter valid amounts");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/api/liquidity/add", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    property_id: propertyId,
                    token_amount: parseFloat(tokenAmount),
                    egp_amount: parseFloat(egpAmount),
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Failed to add liquidity");
            }

            const result = await response.json();

            // Show success message
            alert(
                `Liquidity added successfully! TX Hash: ${result.tx_hash}\nLP Tokens received: ${result.lp_tokens_minted}`
            );

            // Close modal
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const shareOfPool = () => {
        if (!tokenAmount || parseFloat(tokenAmount) <= 0) return 0;

        const tokens = parseFloat(tokenAmount);
        const totalTokensAfter = poolReserves.tokenReserve + tokens;
        return ((tokens / totalTokensAfter) * 100).toFixed(2);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-6 shadow-2xl"
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">
                    Add Liquidity
                </h3>
                <p className="text-gray-400 text-sm">{propertyTitle}</p>
                <p className="text-gray-500 text-xs mt-1">
                    Earn trading fees by providing liquidity
                </p>
            </div>

            {/* Current Pool Info */}
            <div className="bg-slate-800/50 border border-white/5 rounded-xl p-4 mb-6">
                <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Current Price</span>
                    <span className="text-white font-mono">
                        {currentPrice.toFixed(4)} EGP/token
                    </span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Pool Ratio</span>
                    <span className="text-white font-mono">
                        1 Token = {(poolReserves.egpReserve / poolReserves.tokenReserve).toFixed(4)} EGP
                    </span>
                </div>
            </div>

            {/* Token Input */}
            <div className="bg-slate-800/50 border border-white/5 rounded-xl p-4 mb-3">
                <div className="flex justify-between items-center mb-2">
                    <label className="text-gray-400 text-sm">Property Tokens</label>
                    <span className="text-gray-500 text-xs">Balance: 5,000</span>
                </div>
                <div className="flex items-center gap-3">
                    <input
                        type="number"
                        value={tokenAmount}
                        onChange={(e) => setTokenAmount(e.target.value)}
                        placeholder="0.00"
                        className="flex-1 bg-transparent text-white text-2xl font-bold outline-none"
                        min="0"
                        step="0.01"
                    />
                    <button
                        onClick={() => setTokenAmount("5000")}
                        className="bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 text-xs px-3 py-1 rounded-lg transition-colors"
                    >
                        MAX
                    </button>
                </div>
                <div className="text-gray-500 text-sm mt-1">Tokens</div>
            </div>

            {/* Plus Icon */}
            <div className="flex justify-center -my-1 z-10 relative">
                <div className="bg-slate-700 border border-white/10 rounded-full p-2">
                    <Plus size={20} className="text-white" />
                </div>
            </div>

            {/* EGP Input */}
            <div className="bg-slate-800/50 border border-white/5 rounded-xl p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                    <label className="text-gray-400 text-sm">EGP Amount</label>
                    <span className="text-gray-500 text-xs">Balance: 10,000</span>
                </div>
                <div className="flex items-center gap-3">
                    <input
                        type="number"
                        value={egpAmount}
                        readOnly
                        placeholder="0.00"
                        className="flex-1 bg-transparent text-white text-2xl font-bold outline-none"
                    />
                </div>
                <div className="text-gray-500 text-sm mt-1">EGP (Auto-calculated)</div>
            </div>

            {/* Details */}
            {tokenAmount && parseFloat(tokenAmount) > 0 && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="bg-slate-800/30 border border-white/5 rounded-xl p-4 mb-4 space-y-2"
                >
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400 flex items-center gap-1">
                            LP Tokens to Receive
                            <Info size={12} />
                        </span>
                        <span className="text-white font-mono font-bold">
                            {lpTokensToReceive.toFixed(2)}
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Your Share of Pool</span>
                        <span className="text-blue-400 font-mono font-bold">
                            {shareOfPool()}%
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400 flex items-center gap-1">
                            <TrendingUp size={12} />
                            Estimated APY
                        </span>
                        <span className="text-green-400 font-mono font-bold">
                            {estimatedAPY.toFixed(2)}%
                        </span>
                    </div>
                </motion.div>
            )}

            {/* Info Box */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mb-4">
                <div className="flex items-start gap-2">
                    <Info size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                    <div className="text-blue-400 text-xs">
                        <p className="font-medium mb-1">How Liquidity Provision Works:</p>
                        <ul className="list-disc list-inside space-y-1 text-blue-300">
                            <li>Deposit both tokens and EGP in equal value</li>
                            <li>Receive LP tokens representing your share</li>
                            <li>Earn 0.25% of all trading fees proportionally</li>
                            <li>Withdraw anytime by burning LP tokens</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 flex items-start gap-2">
                    <AlertCircle size={16} className="text-red-400 mt-0.5" />
                    <p className="text-red-400 text-sm">{error}</p>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
                <button
                    onClick={onClose}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-3 rounded-xl transition-colors font-medium"
                >
                    Cancel
                </button>
                <button
                    onClick={handleAddLiquidity}
                    disabled={
                        loading ||
                        !tokenAmount ||
                        !egpAmount ||
                        parseFloat(tokenAmount) <= 0
                    }
                    className={`flex-1 py-3 rounded-xl font-bold text-white transition-all ${
                        loading ||
                        !tokenAmount ||
                        !egpAmount ||
                        parseFloat(tokenAmount) <= 0
                            ? "bg-slate-700 cursor-not-allowed"
                            : "bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 shadow-lg hover:shadow-xl"
                    }`}
                >
                    {loading ? "Processing..." : "Add Liquidity"}
                </button>
            </div>
        </motion.div>
    );
}
