"use client";

import { useParams } from 'next/navigation';
import { useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
    MapPin, Bed, Bath, Maximize, Sparkles, Heart, Share2,
    ChevronLeft, ChevronRight, Shield, TrendingUp, Calendar,
    Phone, Mail, Building
} from 'lucide-react';

// Sample property data - in production, fetch from API
const propertyData: Record<string, {
    id: string;
    title: string;
    titleAr: string;
    location: string;
    locationAr: string;
    description: string;
    descriptionAr: string;
    price: number;
    aiEstimate: number;
    bedrooms: number;
    bathrooms: number;
    area: number;
    images: string[];
    type: string;
    features: string[];
    featuresAr: string[];
    yearBuilt: number;
    verified: boolean;
}> = {
    '1': {
        id: '1',
        title: 'Luxury Villa in New Cairo',
        titleAr: 'فيلا فاخرة في القاهرة الجديدة',
        location: 'New Cairo, 5th Settlement',
        locationAr: 'القاهرة الجديدة، التجمع الخامس',
        description: 'Stunning luxury villa with private garden and pool. Features premium finishes, smart home system, and panoramic views. Located in the prestigious 5th Settlement area with easy access to major roads and amenities.',
        descriptionAr: 'فيلا فاخرة مذهلة مع حديقة خاصة ومسبح. تتميز بتشطيبات فاخرة ونظام منزل ذكي وإطلالات بانورامية. تقع في منطقة التجمع الخامس الراقية مع سهولة الوصول إلى الطرق الرئيسية والمرافق.',
        price: 15000000,
        aiEstimate: 14800000,
        bedrooms: 5,
        bathrooms: 4,
        area: 450,
        images: [
            'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&h=800&fit=crop',
        ],
        type: 'villa',
        features: ['Swimming Pool', 'Private Garden', 'Smart Home', 'Security System', 'Garage', 'Gym'],
        featuresAr: ['مسبح', 'حديقة خاصة', 'منزل ذكي', 'نظام أمان', 'جراج', 'صالة رياضية'],
        yearBuilt: 2022,
        verified: true,
    },
    '2': {
        id: '2',
        title: 'Modern Apartment in Zamalek',
        titleAr: 'شقة حديثة في الزمالك',
        location: 'Zamalek, Cairo',
        locationAr: 'الزمالك، القاهرة',
        description: 'Elegant modern apartment in the heart of Zamalek with Nile views. High ceilings, parquet floors, and contemporary design throughout.',
        descriptionAr: 'شقة عصرية أنيقة في قلب الزمالك مع إطلالة على النيل. أسقف عالية وأرضيات باركيه وتصميم معاصر.',
        price: 5500000,
        aiEstimate: 5650000,
        bedrooms: 3,
        bathrooms: 2,
        area: 180,
        images: [
            'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200&h=800&fit=crop',
        ],
        type: 'apartment',
        features: ['Nile View', 'Balcony', 'Doorman', 'Central AC', 'Parking'],
        featuresAr: ['إطلالة على النيل', 'بلكونة', 'بواب', 'تكييف مركزي', 'موقف سيارات'],
        yearBuilt: 2020,
        verified: true,
    },
};

// Default property for IDs not in our sample data
const defaultProperty = {
    id: '0',
    title: 'Property Details',
    titleAr: 'تفاصيل العقار',
    location: 'Cairo, Egypt',
    locationAr: 'القاهرة، مصر',
    description: 'Property details will be loaded from the database.',
    descriptionAr: 'سيتم تحميل تفاصيل العقار من قاعدة البيانات.',
    price: 5000000,
    aiEstimate: 5100000,
    bedrooms: 3,
    bathrooms: 2,
    area: 200,
    images: ['https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200&h=800&fit=crop'],
    type: 'apartment',
    features: ['Air Conditioning', 'Parking', 'Security'],
    featuresAr: ['تكييف', 'موقف سيارات', 'أمن'],
    yearBuilt: 2021,
    verified: false,
};

export default function PropertyDetailsPage() {
    const params = useParams();
    const { language, t } = useLanguage();
    const [currentImage, setCurrentImage] = useState(0);
    const [isLiked, setIsLiked] = useState(false);

    const propertyId = params.id as string;
    const property = propertyData[propertyId] || defaultProperty;

    const formatPrice = (price: number) => {
        if (language === 'ar') {
            return `${(price / 1000000).toFixed(2)} مليون ج.م`;
        }
        return `EGP ${(price / 1000000).toFixed(2)}M`;
    };

    const priceDiff = property.aiEstimate - property.price;
    const priceDiffPercent = ((priceDiff / property.price) * 100).toFixed(1);

    return (
        <main className="min-h-screen bg-[var(--color-background)]">
            <Navigation />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Breadcrumb */}
                <nav className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-6">
                    <Link href="/" className="hover:text-[var(--color-primary)]">
                        {t('nav.home')}
                    </Link>
                    <span>/</span>
                    <Link href="/properties" className="hover:text-[var(--color-primary)]">
                        {t('nav.properties')}
                    </Link>
                    <span>/</span>
                    <span className="text-[var(--color-text-primary)]">
                        {language === 'ar' ? property.titleAr : property.title}
                    </span>
                </nav>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Image Gallery */}
                        <div className="relative rounded-2xl overflow-hidden">
                            <motion.img
                                key={currentImage}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                src={property.images[currentImage]}
                                alt={language === 'ar' ? property.titleAr : property.title}
                                className="w-full h-96 lg:h-[500px] object-cover"
                            />

                            {/* Gallery Controls */}
                            {property.images.length > 1 && (
                                <>
                                    <button
                                        onClick={() => setCurrentImage(prev => prev === 0 ? property.images.length - 1 : prev - 1)}
                                        className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition-colors"
                                    >
                                        <ChevronLeft className="w-6 h-6" />
                                    </button>
                                    <button
                                        onClick={() => setCurrentImage(prev => prev === property.images.length - 1 ? 0 : prev + 1)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 text-white flex items-center justify-center hover:bg-black/70 transition-colors"
                                    >
                                        <ChevronRight className="w-6 h-6" />
                                    </button>
                                </>
                            )}

                            {/* Image Counter */}
                            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-black/50 text-white text-sm">
                                {currentImage + 1} / {property.images.length}
                            </div>

                            {/* Action Buttons */}
                            <div className="absolute top-4 right-4 flex gap-2">
                                <button
                                    onClick={() => setIsLiked(!isLiked)}
                                    className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition-colors"
                                >
                                    <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500 text-red-500' : 'text-gray-600'}`} />
                                </button>
                                <button className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition-colors">
                                    <Share2 className="w-5 h-5 text-gray-600" />
                                </button>
                            </div>

                            {/* Verified Badge */}
                            {property.verified && (
                                <div className="absolute top-4 left-4 flex items-center gap-2 px-4 py-2 rounded-full bg-green-500 text-white text-sm font-semibold">
                                    <Shield className="w-4 h-4" />
                                    {t('property.verified')}
                                </div>
                            )}
                        </div>

                        {/* Thumbnails */}
                        {property.images.length > 1 && (
                            <div className="flex gap-3 overflow-x-auto pb-2">
                                {property.images.map((img, index) => (
                                    <button
                                        key={index}
                                        onClick={() => setCurrentImage(index)}
                                        className={`flex-shrink-0 w-24 h-16 rounded-lg overflow-hidden border-2 transition-all
                      ${currentImage === index ? 'border-[var(--color-primary)]' : 'border-transparent opacity-60 hover:opacity-100'}`}
                                    >
                                        <img src={img} alt="" className="w-full h-full object-cover" />
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Property Info */}
                        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6">
                            <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-3">
                                {language === 'ar' ? property.titleAr : property.title}
                            </h1>

                            <div className="flex items-center gap-2 text-[var(--color-text-secondary)] mb-6">
                                <MapPin className="w-5 h-5 text-[var(--color-primary)]" />
                                {language === 'ar' ? property.locationAr : property.location}
                            </div>

                            {/* Key Features */}
                            <div className="flex flex-wrap gap-6 pb-6 border-b border-[var(--color-border)]">
                                {property.bedrooms > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Bed className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {property.bedrooms} {t('property.bedrooms')}
                                        </span>
                                    </div>
                                )}
                                <div className="flex items-center gap-2">
                                    <Bath className="w-5 h-5 text-[var(--color-primary)]" />
                                    <span className="text-[var(--color-text-primary)] font-medium">
                                        {property.bathrooms} {t('property.bathrooms')}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Maximize className="w-5 h-5 text-[var(--color-primary)]" />
                                    <span className="text-[var(--color-text-primary)] font-medium">
                                        {property.area} {t('common.sqm')}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Calendar className="w-5 h-5 text-[var(--color-primary)]" />
                                    <span className="text-[var(--color-text-primary)] font-medium">
                                        {property.yearBuilt}
                                    </span>
                                </div>
                            </div>

                            {/* Description */}
                            <div className="py-6 border-b border-[var(--color-border)]">
                                <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-3">
                                    {language === 'ar' ? 'الوصف' : 'Description'}
                                </h3>
                                <p className="text-[var(--color-text-secondary)] leading-relaxed">
                                    {language === 'ar' ? property.descriptionAr : property.description}
                                </p>
                            </div>

                            {/* Features */}
                            <div className="pt-6">
                                <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">
                                    {language === 'ar' ? 'المميزات' : 'Features'}
                                </h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {(language === 'ar' ? property.featuresAr : property.features).map((feature, index) => (
                                        <div key={index} className="flex items-center gap-2 text-[var(--color-text-secondary)]">
                                            <div className="w-2 h-2 rounded-full bg-[var(--color-primary)]" />
                                            {feature}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Price Card */}
                        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 sticky top-24">
                            <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-2">
                                {formatPrice(property.price)}
                            </div>

                            {/* AI Estimate */}
                            <div className="flex items-center gap-2 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 mb-6">
                                <Sparkles className="w-5 h-5 text-purple-400" />
                                <div>
                                    <div className="text-sm text-purple-400 font-medium">{t('property.aiEstimate')}</div>
                                    <div className="text-lg font-bold text-purple-300">{formatPrice(property.aiEstimate)}</div>
                                </div>
                                <div className={`ml-auto text-sm font-semibold ${priceDiff > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    <TrendingUp className="w-4 h-4 inline mr-1" />
                                    {priceDiff > 0 ? '+' : ''}{priceDiffPercent}%
                                </div>
                            </div>

                            {/* Contact Buttons */}
                            <div className="space-y-3">
                                <button className="w-full btn-primary flex items-center justify-center gap-2">
                                    <Phone className="w-5 h-5" />
                                    {t('property.contactSeller')}
                                </button>
                                <button className="w-full btn-secondary flex items-center justify-center gap-2">
                                    <Mail className="w-5 h-5" />
                                    {language === 'ar' ? 'إرسال رسالة' : 'Send Message'}
                                </button>
                            </div>

                            {/* Agent Info */}
                            <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center text-white font-bold">
                                        <Building className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <div className="font-semibold text-[var(--color-text-primary)]">Osool Properties</div>
                                        <div className="text-sm text-[var(--color-text-muted)]">Verified Agent</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <Footer />
        </main>
    );
}
