"use client";

import { useState } from "react";
import { ConnectButton, useActiveAccount, useActiveWallet } from "thirdweb/react";
import { inAppWallet, createWallet } from "thirdweb/wallets";
import { client } from "@/lib/client";
import { chain } from "@/lib/contract";
import { X, Mail, Wallet, User as UserIcon, Lock } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
    const [activeTab, setActiveTab] = useState<"wallet" | "login" | "signup" | "otp">("wallet");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [phoneNumber, setPhoneNumber] = useState("");
    const [nationalId, setNationalId] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Phone OTP State
    const [otpCode, setOtpCode] = useState("");
    const [otpSent, setOtpSent] = useState(false);
    const [otpUserId, setOtpUserId] = useState<number | null>(null);

    // Linking State
    const [linkPrompt, setLinkPrompt] = useState(false);
    const [walletAuthData, setWalletAuthData] = useState<{ address: string, message: string, signature: string } | null>(null);

    const account = useActiveAccount();
    const wallet = useActiveWallet();

    // Phase 2: Auth context integration
    const { login: contextLogin } = useAuth();

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
                // Phase 2: Standardized token naming (matches backend)
                localStorage.setItem("access_token", data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem("refresh_token", data.refresh_token);
                }
                localStorage.setItem("user_id", data.user_id);
                // Phase 2: Update auth context
                contextLogin(data.access_token, data.refresh_token);
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
                // SIGNUP - KYC Compliant
                const params = new URLSearchParams({
                    email,
                    password,
                    full_name: fullName,
                    phone_number: phoneNumber,
                    national_id: nationalId
                });
                const res = await fetch(`${API_URL}/api/auth/signup?${params.toString()}`, { method: "POST" });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Signup failed");
                }

                const data = await res.json();

                // Backend sends OTP immediately after signup
                if (data.status === "otp_sent") {
                    setOtpUserId(data.user_id);
                    setOtpSent(true);
                    setActiveTab("otp");

                    // Show dev OTP if in development
                    if (data.dev_otp) {
                        setError(`Development Mode: Your OTP is ${data.dev_otp}`);
                    } else {
                        setError(`OTP sent to ${phoneNumber}. Please verify to complete signup.`);
                    }
                    setIsLoading(false);
                    return; // Don't proceed to login yet
                }
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

        // Phase 2: Standardized token naming (matches backend)
        localStorage.setItem("access_token", finalToken);
        localStorage.setItem("user_id", finalUserId);
        // Phase 2: Update auth context
        contextLogin(finalToken);
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
            // Phase 2: Standardized token naming (matches backend)
            localStorage.setItem("access_token", data.access_token);
            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }
            localStorage.setItem("user_id", data.user_id);
            // Phase 2: Update auth context
            contextLogin(data.access_token, data.refresh_token);
            onSuccess();
            onClose();
        } catch (err) {
            setError("Failed to create account");
        } finally {
            setIsLoading(false);
        }
    };

    // -------------------------------------------------------------
    // PHONE OTP LOGIC
    // -------------------------------------------------------------
    const handleSendOTP = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();

        // Validate Egyptian phone format
        if (!phoneNumber.startsWith('+20') || phoneNumber.length !== 13) {
            setError("Please enter a valid Egyptian phone number (+201234567890)");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(`${API_URL}/api/auth/otp/send`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone_number: phoneNumber })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Failed to send OTP");
            }

            const data = await res.json();
            setOtpSent(true);

            // In development, show OTP code
            if (data.dev_code) {
                setError(`Development Mode: Your OTP is ${data.dev_code}`);
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVerifyOTP = async (e: React.FormEvent) => {
        e.preventDefault();

        if (otpCode.length !== 6) {
            setError("Please enter the 6-digit OTP code");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(`${API_URL}/api/auth/otp/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    phone_number: phoneNumber,
                    otp_code: otpCode
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Invalid OTP code");
            }

            const data = await res.json();

            // Store tokens and login
            localStorage.setItem("access_token", data.access_token);
            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }
            localStorage.setItem("user_id", data.user_id);
            contextLogin(data.access_token, data.refresh_token);

            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // -------------------------------------------------------------
    // GOOGLE OAUTH LOGIC
    // -------------------------------------------------------------
    const handleGoogleSuccess = async (credentialResponse: any) => {
        setIsLoading(true);
        setError(null);

        try {
            const res = await fetch(`${API_URL}/api/auth/google`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_token: credentialResponse.credential })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Google authentication failed");
            }

            const data = await res.json();

            // Store tokens and login
            localStorage.setItem("access_token", data.access_token);
            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }
            localStorage.setItem("user_id", data.user_id);
            contextLogin(data.access_token, data.refresh_token);

            onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.message);
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
                                onClick={() => { setActiveTab("wallet"); setOtpSent(false); }}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "wallet"
                                    ? "bg-white text-green-700 shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                                    }`}
                            >
                                <Wallet size={18} />
                                Wallet
                            </button>
                            <button
                                onClick={() => { setActiveTab("login"); setOtpSent(false); }}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "login" || activeTab === "signup"
                                    ? "bg-white text-green-700 shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                                    }`}
                            >
                                <Mail size={18} />
                                Email
                            </button>
                            <button
                                onClick={() => { setActiveTab("otp"); setOtpSent(false); }}
                                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === "otp"
                                    ? "bg-white text-green-700 shadow-sm ring-1 ring-black/5"
                                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                                    }`}
                            >
                                <Lock size={18} />
                                Phone
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

                                    {/* Google OAuth Button - Only show for login */}
                                    {activeTab === "login" && (
                                        <>
                                            <div className="space-y-3">
                                                {/* Google Sign-In Button Placeholder */}
                                                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-center">
                                                    <p className="text-sm text-gray-600">
                                                        <strong>Google OAuth Integration:</strong> Install <code className="bg-gray-200 px-2 py-1 rounded text-xs">@react-oauth/google</code> and wrap app with GoogleOAuthProvider
                                                    </p>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Backend ready at <code>/api/auth/google</code>
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Divider */}
                                            <div className="flex items-center my-4">
                                                <div className="flex-1 border-t border-gray-300"></div>
                                                <span className="px-4 text-gray-500 text-sm">or continue with email</span>
                                                <div className="flex-1 border-t border-gray-300"></div>
                                            </div>
                                        </>
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
                                        <>
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
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                                                <div className="relative">
                                                    <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
                                                    <input
                                                        type="tel"
                                                        required={activeTab === "signup"}
                                                        pattern="\+20[0-9]{10}"
                                                        value={phoneNumber}
                                                        onChange={(e) => setPhoneNumber(e.target.value)}
                                                        className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                        placeholder="+201234567890"
                                                    />
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">Egyptian phone number in E.164 format</p>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">National ID</label>
                                                <div className="relative">
                                                    <UserIcon className="absolute left-3 top-3 text-gray-400" size={18} />
                                                    <input
                                                        type="text"
                                                        required={activeTab === "signup"}
                                                        pattern="[0-9]{14}"
                                                        value={nationalId}
                                                        onChange={(e) => setNationalId(e.target.value)}
                                                        className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                        placeholder="14-digit Egyptian ID"
                                                        maxLength={14}
                                                    />
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">Required for KYC compliance (CBE Law 194)</p>
                                            </div>
                                        </>
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

                            {/* Phone OTP Tab */}
                            {activeTab === "otp" && (
                                <div className="space-y-4">
                                    <div className="text-center mb-4">
                                        <div className="p-4 bg-blue-50 rounded-full mb-3 inline-block">
                                            <Lock className="w-8 h-8 text-blue-600" />
                                        </div>
                                        <h3 className="text-lg font-semibold text-gray-900">
                                            {otpSent ? "Verify OTP Code" : "Phone Authentication"}
                                        </h3>
                                        <p className="text-gray-500 text-sm mt-1">
                                            {otpSent ? "Enter the 6-digit code sent to your phone" : "Sign in with your Egyptian phone number"}
                                        </p>
                                    </div>

                                    {!otpSent ? (
                                        // Step 1: Phone Number Input
                                        <form onSubmit={handleSendOTP} className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                                                <div className="relative">
                                                    <Lock className="absolute left-3 top-3 text-gray-400" size={18} />
                                                    <input
                                                        type="tel"
                                                        required
                                                        pattern="\+20[0-9]{10}"
                                                        value={phoneNumber}
                                                        onChange={(e) => setPhoneNumber(e.target.value)}
                                                        className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                                                        placeholder="+201234567890"
                                                    />
                                                </div>
                                                <p className="text-xs text-gray-500 mt-1">Egyptian phone numbers only (E.164 format)</p>
                                            </div>

                                            <button
                                                type="submit"
                                                disabled={isLoading}
                                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                                            >
                                                {isLoading ? "Sending..." : "Send OTP Code"}
                                            </button>

                                            <p className="text-center text-xs text-gray-500">
                                                Rate limited to 3 attempts per hour
                                            </p>
                                        </form>
                                    ) : (
                                        // Step 2: OTP Verification
                                        <form onSubmit={handleVerifyOTP} className="space-y-4">
                                            <div className="p-3 bg-green-50 text-green-700 text-sm rounded-lg mb-2">
                                                SMS sent to {phoneNumber}
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 mb-1">OTP Code</label>
                                                <input
                                                    type="text"
                                                    required
                                                    pattern="[0-9]{6}"
                                                    maxLength={6}
                                                    value={otpCode}
                                                    onChange={(e) => setOtpCode(e.target.value)}
                                                    className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all tracking-widest"
                                                    placeholder="000000"
                                                />
                                                <p className="text-xs text-gray-500 mt-1 text-center">Enter the 6-digit code</p>
                                            </div>

                                            <button
                                                type="submit"
                                                disabled={isLoading || otpCode.length !== 6}
                                                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
                                            >
                                                {isLoading ? "Verifying..." : "Verify & Sign In"}
                                            </button>

                                            <button
                                                type="button"
                                                onClick={() => { setOtpSent(false); setOtpCode(""); setError(null); }}
                                                className="w-full text-sm text-gray-600 hover:text-gray-800 py-2"
                                            >
                                                ← Change Phone Number
                                            </button>
                                        </form>
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
