"use client";

import { useState, useEffect, useMemo, useCallback, Suspense } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import { useFilterParams } from '@/hooks/useFilterParams';
import AppShell from '@/components/nav/AppShell';
import PropertyFilter from '@/components/PropertyFilter';
import { toggleFavorite, fetchFavorites } from '@/lib/gamification';
import { buildAdvisorPrompt, formatCompactPrice, propertyBrief } from '@/lib/decision-support';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, Bath, Bed, Building2, Grid3X3, Heart, Loader2, Map, MapPin, Maximize, ShieldCheck, SlidersHorizontal, Sparkles, Wallet } from 'lucide-react';
import dynamic from 'next/dynamic';

const PropertyMap = dynamic(() => import('@/components/PropertyMap'), {
    ssr: false,
    loading: () => (
        <div className="h-[600px] rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
                <Loader2 className="w-8 h-8 animate-spin" />
                <p>Loading map...</p>
            </div>
        </div>
    ),
});

// Hardcoded fallback data (used if API fails)
const fallbackProperties = [
    {
        id: '1',
        title: 'Luxury Villa in New Cairo',
        titleAr: '\u0641\u064a\u0644\u0627 \u0641\u0627\u062e\u0631\u0629 \u0641\u064a \u0627\u0644\u0642\u0627\u0647\u0631\u0629 \u0627\u0644\u062c\u062f\u064a\u062f\u0629',
        location: 'New Cairo, 5th Settlement',
        locationAr: '\u0627\u0644\u0642\u0627\u0647\u0631\u0629 \u0627\u0644\u062c\u062f\u064a\u062f\u0629\u060c \u0627\u0644\u062a\u062c\u0645\u0639 \u0627\u0644\u062e\u0627\u0645\u0633',
        city: 'new-cairo',
        price: 15000000,
        aiEstimate: 14800000,
        bedrooms: 5,
        bathrooms: 4,
        area: 450,
        image: 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop',
        type: 'villa',
        dateAdded: '2026-01-10',
        developer: '',
    },
    {
        id: '2',
        title: 'Modern Apartment in Zamalek',
        titleAr: '\u0634\u0642\u0629 \u062d\u062f\u064a\u062b\u0629 \u0641\u064a \u0627\u0644\u0632\u0645\u0627\u0644\u0643',
        location: 'Zamalek, Cairo',
        locationAr: '\u0627\u0644\u0632\u0645\u0627\u0644\u0643\u060c \u0627\u0644\u0642\u0627\u0647\u0631\u0629',
        city: 'cairo',
        price: 5500000,
        aiEstimate: 5650000,
        bedrooms: 3,
        bathrooms: 2,
        area: 180,
        image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop',
        type: 'apartment',
        dateAdded: '2026-01-12',
        developer: '',
    },
    {
        id: '3',
        title: 'Beachfront Chalet in Ain Sokhna',
        titleAr: '\u0634\u0627\u0644\u064a\u0647 \u0639\u0644\u0649 \u0627\u0644\u0628\u062d\u0631 \u0641\u064a \u0627\u0644\u0639\u064a\u0646 \u0627\u0644\u0633\u062e\u0646\u0629',
        location: 'Ain Sokhna, Red Sea',
        locationAr: '\u0627\u0644\u0639\u064a\u0646 \u0627\u0644\u0633\u062e\u0646\u0629\u060c \u0627\u0644\u0628\u062d\u0631 \u0627\u0644\u0623\u062d\u0645\u0631',
        city: 'ain-sokhna',
        price: 3200000,
        aiEstimate: 3100000,
        bedrooms: 2,
        bathrooms: 2,
        area: 120,
        image: 'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=600&h=400&fit=crop',
        type: 'chalet',
        dateAdded: '2026-01-08',
        developer: '',
    },
    {
        id: '4',
        title: 'Commercial Office in Smart Village',
        titleAr: '\u0645\u0643\u062a\u0628 \u062a\u062c\u0627\u0631\u064a \u0641\u064a \u0627\u0644\u0642\u0631\u064a\u0629 \u0627\u0644\u0630\u0643\u064a\u0629',
        location: 'Smart Village, 6th October',
        locationAr: '\u0627\u0644\u0642\u0631\u064a\u0629 \u0627\u0644\u0630\u0643\u064a\u0629\u060c 6 \u0623\u0643\u062a\u0648\u0628\u0631',
        city: '6th-october',
        price: 8500000,
        aiEstimate: 8750000,
        bedrooms: 0,
        bathrooms: 2,
        area: 250,
        image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop',
        type: 'commercial',
        dateAdded: '2026-01-05',
        developer: '',
    },
    {
        id: '5',
        title: 'Garden Duplex in Maadi',
        titleAr: '\u062f\u0648\u0628\u0644\u0643\u0633 \u0628\u062d\u062f\u064a\u0642\u0629 \u0641\u064a \u0627\u0644\u0645\u0639\u0627\u062f\u064a',
        location: 'Maadi, Cairo',
        locationAr: '\u0627\u0644\u0645\u0639\u0627\u062f\u064a\u060c \u0627\u0644\u0642\u0627\u0647\u0631\u0629',
        city: 'cairo',
        price: 7200000,
        aiEstimate: 7100000,
        bedrooms: 4,
        bathrooms: 3,
        area: 320,
        image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
        type: 'duplex',
        dateAdded: '2026-01-11',
        developer: '',
    },
    {
        id: '6',
        title: 'Penthouse in Sheikh Zayed',
        titleAr: '\u0628\u0646\u062a\u0647\u0627\u0648\u0633 \u0641\u064a \u0627\u0644\u0634\u064a\u062e \u0632\u0627\u064a\u062f',
        location: 'Sheikh Zayed City',
        locationAr: '\u0645\u062f\u064a\u0646\u0629 \u0627\u0644\u0634\u064a\u062e \u0632\u0627\u064a\u062f',
        city: 'sheikh-zayed',
        price: 12000000,
        aiEstimate: 11800000,
        bedrooms: 4,
        bathrooms: 3,
        area: 400,
        image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        type: 'penthouse',
        dateAdded: '2026-01-09',
        developer: '',
    },
    {
        id: '7',
        title: 'Studio Apartment in Heliopolis',
        titleAr: '\u0633\u062a\u0648\u062f\u064a\u0648 \u0641\u064a \u0645\u0635\u0631 \u0627\u0644\u062c\u062f\u064a\u062f\u0629',
        location: 'Heliopolis, Cairo',
        locationAr: '\u0645\u0635\u0631 \u0627\u0644\u062c\u062f\u064a\u062f\u0629\u060c \u0627\u0644\u0642\u0627\u0647\u0631\u0629',
        city: 'cairo',
        price: 1800000,
        aiEstimate: 1750000,
        bedrooms: 1,
        bathrooms: 1,
        area: 65,
        image: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&h=400&fit=crop',
        type: 'apartment',
        dateAdded: '2026-01-13',
        developer: '',
    },
    {
        id: '8',
        title: 'Townhouse in Madinaty',
        titleAr: '\u062a\u0627\u0648\u0646 \u0647\u0627\u0648\u0633 \u0641\u064a \u0645\u062f\u064a\u0646\u062a\u064a',
        location: 'Madinaty, New Cairo',
        locationAr: '\u0645\u062f\u064a\u0646\u062a\u064a\u060c \u0627\u0644\u0642\u0627\u0647\u0631\u0629 \u0627\u0644\u062c\u062f\u064a\u062f\u0629',
        city: 'new-cairo',
        price: 9500000,
        aiEstimate: 9600000,
        bedrooms: 4,
        bathrooms: 3,
        area: 280,
        image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
        type: 'townhouse',
        dateAdded: '2026-01-07',
        developer: '',
    },
];

interface PropertyItem {
    id: string;
    title: string;
    titleAr: string;
    location: string;
    locationAr: string;
    city: string;
    price: number;
    aiEstimate: number;
    bedrooms: number;
    bathrooms: number;
    area: number;
    image: string;
    type: string;
    dateAdded: string;
    developer: string;
    pricePerSqm?: number;
    saleType?: string;
    paymentPlan?: {
        downPayment?: number;
        installmentYears?: number;
        monthlyInstallment?: number;
    } | null;
}

interface RawProperty {
    id?: string | number;
    title?: string;
    name?: string;
    titleAr?: string;
    location?: string;
    locationAr?: string;
    price?: number;
    totalPrice?: number;
    aiValuation?: number;
    aiEstimate?: number;
    bedrooms?: number;
    bathrooms?: number;
    area?: number;
    size?: number;
    sqm?: number;
    bua?: number;
    size_sqm?: number;
    image?: string;
    image_url?: string;
    type?: string;
    dateAdded?: string;
    created_at?: string;
    developer?: string;
    pricePerSqm?: number;
    price_per_sqm?: number;
    saleType?: string;
    paymentPlan?: PropertyItem['paymentPlan'];
}

interface Filters {
    location: string;
    type: string;
    minPrice: number;
    maxPrice: number;
    bedrooms: number;
}

function PropertyCardSkeleton() {
    return (
        <div className="flex items-center gap-4 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 animate-pulse">
            <div className="h-20 w-28 flex-shrink-0 rounded-xl bg-[var(--color-surface-elevated)]" />
            <div className="flex-1 space-y-2">
                <div className="h-4 bg-[var(--color-surface-elevated)] rounded w-2/3" />
                <div className="h-3 bg-[var(--color-surface-elevated)] rounded w-1/3" />
                <div className="flex gap-3">
                    <div className="h-3 bg-[var(--color-surface-elevated)] rounded w-10" />
                    <div className="h-3 bg-[var(--color-surface-elevated)] rounded w-10" />
                    <div className="h-3 bg-[var(--color-surface-elevated)] rounded w-14" />
                </div>
            </div>
            <div className="h-5 w-20 flex-shrink-0 rounded bg-[var(--color-surface-elevated)]" />
        </div>
    );
}

export default function PropertiesPage() {
    return (
        <Suspense>
            <PropertiesPageInner />
        </Suspense>
    );
}

function PropertiesPageInner() {
    const { t, language } = useLanguage();
    const { isAuthenticated } = useAuth();
    const [properties, setProperties] = useState<PropertyItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [usingFallback, setUsingFallback] = useState(false);
    const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());

    const handleToggleFavorite = async (propertyId: string) => {
        if (!isAuthenticated) return;
        // Optimistic UI
        setFavoriteIds(prev => {
            const next = new Set(prev);
            if (next.has(propertyId)) next.delete(propertyId);
            else next.add(propertyId);
            return next;
        });
        try {
            await toggleFavorite(Number(propertyId));
        } catch {
            // Revert on error
            setFavoriteIds(prev => {
                const next = new Set(prev);
                if (next.has(propertyId)) next.delete(propertyId);
                else next.add(propertyId);
                return next;
            });
        }
    };
    const { filters, setFilters, sortBy, setSortBy, viewMode, setViewMode, shareUrl } = useFilterParams();
    const [showFilters, setShowFilters] = useState(false);
    const [failedImages, setFailedImages] = useState<Set<string>>(new Set());

    const FALLBACK_IMAGES = [
        'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop',
        'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&h=400&fit=crop',
    ];

    const getPropertyImage = (property: PropertyItem) => {
        if (failedImages.has(property.id)) {
            // Deterministic fallback based on property id
            const idx = parseInt(property.id, 10) % FALLBACK_IMAGES.length || 0;
            return FALLBACK_IMAGES[idx];
        }
        return property.image;
    };

    const handleImageError = (propertyId: string) => {
        setFailedImages(prev => new Set(prev).add(propertyId));
    };

    // Normalize API property to our internal format
    const normalizeProperty = useCallback((p: RawProperty): PropertyItem => {
        return {
            id: String(p.id),
            title: p.title || p.name || '',
            titleAr: p.titleAr || p.title || '',
            location: p.location || '',
            locationAr: p.locationAr || p.location || '',
            city: inferCity(p.location || ''),
            price: p.price || p.totalPrice || 0,
            aiEstimate: p.aiValuation || p.aiEstimate || 0,
            bedrooms: p.bedrooms ?? 0,
            bathrooms: p.bathrooms ?? 0,
            area: p.area || p.size || p.sqm || p.bua || p.size_sqm || 0,
            image: p.image || p.image_url || 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
            type: (p.type || 'apartment').toLowerCase(),
            dateAdded: p.dateAdded || p.created_at || new Date().toISOString().split('T')[0],
            developer: p.developer || '',
            pricePerSqm: p.pricePerSqm || p.price_per_sqm || 0,
            saleType: p.saleType || '',
            paymentPlan: p.paymentPlan || null,
        };
    }, []);

    // Infer city key from location string for filtering
    function inferCity(location: string): string {
        const loc = location.toLowerCase();
        if (loc.includes('new cairo') || loc.includes('madinaty') || loc.includes('5th settlement') || loc.includes('rehab') || loc.includes('6th settlement')) return 'new-cairo';
        if (loc.includes('zayed') || loc.includes('sheikh zayed')) return 'sheikh-zayed';
        if (loc.includes('october') || loc.includes('smart village')) return '6th-october';
        if (loc.includes('sokhna') || loc.includes('ain sokhna')) return 'ain-sokhna';
        if (loc.includes('north coast') || loc.includes('sahel')) return 'north-coast';
        if (loc.includes('new capital') || loc.includes('capital')) return 'new-capital';
        if (loc.includes('mostakbal') || loc.includes('golden square')) return 'new-cairo';
        if (loc.includes('zamalek') || loc.includes('maadi') || loc.includes('heliopolis') || loc.includes('cairo')) return 'cairo';
        return 'other';
    }

    // Load properties from backend API, fall back to static data then hardcoded
    const fetchProperties = useCallback(async () => {
        try {
            setLoading(true);
            // Try backend API first
            const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
            const apiRes = await fetch(`${API_URL}/api/properties`);
            if (apiRes.ok) {
                const apiData = await apiRes.json();
                if (Array.isArray(apiData) && apiData.length > 0) {
                    const normalized = apiData.map(normalizeProperty);
                    setProperties(normalized);
                    setUsingFallback(false);
                    return;
                }
            }

            // Fallback: static data file
            const res = await fetch('/assets/js/data.js');
            const txt = await res.text();
            const start = txt.indexOf('{');
            const end = txt.lastIndexOf('}');
            if (start !== -1 && end !== -1) {
                const raw = JSON.parse(txt.substring(start, end + 1));
                const props = (raw.properties || []) as RawProperty[];
                if (props.length > 0) {
                    const normalized = props.map(normalizeProperty);
                    setProperties(normalized);
                    setUsingFallback(false);
                    return;
                }
            }
            // Final fallback: hardcoded properties
            setProperties(fallbackProperties);
            setUsingFallback(true);
        } catch (err) {
            console.error('Failed to load properties:', err);
            setProperties(fallbackProperties);
            setUsingFallback(true);
        } finally {
            setLoading(false);
        }
    }, [normalizeProperty]);

    useEffect(() => {
        fetchProperties();
    }, [fetchProperties]);

    // Load user's favorites from API
    useEffect(() => {
        if (!isAuthenticated) return;
        fetchFavorites()
            .then(data => {
                const ids = new Set((data.favorites || []).map(f => String(f.property_id)));
                setFavoriteIds(ids);
            })
            .catch(() => { /* non-critical */ });
    }, [isAuthenticated]);

    // Client-side filtering and sorting
    const filteredProperties = useMemo(() => {
        const result = properties.filter((p) => {
            if (filters.location !== 'all' && p.city !== filters.location) return false;
            if (filters.type !== 'all' && p.type !== filters.type) return false;
            if (p.price < filters.minPrice || p.price > filters.maxPrice) return false;
            if (filters.bedrooms > 0 && p.bedrooms < filters.bedrooms) return false;
            return true;
        });

        // Sort
        if (sortBy === 'price-asc') {
            result.sort((a, b) => a.price - b.price);
        } else if (sortBy === 'price-desc') {
            result.sort((a, b) => b.price - a.price);
        } else {
            result.sort((a, b) => new Date(b.dateAdded).getTime() - new Date(a.dateAdded).getTime());
        }

        return result;
    }, [properties, filters, sortBy]);

    const formatPrice = (price: number) => {
        if (language === 'ar') {
            return `${(price / 1000000).toFixed(1)} \u0645\u0644\u064a\u0648\u0646 \u062c.\u0645`;
        }
        return `EGP ${(price / 1000000).toFixed(1)}M`;
    };

    const boardSummary = useMemo(() => {
        if (filteredProperties.length === 0) {
            return {
                averagePrice: null,
                planFriendlyCount: 0,
                signalLabel: 'No active shortlist signal',
                signalBody: 'Adjust the filters or ask Osool Advisor to narrow the market for you.',
            };
        }

        const averagePrice = filteredProperties.reduce((sum, property) => sum + property.price, 0) / filteredProperties.length;
        const planFriendlyCount = filteredProperties.filter((property) => {
            const downPayment = property.paymentPlan?.downPayment ?? 100;
            const installmentYears = property.paymentPlan?.installmentYears ?? 0;
            return downPayment <= 10 && installmentYears >= 8;
        }).length;

        const bestSignal = filteredProperties
            .map((property) => ({ property, brief: propertyBrief(property) }))
            .sort((left, right) => {
                const leftRank = left.brief.confidenceLabel === 'Value pocket' ? 3 : left.brief.confidenceLabel === 'Plan-friendly' ? 2 : 1;
                const rightRank = right.brief.confidenceLabel === 'Value pocket' ? 3 : right.brief.confidenceLabel === 'Plan-friendly' ? 2 : 1;
                return rightRank - leftRank;
            })[0];

        return {
            averagePrice,
            planFriendlyCount,
            signalLabel: bestSignal.brief.confidenceLabel,
            signalBody: `${bestSignal.property.title}: ${bestSignal.brief.thesis}`,
        };
    }, [filteredProperties]);

    return (
        <AppShell>
        <main className="h-full overflow-y-auto bg-[var(--color-background)]">
            <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
                <section className="grid gap-6 lg:grid-cols-[1fr_0.95fr] lg:items-start">
                    <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
                        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
                            <ShieldCheck className="h-3.5 w-3.5" />
                            Property decision board
                        </div>
                        <h1 className="mt-5 text-4xl font-semibold tracking-tight">Use live inventory as a shortlist workspace, not a passive catalog.</h1>
                        <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)]">
                            Review pricing signal, payment fit, and use-case before deciding which units deserve deeper advisor work.
                        </p>
                        <div className="mt-6 flex flex-wrap gap-3 text-sm text-[var(--color-text-muted)]">
                            <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">
                                {loading
                                    ? (language === 'ar' ? '\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0645\u064a\u0644...' : 'Loading properties...')
                                    : `${filteredProperties.length} active matches`}
                            </span>
                            <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">
                                Strategy: value, payment fit, and readiness
                            </span>
                            {usingFallback && !loading && (
                                <span className="rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-2 text-amber-600 dark:text-amber-300">
                                    Cached data fallback active
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Average ticket</div>
                                <Wallet className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">
                                {boardSummary.averagePrice ? formatCompactPrice(boardSummary.averagePrice) : '—'}
                            </div>
                            <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Typical price level across the current filtered board.</div>
                        </div>
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Plan-friendly units</div>
                                <Sparkles className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-2 text-2xl font-semibold text-[var(--color-text-primary)]">{boardSummary.planFriendlyCount}</div>
                            <div className="mt-2 text-sm text-[var(--color-text-secondary)]">Units currently showing lower-entry payment structures.</div>
                        </div>
                        <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                            <div className="flex items-center justify-between">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Strongest signal</div>
                                <Building2 className="h-4 w-4 text-emerald-500" />
                            </div>
                            <div className="mt-2 text-lg font-semibold text-[var(--color-text-primary)]">{boardSummary.signalLabel}</div>
                            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{boardSummary.signalBody}</div>
                        </div>
                    </div>
                </section>

                <div className="flex flex-col lg:flex-row gap-8">
                    {/* Filters Sidebar - Desktop */}
                    <aside className="hidden lg:block w-72 flex-shrink-0">
                        <PropertyFilter filters={filters} setFilters={setFilters} />
                    </aside>

                    {/* Mobile Filters Toggle */}
                    <div className="lg:hidden">
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)]"
                        >
                            <SlidersHorizontal className="w-5 h-5" />
                            {language === 'ar' ? '\u0627\u0644\u0641\u0644\u0627\u062a\u0631' : 'Filters'}
                        </button>

                        {showFilters && (
                            <div className="mt-4">
                                <PropertyFilter filters={filters} setFilters={setFilters} />
                            </div>
                        )}
                    </div>

                    {/* Main Content */}
                    <div className="flex-1">
                        {/* Toolbar */}
                        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                            {/* Sort */}
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                                className="px-4 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                            >
                                <option value="date">{language === 'ar' ? '\u0627\u0644\u0623\u062d\u062f\u062b' : 'Newest'}</option>
                                <option value="price-asc">{language === 'ar' ? '\u0627\u0644\u0633\u0639\u0631: \u0645\u0646 \u0627\u0644\u0623\u0642\u0644' : 'Price: Low to High'}</option>
                                <option value="price-desc">{language === 'ar' ? '\u0627\u0644\u0633\u0639\u0631: \u0645\u0646 \u0627\u0644\u0623\u0639\u0644\u0649' : 'Price: High to Low'}</option>
                            </select>

                            {/* View Toggle + Share */}
                            <div className="flex items-center gap-2">
                                <div className="flex items-center rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
                                    <button
                                        onClick={() => setViewMode('grid')}
                                        className={`p-2.5 ${viewMode === 'grid' ? 'bg-[var(--color-primary)] text-white' : 'text-[var(--color-text-secondary)]'}`}
                                    >
                                        <Grid3X3 className="w-5 h-5" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode('map')}
                                        className={`p-2.5 ${viewMode === 'map' ? 'bg-[var(--color-primary)] text-white' : 'text-[var(--color-text-secondary)]'}`}
                                    >
                                        <Map className="w-5 h-5" />
                                    </button>
                                </div>
                                {shareUrl && (
                                    <button
                                        onClick={() => { navigator.clipboard.writeText(shareUrl); }}
                                        className="px-3 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:text-[var(--color-primary)] transition-colors text-sm"
                                        title={language === 'ar' ? 'نسخ رابط الفلاتر' : 'Copy filter link'}
                                    >
                                        {language === 'ar' ? '🔗 نسخ الرابط' : '🔗 Share'}
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Loading Skeletons */}
                        {loading && viewMode === 'grid' && (
                            <div className="flex flex-col gap-3">
                                {Array.from({ length: 6 }).map((_, i) => (
                                    <PropertyCardSkeleton key={i} />
                                ))}
                            </div>
                        )}

                        {/* Properties List */}
                        {!loading && viewMode === 'grid' && (
                            <div className="flex flex-col gap-3">
                                {filteredProperties.map((property, index) => (
                                    (() => {
                                        const brief = propertyBrief(property);
                                        const advisorPrompt = buildAdvisorPrompt(property);

                                        return (
                                            <motion.div
                                                key={property.id}
                                                initial={{ opacity: 0, y: 8 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ duration: 0.25, delay: index * 0.03 }}
                                                className="group relative flex items-stretch gap-0 overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/30 transition-colors"
                                            >
                                                {/* Thumbnail */}
                                                <Link href={`/property/${property.id}`} className="relative w-44 flex-shrink-0 overflow-hidden sm:w-52">
                                                    <img
                                                        src={getPropertyImage(property)}
                                                        alt={language === 'ar' ? property.titleAr : property.title}
                                                        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                                                        onError={() => handleImageError(property.id)}
                                                    />
                                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent to-black/10" />
                                                    {/* Availability dot */}
                                                    <span className="absolute left-3 top-3 rounded-full bg-emerald-500/90 px-2.5 py-0.5 text-[10px] font-semibold text-white">
                                                        {brief.confidenceLabel}
                                                    </span>
                                                </Link>

                                                {/* Info body */}
                                                <div className="flex flex-1 flex-col justify-center gap-1.5 px-5 py-4 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <h3 className="text-[15px] font-semibold text-[var(--color-text-primary)] truncate">
                                                            {language === 'ar' ? property.titleAr : property.title}
                                                        </h3>
                                                        {property.saleType && (
                                                            <span className="flex-shrink-0 rounded-full border border-[var(--color-border)] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
                                                                {property.saleType}
                                                            </span>
                                                        )}
                                                    </div>

                                                    <div className="flex items-center gap-1 text-sm text-[var(--color-text-secondary)]">
                                                        <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
                                                        <span className="truncate">{language === 'ar' ? property.locationAr : property.location}</span>
                                                        {property.developer && (
                                                            <>
                                                                <span className="text-[var(--color-border)]">·</span>
                                                                <span className="truncate text-[var(--color-text-muted)]">{property.developer}</span>
                                                            </>
                                                        )}
                                                    </div>

                                                    {/* Specs row */}
                                                    <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
                                                        {property.bedrooms > 0 && (
                                                            <span className="flex items-center gap-1"><Bed className="h-3.5 w-3.5" />{property.bedrooms} bed</span>
                                                        )}
                                                        {property.bathrooms > 0 && (
                                                            <span className="flex items-center gap-1"><Bath className="h-3.5 w-3.5" />{property.bathrooms} bath</span>
                                                        )}
                                                        {property.area > 0 && (
                                                            <span className="flex items-center gap-1"><Maximize className="h-3.5 w-3.5" />{property.area} {language === 'ar' ? '\u0645\u00B2' : 'sqm'}</span>
                                                        )}
                                                        {property.pricePerSqm ? (
                                                            <span className="text-[var(--color-text-secondary)]">{Math.round(property.pricePerSqm).toLocaleString('en-EG')} EGP/m²</span>
                                                        ) : null}
                                                        {property.paymentPlan?.downPayment != null && property.paymentPlan?.installmentYears != null ? (
                                                            <span className="text-[var(--color-text-secondary)]">{property.paymentPlan.downPayment}% down · {property.paymentPlan.installmentYears}yr</span>
                                                        ) : null}
                                                    </div>
                                                </div>

                                                {/* Price + actions column */}
                                                <div className="flex flex-shrink-0 flex-col items-end justify-center gap-2 border-l border-[var(--color-border)]/50 px-5 py-4">
                                                    <div className="text-lg font-bold text-[var(--color-text-primary)] whitespace-nowrap">{formatPrice(property.price)}</div>
                                                    {property.aiEstimate > 0 && (
                                                        <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400">{brief.priceSignal}</span>
                                                    )}
                                                    <div className="flex items-center gap-1.5 mt-1">
                                                        <Link
                                                            href={`/property/${property.id}`}
                                                            className="inline-flex items-center gap-1 rounded-lg bg-[var(--color-text-primary)] px-3 py-1.5 text-xs font-semibold text-[var(--color-background)] hover:opacity-90 transition-opacity"
                                                        >
                                                            {t('property.viewDetails')}
                                                            <ArrowRight className="h-3 w-3" />
                                                        </Link>
                                                        <button
                                                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); handleToggleFavorite(property.id); }}
                                                            className={`flex h-7 w-7 items-center justify-center rounded-lg border transition-colors ${favoriteIds.has(property.id) ? 'border-red-300 bg-red-50 dark:bg-red-500/10 dark:border-red-500/30' : 'border-[var(--color-border)] hover:border-emerald-500/40'}`}
                                                        >
                                                            <Heart className={`h-3.5 w-3.5 ${favoriteIds.has(property.id) ? 'fill-red-500 text-red-500' : 'text-[var(--color-text-muted)]'}`} />
                                                        </button>
                                                        <Link
                                                            href={`/chat?prompt=${encodeURIComponent(advisorPrompt)}&autostart=1`}
                                                            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--color-border)] hover:border-emerald-500/40 transition-colors"
                                                            title="Ask advisor"
                                                        >
                                                            <Sparkles className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                                                        </Link>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        );
                                    })()
                                ))}
                            </div>
                        )}

                        {/* Map View */}
                        {!loading && viewMode === 'map' && (
                            <PropertyMap
                                properties={filteredProperties}
                                language={language}
                                formatPrice={formatPrice}
                            />
                        )}

                        {/* Loading state for map view */}
                        {loading && viewMode === 'map' && (
                            <div className="h-[600px] rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
                                <div className="flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
                                    <Loader2 className="w-8 h-8 animate-spin" />
                                    <p>{language === 'ar' ? 'Ø¬Ø§Ø±ÙŠ Ø§Ù„ØªØ­Ù…ÙŠÙ„...' : 'Loading...'}</p>
                                </div>
                            </div>
                        )}

                        {/* Empty State */}
                        {!loading && filteredProperties.length === 0 && (
                            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-16 text-center">
                                <div className="w-20 h-20 bg-[var(--color-surface-elevated)] rounded-full flex items-center justify-center mx-auto mb-4">
                                    <MapPin className="w-8 h-8 text-[var(--color-text-muted)]" />
                                </div>
                                <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
                                    {language === 'ar' ? '\u0644\u0627 \u062a\u0648\u062c\u062f \u0639\u0642\u0627\u0631\u0627\u062a' : 'No properties found'}
                                </h3>
                                <p className="text-[var(--color-text-secondary)]">
                                    {language === 'ar' ? '\u062c\u0631\u0628 \u062a\u0639\u062f\u064a\u0644 \u0627\u0644\u0641\u0644\u0627\u062a\u0631' : 'Try adjusting your filters'}
                                </p>
                                <div className="mt-6 flex flex-wrap justify-center gap-3">
                                    <button
                                        onClick={() => setFilters({ location: 'all', type: 'all', minPrice: 0, maxPrice: 50000000, bedrooms: 0 })}
                                        className="rounded-full border border-[var(--color-border)] px-5 py-2.5 text-sm font-medium text-[var(--color-text-primary)]"
                                    >
                                        Reset filters
                                    </button>
                                    <Link
                                        href="/chat?prompt=Help me build a shortlist based on my budget, area preference, and risk tolerance.&autostart=1"
                                        className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-2.5 text-sm font-semibold text-[var(--color-background)]"
                                    >
                                        <Sparkles className="h-4 w-4" />
                                        Ask Osool to shortlist for me
                                    </Link>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

        </main>
        </AppShell>
    );
}
