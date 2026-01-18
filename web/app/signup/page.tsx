'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, UserPlus, Mail, Lock, User, Gift, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

interface InvitationStatus {
    valid: boolean;
    message: string;
    invited_by?: string;
}

export default function SignupPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login: contextLogin } = useAuth();

    // Form state
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [invitationCode, setInvitationCode] = useState('');

    // UI state
    const [isLoading, setIsLoading] = useState(false);
    const [isValidating, setIsValidating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [invitationStatus, setInvitationStatus] = useState<InvitationStatus | null>(null);

    // Get invitation code from URL on mount
    useEffect(() => {
        const inviteCode = searchParams.get('invite');
        if (inviteCode) {
            setInvitationCode(inviteCode);
            validateInvitation(inviteCode);
        }
    }, [searchParams]);

    // Validate invitation code
    const validateInvitation = async (code: string) => {
        if (!code) {
            setInvitationStatus(null);
            return;
        }

        setIsValidating(true);
        try {
            const res = await fetch(`${API_URL}/api/auth/invitation/validate/${code}`);
            const data = await res.json();
            setInvitationStatus(data);
        } catch (err) {
            setInvitationStatus({
                valid: false,
                message: 'Failed to validate invitation code'
            });
        } finally {
            setIsValidating(false);
        }
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        // Validate inputs
        if (!fullName.trim()) {
            setError('Please enter your full name');
            return;
        }
        if (!email.trim()) {
            setError('Please enter your email');
            return;
        }
        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }
        if (!invitationCode.trim()) {
            setError('Invitation code is required. Please request an invitation from an existing user.');
            return;
        }

        setIsLoading(true);

        try {
            const res = await fetch(`${API_URL}/api/auth/signup-with-invitation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    full_name: fullName,
                    email,
                    password,
                    invitation_code: invitationCode
                })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Signup failed');
            }

            // Store tokens and login
            localStorage.setItem('access_token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
            }
            localStorage.setItem('user_id', data.user_id);
            contextLogin(data.access_token, data.refresh_token);

            // Redirect to chat
            router.push('/chat');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)] px-6 py-12">
            <div className="w-full max-w-md bg-[var(--color-surface)] rounded-3xl shadow-xl border border-[var(--color-border)] p-8 space-y-6">
                {/* Header */}
                <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto">
                        <UserPlus className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Join Osool</h1>
                    <p className="text-[var(--color-text-muted)] text-sm">
                        Create your account to chat with AMR
                    </p>
                </div>

                {/* Invitation Status */}
                {isValidating && (
                    <div className="flex items-center justify-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                        <span className="text-sm text-blue-500">Validating invitation...</span>
                    </div>
                )}

                {invitationStatus && !isValidating && (
                    <div className={`flex items-center gap-2 p-3 rounded-xl ${
                        invitationStatus.valid
                            ? 'bg-emerald-500/10 border border-emerald-500/20'
                            : 'bg-red-500/10 border border-red-500/20'
                    }`}>
                        {invitationStatus.valid ? (
                            <>
                                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                <span className="text-sm text-emerald-500">
                                    Invited by <strong>{invitationStatus.invited_by}</strong>
                                </span>
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                                <span className="text-sm text-red-500">{invitationStatus.message}</span>
                            </>
                        )}
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                        <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                        <span className="text-sm text-red-500">{error}</span>
                    </div>
                )}

                {/* Form */}
                <form className="space-y-4" onSubmit={handleSubmit}>
                    {/* Full Name */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">Full Name</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="Ahmed Mohamed"
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                            />
                        </div>
                    </div>

                    {/* Email */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="ahmed@example.com"
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                            />
                        </div>
                        <p className="text-xs text-[var(--color-text-muted)]">Minimum 8 characters</p>
                    </div>

                    {/* Invitation Code */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">Invitation Code</label>
                        <div className="relative">
                            <Gift className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                            <input
                                type="text"
                                value={invitationCode}
                                onChange={(e) => {
                                    setInvitationCode(e.target.value);
                                    if (e.target.value.length > 10) {
                                        validateInvitation(e.target.value);
                                    }
                                }}
                                placeholder="Enter invitation code"
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                            />
                        </div>
                        <p className="text-xs text-[var(--color-text-muted)]">
                            You need an invitation from an existing user to sign up
                        </p>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={isLoading || (invitationStatus !== null && !invitationStatus.valid)}
                        className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition-all flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Creating account...
                            </>
                        ) : (
                            <>
                                Create Account
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </form>

                {/* Footer */}
                <div className="pt-4 text-center border-t border-[var(--color-border)]">
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Already have an account?{' '}
                        <Link href="/login" className="text-emerald-500 font-semibold hover:underline">
                            Sign In
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
