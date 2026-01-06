"use client";

/**
 * Login Component with Invisible Wallet + Backend JWT Sync
 * 
 * Users log in with Google, Facebook, or Phone Number.
 * We create a blockchain wallet for them automatically.
 * After wallet creation, we sync with the backend for JWT.
 */

import { useState } from "react";
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
            // Thirdweb v5: use account.signMessage directly
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

            console.log("✅ Logged in and synced with backend!");

        } catch (err: any) {
            console.error("Login sync error:", err);
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
        </div>
    );
}
