"use client";

import { useState } from "react";
import { X, Mail, User as UserIcon, Lock } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
    const [activeTab, setActiveTab] = useState<"login" | "signup">("login");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { login: contextLogin } = useAuth();

    const handleEmailAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            if (activeTab === "signup") {
                // SIGNUP - Simplified for Phase 1
                const params = new URLSearchParams({
                    email,
                    password,
                    full_name: fullName,
                });
                const res = await fetch(`${API_URL}/api/auth/signup?${params.toString()}`, { method: "POST" });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || "Signup failed");
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
            } else {
                // LOGIN
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

                // Store tokens and login
                localStorage.setItem("access_token", data.access_token);
                if (data.refresh_token) {
                    localStorage.setItem("refresh_token", data.refresh_token);
                }
                localStorage.setItem("user_id", data.user_id);
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

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900">
                        {activeTab === "signup" ? "Create your Osool account" : "Welcome back to Osool"}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
                        <X size={24} />
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

                    {/* Email/Password Form */}
                    <form onSubmit={handleEmailAuth} className="space-y-4">
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
                                        required
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
                                    minLength={8}
                                />
                            </div>
                            {activeTab === "signup" && (
                                <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-black hover:bg-gray-800 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-black/20 flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {isLoading ? "Processing..." : (activeTab === "signup" ? "Create Account" : "Sign In")}
                        </button>

                        {activeTab === "signup" && (
                            <p className="text-xs text-gray-500 text-center mt-4">
                                By creating an account, you agree to our Terms of Service and Privacy Policy
                            </p>
                        )}
                    </form>
                </div>
            </div>
        </div>
    );
}
