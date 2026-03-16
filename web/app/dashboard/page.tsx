 'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Award, Bed, Check, Clock3, Copy, Gift, Heart, Loader2, MapPin, Maximize, Scale, ShieldCheck, Sparkles, TrendingUp, UserCheck, Users } from 'lucide-react';
import { generateInvitation, getMyInvitations, InvitationResponse, MyInvitationsResponse } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import { useLanguage } from '@/contexts/LanguageContext';
import AppShell from '@/components/nav/AppShell';
import InvestorProfileCard from '@/components/InvestorProfileCard';
import { TIER_COLORS, fetchFavorites, FavoriteProperty } from '@/lib/gamification';

const QUICK_ACTIONS = [
    {
        titleKey: 'dashboard.actionResumeAdvisor',
        descKey: 'dashboard.actionResumeAdvisorDesc',
        href: '/chat',
        icon: Sparkles,
    },
    {
        titleKey: 'dashboard.actionCompareShortlist',
        descKey: 'dashboard.actionCompareShortlistDesc',
        href: '/favorites',
        icon: Scale,
    },
    {
        titleKey: 'dashboard.actionMarketPulse',
        descKey: 'dashboard.actionMarketPulseDesc',
        href: '/explore',
        icon: TrendingUp,
    },
    {
        titleKey: 'dashboard.actionInviteFriend',
        descKey: 'dashboard.actionInviteFriendDesc',
        href: '#invitations',
        icon: Gift,
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
    const { language, t } = useLanguage();
    const router = useRouter();
    const [invitationsData, setInvitationsData] = useState<MyInvitationsResponse | null>(null);
    const [generatedInvite, setGeneratedInvite] = useState<InvitationResponse | null>(null);
    const [isLoadingInvites, setIsLoadingInvites] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [copySuccess, setCopySuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [shortlist, setShortlist] = useState<FavoriteProperty[]>([]);
    const [isLoadingShortlist, setIsLoadingShortlist] = useState(true);

    const [shortlistError, setShortlistError] = useState(false);

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    useEffect(() => {
        if (isAuthenticated) {
            void fetchInvitations();
            void loadShortlist();
        }
    }, [isAuthenticated]);

    const loadShortlist = async () => {
        setShortlistError(false);
        try {
            const data = await fetchFavorites();
            setShortlist(data.favorites?.slice(0, 4) || []);
        } catch {
            console.warn('[Dashboard] Failed to load shortlist');
            setShortlistError(true);
        } finally {
            setIsLoadingShortlist(false);
        }
    };

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

    const formatPrice = (price: number) => {
        if (price >= 1_000_000) return `${(price / 1_000_000).toFixed(1)}M EGP`;
        if (price >= 1_000) return `${(price / 1_000).toFixed(0)}K EGP`;
        return `${price} EGP`;
    };

    return (
        <AppShell>
            <div className="h-full overflow-y-auto">
                <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 pb-10 sm:px-6 lg:px-8">
                    {/* Row 1: Welcome header */}
                    <div>
                        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                            <Sparkles className="h-3.5 w-3.5" />
                            {t('dashboard.badge')}
                        </div>
                        <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">{t('dashboard.welcomeTitle')} {firstName}.</h1>
                        <p className="mt-2 max-w-xl text-base text-[var(--color-text-secondary)]">
                            {t('dashboard.welcomeSubtitle')}
                        </p>
                    </div>

                    {/* Row 2: Bento grid — Profile + Quick Actions */}
                    <section className="grid gap-4 lg:grid-cols-2">
                        {/* Investor Profile Card */}
                        {profile && (
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-0 overflow-hidden">
                                <InvestorProfileCard profile={profile} language={language} />
                            </div>
                        )}

                        {/* Quick Actions */}
                        <div className="grid grid-cols-2 gap-3">
                            {QUICK_ACTIONS.map((action) => {
                                const Icon = action.icon;
                                const isAnchor = action.href.startsWith('#');
                                const Comp = isAnchor ? 'a' : Link;
                                return (
                                    <Comp
                                        key={action.titleKey}
                                        href={action.href}
                                        className="rounded-[22px] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40"
                                    >
                                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                            <Icon className="h-4 w-4" />
                                        </div>
                                        <div className="mt-3 text-sm font-semibold text-[var(--color-text-primary)]">{t(action.titleKey)}</div>
                                        <div className="mt-1 text-xs leading-5 text-[var(--color-text-secondary)]">{t(action.descKey)}</div>
                                    </Comp>
                                );
                            })}
                        </div>
                    </section>

                    {/* Row 3: Bento grid — Shortlist + Market Snapshot */}
                    <section className="grid gap-4 lg:grid-cols-2">
                        {/* My Shortlist */}
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                                    {t('dashboard.shortlistTitle')} ({shortlist.length})
                                </div>
                                <Heart className="h-4 w-4 text-emerald-500" />
                            </div>

                            {isLoadingShortlist ? (
                                <div className="mt-6 flex items-center justify-center py-8">
                                    <Loader2 className="h-5 w-5 animate-spin text-emerald-500" />
                                </div>
                            ) : shortlistError ? (
                                <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/5 p-4 text-center">
                                    <p className="text-sm text-red-500">{t('dashboard.shortlistError')}</p>
                                    <button onClick={() => { setIsLoadingShortlist(true); void loadShortlist(); }} className="mt-2 text-xs font-medium text-red-400 hover:text-red-300 underline">
                                        {t('common.tryAgain')}
                                    </button>
                                </div>
                            ) : shortlist.length > 0 ? (
                                <>
                                    <div className="mt-4 grid grid-cols-2 gap-3">
                                        {shortlist.map((prop) => (
                                            <Link
                                                key={prop.property_id}
                                                href={`/chat?q=Tell me about ${encodeURIComponent(prop.title)}`}
                                                className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 transition-all hover:border-emerald-500/40"
                                            >
                                                <div className="text-sm font-semibold text-[var(--color-text-primary)] truncate">{prop.title}</div>
                                                <div className="mt-1 flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
                                                    <MapPin className="h-3 w-3" />
                                                    <span className="truncate">{prop.location}</span>
                                                </div>
                                                <div className="mt-2 flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
                                                    {prop.bedrooms > 0 && <span className="flex items-center gap-0.5"><Bed className="h-3 w-3" />{prop.bedrooms}</span>}
                                                    {prop.size_sqm > 0 && <span className="flex items-center gap-0.5"><Maximize className="h-3 w-3" />{prop.size_sqm}m²</span>}
                                                </div>
                                                <div className="mt-2 text-sm font-semibold text-emerald-600 dark:text-emerald-400">{formatPrice(prop.price)}</div>
                                            </Link>
                                        ))}
                                    </div>
                                    <Link href="/favorites" className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400">
                                        {t('dashboard.compareAll')} &rarr;
                                    </Link>
                                </>
                            ) : (
                                <div className="mt-4 rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-6 text-center">
                                    <Heart className="mx-auto h-8 w-8 text-[var(--color-text-muted)] opacity-40" />
                                    <p className="mt-3 text-sm font-medium text-[var(--color-text-primary)]">{t('dashboard.emptyShortlistTitle')}</p>
                                    <p className="mt-1 text-xs text-[var(--color-text-secondary)]">{t('dashboard.emptyShortlistDesc')}</p>
                                    <Link href="/chat" className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-600 hover:bg-emerald-500/20 dark:text-emerald-400">
                                        <Sparkles className="h-3.5 w-3.5" />
                                        {t('dashboard.emptyOpenChat')}
                                    </Link>
                                </div>
                            )}
                        </div>

                        {/* Market Snapshot */}
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.marketSnapshotTitle')}</div>
                                <TrendingUp className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-4 space-y-3">
                                <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                    <div className="text-xs text-[var(--color-text-muted)]">{t('dashboard.askTheAdvisor')}</div>
                                    <div className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">{t('dashboard.marketExample1')}</div>
                                </div>
                                <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                    <div className="text-xs text-[var(--color-text-muted)]">{t('dashboard.popularComparison')}</div>
                                    <div className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">{t('dashboard.marketExample2')}</div>
                                </div>
                                <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                    <div className="text-xs text-[var(--color-text-muted)]">{t('dashboard.trendingAnalysis')}</div>
                                    <div className="mt-1 text-sm font-medium text-[var(--color-text-primary)]">{t('dashboard.marketExample3')}</div>
                                </div>
                            </div>
                            <Link href="/chat" className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400">
                                {t('dashboard.askButton')} &rarr;
                            </Link>
                        </div>
                    </section>

                    {/* Row 4: Stats strip */}
                    <section className="grid grid-cols-3 gap-4">
                        <div className="rounded-[22px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.invitesRemaining')}</div>
                                <Users className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{remaining === 'unlimited' ? 'âˆž' : remaining}</div>
                        </div>
                        <div className="rounded-[22px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.usedInvites')}</div>
                                <UserCheck className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{usedCount}</div>
                        </div>
                        <div className="rounded-[22px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.pendingInvites')}</div>
                                <Clock3 className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-3 text-3xl font-semibold text-[var(--color-text-primary)]">{pendingCount}</div>
                        </div>
                    </section>

                    {/* Row 5: Achievements */}
                    {profile && profile.achievements && profile.achievements.length > 0 && (
                        <section className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.recentAchievements')}</h2>
                                <Award className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-4 flex flex-wrap gap-3">
                                {profile.achievements.slice(0, 5).map((achievement) => (
                                    <div key={achievement.key} className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3">
                                        <div
                                            className="flex h-9 w-9 items-center justify-center rounded-xl"
                                            style={{
                                                background: `linear-gradient(135deg, ${TIER_COLORS[achievement.tier] || '#CD7F32'}33, ${TIER_COLORS[achievement.tier] || '#CD7F32'}15)`,
                                                border: `1px solid ${TIER_COLORS[achievement.tier] || '#CD7F32'}44`,
                                            }}
                                        >
                                            <Award className="h-4 w-4" style={{ color: TIER_COLORS[achievement.tier] || '#CD7F32' }} />
                                        </div>
                                        <div className="min-w-0">
                                            <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                                                {language === 'ar' ? (achievement.title_ar || achievement.title_en) : achievement.title_en}
                                            </div>
                                            <div className="text-xs uppercase tracking-[0.16em] text-[var(--color-text-muted)]">{achievement.tier}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Row 6: Invitations */}
                    <section id="invitations" className="grid gap-4 lg:grid-cols-2">
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.invitationAccess')}</div>
                                    <h2 className="mt-2 text-lg font-semibold tracking-tight">{t('dashboard.invitationAccessDesc')}</h2>
                                </div>
                                <Gift className="h-5 w-5 text-emerald-500" />
                            </div>

                            {error && (
                                <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-500">
                                    {error}
                                </div>
                            )}

                            <button
                                onClick={handleGenerate}
                                disabled={isGenerating}
                                className="mt-5 inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
                            >
                                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Gift className="h-4 w-4" />}
                                {isGenerating ? t('dashboard.generating') : t('dashboard.generateInvitation')}
                            </button>

                            {generatedInvite && (
                                <div className="mt-5 rounded-[22px] border border-emerald-500/20 bg-emerald-500/10 p-4">
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">{t('dashboard.latestInvite')}</div>
                                    <div className="mt-2 rounded-xl border border-emerald-500/20 bg-[var(--color-background)] px-3 py-2 text-sm font-medium text-[var(--color-text-primary)] break-all">
                                        {generatedInvite.invitation_link}
                                    </div>
                                    <div className="mt-3 flex flex-wrap gap-2">
                                        <button
                                            onClick={() => handleCopy(generatedInvite.invitation_link, 'latest_link')}
                                            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-1.5 text-xs font-medium"
                                        >
                                            {copySuccess === 'latest_link' ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                                            {copySuccess === 'latest_link' ? t('common.copied') : t('dashboard.copyLink')}
                                        </button>
                                        <button
                                            onClick={() => handleCopy(generatedInvite.invitation_code, 'latest_code')}
                                            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-3 py-1.5 text-xs font-medium"
                                        >
                                            {copySuccess === 'latest_code' ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                                            {copySuccess === 'latest_code' ? t('common.copied') : t('dashboard.copyCode')}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{t('dashboard.recentInvites')}</div>
                                    <h2 className="mt-2 text-lg font-semibold tracking-tight">{t('dashboard.recentInvitesDesc')}</h2>
                                </div>
                                <ShieldCheck className="h-5 w-5 text-emerald-500" />
                            </div>

                            {isLoadingInvites ? (
                                <div className="mt-6 flex items-center justify-center py-8">
                                    <Loader2 className="h-5 w-5 animate-spin text-emerald-500" />
                                </div>
                            ) : recentInvitations.length > 0 ? (
                                <div className="mt-4 space-y-2">
                                    {recentInvitations.map((invite) => (
                                        <div key={invite.code} className="flex flex-col gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 sm:flex-row sm:items-center sm:justify-between">
                                            <div>
                                                <div className="text-sm font-semibold text-[var(--color-text-primary)]">{invite.code}</div>
                                                <div className="mt-0.5 text-xs text-[var(--color-text-muted)]">{t('dashboard.created')} {formatDate(invite.created_at)}{invite.used_at ? ` Â· ${t('dashboard.used')} ${formatDate(invite.used_at)}` : ''}</div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${invite.is_used ? 'bg-slate-500/10 text-slate-600 dark:text-slate-300' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'}`}>
                                                    {invite.is_used ? t('dashboard.used') : t('dashboard.statusAvailable')}
                                                </span>
                                                <button
                                                    onClick={() => handleCopy(`${window.location.origin}/signup?invite=${invite.code}`, `invite_${invite.code}`)}
                                                    className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)] px-2.5 py-1 text-xs font-medium"
                                                >
                                                    {copySuccess === `invite_${invite.code}` ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                                    {copySuccess === `invite_${invite.code}` ? t('common.copied') : t('common.copy')}
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="mt-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm text-[var(--color-text-secondary)]">
                                    {t('dashboard.noInvitationsEmpty')}
                                </div>
                            )}
                        </div>
                    </section>
                </div>
            </div>
        </AppShell>
    );
}
