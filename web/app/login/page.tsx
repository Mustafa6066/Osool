"use client";

import { FormEvent, Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowRight, Loader2, Lock, Mail, ShieldCheck, Sparkles } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const CONTINUITY_KEYS = [
    'login.continuityAdvisor',
    'login.continuityShortlist',
    'login.continuityContext',
];

function LoginContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login: contextLogin, isAuthenticated } = useAuth();
    const { t } = useLanguage();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isAuthenticated) {
            router.replace('/dashboard');
        }
    }, [isAuthenticated, router]);

    const continueTo = searchParams.get('next') || '/dashboard';

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setError(null);

        // Client-side validation
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
            setError(t('login.errorInvalidEmail'));
            return;
        }
        if (!password) {
            setError(t('login.errorNoPassword'));
            return;
        }

        setIsLoading(true);

        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch(`${API_URL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }

            localStorage.setItem('access_token', data.access_token);
            if (data.refresh_token) {
                localStorage.setItem('refresh_token', data.refresh_token);
            }
            localStorage.setItem('user_id', data.user_id);
            contextLogin(data.access_token, data.refresh_token, data.full_name || data.display_name);
            router.push(continueTo);
        } catch (loginError: unknown) {
            setError(loginError instanceof Error ? loginError.message : 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl gap-8 px-4 py-8 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:py-14">
            <section className="hidden rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 sm:p-10 lg:block">
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    {t('login.badge')}
                </div>
                <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">{t('login.title')}</h1>
                <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                    {t('login.subtitle')}
                </p>

                <div className="mt-8 space-y-3">
                    {CONTINUITY_KEYS.map((key) => (
                        <div key={key} className="flex items-start gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                            <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                <Sparkles className="h-4 w-4" />
                            </div>
                            <div className="text-sm leading-6 text-[var(--color-text-primary)]">{t(key)}</div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_32px_80px_rgba(0,0,0,0.05)] sm:p-10">
                <div className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('auth.welcomeBack')}</div>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight">{t('login.formSubtitle')}</h2>

                {error && (
                    <div className="mt-6 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
                        {error}
                    </div>
                )}

                <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
                    <label className="block">
                        <span className="mb-1.5 block text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.emailAddress')}</span>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder={t('login.emailPlaceholder')}
                                className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] py-3 pl-10 pr-4 text-[var(--color-text-primary)] outline-none transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                            />
                        </div>
                    </label>

                    <label className="block">
                        <span className="mb-1.5 block text-sm font-medium text-[var(--color-text-secondary)]">{t('auth.password')}</span>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-muted)]" />
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="········"
                                className="w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] py-3 pl-10 pr-4 text-[var(--color-text-primary)] outline-none transition-all focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                            />
                        </div>
                    </label>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
                    >
                        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                        {isLoading ? t('auth.signingIn') : t('login.submit')}
                    </button>
                </form>

                <div className="mt-6 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-text-muted)]">
                    {t('auth.newToOsool')}{' '}
                    <Link href="/signup" className="font-semibold text-emerald-600 hover:underline dark:text-emerald-400">
                        {t('login.createAccount')}
                    </Link>
                </div>
            </section>
        </div>
    );
}

export default function LoginPage() {
    return (
        <AppShell>
            <Suspense
                fallback={
                    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center px-4 py-8">
                        <Loader2 className="h-10 w-10 animate-spin text-emerald-500" />
                    </div>
                }
            >
                <LoginContent />
            </Suspense>
        </AppShell>
    );
}
