"use client";

/**
 * FractionalInvestment Component
 * 
 * Premium component for the fractional ownership marketplace.
 * Displays investment opportunities with real-time market data from Backend.
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FractionalProperty {
    id: number;
    name: string;
    location: string;
    totalPrice: number;
    minimumInvestment: number;
    expectedReturn: number;
    expectedExitDate: string;
    fundingPercentage: number;
    aiRiskScore: number;
    aiValuation: number;
    description: string;
    image: string;
}

export default function FractionalInvestment() {
    const [selectedProperty, setSelectedProperty] = useState<FractionalProperty | null>(null);
    const [properties, setProperties] = useState<FractionalProperty[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchProperties = async () => {
            try {
                const response = await fetch(`${API_URL}/api/properties`);
                if (!response.ok) throw new Error("Failed to fetch properties");
                const data = await response.json();
                setProperties(data);
            } catch (err) {
                console.error("Error fetching properties:", err);
                // Fallback to empty or could keep mock for demo if preferred, 
                // but mandate says "Fetch real properties"
                setError("Could not load market data.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchProperties();
    }, []);

    const getRiskColor = (score: number) => {
        if (score < 20) return "text-green-400";
        if (score < 40) return "text-yellow-400";
        return "text-red-400";
    };

    const getRiskBadge = (score: number) => {
        if (score < 20) return { text: "Low Risk", bg: "bg-green-500/20", border: "border-green-500/50" };
        if (score < 40) return { text: "Medium Risk", bg: "bg-yellow-500/20", border: "border-yellow-500/50" };
        return { text: "High Risk", bg: "bg-red-500/20", border: "border-red-500/50" };
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 py-16">
            {/* Hero Section */}
            <section className="max-w-7xl mx-auto px-4 mb-16">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="text-center"
                >
                    <h1 className="text-5xl md:text-7xl font-bold text-white mb-4">
                        Own Real Estate, <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Not Just Listings</span>
                    </h1>
                    <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
                        Invest in verified, AI-analyzed properties with as little as 5%. Transparent ownership on the blockchain.
                    </p>
                    <div className="flex gap-4 justify-center flex-wrap">
                        <button className="px-8 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white font-bold rounded-lg hover:shadow-lg hover:shadow-emerald-500/50 transition-all transform hover:scale-105">
                            Explore Opportunities
                        </button>
                    </div>
                </motion.div>
            </section>

            {/* Stats Section */}
            <section className="max-w-7xl mx-auto px-4 mb-16">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: "Total Invested", value: "12.5M EGP", icon: "💰" },
                        { label: "Properties Funded", value: "8", icon: "🏠" },
                        { label: "Avg. Return", value: "24%", icon: "📈" },
                        { label: "Active Investors", value: "156", icon: "👥" }
                    ].map((stat, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                            className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 rounded-xl p-6 border border-slate-700/50 backdrop-blur-sm text-center"
                        >
                            <div className="text-3xl mb-2">{stat.icon}</div>
                            <p className="text-2xl font-bold text-white">{stat.value}</p>
                            <p className="text-gray-400 text-sm">{stat.label}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* Investment Opportunities Grid */}
            <section className="max-w-7xl mx-auto px-4 mb-16">
                <h2 className="text-3xl font-bold text-white mb-8">Featured Investment Opportunities</h2>

                {isLoading ? (
                    /* Loading Skeleton */
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-slate-800/50 h-[500px] rounded-2xl animate-pulse"></div>
                        ))}
                    </div>
                ) : error ? (
                    <div className="text-center text-red-400 py-8">{error}</div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {properties.map((property, idx) => {
                            const riskBadge = getRiskBadge(property.aiRiskScore);

                            return (
                                <motion.div
                                    key={property.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.5, delay: idx * 0.1 }}
                                    onClick={() => setSelectedProperty(property)}
                                    className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl overflow-hidden hover:shadow-2xl hover:shadow-emerald-500/20 transition-all cursor-pointer border border-slate-700 group"
                                >
                                    {/* Image Placeholder */}
                                    <div className="h-48 bg-gradient-to-br from-emerald-600 to-cyan-600 flex items-center justify-center relative overflow-hidden">
                                        <div className="absolute inset-0 bg-black/30 group-hover:bg-black/20 transition-all" />
                                        <span className="text-white text-lg font-bold z-10 px-4 text-center">{property.name}</span>

                                        {/* AI Verified Badge */}
                                        <div className="absolute top-3 left-3 bg-emerald-500/90 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                                            <span>🤖</span> AI Verified
                                        </div>

                                        {/* Risk Badge */}
                                        <div className={`absolute top-3 right-3 ${riskBadge.bg} ${riskBadge.border} border text-white text-xs font-bold px-3 py-1 rounded-full`}>
                                            {riskBadge.text}
                                        </div>
                                    </div>

                                    {/* Content */}
                                    <div className="p-6">
                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold text-white group-hover:text-emerald-400 transition-colors">{property.name}</h3>
                                                <p className="text-gray-400 text-sm flex items-center gap-1">
                                                    <span>📍</span> {property.location}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Key Metrics */}
                                        <div className="grid grid-cols-2 gap-4 mb-6 py-4 border-y border-slate-700">
                                            <div>
                                                <p className="text-gray-500 text-xs uppercase">Total Price</p>
                                                <p className="text-white font-bold text-lg">{(property.totalPrice / 1000000).toFixed(1)}M EGP</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500 text-xs uppercase">Min Investment</p>
                                                <p className="text-emerald-400 font-bold text-lg">{(property.minimumInvestment / 1000).toFixed(0)}K EGP</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500 text-xs uppercase">Expected Return</p>
                                                <p className="text-cyan-400 font-bold text-lg">{property.expectedReturn}%</p>
                                            </div>
                                            <div>
                                                <p className="text-gray-500 text-xs uppercase">Exit Date</p>
                                                <p className="text-white font-bold text-lg">{property.expectedExitDate}</p>
                                            </div>
                                        </div>

                                        {/* Funding Progress (Mocked/Real mix) */}
                                        <div className="mb-6">
                                            <div className="flex justify-between text-sm mb-2">
                                                <span className="text-gray-400">Funding Progress</span>
                                                <span className="text-emerald-400 font-bold">{property.fundingPercentage}%</span>
                                            </div>
                                            <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                                                <motion.div
                                                    className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-2 rounded-full"
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${property.fundingPercentage}%` }}
                                                    transition={{ duration: 1, delay: idx * 0.2 }}
                                                />
                                            </div>
                                        </div>

                                        {/* AI Insights */}
                                        <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700">
                                            <p className="text-xs text-gray-500 uppercase mb-2 flex items-center gap-1">
                                                <span>🧠</span> AI Valuation Insight
                                            </p>
                                            <p className="text-white font-bold text-lg">
                                                {property.aiValuation.toLocaleString()} EGP
                                            </p>
                                            <p className={`text-sm mt-1 ${property.fundingPercentage >= 100 ? 'text-emerald-400' : 'text-orange-400'}`}>
                                                {property.fundingPercentage >= 100 ? "✅ Fully Funded" : "🔥 Limited Spots Available"}
                                            </p>
                                        </div>

                                        {/* CTA Button */}
                                        <button
                                            className={`w-full py-3 font-bold rounded-lg transition-all transform hover:scale-[1.02] ${property.fundingPercentage >= 100
                                                ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                                                : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-emerald-500/50'
                                                }`}
                                            disabled={property.fundingPercentage >= 100}
                                        >
                                            {property.fundingPercentage >= 100 ? 'Sold Out' : 'Invest Now'}
                                        </button>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                )}
            </section>
        </div>
    );
}
