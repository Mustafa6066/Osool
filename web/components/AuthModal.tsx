"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { X, Mail, Lock, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import Link from "next/link";

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export default function AuthModal({ isOpen, onClose, onSuccess }: AuthModalProps) {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { login: contextLogin } = useAuth();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);

            const res = await fetch(`${API_URL}/api/auth/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: formData.toString(),
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
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[var(--color-surface)] rounded-2xl w-full max-w-md overflow-hidden shadow-2xl border border-[var(--color-border)] animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-[var(--color-border)]">
                    <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
                        Welcome back to Osool
                    </h2>
                    <button onClick={onClose} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {/* Error Message */}
                    {error && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-500 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            {error}
                        </div>
                    )}

                    {/* Login Form */}
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">Email Address</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3 text-[var(--color-text-muted)]" size={18} />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2.5 bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none"
                                    placeholder="you@example.com"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 text-[var(--color-text-muted)]" size={18} />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2.5 bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-xl text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none"
                                    placeholder="••••••••"
                                    minLength={8}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/25 flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                "Sign In"
                            )}
                        </button>
                    </form>

                    {/* Signup Link */}
                    <div className="mt-6 pt-4 border-t border-[var(--color-border)] text-center">
                        <p className="text-sm text-[var(--color-text-muted)]">
                            New to Osool?{" "}
                            <Link
                                href="/signup"
                                className="text-emerald-500 font-semibold hover:underline"
                                onClick={onClose}
                            >
                                Request an invitation
                            </Link>
                        </p>
                        <p className="text-xs text-[var(--color-text-muted)] mt-2">
                            You need an invitation code from an existing user to sign up
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
