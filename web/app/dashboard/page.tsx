 'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Award, Check, Clock3, Copy, Gift, Heart, Loader2, ShieldCheck, Sparkles, TrendingUp, UserCheck, Users } from 'lucide-react';
import { generateInvitation, getMyInvitations, InvitationResponse, MyInvitationsResponse } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import { useLanguage } from '@/contexts/LanguageContext';
import SmartNav from '@/components/SmartNav';
import InvestorProfileCard from '@/components/InvestorProfileCard';
import { TIER_COLORS } from '@/lib/gamification';

const QUICK_ACTIONS = [
    {
        title: 'Resume advisor',
        description: 'Go back to Osool Advisor and continue your investment analysis.',
        href: '/chat',
        icon: Sparkles,
    },
    {
        title: 'Explore market',
        description: 'Review areas, developers, and projects with intent-first discovery.',
        href: '/explore',
        icon: TrendingUp,
    },
    {
        title: 'Open shortlist',
        description: 'Work through saved properties and compare what deserves action next.',
        href: '/favorites',
        icon: Heart,
    },
];

function getApiDetail(error: unknown, fallback: string): string {
    if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof error.response === 'object' &&
        error.response !== null &&
        'data' in error.response &&
        typeof error.response.data === 'object' &&
        error.response.data !== null &&
        'detail' in error.response &&
        false
    ) {
        return fallback;
    }

    if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof error.response === 'object' &&
        error.response !== null &&
        'data' in error.response &&
        typeof error.response.data === 'object' &&
        error.response.data !== null &&
        'detail' in error.response.data &&
        typeof error.response.data.detail === 'string'
    ) {
        return error.response.data.detail;
    }

    if (error instanceof Error && error.message) {
        return error.message;
    }

    return fallback;
}

export default function DashboardPage() {
    const { user, isAuthenticated, loading } = useAuth();
    const { profile } = useGamification();
    const { language } = useLanguage();
    const router = useRouter();
    const [invitationsData, setInvitationsData] = useState<MyInvitationsResponse | null>(null);
    const [generatedInvite, setGeneratedInvite] = useState<InvitationResponse | null>(null);
    const [isLoadingInvites, setIsLoadingInvites] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [copySuccess, setCopySuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    useEffect(() => {
        if (isAuthenticated) {
            void fetchInvitations();
        }
    }, [isAuthenticated]);

    const fetchInvitations = async () => {
        try {
            const data = await getMyInvitations();
            setInvitationsData(data);
        } catch (fetchError) {
            console.error('Failed to fetch invitations:', fetchError);
        } finally {
            setIsLoadingInvites(false);
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            const data = await generateInvitation();
            setGeneratedInvite(data);
            await fetchInvitations();
        } catch (generationError: unknown) {
            setError(getApiDetail(generationError, 'Failed to generate invitation'));
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopy = async (text: string, id: string) => {
        await navigator.clipboard.writeText(text);
        setCopySuccess(id);
        setTimeout(() => setCopySuccess(null), 2000);
    };

    const formatDate = (dateString: string | null) => {
        if (!dateString) {
            return 'N/A';
        }
        return new Date(dateString).toLocaleDateString(language === 'ar' ? 'ar-EG' : 'en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    if (loading || !isAuthenticated) {
        return (
            <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            </div>
        );
    }

    const usedCount = invitationsData?.invitations.filter((invite) => invite.is_used).length || 0;
    const pendingCount = invitationsData?.invitations.filter((invite) => !invite.is_used).length || 0;
    const remaining = invitationsData?.invitations_remaining ?? 0;
    const recentInvitations = invitationsData?.invitations.slice(0, 5) || [];
    const firstName = user?.full_name?.split(' ')[0] || 'there';

    return (
        <SmartNav>
            <div className="h-full overflow-y-auto">
                <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 pb-24 sm:px-6 md:pb-10 lg:px-8">
                    <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
                        <div className="rounded-[36px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_32px_100px_rgba(0,0,0,0.04)] sm:p-10">
                            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                                <Sparkles className="h-3.5 w-3.5" />
                                Decision cockpit
                            </div>
                            <h1 className="mt-5 text-4xl font-semibold tracking-tight sm:text-5xl">Welcome back, {firstName}. Your next best move is ready.</h1>
                            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)] sm:text-lg">
                                Use this workspace to continue your advisor flow, work through your shortlist, and keep the market signals that matter in one place.
                            </p>

                            <div className="mt-8 grid gap-4 sm:grid-cols-3">
                                {QUICK_ACTIONS.map((action) => {
                                    const Icon = action.icon;
                                    return (
                                        <Link
                                            key={action.title}
                                            href={action.href}
                                            className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-background)] p-5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40"
                                        >
                                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                                <Icon className="h-5 w-5" />
                                            </div>
                                            <div className="mt-4 text-lg font-semibold text-[var(--color-text-primary)]">{action.title}</div>
                                            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{action.description}</div>
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="flex items-center justify-between">
                                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Invites remaining</div>
                                    <Users className="h-4 w-4 text-emerald-500" />
                                </div>
                                <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{remaining === 'unlimited' ? '∞' : remaining}</div>
                                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Keep access controlled while inviting collaborators or friends.</div>
                            </div>
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="flex items-center justify-between">
                                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Used invites</div>
                                    <UserCheck className="h-4 w-4 text-emerald-500" />
                                </div>
                                <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{usedCount}</div>
                                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">People already onboarded through your invitation links.</div>
                            </div>
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="flex items-center justify-between">
                                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Pending invites</div>
                                    <Clock3 className="h-4 w-4 text-emerald-500" />
                                </div>
                                <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{pendingCount}</div>
                                <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Outstanding links that can still be shared.</div>
                            </div>
                        </div>
                    </section>

                    {profile && (
                        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
                            <InvestorProfileCard profile={profile} language={language} />

                            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                                <div className="flex items-center justify-between">
                                    <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Momentum</h2>
                                    <Award className="h-4 w-4 text-emerald-500" />
                                </div>

                                {profile.achievements && profile.achievements.length > 0 ? (
                                    <div className="mt-4 space-y-3">
                                        {profile.achievements.slice(0, 4).map((achievement) => (
                                            <div key={achievement.key} className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                                                <div
                                                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                                                    style={{
                                                        background: `linear-gradient(135deg, ${TIER_COLORS[achievement.tier] || '#CD7F32'}33, ${TIER_COLORS[achievement.tier] || '#CD7F32'}15)`,
                                                        border: `1px solid ${TIER_COLORS[achievement.tier] || '#CD7F32'}44`,
                                                    }}
                                                >
                                                    <Award className="h-4 w-4" style={{ color: TIER_COLORS[achievement.tier] || '#CD7F32' }} />
                                                </div>
                                                <div className="min-w-0 flex-1">
                                                    <div className="truncate text-sm font-semibold text-[var(--color-text-primary)]">
                                                        {language === 'ar' ? (achievement.title_ar || achievement.title_en) : achievement.title_en}
                                                    </div>
                                                    <div className="text-xs uppercase tracking-[0.16em] text-[var(--color-text-muted)]">{achievement.tier} tier</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="mt-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm text-[var(--color-text-secondary)]">
                                        Start analyzing opportunities to build your investor profile and unlock achievements.
                                    </div>
                                )}
                            </div>
                        </section>
                    )}

                    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
                        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Invitation access</div>
                                    <h2 className="mt-2 text-2xl font-semibold tracking-tight">Generate and share invite links without leaving your workspace.</h2>
                                </div>
                                <Gift className="h-5 w-5 text-emerald-500" />
                            </div>

                            <p className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                                Invite collaborators into Osool while keeping access controlled. Existing invitation rules and limits remain unchanged.
                            </p>

                            {error && (
                                <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="mt-6 inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
                            >
                                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Gift className="h-4 w-4" />}
                                {isGenerating ? 'Generating invite...' : 'Generate invitation'}
                            </button>

                            {generatedInvite && (
                                <div className="mt-6 rounded-[28px] border border-emerald-500/20 bg-emerald-500/10 p-5">
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Latest invite</div>
                                    <div className="mt-3 rounded-2xl border border-emerald-500/20 bg-[var(--color-background)] px-4 py-3 text-sm font-medium text-[var(--color-text-primary)]">
                                        {generatedInvite.invitation_link}
                                    </div>
                                    <div className="mt-4 flex flex-wrap gap-3">
                                        <button
                                            onClick={() => handleCopy(generatedInvite.invitation_link, 'latest_link')}
                                            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2 text-sm font-medium"
                                        >
                                            {copySuccess === 'latest_link' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                            {copySuccess === 'latest_link' ? 'Copied' : 'Copy link'}
                                        </button>
                                        <button
                                            onClick={() => handleCopy(generatedInvite.invitation_code, 'latest_code')}
                                            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2 text-sm font-medium"
                                        >
                                            {copySuccess === 'latest_code' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                            {copySuccess === 'latest_code' ? 'Copied code' : 'Copy code'}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Recent invite activity</div>
                                    <h2 className="mt-2 text-2xl font-semibold tracking-tight">Track which links are still available and which were already used.</h2>
                                </div>
                                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                            </div>

                            {isLoadingInvites ? (
                                <div className="mt-6 flex items-center justify-center py-12">
                                    <Loader2 className="h-5 w-5 animate-spin text-emerald-500" />
                                </div>
                            ) : recentInvitations.length > 0 ? (
                                <div className="mt-6 space-y-3">
                                    {recentInvitations.map((invite) => (
                                        <div key={invite.code} className="flex flex-col gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 sm:flex-row sm:items-center sm:justify-between">
                                            <div>
                                                <div className="text-sm font-semibold text-[var(--color-text-primary)]">{invite.code}</div>
                                                <div className="mt-1 text-xs text-[var(--color-text-muted)]">Created {formatDate(invite.created_at)}{invite.used_at ? ` • Used ${formatDate(invite.used_at)}` : ''}</div>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${invite.is_used ? 'bg-slate-500/10 text-slate-600 dark:text-slate-300' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'}`}>
                                                    {invite.is_used ? 'Used' : 'Available'}
                                                </span>
                                                <button
                                                    onClick={() => handleCopy(`${window.location.origin}/signup?invite=${invite.code}`, `invite_${invite.code}`)}
                                                    className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] px-3 py-1.5 text-xs font-medium"
                                                >
                                                    {copySuccess === `invite_${invite.code}` ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                                                    {copySuccess === `invite_${invite.code}` ? 'Copied' : 'Copy'}
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="mt-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-5 text-sm text-[var(--color-text-secondary)]">
                                    No invitations yet. Generate your first invite when you need to onboard someone.
                                </div>
                            )}
                        </div>
                    </section>
                </div>
            </div>
        </SmartNav>
    );
}
