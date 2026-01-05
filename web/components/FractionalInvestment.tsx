"use client";

/**
 * FractionalInvestment Component
 * 
 * Premium component for the fractional ownership marketplace.
 * Displays investment opportunities with real-time market data and AI insights.
 */

import { useState } from "react";
import { motion } from "framer-motion";

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

const mockProperties: FractionalProperty[] = [
    {
        id: 1,
        name: "Luxury Apartment - Sodic Eastvale",
        location: "Mostakbal City",
        totalPrice: 3500000,
        minimumInvestment: 175000,
        expectedReturn: 25,
        expectedExitDate: "Mar 2029",
        fundingPercentage: 100,
        aiRiskScore: 15,
        aiValuation: 3650000,
        description: "Premium 3BR apartment in the most sought-after compound in Mostakbal City.",
        image: "/assets/property1.jpg"
    },
    {
        id: 2,
        name: "Modern Townhouse - New Heliopolis",
        location: "New Heliopolis",
        totalPrice: 2800000,
        minimumInvestment: 140000,
        expectedReturn: 22,
        expectedExitDate: "Jun 2029",
        fundingPercentage: 85,
        aiRiskScore: 18,
        aiValuation: 2900000,
        description: "Spacious 4BR townhouse with premium finishes in New Heliopolis.",
        image: "/assets/property2.jpg"
    },
    {
        id: 3,
        name: "Garden Villa - Sheikh Zayed",
        location: "Sheikh Zayed",
        totalPrice: 5200000,
        minimumInvestment: 260000,
        expectedReturn: 28,
        expectedExitDate: "Dec 2028",
        fundingPercentage: 65,
        aiRiskScore: 12,
        aiValuation: 5400000,
        description: "Exclusive villa with private garden in prime Sheikh Zayed location.",
        image: "/assets/property3.jpg"
    }
];

export default function FractionalInvestment() {
    const [selectedProperty, setSelectedProperty] = useState<FractionalProperty | null>(null);
    const [investmentAmount, setInvestmentAmount] = useState(0);

    const calculateOwnership = (investment: number, totalPrice: number) => {
        return ((investment / totalPrice) * 100).toFixed(2);
    };

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
                        <button className="px-8 py-3 border-2 border-gray-400 text-white font-bold rounded-lg hover:border-emerald-400 hover:text-emerald-400 transition-all">
                            Learn More
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

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {mockProperties.map((property, idx) => {
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

                                    {/* Funding Progress */}
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
                                        <p className={`text-sm mt-1 ${property.fundingPercentage === 100 ? 'text-emerald-400' : 'text-orange-400'}`}>
                                            {property.fundingPercentage === 100 ? "✅ Fully Funded" : "🔥 Limited Spots Available"}
                                        </p>
                                    </div>

                                    {/* CTA Button */}
                                    <button
                                        className={`w-full py-3 font-bold rounded-lg transition-all transform hover:scale-[1.02] ${property.fundingPercentage === 100
                                                ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                                                : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-emerald-500/50'
                                            }`}
                                        disabled={property.fundingPercentage === 100}
                                    >
                                        {property.fundingPercentage === 100 ? 'Sold Out' : 'Invest Now'}
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </section>

            {/* Why Osool Section */}
            <section className="max-w-7xl mx-auto px-4 mb-16">
                <h2 className="text-3xl font-bold text-white mb-8 text-center">Why Choose Osool Fractional?</h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                        {
                            title: "AI-Verified Assets",
                            description: "Every property is analyzed by our hybrid AI (XGBoost + GPT-4o) for legal and financial risks.",
                            icon: "🤖",
                            color: "from-emerald-500 to-teal-500"
                        },
                        {
                            title: "Blockchain Transparency",
                            description: "Your ownership is recorded on the Polygon blockchain, immutable and verifiable.",
                            icon: "⛓️",
                            color: "from-cyan-500 to-blue-500"
                        },
                        {
                            title: "FRA Compliant",
                            description: "Fully regulated under FRA Decision 125/2025 for digital real estate investment platforms.",
                            icon: "✅",
                            color: "from-purple-500 to-pink-500"
                        }
                    ].map((feature, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                            className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 hover:border-slate-600 transition-all group"
                        >
                            <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-3xl mb-4 group-hover:scale-110 transition-transform`}>
                                {feature.icon}
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                            <p className="text-gray-400">{feature.description}</p>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* How It Works Section */}
            <section className="max-w-7xl mx-auto px-4 mb-16">
                <h2 className="text-3xl font-bold text-white mb-8 text-center">How It Works</h2>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {[
                        { step: 1, title: "Browse", description: "Explore AI-vetted investment opportunities" },
                        { step: 2, title: "Invest", description: "Pay via EGP (InstaPay, Fawry, Bank)" },
                        { step: 3, title: "Own", description: "Receive blockchain-verified ownership shares" },
                        { step: 4, title: "Earn", description: "Collect returns when property is sold or rented" }
                    ].map((item, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.5, delay: idx * 0.15 }}
                            className="relative"
                        >
                            <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700 text-center h-full">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 flex items-center justify-center text-white font-bold text-xl mx-auto mb-4">
                                    {item.step}
                                </div>
                                <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                                <p className="text-gray-400 text-sm">{item.description}</p>
                            </div>
                            {idx < 3 && (
                                <div className="hidden md:block absolute top-1/2 -right-2 transform -translate-y-1/2 text-emerald-500 text-2xl">
                                    →
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* CTA Section */}
            <section className="max-w-7xl mx-auto px-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8 }}
                    className="bg-gradient-to-r from-emerald-600 to-cyan-600 rounded-2xl p-8 md:p-12 text-center"
                >
                    <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                        Start Your Investment Journey Today
                    </h2>
                    <p className="text-emerald-100 text-lg mb-8 max-w-2xl mx-auto">
                        Join hundreds of smart investors building wealth through AI-verified real estate in Egypt.
                    </p>
                    <button className="px-8 py-4 bg-white text-emerald-600 font-bold rounded-lg hover:shadow-xl transition-all transform hover:scale-105">
                        Create Free Account
                    </button>
                </motion.div>
            </section>
        </div>
    );
}
