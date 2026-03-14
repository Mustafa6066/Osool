"use client";

import { useLanguage } from '@/contexts/LanguageContext';
import { MapPin, Home, X } from 'lucide-react';

interface Filters {
    location: string;
    type: string;
    minPrice: number;
    maxPrice: number;
    bedrooms: number;
}

interface PropertyFilterProps {
    filters: Filters;
    setFilters: React.Dispatch<React.SetStateAction<Filters>>;
}

export default function PropertyFilter({ filters, setFilters }: PropertyFilterProps) {
    const { language, t } = useLanguage();

    const locations = [
        { value: 'all', labelEn: 'All Locations', labelAr: 'جميع المواقع' },
        { value: 'cairo', labelEn: 'Cairo', labelAr: 'القاهرة' },
        { value: 'new-cairo', labelEn: 'New Cairo', labelAr: 'القاهرة الجديدة' },
        { value: '6th-october', labelEn: '6th October', labelAr: '6 أكتوبر' },
        { value: 'sheikh-zayed', labelEn: 'Sheikh Zayed', labelAr: 'الشيخ زايد' },
        { value: 'ain-sokhna', labelEn: 'Ain Sokhna', labelAr: 'العين السخنة' },
    ];

    const propertyTypes = [
        { value: 'all', labelEn: 'All Types', labelAr: 'جميع الأنواع' },
        { value: 'apartment', labelEn: 'Apartment', labelAr: 'شقة' },
        { value: 'villa', labelEn: 'Villa', labelAr: 'فيلا' },
        { value: 'duplex', labelEn: 'Duplex', labelAr: 'دوبلكس' },
        { value: 'penthouse', labelEn: 'Penthouse', labelAr: 'بنتهاوس' },
        { value: 'townhouse', labelEn: 'Townhouse', labelAr: 'تاون هاوس' },
        { value: 'chalet', labelEn: 'Chalet', labelAr: 'شاليه' },
        { value: 'commercial', labelEn: 'Commercial', labelAr: 'تجاري' },
    ];

    const formatPrice = (price: number) => {
        if (price >= 1000000) {
            return `${(price / 1000000).toFixed(0)}M`;
        }
        return `${(price / 1000).toFixed(0)}K`;
    };

    const resetFilters = () => {
        setFilters({
            location: 'all',
            type: 'all',
            minPrice: 0,
            maxPrice: 50000000,
            bedrooms: 0,
        });
    };

    const hasActiveFilters = filters.location !== 'all' ||
        filters.type !== 'all' ||
        filters.minPrice > 0 ||
        filters.maxPrice < 50000000 ||
        filters.bedrooms > 0;

    return (
        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 sticky top-24">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-[var(--color-text-primary)]">
                    {language === 'ar' ? 'الفلاتر' : 'Filters'}
                </h3>
                {hasActiveFilters && (
                    <button
                        onClick={resetFilters}
                        className="flex items-center gap-1 text-sm text-[var(--color-primary)] hover:underline"
                    >
                        <X className="w-4 h-4" />
                        {t('common.reset')}
                    </button>
                )}
            </div>

            {/* Location */}
            <div className="mb-6">
                <label className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)] mb-3">
                    <MapPin className="w-4 h-4 text-[var(--color-primary)]" />
                    {t('showcase.filters.location')}
                </label>
                <select
                    value={filters.location}
                    onChange={(e) => setFilters(prev => ({ ...prev, location: e.target.value }))}
                    className="w-full px-4 py-3 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                >
                    {locations.map((loc) => (
                        <option key={loc.value} value={loc.value}>
                            {language === 'ar' ? loc.labelAr : loc.labelEn}
                        </option>
                    ))}
                </select>
            </div>

            {/* Property Type */}
            <div className="mb-6">
                <label className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)] mb-3">
                    <Home className="w-4 h-4 text-[var(--color-primary)]" />
                    {t('showcase.filters.propertyType')}
                </label>
                <select
                    value={filters.type}
                    onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
                    className="w-full px-4 py-3 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                >
                    {propertyTypes.map((type) => (
                        <option key={type.value} value={type.value}>
                            {language === 'ar' ? type.labelAr : type.labelEn}
                        </option>
                    ))}
                </select>
            </div>

            {/* Price Range */}
            <div className="mb-6">
                <label className="text-sm font-semibold text-[var(--color-text-primary)] mb-3 block">
                    {t('showcase.filters.priceRange')}
                </label>
                <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm text-[var(--color-text-secondary)]">
                        {formatPrice(filters.minPrice)}
                    </span>
                    <div className="flex-1 h-[2px] bg-[var(--color-border)] relative">
                        <div
                            className="absolute h-full bg-[var(--color-primary)]"
                            style={{
                                left: `${(filters.minPrice / 50000000) * 100}%`,
                                right: `${100 - (filters.maxPrice / 50000000) * 100}%`,
                            }}
                        />
                    </div>
                    <span className="text-sm text-[var(--color-text-secondary)]">
                        {formatPrice(filters.maxPrice)}
                    </span>
                </div>
                <div className="space-y-2">
                    <input
                        type="range"
                        min={0}
                        max={50000000}
                        step={500000}
                        value={filters.minPrice}
                        onChange={(e) => setFilters(prev => ({
                            ...prev,
                            minPrice: Math.min(Number(e.target.value), prev.maxPrice - 500000)
                        }))}
                        className="w-full accent-[var(--color-primary)]"
                    />
                    <input
                        type="range"
                        min={0}
                        max={50000000}
                        step={500000}
                        value={filters.maxPrice}
                        onChange={(e) => setFilters(prev => ({
                            ...prev,
                            maxPrice: Math.max(Number(e.target.value), prev.minPrice + 500000)
                        }))}
                        className="w-full accent-[var(--color-primary)]"
                    />
                </div>
            </div>

            {/* Bedrooms */}
            <div className="mb-6">
                <label className="text-sm font-semibold text-[var(--color-text-primary)] mb-3 block">
                    {t('property.bedrooms')}
                </label>
                <div className="flex gap-2">
                    {[0, 1, 2, 3, 4, 5].map((num) => (
                        <button
                            key={num}
                            onClick={() => setFilters(prev => ({ ...prev, bedrooms: num }))}
                            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors
                ${filters.bedrooms === num
                                    ? 'bg-[var(--color-primary)] text-white'
                                    : 'bg-[var(--color-background)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:border-[var(--color-primary)]'
                                }`}
                        >
                            {num === 0 ? (language === 'ar' ? 'الكل' : 'Any') : `${num}+`}
                        </button>
                    ))}
                </div>
            </div>

            {/* Apply Button */}
            <button className="w-full btn-primary">
                {t('common.apply')}
            </button>
        </div>
    );
}
