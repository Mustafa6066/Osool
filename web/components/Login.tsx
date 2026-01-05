"use client";

/**
 * Login Component with Invisible Wallet
 * 
 * Users log in with Google, Facebook, or Phone Number.
 * We create a blockchain wallet for them automatically.
 * They don't need to know about crypto at all.
 */

import { ConnectButton } from "thirdweb/react";
import { inAppWallet } from "thirdweb/wallets";
import { client } from "@/lib/client";
import { chain } from "@/lib/contract";

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
        // Enable Account Abstraction for gasless transactions
        smartAccount: {
            chain: chain,
            sponsorGas: true, // Osool pays gas fees for users!
        },
    }),
];

export default function Login() {
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
                connectButton={{
                    label: "تسجيل الدخول",
                    className: "bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg"
                }}
                connectModal={{
                    size: "compact",
                    title: "تسجيل الدخول الآمن",
                    titleIcon: "https://osool.vercel.app/assets/logo.png",
                }}
            />

            <p className="mt-4 text-xs text-gray-400">
                مدعوم بتقنية Polygon Blockchain
            </p>
        </div>
    );
}
