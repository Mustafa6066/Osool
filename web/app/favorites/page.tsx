'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Heart, MapPin, Bed, Maximize, Trash2, Loader2, Building2, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchFavorites, toggleFavorite, FavoriteProperty } from '@/lib/gamification';
import Link from 'next/link';
import SmartNav from '@/components/SmartNav';

export default function FavoritesPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
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
        setRemoving(propertyId);
        try {
            await toggleFavorite(propertyId);
            setFavorites(prev => prev.filter(f => f.property_id !== propertyId));
        } catch (err) {
            console.error('[Favorites] Failed to remove:', err);
        } finally {
            setRemoving(null);
        }
    };

    if (authLoading) return null;

    return (
        <SmartNav>
            <div className="h-full overflow-y-auto">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 pb-24 md:pb-8">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text-primary)] flex items-center gap-3">
                            <Heart className="w-7 h-7 text-red-400" />
                            Saved Properties
                        </h1>
                        <p className="text-sm text-[var(--color-text-muted)] mt-1">
                            Your shortlisted properties for quick comparison
                        </p>
                    </div>

                    {/* Loading State */}
                    {loading && (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-6 h-6 animate-spin text-[var(--color-primary)]" />
                        </div>
                    )}

                    {/* Empty State */}
                    {!loading && favorites.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20 text-center">
                            <div className="w-20 h-20 rounded-2xl bg-[var(--color-surface-elevated)] flex items-center justify-center mb-4">
                                <Heart className="w-10 h-10 text-[var(--color-text-muted)]" />
                            </div>
                            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                                No saved properties yet
                            </h2>
                            <p className="text-sm text-[var(--color-text-muted)] max-w-md mb-6">
                                Browse properties and tap the heart icon to save them here for easy comparison.
                            </p>
                            <Link
                                href="/properties"
                                className="px-6 py-2.5 bg-[var(--color-primary)] text-white rounded-full text-sm font-medium hover:bg-[var(--color-primary)]/90 transition-colors"
                            >
                                Explore Properties
                            </Link>
                        </div>
                    )}

                    {/* Favorites Grid */}
                    {!loading && favorites.length > 0 && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                            {favorites.map((fav) => (
                                <div
                                    key={fav.id}
                                    className="group bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden hover:border-[var(--color-primary)]/30 hover:shadow-lg transition-all duration-300"
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

                                        {/* Specs */}
                                        <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
                                            {fav.bedrooms > 0 && (
                                                <span className="flex items-center gap-1">
                                                    <Bed className="w-3.5 h-3.5" />
                                                    {fav.bedrooms} Beds
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

                                        {/* Notes */}
                                        {fav.notes && (
                                            <div className="mt-3 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-elevated)] rounded-lg px-3 py-2 italic">
                                                {fav.notes}
                                            </div>
                                        )}

                                        {/* Ask AMR button */}
                                        <Link
                                            href={`/chat`}
                                            className="mt-3 flex items-center justify-center gap-2 w-full py-2 rounded-xl border border-[var(--color-border)] hover:border-[var(--color-primary)]/30 hover:bg-[var(--color-primary)]/5 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-all"
                                        >
                                            <Sparkles className="w-3.5 h-3.5" />
                                            Ask AMR about this
                                        </Link>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </SmartNav>
    );
}
