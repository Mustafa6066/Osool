"use client";

import { useState, useEffect } from "react";
import PriceValuation from "@/components/PriceValuation";
import LegalCheck from "@/components/LegalCheck";
import ChatInterface from "@/components/ChatInterface";
import AuthModal from "@/components/AuthModal";
import { useActiveAccount } from "thirdweb/react";
import { Lock } from "lucide-react";

export default function Home() {
    const [activeTab, setActiveTab] = useState<"valuation" | "legal" | "chat">("chat");
    const [isAuthModalOpen, setAuthModalOpen] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const account = useActiveAccount();

    useEffect(() => {
        // Check for Wallet OR Email (JWT)
        const jwt = localStorage.getItem("osool_jwt");
        if (jwt || account) {
            setIsAuthenticated(true);
        } else {
            setIsAuthenticated(false);
        }
    }, [account]);

    const handleProtectedAction = (tab: "valuation" | "legal" | "chat") => {
        if (isAuthenticated) {
            setActiveTab(tab);
        } else {
            // If trying to access protected tabs
            if (tab === "chat" || tab === "legal") {
                setAuthModalOpen(true);
            } else {
                setActiveTab(tab); // Valuation might be public? But let's gate everything for "Wolf" feel.
                setAuthModalOpen(true);
            }
        }
    };

    return (
        <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
            <AuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setAuthModalOpen(false)}
                onSuccess={() => { setIsAuthenticated(true); setAuthModalOpen(false); }}
            />

            {/* Header */}
            <header className="border-b border-gray-700/50 backdrop-blur-lg sticky top-0 z-40 bg-gray-900/80">
                <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-green-500/20">
                            O
                        </div>
                        <span className="text-2xl font-bold text-white tracking-tight">Osool</span>
                        <span className="text-sm text-gray-400 hidden sm:block border-l border-gray-700 pl-3 ml-3">
                            Real Estate Intelligence
                        </span>
                    </div>

                    <div className="flex items-center gap-4">
                        {isAuthenticated ? (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-900/30 border border-green-500/30 rounded-full">
                                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                <span className="text-green-400 text-xs font-mono font-bold">CONNECTED</span>
                            </div>
                        ) : (
                            <button
                                onClick={() => setAuthModalOpen(true)}
                                className="px-4 py-2 bg-white text-black font-bold rounded-lg hover:bg-gray-100 transition-colors text-sm"
                            >
                                Sign In
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* Hero */}
            <section className="max-w-6xl mx-auto px-4 py-12 text-center">
                <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 tracking-tight">
                    The <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">Wolf of Cairo</span>
                    <br /> Is At Your Service.
                </h1>
                <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed">
                    Artificial Intelligence that scans contracts for scams, calculates real ROI,
                    and secures your investment on the Polygon Blockchain.
                </p>
            </section>

            {/* Tab Navigation */}
            <div className="max-w-2xl mx-auto px-4 relative z-10">
                <div className="flex bg-gray-800/50 rounded-xl p-1 mb-8 backdrop-blur-sm border border-gray-700/50">
                    <button
                        onClick={() => handleProtectedAction("valuation")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "valuation"
                            ? "bg-gradient-to-r from-green-600 to-green-700 text-white shadow-lg"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        Price Valuation
                    </button>
                    <button
                        onClick={() => handleProtectedAction("legal")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "legal"
                            ? "bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        Legal Check
                    </button>
                    <button
                        onClick={() => handleProtectedAction("chat")}
                        className={`flex-1 py-3 rounded-lg font-medium transition-all ${activeTab === "chat"
                            ? "bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg"
                            : "text-gray-400 hover:text-white"
                            }`}
                    >
                        AI Consultant
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="max-w-4xl mx-auto px-4 pb-16 min-h-[400px]">
                {/* 
                   Ideally, we don't even render the component if not auth, 
                   but handleProtectedAction handles the switching. 
                   If user is NOT auth, activeTab stays on default or we force a 'Lock' screen.
                   Since we setAuthModalOpen(true), the modal will cover.
                   But to be strict, let's wrap content in a check or just rely on the modal.
                   Strict Gating:
                */}

                {isAuthenticated ? (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {activeTab === "valuation" && <PriceValuation />}
                        {activeTab === "legal" && <LegalCheck />}
                        {activeTab === "chat" && <ChatInterface />}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center p-12 bg-gray-800/20 border border-gray-700/50 rounded-2xl backdrop-blur-sm text-center">
                        <Lock size={48} className="text-gray-600 mb-4" />
                        <h3 className="text-xl font-bold text-white mb-2">Access Restricted</h3>
                        <p className="text-gray-400 mb-6">Please sign in to access Osool's AI Intelligence Layer.</p>
                        <button
                            onClick={() => setAuthModalOpen(true)}
                            className="px-8 py-3 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-500 hover:to-blue-500 text-white font-bold rounded-xl transition-all shadow-lg shadow-green-900/20"
                        >
                            Unlock Access
                        </button>
                    </div>
                )}
            </div>

            {/* Footer */}
            <footer className="border-t border-gray-700/50 py-8 mt-auto">
                <div className="max-w-6xl mx-auto px-4 text-center text-gray-600 text-sm">
                    <p>Powered by XGBoost + GPT-4o Hybrid AI</p>
                    <p className="mt-2">CBE Law 194 Compliant | Polygon Blockchain</p>
                </div>
            </footer>
        </main>
    );
}
