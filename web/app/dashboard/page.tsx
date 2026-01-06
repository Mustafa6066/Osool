"use client";

/**
 * Osool Dashboard Page
 * 
 * Displays:
 * - User Portfolio (Tokens Owned)
 * - Saved Properties
 * - Quick Access to AI Chat
 */

import { useState, useEffect } from "react";
import { useActiveAccount } from "thirdweb/react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Simple Toast Component
function Toast({ message, type, onClose }: { message: string; type: "success" | "info" | "warning"; onClose: () => void }) {
    useEffect(() => {
        const timer = setTimeout(onClose, 5000);
        return () => clearTimeout(timer);
    }, [onClose]);

    const colors = {
        success: "bg-green-500",
        info: "bg-blue-500",
        warning: "bg-yellow-500"
    };

    return (
        <div className={`fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3 z-50`}>
            <span>{message}</span>
            <button onClick={onClose} className="text-white/80 hover:text-white">✕</button>
        </div>
    );
}

export default function Dashboard() {
    const account = useActiveAccount();
    const [portfolio, setPortfolio] = useState<any[]>([]);
    const [savedProperties, setSavedProperties] = useState<any[]>([]);
    const [toast, setToast] = useState<{ message: string; type: "success" | "info" | "warning" } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Simulated AI alert after 3 seconds
        const alertTimer = setTimeout(() => {
            setToast({ message: "🤖 AI found a high-yield property match!", type: "info" });
        }, 3000);

        // Load saved properties from localStorage
        const saved = localStorage.getItem("osool_saved_properties");
        if (saved) {
            setSavedProperties(JSON.parse(saved));
        }

        // Load portfolio (mock for now, would be from blockchain)
        setPortfolio([
            { id: 1, name: "Solana East Villa", shares: 1500, value: 150000 },
            { id: 2, name: "Palm Hills Apartment", shares: 500, value: 50000 },
        ]);

        setLoading(false);

        return () => clearTimeout(alertTimer);
    }, []);

    if (!account) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-4">Please Connect Your Wallet</h1>
                    <Link href="/" className="text-blue-600 hover:underline">Go to Login</Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                        <p className="text-gray-500">
                            Wallet: {account.address.slice(0, 6)}...{account.address.slice(-4)}
                        </p>
                    </div>
                    <Link
                        href="/chat"
                        className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition"
                    >
                        💬 Chat with AI
                    </Link>
                </div>

                {/* Portfolio Section */}
                <section className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">📊 My Portfolio</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {portfolio.map((item) => (
                            <div key={item.id} className="bg-white p-6 rounded-xl shadow-sm border">
                                <h3 className="font-semibold text-lg">{item.name}</h3>
                                <p className="text-gray-500 text-sm">{item.shares} shares</p>
                                <p className="text-2xl font-bold text-green-600 mt-2">
                                    {item.value.toLocaleString()} EGP
                                </p>
                            </div>
                        ))}
                        {portfolio.length === 0 && (
                            <p className="text-gray-500 col-span-full">No tokens owned yet.</p>
                        )}
                    </div>
                </section>

                {/* Saved Properties Section */}
                <section className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">❤️ Saved Properties</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {savedProperties.map((prop, i) => (
                            <div key={i} className="bg-white p-4 rounded-xl shadow-sm border flex gap-4">
                                <img
                                    src={prop.image || "https://via.placeholder.com/100"}
                                    alt={prop.title}
                                    className="w-24 h-24 object-cover rounded-lg"
                                />
                                <div>
                                    <h3 className="font-semibold">{prop.title}</h3>
                                    <p className="text-gray-500 text-sm">{prop.location}</p>
                                    <p className="text-lg font-bold text-gray-900">
                                        {prop.price?.toLocaleString()} EGP
                                    </p>
                                </div>
                            </div>
                        ))}
                        {savedProperties.length === 0 && (
                            <p className="text-gray-500">No saved properties. Chat with AI to find some!</p>
                        )}
                    </div>
                </section>

                {/* Quick Actions */}
                <section>
                    <h2 className="text-xl font-semibold mb-4">⚡ Quick Actions</h2>
                    <div className="flex gap-4 flex-wrap">
                        <Link href="/chat" className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200">
                            🔍 Search Properties
                        </Link>
                        <button
                            onClick={() => setToast({ message: "Coming soon!", type: "warning" })}
                            className="px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
                        >
                            📄 Contract Analysis
                        </button>
                        <button
                            onClick={() => setToast({ message: "Coming soon!", type: "warning" })}
                            className="px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200"
                        >
                            💰 Withdraw Dividends
                        </button>
                    </div>
                </section>
            </div>
        </div>
    );
}
