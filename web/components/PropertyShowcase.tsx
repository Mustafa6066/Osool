"use client";

import { useState, useEffect } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { MapPin, Bed, Bath, Maximize, Sparkles, Heart } from 'lucide-react';

// Sample featured properties - In production, this would come from API
const sampleProperties = [
    {
        id: '1',
        title: 'Luxury Villa in New Cairo',
        titleAr: 'فيلا فاخرة في القاهرة الجديدة',
        location: 'New Cairo, 5th Settlement',
        locationAr: 'القاهرة الجديدة، التجمع الخامس',
        price: 15000000,
        aiEstimate: 14800000,
        bedrooms: 5,
        bathrooms: 4,
        area: 450,
        image: 'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600&h=400&fit=crop',
        type: 'villa',
    },
    {
        id: '2',
        title: 'Modern Apartment in Zamalek',
        titleAr: 'شقة حديثة في الزمالك',
        location: 'Zamalek, Cairo',
        locationAr: 'الزمالك، القاهرة',
        price: 5500000,
        aiEstimate: 5650000,
        bedrooms: 3,
        bathrooms: 2,
        area: 180,
        image: 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600&h=400&fit=crop',
        type: 'apartment',
    },
    {
        id: '3',
        title: 'Beachfront Chalet in Ain Sokhna',
        titleAr: 'شاليه على البحر في العين السخنة',
        location: 'Ain Sokhna, Red Sea',
        locationAr: 'العين السخنة، البحر الأحمر',
        price: 3200000,
        aiEstimate: 3100000,
        bedrooms: 2,
        bathrooms: 2,
        area: 120,
        image: 'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=600&h=400&fit=crop',
        type: 'chalet',
    },
    {
        id: '4',
        title: 'Commercial Office in Smart Village',
        titleAr: 'مكتب تجاري في القرية الذكية',
        location: 'Smart Village, 6th October',
        locationAr: 'القرية الذكية، 6 أكتوبر',
        price: 8500000,
        aiEstimate: 8750000,
        bedrooms: 0,
        bathrooms: 2,
        area: 250,
        image: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=400&fit=crop',
        type: 'commercial',
    },
    {
        id: '5',
        title: 'Garden Duplex in Maadi',
        titleAr: 'دوبلكس بحديقة في المعادي',
        location: 'Maadi, Cairo',
        locationAr: 'المعادي، القاهرة',
        price: 7200000,
        aiEstimate: 7100000,
        bedrooms: 4,
        bathrooms: 3,
        area: 320,
        image: 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600&h=400&fit=crop',
        type: 'duplex',
    },
    {
        id: '6',
        title: 'Penthouse in Sheikh Zayed',
        titleAr: 'بنتهاوس في الشيخ زايد',
        location: 'Sheikh Zayed City',
        locationAr: 'مدينة الشيخ زايد',
        price: 12000000,
        aiEstimate: 11800000,
        bedrooms: 4,
        bathrooms: 3,
        area: 400,
        image: 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&h=400&fit=crop',
        type: 'penthouse',
    },
];

interface PropertyCardProps {
    property: typeof sampleProperties[0];
    language: 'en' | 'ar';
}

function PropertyCard({ property, language }: PropertyCardProps) {
    const [isLiked, setIsLiked] = useState(false);

    const formatPrice = (price: number) => {
        if (language === 'ar') {
            return `${(price / 1000000).toFixed(1)} مليون ج.م`;
        }
        return `EGP ${(price / 1000000).toFixed(1)}M`;
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="group relative rounded-2xl overflow-hidden bg-[var(--color-surface)] border border-[var(--color-border)] card-hover"
        >
            {/* Image Container */}
            <div className="relative h-56 overflow-hidden">
                <img
                    src={property.image}
                    alt={language === 'ar' ? property.titleAr : property.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />
                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />

                {/* AI Badge */}
                <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-500/90 backdrop-blur-sm text-white text-xs font-semibold">
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Verified
                </div>

                {/* Like Button */}
                <button
                    onClick={() => setIsLiked(!isLiked)}
                    className="absolute top-4 right-4 w-9 h-9 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/40 transition-colors"
                >
                    <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500 text-red-500' : 'text-white'}`} />
                </button>

                {/* Price */}
                <div className="absolute bottom-4 left-4">
                    <div className="text-2xl font-bold text-white">
                        {formatPrice(property.price)}
                    </div>
                    <div className="text-xs text-white/80 flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        AI: {formatPrice(property.aiEstimate)}
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

                {/* Features */}
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

                {/* View Details Button */}
                <Link
                    href={`/property/${property.id}`}
                    className="mt-4 w-full py-2.5 rounded-lg bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-semibold text-sm text-center block hover:bg-[var(--color-primary)] hover:text-white transition-colors"
                >
                    {language === 'ar' ? 'عرض التفاصيل' : 'View Details'}
                </Link>
            </div>
        </motion.div>
    );
}

export default function PropertyShowcase() {
    const { t, language } = useLanguage();
    const [filter, setFilter] = useState('all');

    const filteredProperties = filter === 'all'
        ? sampleProperties
        : sampleProperties.filter(p => p.type === filter);

    const filters = [
        { key: 'all', label: language === 'ar' ? 'الكل' : 'All' },
        { key: 'villa', label: language === 'ar' ? 'فيلا' : 'Villa' },
        { key: 'apartment', label: language === 'ar' ? 'شقة' : 'Apartment' },
        { key: 'commercial', label: language === 'ar' ? 'تجاري' : 'Commercial' },
    ];

    return (
        <section className="section-padding bg-[var(--color-surface)]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Section Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mb-12"
                >
                    <h2 className="text-h1 text-[var(--color-text-primary)] mb-4">
                        {t('showcase.title')}
                    </h2>
                    <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
                        {t('showcase.subtitle')}
                    </p>
                </motion.div>

                {/* Filters */}
                <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
                    {filters.map((f) => (
                        <button
                            key={f.key}
                            onClick={() => setFilter(f.key)}
                            className={`px-5 py-2.5 rounded-full font-medium text-sm transition-all
                ${filter === f.key
                                    ? 'bg-[var(--color-primary)] text-white shadow-lg shadow-[var(--color-primary)]/30'
                                    : 'bg-[var(--color-background)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:border-[var(--color-primary)]'
                                }`}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>

                {/* Properties Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
                    {filteredProperties.map((property) => (
                        <PropertyCard key={property.id} property={property} language={language} />
                    ))}
                </div>

                {/* View All Button */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="text-center mt-12"
                >
                    <Link
                        href="/properties"
                        className="btn-primary inline-flex items-center gap-2 text-lg px-8 py-4"
                    >
                        {t('showcase.viewAll')}
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                        </svg>
                    </Link>
                </motion.div>
            </div>
        </section>
    );
}
