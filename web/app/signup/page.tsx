'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, Mail, Lock, User, Gift, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { trackSignup } from '@/lib/orchestrator';
import { getAnonymousId } from '@/lib/session';
import OsoolAvatar from '@/components/osool/OsoolAvatar';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Shared input styling — warm well, terracotta focus (Osool palette per DESIGN.md).
const INPUT_CLASS =
    "w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--osool-surface-2)] border border-[var(--osool-border)] text-[var(--osool-text)] placeholder-[var(--osool-muted)] focus:ring-2 focus:ring-[var(--osool-accent-mid)] focus:border-[var(--osool-accent)] outline-none transition-all";

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
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Honor ?next= so a user arriving from the landing-page composer with
    // a pending chat prompt is sent to /chat (with their prompt replayed
    // from localStorage), not the dashboard.
    const continueTo = searchParams.get('next') || '/chat';

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            router.replace(continueTo);
        }
    }, [isAuthenticated, router, continueTo]);

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

            // Notify orchestrator — triggers welcome email sequence + lead scoring
            trackSignup({
                userId: data.user_id,
                email,
                name: fullName,
                source: 'signup',
                anonymousId: getAnonymousId(),
            });

            // Redirect — honor ?next= so the landing-page composer's
            // pending prompt gets replayed in /chat.
            router.push(continueTo);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ width: '100%', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem' }} className="bg-[var(--osool-bg)]">
            <div style={{ width: '100%', maxWidth: '28rem' }} className="bg-[var(--osool-surface)] rounded-3xl shadow-xl border border-[var(--osool-border)] p-8 space-y-6">
                {/* Header — Osool mascot, not a generic icon */}
                <div className="text-center space-y-2">
                    <div className="mx-auto" style={{ width: 64, height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <OsoolAvatar size={56} animated />
                    </div>
                    <h1 className="text-2xl font-bold text-[var(--osool-text)]" style={{ fontFamily: 'var(--osool-font-serif)' }}>{t('auth.joinTitle')}</h1>
                    <p className="text-[var(--osool-muted)] text-sm">
                        {t('auth.joinSubtitle')}
                    </p>
                </div>

                {/* Invitation Status — validating (Nile = verification signal) */}
                {isValidating && (
                    <div className="flex items-center justify-center gap-2 p-3 bg-[var(--osool-nile-soft)] border border-[var(--osool-nile-mid)] rounded-xl">
                        <Loader2 className="w-4 h-4 text-[var(--osool-nile)] animate-spin" />
                        <span className="text-sm text-[var(--osool-nile)]">{t('auth.validating')}</span>
                    </div>
                )}

                {invitationStatus && !isValidating && (
                    <div className={`flex items-center gap-2 p-3 rounded-xl ${invitationStatus.valid
                        ? 'bg-[var(--osool-nile-soft)] border border-[var(--osool-nile-mid)]'
                        : 'bg-[var(--osool-danger-soft)] border border-[var(--osool-danger)]'
                        }`}>
                        {invitationStatus.valid ? (
                            <>
                                <CheckCircle2 className="w-4 h-4 text-[var(--osool-nile)] flex-shrink-0" />
                                <span className="text-sm text-[var(--osool-nile)]">
                                    {t('auth.invitedByLabel')} <strong>{invitationStatus.invited_by}</strong>
                                </span>
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-4 h-4 text-[var(--osool-danger)] flex-shrink-0" />
                                <span className="text-sm text-[var(--osool-danger)]">{invitationStatus.message}</span>
                            </>
                        )}
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="flex items-center gap-2 p-3 bg-[var(--osool-danger-soft)] border border-[var(--osool-danger)] rounded-xl">
                        <AlertCircle className="w-4 h-4 text-[var(--osool-danger)] flex-shrink-0" />
                        <span className="text-sm text-[var(--osool-danger)]">{error}</span>
                    </div>
                )}

                {/* Form */}
                <form className="space-y-4" onSubmit={handleSubmit}>
                    {/* Full Name */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--osool-text-2)]">{t('auth.fullName')}</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--osool-muted)]" />
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="Ahmed Mohamed"
                                className={INPUT_CLASS}
                            />
                        </div>
                    </div>

                    {/* Email */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--osool-text-2)]">{t('auth.emailAddress')}</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--osool-muted)]" />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="ahmed@example.com"
                                className={INPUT_CLASS}
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--osool-text-2)]">{t('auth.password')}</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--osool-muted)]" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className={INPUT_CLASS}
                            />
                        </div>
                        <p className="text-xs text-[var(--osool-muted)]">{t('auth.minChars')}</p>
                    </div>

                    {/* Invitation Code */}
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-[var(--osool-text-2)]">{t('auth.invitationCode')}</label>
                        <div className="relative">
                            <Gift className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--osool-muted)]" />
                            <input
                                type="text"
                                value={invitationCode}
                                onChange={(e) => handleInvitationChange(e.target.value)}
                                placeholder="Enter invitation code"
                                className={INPUT_CLASS}
                            />
                        </div>
                        <p className="text-xs text-[var(--osool-muted)]">
                            {t('auth.needInvitationToSignup')}
                        </p>
                    </div>

                    {/* Submit Button — terracotta keystone CTA */}
                    <button
                        type="submit"
                        disabled={isLoading || (invitationStatus !== null && !invitationStatus.valid)}
                        className="w-full py-3.5 bg-[var(--osool-accent)] hover:bg-[var(--osool-accent-dark)] disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-[var(--osool-accent-mid)] transition-all flex items-center justify-center gap-2"
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
                <div className="pt-4 text-center border-t border-[var(--osool-border)]">
                    <p className="text-sm text-[var(--osool-muted)]">
                        {t('auth.alreadyHaveAccount')}{' '}
                        <Link href="/login" className="text-[var(--osool-accent)] font-semibold hover:underline">
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
            <div style={{ width: '100%', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="bg-[var(--osool-bg)]">
                <Loader2 className="w-8 h-8 text-[var(--osool-accent)] animate-spin" />
            </div>
        }>
            <SignupContent />
        </Suspense>
    );
}
