'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, UserPlus, Mail, Lock, User, Gift, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface InvitationStatus {
    valid: boolean;
    message: string;
    invited_by?: string;
}

function SignupContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login: contextLogin, isAuthenticated } = useAuth();
    const { t, language } = useLanguage();
    const debounceRef = useRef<ReturnType<typeof setTimeout>>();

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, router]);

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
        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
        };
    }, [searchParams]);

    // Validate invitation code (with debounce for manual input)
    const validateInvitation = async (code: string) => {
        if (!code || code.length < 4) {
            setInvitationStatus(null);
            return;
        }

        setIsValidating(true);
        try {
            const res = await fetch(`${API_URL}/api/auth/invitation/validate/${encodeURIComponent(code)}`);
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

    const handleInvitationChange = (code: string) => {
        setInvitationCode(code);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => validateInvitation(code), 500);
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
        if (!email.trim() || !EMAIL_REGEX.test(email)) {
            setError('Please enter a valid email address');
            return;
        }
        if (password.length < 8 || !/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
            setError('Password must be at least 8 characters with 1 uppercase letter and 1 number');
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
            contextLogin(data.access_token, data.refresh_token, data.full_name || data.display_name);

            // Redirect to chat
            router.push('/chat');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ width: '100%', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }} className="bg-[var(--color-background)]">
            <div style={{ width: '100%', maxWidth: '28rem' }} className="bg-[var(--color-surface)] rounded-3xl shadow-xl border border-[var(--color-border)] p-8 space-y-6">
                {/* Header */}
                <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto">
                        <UserPlus className="w-8 h-8 text-emerald-500" />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">{t('auth.joinTitle')}</h1>
                    <p className="text-[var(--color-text-muted)] text-sm">
                        {t('auth.joinSubtitle')}
                    </p>
                </div>

                {/* Invitation Status */}
                {isValidating && (
                    <div className="flex items-center justify-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                        <span className="text-sm text-blue-500">{t('auth.validating')}</span>
                    </div>
                )}

                {invitationStatus && !isValidating && (
                    <div className={`flex items-center gap-2 p-3 rounded-xl ${invitationStatus.valid
                        ? 'bg-emerald-500/10 border border-emerald-500/20'
                        : 'bg-red-500/10 border border-red-500/20'
                        }`}>
                        {invitationStatus.valid ? (
                            <>
                                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                                <span className="text-sm text-emerald-500">
                                    {t('auth.invitedByLabel')} <strong>{invitationStatus.invited_by}</strong>
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
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.fullName')}</label>
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
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.emailAddress')}</label>
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
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.password')}</label>
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
                        <p className="text-xs text-[var(--color-text-muted)]">{t('auth.minChars')}</p>
                    </div>

                    {/* Invitation Code */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.invitationCode')}</label>
                        <div className="relative">
                            <Gift className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-muted)]" />
                            <input
                                type="text"
                                value={invitationCode}
                                onChange={(e) => handleInvitationChange(e.target.value)}
                                placeholder="Enter invitation code"
                                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--color-surface-elevated)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
                            />
                        </div>
                        <p className="text-xs text-[var(--color-text-muted)]">
                            {t('auth.needInvitationToSignup')}
                        </p>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={isLoading || (invitationStatus !== null && !invitationStatus.valid)}
                        className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-emerald-500 hover:from-emerald-600 hover:to-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-500/25 transition-all flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                {t('auth.creating')}
                            </>
                        ) : (
                            <>
                                {t('auth.createAccount')}
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>
                </form>

                {/* Footer */}
                <div className="pt-4 text-center border-t border-[var(--color-border)]">
                    <p className="text-sm text-[var(--color-text-muted)]">
                        {t('auth.alreadyHaveAccount')}{' '}
                        <Link href="/login" className="text-emerald-500 font-semibold hover:underline">
                            {t('nav.signIn')}
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

// Wrap with Suspense for useSearchParams
export default function SignupPage() {
    return (
        <Suspense fallback={
            <div style={{ width: '100%', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="bg-[var(--color-background)]">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            </div>
        }>
            <SignupContent />
        </Suspense>
    );
}
