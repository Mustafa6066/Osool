"use client";

import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useCallback, useMemo } from 'react';

interface Filters {
    location: string;
    type: string;
    minPrice: number;
    maxPrice: number;
    bedrooms: number;
}

const DEFAULTS: Filters = {
    location: 'all',
    type: 'all',
    minPrice: 0,
    maxPrice: 50000000,
    bedrooms: 0,
};

/**
 * Syncs property filter state with URL search params.
 * Reading is from searchParams (SSR-safe), writing pushes to URL.
 */
export function useFilterParams() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();

    const filters: Filters = useMemo(() => ({
        location: searchParams.get('location') || DEFAULTS.location,
        type: searchParams.get('type') || DEFAULTS.type,
        minPrice: Number(searchParams.get('minPrice')) || DEFAULTS.minPrice,
        maxPrice: Number(searchParams.get('maxPrice')) || DEFAULTS.maxPrice,
        bedrooms: Number(searchParams.get('bedrooms')) || DEFAULTS.bedrooms,
    }), [searchParams]);

    const sortBy = (searchParams.get('sort') || 'date') as 'price-asc' | 'price-desc' | 'date';
    const viewMode = (searchParams.get('view') || 'grid') as 'grid' | 'map';

    const setFilters = useCallback((updater: Filters | ((prev: Filters) => Filters)) => {
        const next = typeof updater === 'function' ? updater(filters) : updater;
        const params = new URLSearchParams(searchParams.toString());

        // Only set non-default values to keep URL clean
        if (next.location !== DEFAULTS.location) params.set('location', next.location);
        else params.delete('location');

        if (next.type !== DEFAULTS.type) params.set('type', next.type);
        else params.delete('type');

        if (next.minPrice !== DEFAULTS.minPrice) params.set('minPrice', String(next.minPrice));
        else params.delete('minPrice');

        if (next.maxPrice !== DEFAULTS.maxPrice) params.set('maxPrice', String(next.maxPrice));
        else params.delete('maxPrice');

        if (next.bedrooms !== DEFAULTS.bedrooms) params.set('bedrooms', String(next.bedrooms));
        else params.delete('bedrooms');

        router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }, [filters, searchParams, router, pathname]);

    const setSortBy = useCallback((sort: 'price-asc' | 'price-desc' | 'date') => {
        const params = new URLSearchParams(searchParams.toString());
        if (sort !== 'date') params.set('sort', sort);
        else params.delete('sort');
        router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }, [searchParams, router, pathname]);

    const setViewMode = useCallback((view: 'grid' | 'map') => {
        const params = new URLSearchParams(searchParams.toString());
        if (view !== 'grid') params.set('view', view);
        else params.delete('view');
        router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }, [searchParams, router, pathname]);

    const shareUrl = useMemo(() => {
        if (typeof window === 'undefined') return '';
        return window.location.href;
    }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

    return { filters, setFilters, sortBy, setSortBy, viewMode, setViewMode, shareUrl };
}
