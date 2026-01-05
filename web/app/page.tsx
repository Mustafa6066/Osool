"use client";

import { useState } from "react";
import PriceValuation from "@/components/PriceValuation";
import LegalCheck from "@/components/LegalCheck";
import ChatInterface from "@/components/ChatInterface";

export default function Home() {
    const [activeTab, setActiveTab] = useState<"valuation" | "legal" | "chat">("chat");

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            {/* Header */}
            <header className="border-b border-gray-700/50 backdrop-blur-lg">
                <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl">
                            O
                        </div>
                        <span className="text-2xl font-bold text-white">Osool</span>
                        <span className="text-sm text-gray-400 hidden sm:block">| Real Estate Intelligence</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-green-400 text-sm">Backend: Online</span>
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    </div>
                </div>
            </header>

            {/* Hero */}
            <section className="max-w-6xl mx-auto px-4 py-16 text-center">
                <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
                    AI-Powered Real Estate
                </h1>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    Smart valuations, legal contract analysis, and blockchain-verified transactions
                    for the Egyptian market.
                </p>
            </section>

            {/* Tab Navigation */}
            <div className="max-w-2xl mx-auto px-4">
                <div className="flex bg-gray-800/50 rounded-xl p-1 mb-8">
                    <button
                        onClick={() => setActiveTab("valuation")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "valuation"
                            ? "bg-gradient-to-r from-green-600 to-green-700 text-white"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        Price Valuation
                    </button>
                    <button
                        onClick={() => setActiveTab("legal")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "legal"
                            ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        Legal Check
                    </button>
                    <button
                        onClick={() => setActiveTab("chat")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "chat"
                            ? "bg-gradient-to-r from-blue-600 to-cyan-600 text-white"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        AI Consultant
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-2xl mx-auto px-4 pb-16">
                {activeTab === "valuation" && <PriceValuation />}
                {activeTab === "legal" && <LegalCheck />}
                {activeTab === "chat" && <ChatInterface />}
            </div>

            {/* Footer */}
            <footer className="border-t border-gray-700/50 py-8">
                <div className="max-w-6xl mx-auto px-4 text-center text-gray-500 text-sm">
                    <p>Powered by XGBoost + GPT-4o Hybrid AI</p>
                    <p className="mt-2">CBE Law 194 Compliant | Polygon Blockchain</p>
                </div>
            </footer>
        </main>
    );
}
