'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Heart, MapPin, Bed, Maximize, Trash2, Loader2, Building2, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { fetchFavorites, toggleFavorite, FavoriteProperty } from '@/lib/gamification';
import Link from 'next/link';
import SmartNav from '@/components/SmartNav';

export default function FavoritesPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const { t } = useLanguage();
    const router = useRouter();
    const [favorites, setFavorites] = useState<FavoriteProperty[]>([]);
    const [loading, setLoading] = useState(true);
    const [removing, setRemoving] = useState<number | null>(null);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, authLoading, router]);

    useEffect(() => {
        if (isAuthenticated) {
            loadFavorites();
        }
    }, [isAuthenticated]);

    const loadFavorites = async () => {
        try {
            const data = await fetchFavorites();
            setFavorites(data.favorites || []);
        } catch (err) {
            console.warn('[Favorites] Failed to load:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRemove = async (propertyId: number) => {
        if (removing !== null) return; // guard against double-click
        setRemoving(propertyId);
        const previous = favorites; // snapshot for rollback
        setFavorites(prev => prev.filter(f => f.property_id !== propertyId)); // optimistic
        try {
            await toggleFavorite(propertyId);
        } catch (err) {
            console.error('[Favorites] Failed to remove:', err);
            setFavorites(previous); // rollback on failure
        } finally {
            setRemoving(null);
        }
    };

    if (authLoading) return null;

    return (
        <SmartNav>
            <div className="h-full overflow-y-auto">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 pb-24 md:pb-8">
                    <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-start mb-8">
                        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-7">
                            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                                <Heart className="h-3.5 w-3.5" />
                                Saved workspace
                            </div>
                            <h1 className="mt-5 text-3xl font-semibold tracking-tight md:text-4xl">Your shortlist should feel like a working board, not a passive bookmark list.</h1>
                            <p className="mt-3 text-sm leading-7 text-[var(--color-text-secondary)]">
                                Keep high-conviction opportunities in one place, move them back into Osool Advisor, and compare what deserves action next.
                            </p>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-3">
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Saved items</div>
                                <div className="mt-2 text-3xl font-semibold">{favorites.length}</div>
                            </div>
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Ready to review</div>
                                <div className="mt-2 text-3xl font-semibold">{favorites.filter((fav) => fav.price_per_sqm > 0).length}</div>
                            </div>
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Next move</div>
                                <div className="mt-2 text-sm font-semibold">Compare, ask Osool, or keep refining.</div>
                            </div>
                        </div>
                    </div>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-6 h-6 animate-spin text-[var(--color-primary)]" />
                        </div>
                    )}

                    {/* Empty State — teach & motivate */}
                    {!loading && favorites.length === 0 && (
                        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 sm:p-12">
                            <div className="mx-auto max-w-lg text-center">
                                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-emerald-500/10">
                                    <Heart className="h-10 w-10 text-emerald-500" />
                                </div>
                                <h2 className="mt-6 text-2xl font-semibold text-[var(--color-text-primary)]">
                                    Your shortlist is your working board.
                                </h2>
                                <p className="mt-3 text-sm leading-7 text-[var(--color-text-secondary)]">
                                    The best investors don&rsquo;t just browse — they shortlist, compare, and strike.
                                    Start by asking the advisor for recommendations, then save the ones worth deeper analysis.
                                </p>

                                {/* Mini-roadmap */}
                                <div className="mx-auto mt-8 grid max-w-sm gap-3 text-left">
                                    <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-xs font-bold text-emerald-600">1</div>
                                        <div className="text-sm text-[var(--color-text-secondary)]">Ask the advisor: <span className="font-medium text-[var(--color-text-primary)]">&ldquo;Show me apartments in New Cairo under 5M&rdquo;</span></div>
                                    </div>
                                    <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-xs font-bold text-emerald-600">2</div>
                                        <div className="text-sm text-[var(--color-text-secondary)]">Tap the <Heart className="inline h-3.5 w-3.5 text-emerald-500" /> icon on any property card to save it here</div>
                                    </div>
                                    <div className="flex items-center gap-3 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-xs font-bold text-emerald-600">3</div>
                                        <div className="text-sm text-[var(--color-text-secondary)]">Come back here to compare, run valuations, and decide</div>
                                    </div>
                                </div>

                                <div className="mt-8 flex flex-wrap justify-center gap-3">
                                    <Link
                                        href="/chat"
                                        className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-6 py-3 text-sm font-semibold text-[var(--color-background)]"
                                    >
                                        <Sparkles className="h-4 w-4" />
                                        Open advisor chat
                                    </Link>
                                    <Link
                                        href="/explore"
                                        className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] px-6 py-3 text-sm font-medium hover:border-emerald-500/40"
                                    >
                                        Explore market
                                    </Link>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Favorites Grid */}
                    {!loading && favorites.length > 0 && (
                        <div className="space-y-5">
                            <div className="flex flex-wrap items-center gap-3 text-sm text-[var(--color-text-muted)]">
                                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">Most promising</span>
                                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">Highest conviction</span>
                                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">Need follow-up</span>
                            </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                            {favorites.map((fav) => (
                                <div
                                    key={fav.id}
                                    className="group bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[28px] overflow-hidden hover:border-emerald-500/30 hover:shadow-lg transition-all duration-300"
                                >
                                    {/* Image */}
                                    <div className="relative aspect-[16/10] bg-[var(--color-surface-elevated)] overflow-hidden">
                                        {fav.image_url ? (
                                            <img
                                                src={fav.image_url}
                                                alt={fav.title}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center">
                                                <Building2 className="w-12 h-12 text-[var(--color-text-muted)]" />
                                            </div>
                                        )}

                                        {/* Remove Button */}
                                        <button
                                            onClick={() => handleRemove(fav.property_id)}
                                            disabled={removing === fav.property_id}
                                            className="absolute top-3 right-3 p-2 bg-black/50 backdrop-blur-sm rounded-full text-white hover:bg-red-500 transition-colors"
                                            title="Remove from favorites"
                                        >
                                            {removing === fav.property_id ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <Trash2 className="w-4 h-4" />
                                            )}
                                        </button>

                                        {/* Price Badge */}
                                        <div className="absolute bottom-3 left-3 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-full text-white text-sm font-bold">
                                            {(fav.price / 1000000).toFixed(1)}M EGP
                                        </div>

                                        <div className="absolute top-3 left-3 rounded-full bg-emerald-500/90 px-3 py-1 text-[11px] font-semibold text-white">
                                            Saved for review
                                        </div>
                                    </div>

                                    {/* Info */}
                                    <div className="p-4">
                                        <h3 className="font-semibold text-[var(--color-text-primary)] truncate mb-1" dir="auto">
                                            {fav.title}
                                        </h3>
                                        <p className="text-xs text-[var(--color-text-muted)] flex items-center gap-1 mb-3" dir="auto">
                                            <MapPin className="w-3 h-3" />
                                            {fav.location}
                                            {fav.developer && ` · ${fav.developer}`}
                                        </p>

                                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3 text-xs text-[var(--color-text-secondary)] mb-3">
                                            {fav.notes ? fav.notes : 'Use this as a comparison candidate or pull it back into Osool Advisor for valuation, fit, and next-step guidance.'}
                                        </div>

                                        <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
                                            {fav.bedrooms > 0 && (
                                                <span className="flex items-center gap-1">
                                                    <Bed className="w-3.5 h-3.5" />
                                                    {fav.bedrooms} {t('favorites.beds')}
                                                </span>
                                            )}
                                            {fav.size_sqm > 0 && (
                                                <span className="flex items-center gap-1">
                                                    <Maximize className="w-3.5 h-3.5" />
                                                    {fav.size_sqm} sqm
                                                </span>
                                            )}
                                            {fav.price_per_sqm > 0 && (
                                                <span className="text-emerald-500 font-medium">
                                                    {fav.price_per_sqm.toLocaleString()}/m²
                                                </span>
                                            )}
                                        </div>

                                        <div className="mt-4 grid gap-2 sm:grid-cols-2">
                                            <Link
                                                href={`/chat?property=${encodeURIComponent(fav.title)}`}
                                                className="flex items-center justify-center gap-2 rounded-xl bg-[var(--color-text-primary)] px-4 py-2.5 text-sm font-medium text-[var(--color-background)]"
                                            >
                                                <Sparkles className="w-3.5 h-3.5" />
                                                {t('favorites.askCoInvestor')}
                                            </Link>
                                            <Link
                                                href={`/property/${fav.property_id}`}
                                                className="flex items-center justify-center rounded-xl border border-[var(--color-border)] px-4 py-2.5 text-sm font-medium text-[var(--color-text-primary)] hover:border-emerald-500/40"
                                            >
                                                Open detail
                                            </Link>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        </div>
                    )}
                </div>
            </div>
        </SmartNav>
    );
}
