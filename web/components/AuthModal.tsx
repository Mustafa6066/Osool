"use client";

import { useState } from "react";
import { ConnectButton, useActiveAccount, useActiveWallet } from "thirdweb/react";
import { inAppWallet, createWallet } from "thirdweb/wallets";
import { client } from "@/lib/client";
import { chain } from "@/lib/contract";
import { X, Mail, Wallet, User as UserIcon, Lock } from "lucide-react";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
    const [activeTab, setActiveTab] = useState<"wallet" | "login" | "signup">("wallet");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Linking State
    const [linkPrompt, setLinkPrompt] = useState(false);
    const [walletAuthData, setWalletAuthData] = useState<{ address: string, message: string, signature: string } | null>(null);

    const account = useActiveAccount();
    const wallet = useActiveWallet();

    // -------------------------------------------------------------
    // WALLET AUTH LOGIC
    // -------------------------------------------------------------
    const handleWalletSuccess = async () => {
        if (!account) return;
        setIsLoading(true);
        setError(null);
        try {
            const timestamp = Date.now();
            const message = `Login to Osool: ${timestamp}`;
            const signature = await account.signMessage({ message });

            const payload = { address: account.address, message, signature };
            setWalletAuthData(payload);

            const res = await fetch(`${API_URL}/api/auth/verify-wallet`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error("Wallet verification failed");
            const data = await res.json();

            if (data.is_new_user) {
                // Intercept flow to ask for linking
                setLinkPrompt(true);
                // We don't save token yet, we wait for user decision
            } else {
                // Existing user, proceed
                localStorage.setItem("osool_jwt", data.access_token);
                localStorage.setItem("osool_user_id", data.user_id);
                onSuccess();
                onClose();
            }

        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // -------------------------------------------------------------
    // EMAIL AUTH / LINKING LOGIC
    // -------------------------------------------------------------
    const handleEmailAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            if (activeTab === "signup") {
                // SIGNUP
                const params = new URLSearchParams({ email, password, full_name: fullName });
                const res = await fetch(`${API_URL}/api/auth/signup?${params.toString()}`, { method: "POST" });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Signup failed");
                }
                await loginAndLink(); // Proceed to login (and link if needed)
            } else {
                // LOGIN
                await loginAndLink();
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const loginAndLink = async () => {
        // 1. Login to get Email Token
        const formData = new FormData();
        formData.append("username", email);
        formData.append("password", password);

        const res = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Login failed");
        }

        const data = await res.json();
        let finalToken = data.access_token;
        let finalUserId = data.user_id;

        // 2. If Linking is active, link wallet now
        if (linkPrompt && walletAuthData) {
            const linkRes = await fetch(`${API_URL}/api/auth/link-wallet`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${finalToken}`
                },
                body: JSON.stringify(walletAuthData),
            });

            if (!linkRes.ok) {
                const linkErr = await linkRes.json();
                if (linkErr.status === "already_linked") {
                    throw new Error("This wallet is already linked to this account.");
                }
                throw new Error(linkErr.detail || "Linking failed");
            }

            const linkData = await linkRes.json();
            finalToken = linkData.access_token; // Use the enriched token
            finalUserId = linkData.user_id;
        }

        localStorage.setItem("osool_jwt", finalToken);
        localStorage.setItem("osool_user_id", finalUserId);
        onSuccess();
        onClose();
    };

    const handleCreateNewAccount = async () => {
        // User chose NOT to link, just use the wallet account created by verify-wallet
        // We need to re-fetch the token because we didn't save it yet
        if (!walletAuthData) return;

        setIsLoading(true);
        try {
            const res = await fetch(`${API_URL}/api/auth/verify-wallet`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(walletAuthData),
            });
            const data = await res.json();
            localStorage.setItem("osool_jwt", data.access_token);
            localStorage.setItem("osool_user_id", data.user_id);
            onSuccess();
            onClose();
        } catch (err) {
            setError("Failed to create account");
        } finally {
            setIsLoading(false);
        }
    };


    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900">
                        {linkPrompt ? "Link Account?" : "Sign in to Osool"}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* LINK PROMPT UI */}
                {linkPrompt ? (
                    <div className="p-6 text-center space-y-6">
                        <div className="p-4 bg-blue-50 text-blue-800 rounded-xl text-sm">
                            We noticed this wallet is new. Do you have an existing email account you want to link it to?
                        </div>

                        <div className="grid gap-3">
                            <button
                                onClick={() => { setActiveTab("login"); setLinkPrompt(false); /* Keep isLinking state implict via walletAuthData presence */ }}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all"
                            >
                                Yes, Link to Existing Email
                            </button>
                            <button
                                onClick={handleCreateNewAccount}
                                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-bold py-3 rounded-xl transition-all"
                            >
                                No, Create New Account
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Tabs */}
                        <div className="flex p-2 gap-2 bg-gray-50 border-b border-gray-100">
                            <button
                                onClick={() => setActiveTab("wallet")}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "wallet"
                                    ? "bg-white text-green-700 shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                                    }`}
                            >
                                <Wallet size={18} />
                                Web3 Wallet
                            </button>
                            <button
                                onClick={() => setActiveTab("login")}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "login" || activeTab === "signup"
                                    ? "bg-white text-green-700 shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                                    }`}
                            >
                                <Mail size={18} />
                                Email
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6">
                            {/* ERROR MSG */}
                            {error && (
                                <div className="mb-4 p-3 bg-red-50 border border-red-100 rounded-lg text-sm text-red-600 flex items-center gap-2">
                                    ⚠️ {error}
                                </div>
                            )}

                            {/* Wallet Tab */}
                            {activeTab === "wallet" && (
                                <div className="flex flex-col items-center py-4 space-y-4">
                                    <div className="p-4 bg-green-50 rounded-full mb-2">
                                        <Wallet className="w-8 h-8 text-green-600" />
                                    </div>
                                    <h3 className="text-lg font-semibold text-gray-900 text-center">
                                        Connect your Wallet
                                    </h3>
                                    <p className="text-gray-500 text-center text-sm mb-4">
                                        Use MetaMask, Coinbase, or Social Login via Thirdweb.
                                    </p>

                                    <div className="w-full">
                                        <ConnectButton
                                            client={client}
                                            wallets={[
                                                inAppWallet({ auth: { options: ["google", "facebook", "phone"] } }),
                                                createWallet("io.metamask"),
                                            ]}
                                            onConnect={handleWalletSuccess}
                                            connectButton={{
                                                label: isLoading ? "Verifying..." : "Connect Wallet",
                                                className: "!w-full !bg-green-600 !hover:bg-green-700 !py-3 !rounded-xl !font-bold"
                                            }}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Email Tab */}
                            {(activeTab === "login" || activeTab === "signup") && (
                                <form onSubmit={handleEmailAuth} className="space-y-4">
                                    {walletAuthData && (
                                        <div className="p-3 bg-blue-50 text-blue-700 text-xs rounded-lg mb-2">
                                            🔗 Linking Wallet: {walletAuthData.address.slice(0, 6)}...{walletAuthData.address.slice(-4)}
                                        </div>
                                    )}

                                    {/* Toggle Sign In / Sign Up */}
                                    <div className="flex justify-center mb-4">
                                        <span className="text-sm text-gray-500 mr-2">
                                            {activeTab === "signup" ? "Already have an account?" : "New to Osool?"}
                                        </span>
                                        <button
                                            type="button"
                                            onClick={() => setActiveTab(activeTab === "signup" ? "login" : "signup")}
                                            className="text-sm font-bold text-green-600 hover:underline"
                                        >
                                            {activeTab === "signup" ? "Sign In" : "Create Account"}
                                        </button>
                                    </div>

                                    {activeTab === "signup" && (
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                            <div className="relative">
                                                <UserIcon className="absolute left-3 top-3 text-gray-400" size={18} />
                                                <input
                                                    type="text"
                                                    required={activeTab === "signup"}
                                                    value={fullName}
                                                    onChange={(e) => setFullName(e.target.value)}
                                                    className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                    placeholder="John Doe"
                                                />
                                            </div>
                                        </div>
                                    )}

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                                        <div className="relative">
                                            <Mail className="absolute left-3 top-3 text-gray-400" size={18} />
                                            <input
                                                type="email"
                                                required
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                placeholder="you@example.com"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                                        <div className="relative">
                                            <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
                                            <input
                                                type="password"
                                                required
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                placeholder="••••••••"
                                            />
                                        </div>
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={isLoading}
                                        className="w-full bg-black hover:bg-gray-800 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-black/20 flex items-center justify-center gap-2 disabled:opacity-50"
                                    >
                                        {isLoading ? "Processing..." : (activeTab === "signup" ? "Sign Up" : (walletAuthData ? "Link Account" : "Sign In"))}
                                    </button>
                                </form>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
