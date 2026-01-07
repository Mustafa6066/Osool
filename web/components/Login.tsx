"use client";

/**
 * Login Component with Invisible Wallet + Backend JWT Sync
 * 
 * Users log in with Google, Facebook, or Phone Number.
 * We create a blockchain wallet for them automatically.
 * After wallet creation, we sync with the backend for JWT.
 * NEW: Profile completion modal for new users (name + phone)
 */

import { useState, useEffect } from "react";
import { ConnectButton, useActiveAccount, useActiveWallet } from "thirdweb/react";
import { inAppWallet, createWallet } from "thirdweb/wallets";
import { client } from "@/lib/client";
import { chain } from "@/lib/contract";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Configure the wallets to allow
const wallets = [
    inAppWallet({
        auth: {
            options: [
                "google",      // Login with Google -> Wallet created
                "facebook",    // Login with Facebook
                "phone",       // Phone OTP -> Wallet created  
                "email",       // Email code -> Wallet created
            ],
        },
        smartAccount: {
            chain: chain,
            sponsorGas: true, // Osool pays gas fees for users!
        },
    }),
    createWallet("io.metamask"), // Also allow MetaMask for advanced users
];

export default function Login() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showProfileModal, setShowProfileModal] = useState(false);
    const [profileData, setProfileData] = useState({ fullName: "", phoneNumber: "" });
    const account = useActiveAccount();
    const wallet = useActiveWallet();

    // Sync with backend after wallet connection
    const handlePostConnect = async () => {
        if (!account || !wallet) return;

        setIsLoading(true);
        setError(null);

        try {
            // 1. Create message to sign
            const timestamp = Date.now();
            const message = `Login to Osool: ${timestamp}`;

            // 2. Sign the message using wallet account
            const signature = await account.signMessage({ message });

            // 3. Send to backend for JWT
            const response = await fetch(`${API_URL}/api/auth/verify-wallet`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    address: account.address,
                    message: message,
                    signature: signature,
                }),
            });

            if (!response.ok) {
                throw new Error("Backend verification failed");
            }

            const data = await response.json();

            // 4. Store JWT for future API calls
            localStorage.setItem("osool_jwt", data.access_token);
            localStorage.setItem("osool_user_id", data.user_id);

            // 5. Check if new user needs profile completion
            if (data.is_new_user) {
                setShowProfileModal(true);
            } else {
                console.log("✅ Logged in and synced with backend!");
            }

        } catch (err: any) {
            console.error("Login sync error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Handle profile form submission
    const handleProfileSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const jwt = localStorage.getItem("osool_jwt");
            const response = await fetch(`${API_URL}/api/auth/update-profile`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${jwt}`
                },
                body: JSON.stringify({
                    full_name: profileData.fullName,
                    phone_number: profileData.phoneNumber,
                }),
            });

            if (!response.ok) {
                throw new Error("Failed to update profile");
            }

            setShowProfileModal(false);
            console.log("✅ Profile completed and logged in!");

        } catch (err: any) {
            console.error("Profile update error:", err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[400px]">
            <h1 className="text-3xl font-bold mb-4 text-gray-900">
                مرحباً بك في أصول
            </h1>
            <p className="mb-8 text-gray-500 text-center max-w-md">
                سجل دخولك للشراء والبيع بأمان عبر البلوكتشين
            </p>

            {/* This button handles EVERYTHING (Login + Wallet Creation) */}
            <ConnectButton
                client={client}
                wallets={wallets}
                onConnect={handlePostConnect}
                connectButton={{
                    label: isLoading ? "جاري التحقق..." : "تسجيل الدخول",
                    className: "bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg"
                }}
                connectModal={{
                    size: "compact",
                    title: "تسجيل الدخول الآمن",
                    titleIcon: "https://osool.vercel.app/assets/logo.png",
                }}
            />

            {error && (
                <p className="mt-4 text-sm text-red-500">{error}</p>
            )}

            {account && (
                <p className="mt-4 text-xs text-gray-400">
                    محفظتك: {account.address.slice(0, 6)}...{account.address.slice(-4)}
                </p>
            )}

            <p className="mt-4 text-xs text-gray-400">
                مدعوم بتقنية Polygon Blockchain
            </p>

            {/* Profile Completion Modal */}
            {showProfileModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2 text-center">
                            أكمل ملفك الشخصي 👋
                        </h2>
                        <p className="text-gray-500 text-center mb-6">
                            نحتاج بعض المعلومات للتواصل معك
                        </p>

                        <form onSubmit={handleProfileSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    الاسم الكامل
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={profileData.fullName}
                                    onChange={(e) => setProfileData({ ...profileData, fullName: e.target.value })}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                    placeholder="أدخل اسمك الكامل"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    رقم الهاتف
                                </label>
                                <input
                                    type="tel"
                                    required
                                    value={profileData.phoneNumber}
                                    onChange={(e) => setProfileData({ ...profileData, phoneNumber: e.target.value })}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                                    placeholder="+20 1xxxxxxxxx"
                                    dir="ltr"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
                            >
                                {isLoading ? "جاري الحفظ..." : "متابعة ➜"}
                            </button>
                        </form>

                        {error && (
                            <p className="mt-4 text-sm text-red-500 text-center">{error}</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
