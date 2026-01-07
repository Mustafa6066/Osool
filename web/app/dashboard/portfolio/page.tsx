"use client";

/**
 * My Portfolio Dashboard
 * 
 * Displays the user's active investments, reserved units, and asset performance.
 * Visualizes Funding Percentage and Blockchain Ownership.
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

// Mock data for the Portfolio (In prod, fetch from /api/user/portfolio)
const MOCK_PORTFOLIO = [
    {
        id: 1,
        name: "Luxury Apartment - Sodic Eastvale",
        location: "Mostakbal City",
        investedAmount: 50000,
        sharesOwned: 500, // 100 EGP per share
        currentValuation: 55000, // +10%
        purchaseDate: "2025-11-15",
        status: "CONFIRMED",
        fundingPercentage: 100,
        image: "/assets/property1.jpg"
    },
    {
        id: 3,
        name: "Garden Villa - Sheikh Zayed",
        location: "Sheikh Zayed",
        investedAmount: 25000,
        sharesOwned: 0, // Pending
        currentValuation: 25000,
        purchaseDate: "2026-01-05",
        status: "RESERVED", // Payment pending or processing
        fundingPercentage: 65,
        image: "/assets/property3.jpg"
    }
];

export default function PortfolioPage() {
    const [assets, setAssets] = useState(MOCK_PORTFOLIO);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Simulate API fetch delay
        setTimeout(() => setIsLoading(false), 1000);
    }, []);

    const totalInvested = assets.reduce((acc, asset) => acc + asset.investedAmount, 0);
    const currentValue = assets.reduce((acc, asset) => acc + asset.currentValuation, 0);
    const profit = currentValue - totalInvested;
    const profitPercent = ((profit / totalInvested) * 100).toFixed(1);

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-800">My Portfolio</h1>
                        <p className="text-slate-500">Track your real estate assets on the blockchain</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex gap-6">
                        <div>
                            <p className="text-xs text-slate-500 uppercase">Total Invested</p>
                            <p className="text-xl font-bold text-slate-800">{totalInvested.toLocaleString()} EGP</p>
                        </div>
                        <div className="border-r border-slate-200"></div>
                        <div>
                            <p className="text-xs text-slate-500 uppercase">Current Value</p>
                            <p className="text-xl font-bold text-emerald-600">{currentValue.toLocaleString()} EGP</p>
                        </div>
                        <div className="border-r border-slate-200"></div>
                        <div>
                            <p className="text-xs text-slate-500 uppercase">Total Profit</p>
                            <p className="text-xl font-bold text-emerald-500">+{profit.toLocaleString()} EGP ({profitPercent}%)</p>
                        </div>
                    </div>
                </div>

                {/* Assets Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {assets.map((asset, idx) => (
                        <motion.div
                            key={asset.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5, delay: idx * 0.1 }}
                            className="bg-white rounded-xl overflow-hidden shadow-sm border border-slate-200 hover:shadow-md transition-all"
                        >
                            {/* Asset Header */}
                            <div className="h-40 bg-slate-200 relative">
                                <span className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold text-white ${asset.status === 'CONFIRMED' ? 'bg-emerald-500' : 'bg-orange-400'}`}>
                                    {asset.status}
                                </span>
                            </div>

                            <div className="p-6">
                                <h3 className="text-lg font-bold text-slate-800 mb-1">{asset.name}</h3>
                                <p className="text-slate-500 text-sm mb-4">📍 {asset.location}</p>

                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div className="bg-slate-50 p-3 rounded-lg">
                                        <p className="text-xs text-slate-500">Invested</p>
                                        <p className="font-bold text-slate-700">{asset.investedAmount.toLocaleString()}</p>
                                    </div>
                                    <div className={`bg-slate-50 p-3 rounded-lg ${asset.currentValuation > asset.investedAmount ? 'bg-emerald-50' : ''}`}>
                                        <p className="text-xs text-slate-500">Value</p>
                                        <p className={`font-bold ${asset.currentValuation > asset.investedAmount ? 'text-emerald-600' : 'text-slate-700'}`}>
                                            {asset.currentValuation.toLocaleString()}
                                        </p>
                                    </div>
                                </div>

                                {/* Blockchain status */}
                                {asset.status === 'CONFIRMED' && (
                                    <div className="mb-4">
                                        <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
                                            <span>Ownership Tokens</span>
                                            <span>{asset.sharesOwned} Shares</span>
                                        </div>
                                        <div className="text-xs font-mono bg-slate-100 p-2 rounded text-slate-500 truncate">
                                            0x71C...{asset.id}F9a (Polygon)
                                        </div>
                                    </div>
                                )}

                                {/* Funding Progress (for Reserved items) */}
                                {asset.status === 'RESERVED' && (
                                    <div className="mb-4">
                                        <div className="flex justify-between text-xs mb-1">
                                            <span className="text-slate-500">Funding Round</span>
                                            <span className="text-emerald-600 font-bold">{asset.fundingPercentage}%</span>
                                        </div>
                                        <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                                            <div
                                                className="bg-emerald-500 h-1.5 rounded-full"
                                                style={{ width: `${asset.fundingPercentage}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                )}

                                <button className="w-full py-2 border border-slate-300 rounded-lg text-slate-600 font-medium hover:bg-slate-50 transition-colors">
                                    View Details
                                </button>
                            </div>
                        </motion.div>
                    ))}

                    {/* Add New Investment Card */}
                    <div className="border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center p-8 text-slate-400 hover:border-emerald-400 hover:text-emerald-500 transition-all cursor-pointer bg-slate-50/50">
                        <div className="text-4xl mb-2">+</div>
                        <p className="font-bold">Invest in New Asset</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
