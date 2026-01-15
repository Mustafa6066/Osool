"use client";

import { useState, useMemo } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import PropertyFilter from '@/components/PropertyFilter';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { MapPin, Bed, Bath, Maximize, Sparkles, Heart, Grid3X3, Map, SlidersHorizontal } from 'lucide-react';

// Extended sample properties data
const allProperties = [
    {
        id: '1',
        title: 'Luxury Villa in New Cairo',
        titleAr: 'فيلا فاخرة في القاهرة الجديدة',
        location: 'New Cairo, 5th Settlement',
        locationAr: 'القاهرة الجديدة، التجمع الخامس',
        city: 'new-cairo',
        price: 15000000,
        aiEstimate: 14800000,
        bedrooms: 5,
        bathrooms: 4,
        area: 450,
        image: 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop',
        type: 'villa',
        dateAdded: '2026-01-10',
    },
    {
        id: '2',
        title: 'Modern Apartment in Zamalek',
        titleAr: 'شقة حديثة في الزمالك',
        location: 'Zamalek, Cairo',
        locationAr: 'الزمالك، القاهرة',
        city: 'cairo',
        price: 5500000,
        aiEstimate: 5650000,
        bedrooms: 3,
        bathrooms: 2,
        area: 180,
        image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop',
        type: 'apartment',
        dateAdded: '2026-01-12',
    },
    {
        id: '3',
        title: 'Beachfront Chalet in Ain Sokhna',
        titleAr: 'شاليه على البحر في العين السخنة',
        location: 'Ain Sokhna, Red Sea',
        locationAr: 'العين السخنة، البحر الأحمر',
        city: 'ain-sokhna',
        price: 3200000,
        aiEstimate: 3100000,
        bedrooms: 2,
        bathrooms: 2,
        area: 120,
        image: 'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=600&h=400&fit=crop',
        type: 'chalet',
        dateAdded: '2026-01-08',
    },
    {
        id: '4',
        title: 'Commercial Office in Smart Village',
        titleAr: 'مكتب تجاري في القرية الذكية',
        location: 'Smart Village, 6th October',
        locationAr: 'القرية الذكية، 6 أكتوبر',
        city: '6th-october',
        price: 8500000,
        aiEstimate: 8750000,
        bedrooms: 0,
        bathrooms: 2,
        area: 250,
        image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop',
        type: 'commercial',
        dateAdded: '2026-01-05',
    },
    {
        id: '5',
        title: 'Garden Duplex in Maadi',
        titleAr: 'دوبلكس بحديقة في المعادي',
        location: 'Maadi, Cairo',
        locationAr: 'المعادي، القاهرة',
        city: 'cairo',
        price: 7200000,
        aiEstimate: 7100000,
        bedrooms: 4,
        bathrooms: 3,
        area: 320,
        image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
        type: 'duplex',
        dateAdded: '2026-01-11',
    },
    {
        id: '6',
        title: 'Penthouse in Sheikh Zayed',
        titleAr: 'بنتهاوس في الشيخ زايد',
        location: 'Sheikh Zayed City',
        locationAr: 'مدينة الشيخ زايد',
        city: 'sheikh-zayed',
        price: 12000000,
        aiEstimate: 11800000,
        bedrooms: 4,
        bathrooms: 3,
        area: 400,
        image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        type: 'penthouse',
        dateAdded: '2026-01-09',
    },
    {
        id: '7',
        title: 'Studio Apartment in Heliopolis',
        titleAr: 'ستوديو في مصر الجديدة',
        location: 'Heliopolis, Cairo',
        locationAr: 'مصر الجديدة، القاهرة',
        city: 'cairo',
        price: 1800000,
        aiEstimate: 1750000,
        bedrooms: 1,
        bathrooms: 1,
        area: 65,
        image: 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600&h=400&fit=crop',
        type: 'apartment',
        dateAdded: '2026-01-13',
    },
    {
        id: '8',
        title: 'Townhouse in Madinaty',
        titleAr: 'تاون هاوس في مدينتي',
        location: 'Madinaty, New Cairo',
        locationAr: 'مدينتي، القاهرة الجديدة',
        city: 'new-cairo',
        price: 9500000,
        aiEstimate: 9600000,
        bedrooms: 4,
        bathrooms: 3,
        area: 280,
        image: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&h=400&fit=crop',
        type: 'townhouse',
        dateAdded: '2026-01-07',
    },
];

interface Filters {
    location: string;
    type: string;
    minPrice: number;
    maxPrice: number;
    bedrooms: number;
}

export default function PropertiesPage() {
    const { t, language } = useLanguage();
    const [filters, setFilters] = useState<Filters>({
        location: 'all',
        type: 'all',
        minPrice: 0,
        maxPrice: 50000000,
        bedrooms: 0,
    });
    const [sortBy, setSortBy] = useState<'price-asc' | 'price-desc' | 'date'>('date');
    const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');
    const [showFilters, setShowFilters] = useState(false);

    const filteredProperties = useMemo(() => {
        let result = allProperties.filter((p) => {
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
    }, [filters, sortBy]);

    const formatPrice = (price: number) => {
        if (language === 'ar') {
            return `${(price / 1000000).toFixed(1)} مليون ج.م`;
        }
        return `EGP ${(price / 1000000).toFixed(1)}M`;
    };

    return (
        <main className="min-h-screen bg-[var(--color-background)]">
            <Navigation />

            {/* Page Header */}
            <div className="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <h1 className="text-h1 text-[var(--color-text-primary)] mb-2">
                        {t('nav.properties')}
                    </h1>
                    <p className="text-[var(--color-text-secondary)]">
                        {language === 'ar'
                            ? `${filteredProperties.length} عقار متاح`
                            : `${filteredProperties.length} properties available`
                        }
                    </p>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                            {language === 'ar' ? 'الفلاتر' : 'Filters'}
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
                                <option value="date">{language === 'ar' ? 'الأحدث' : 'Newest'}</option>
                                <option value="price-asc">{language === 'ar' ? 'السعر: من الأقل' : 'Price: Low to High'}</option>
                                <option value="price-desc">{language === 'ar' ? 'السعر: من الأعلى' : 'Price: High to Low'}</option>
                            </select>

                            {/* View Toggle */}
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
                        </div>

                        {/* Properties Grid */}
                        {viewMode === 'grid' ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                                {filteredProperties.map((property, index) => (
                                    <motion.div
                                        key={property.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ duration: 0.4, delay: index * 0.05 }}
                                        className="group relative rounded-2xl overflow-hidden bg-[var(--color-surface)] border border-[var(--color-border)] card-hover"
                                    >
                                        {/* Image */}
                                        <div className="relative h-52 overflow-hidden">
                                            <img
                                                src={property.image}
                                                alt={language === 'ar' ? property.titleAr : property.title}
                                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

                                            <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-500/90 backdrop-blur-sm text-white text-xs font-semibold">
                                                <Sparkles className="w-3.5 h-3.5" />
                                                AI Verified
                                            </div>

                                            <button className="absolute top-4 right-4 w-9 h-9 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/40 transition-colors">
                                                <Heart className="w-5 h-5 text-white" />
                                            </button>

                                            <div className="absolute bottom-4 left-4">
                                                <div className="text-xl font-bold text-white">
                                                    {formatPrice(property.price)}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <div className="p-5">
                                            <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-2 line-clamp-1">
                                                {language === 'ar' ? property.titleAr : property.title}
                                            </h3>

                                            <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)] text-sm mb-4">
                                                <MapPin className="w-4 h-4 text-[var(--color-primary)]" />
                                                {language === 'ar' ? property.locationAr : property.location}
                                            </div>

                                            <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                                                {property.bedrooms > 0 && (
                                                    <div className="flex items-center gap-1.5">
                                                        <Bed className="w-4 h-4" />
                                                        {property.bedrooms}
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-1.5">
                                                    <Bath className="w-4 h-4" />
                                                    {property.bathrooms}
                                                </div>
                                                <div className="flex items-center gap-1.5">
                                                    <Maximize className="w-4 h-4" />
                                                    {property.area} {language === 'ar' ? 'م²' : 'sqm'}
                                                </div>
                                            </div>

                                            <Link
                                                href={`/property/${property.id}`}
                                                className="mt-4 w-full py-2.5 rounded-lg bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold text-sm text-center block hover:bg-[var(--color-primary)] hover:text-white transition-colors"
                                            >
                                                {t('property.viewDetails')}
                                            </Link>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        ) : (
                            <div className="h-[600px] rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
                                <div className="text-center text-[var(--color-text-muted)]">
                                    <Map className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                    <p>{language === 'ar' ? 'عرض الخريطة قريباً' : 'Map view coming soon'}</p>
                                </div>
                            </div>
                        )}

                        {/* Empty State */}
                        {filteredProperties.length === 0 && (
                            <div className="text-center py-16">
                                <div className="text-6xl mb-4">🏠</div>
                                <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
                                    {language === 'ar' ? 'لا توجد عقارات' : 'No properties found'}
                                </h3>
                                <p className="text-[var(--color-text-secondary)]">
                                    {language === 'ar' ? 'جرب تعديل الفلاتر' : 'Try adjusting your filters'}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
