"use client";

import { useState, useEffect } from "react";
import { ArrowUpDown, Info, TrendingUp, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

interface SwapInterfaceProps {
    propertyId: number;
    propertyTitle: string;
    currentPrice: number;
    poolReserves?: {
        tokenReserve: number;
        egpReserve: number;
    };
}

export default function SwapInterface({
    propertyId,
    propertyTitle,
    currentPrice,
    poolReserves,
}: SwapInterfaceProps) {
    const [tradeType, setTradeType] = useState<"BUY" | "SELL">("BUY");
    const [amountIn, setAmountIn] = useState<string>("");
    const [amountOut, setAmountOut] = useState<string>("");
    const [quote, setQuote] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [slippageTolerance, setSlippageTolerance] = useState<number>(2);

    // Fetch quote when amount changes
    useEffect(() => {
        const fetchQuote = async () => {
            if (!amountIn || parseFloat(amountIn) <= 0) {
                setAmountOut("");
                setQuote(null);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await fetch("/api/liquidity/quote", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        property_id: propertyId,
                        trade_type: tradeType,
                        amount_in: parseFloat(amountIn),
                    }),
                });

                if (!response.ok) {
                    throw new Error("Failed to fetch quote");
                }

                const data = await response.json();
                setQuote(data);
                setAmountOut(data.amount_out.toFixed(2));
            } catch (err: any) {
                setError(err.message);
                setAmountOut("");
            } finally {
                setLoading(false);
            }
        };

        const debounceTimer = setTimeout(fetchQuote, 500);
        return () => clearTimeout(debounceTimer);
    }, [amountIn, tradeType, propertyId]);

    const handleFlip = () => {
        setTradeType(tradeType === "BUY" ? "SELL" : "BUY");
        setAmountIn(amountOut);
        setAmountOut("");
    };

    const handleSwap = async () => {
        if (!quote || !amountIn || !amountOut) {
            setError("Invalid swap parameters");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const minAmountOut = parseFloat(amountOut) * (1 - slippageTolerance / 100);

            const response = await fetch("/api/liquidity/swap", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
                },
                body: JSON.stringify({
                    property_id: propertyId,
                    trade_type: tradeType,
                    amount_in: parseFloat(amountIn),
                    min_amount_out: minAmountOut,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Swap failed");
            }

            const result = await response.json();

            // Show success message
            alert(`Swap successful! TX Hash: ${result.tx_hash}`);

            // Reset form
            setAmountIn("");
            setAmountOut("");
            setQuote(null);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-6 max-w-md mx-auto shadow-2xl"
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">Swap Tokens</h3>
                <p className="text-gray-400 text-sm">{propertyTitle}</p>
            </div>

            {/* From Section */}
            <div className="bg-slate-800/50 border border-white/5 rounded-xl p-4 mb-2">
                <div className="flex justify-between items-center mb-2">
                    <label className="text-gray-400 text-sm">You Pay</label>
                    <span className="text-gray-500 text-xs">
                        Balance: {tradeType === "BUY" ? "10,000" : "5,000"}
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <input
                        type="number"
                        value={amountIn}
                        onChange={(e) => setAmountIn(e.target.value)}
                        placeholder="0.00"
                        className="flex-1 bg-transparent text-white text-2xl font-bold outline-none"
                        min="0"
                        step="0.01"
                    />
                    <button
                        onClick={() =>
                            setAmountIn(tradeType === "BUY" ? "10000" : "5000")
                        }
                        className="bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 text-xs px-3 py-1 rounded-lg transition-colors"
                    >
                        MAX
                    </button>
                </div>
                <div className="text-gray-500 text-sm mt-1">
                    {tradeType === "BUY" ? "EGP" : "Tokens"}
                </div>
            </div>

            {/* Flip Button */}
            <div className="flex justify-center -my-3 z-10 relative">
                <button
                    onClick={handleFlip}
                    className="bg-slate-700 hover:bg-slate-600 border border-white/10 rounded-full p-2 transition-colors shadow-lg"
                >
                    <ArrowUpDown size={20} className="text-white" />
                </button>
            </div>

            {/* To Section */}
            <div className="bg-slate-800/50 border border-white/5 rounded-xl p-4 mb-4">
                <div className="flex justify-between items-center mb-2">
                    <label className="text-gray-400 text-sm">You Receive</label>
                </div>
                <div className="flex items-center gap-3">
                    <input
                        type="text"
                        value={loading ? "..." : amountOut}
                        readOnly
                        placeholder="0.00"
                        className="flex-1 bg-transparent text-white text-2xl font-bold outline-none"
                    />
                </div>
                <div className="text-gray-500 text-sm mt-1">
                    {tradeType === "BUY" ? "Tokens" : "EGP"}
                </div>
            </div>

            {/* Quote Details */}
            {quote && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="bg-slate-800/30 border border-white/5 rounded-xl p-4 mb-4 space-y-2"
                >
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Price</span>
                        <span className="text-white font-mono">
                            {quote.execution_price.toFixed(4)} EGP/token
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400 flex items-center gap-1">
                            Price Impact
                            <Info size={12} />
                        </span>
                        <span
                            className={`font-mono ${
                                quote.price_impact > 5
                                    ? "text-red-400"
                                    : quote.price_impact > 2
                                    ? "text-yellow-400"
                                    : "text-green-400"
                            }`}
                        >
                            {quote.price_impact.toFixed(2)}%
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Slippage Tolerance</span>
                        <div className="flex items-center gap-2">
                            <input
                                type="number"
                                value={slippageTolerance}
                                onChange={(e) =>
                                    setSlippageTolerance(parseFloat(e.target.value))
                                }
                                className="bg-slate-700 text-white text-xs px-2 py-1 rounded w-16 text-right"
                                min="0.1"
                                max="50"
                                step="0.1"
                            />
                            <span className="text-white font-mono">%</span>
                        </div>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Fee (0.3%)</span>
                        <span className="text-white font-mono">
                            {quote.fee_amount.toFixed(2)}{" "}
                            {tradeType === "BUY" ? "EGP" : "Tokens"}
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-400">Minimum Received</span>
                        <span className="text-white font-mono">
                            {(
                                parseFloat(amountOut) *
                                (1 - slippageTolerance / 100)
                            ).toFixed(2)}{" "}
                            {tradeType === "BUY" ? "Tokens" : "EGP"}
                        </span>
                    </div>
                </motion.div>
            )}

            {/* Error Message */}
            {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 flex items-start gap-2">
                    <AlertCircle size={16} className="text-red-400 mt-0.5" />
                    <p className="text-red-400 text-sm">{error}</p>
                </div>
            )}

            {/* Price Impact Warning */}
            {quote && quote.price_impact > 5 && (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mb-4 flex items-start gap-2">
                    <AlertCircle size={16} className="text-yellow-400 mt-0.5" />
                    <p className="text-yellow-400 text-sm">
                        High price impact! Consider reducing your swap amount.
                    </p>
                </div>
            )}

            {/* Swap Button */}
            <button
                onClick={handleSwap}
                disabled={loading || !quote || !amountIn || error !== null}
                className={`w-full py-4 rounded-xl font-bold text-white transition-all ${
                    loading || !quote || !amountIn || error !== null
                        ? "bg-slate-700 cursor-not-allowed"
                        : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 shadow-lg hover:shadow-xl"
                }`}
            >
                {loading ? "Processing..." : "Swap"}
            </button>

            {/* Pool Info */}
            {poolReserves && (
                <div className="mt-4 pt-4 border-t border-white/5">
                    <div className="flex items-center justify-between text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                            <TrendingUp size={12} />
                            Pool Liquidity
                        </span>
                        <span className="text-white font-mono">
                            {poolReserves.egpReserve.toLocaleString()} EGP
                        </span>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
