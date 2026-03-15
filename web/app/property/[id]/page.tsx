"use client";

import { useParams } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/contexts/AuthContext';
import AppShell from '@/components/nav/AppShell';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
    MapPin, Bed, Bath, Maximize, Sparkles, Heart, Share2,
    Shield, TrendingUp, Calendar, Clock, CreditCard,
    Phone, Building, ExternalLink, Tag, Ruler, Home,
    ArrowLeft, Loader2, AlertCircle, Banknote, Percent
} from 'lucide-react';
import { toggleFavorite } from '@/lib/gamification';
import { buildAdvisorPrompt, formatCompactPrice, propertyBrief } from '@/lib/decision-support';

// ── Types ────────────────────────────────────────────────────
interface PaymentPlan {
    downPayment: number;
    installmentYears: number;
    monthlyInstallment: number;
}

interface RawProperty {
    id: string;
    title: string;
    type: string;
    location: string;
    compound: string;
    developer: string;
    area: number;
    size: number;
    sqm: number;
    bua: number;
    bedrooms: number;
    bathrooms: number;
    price: number;
    pricePerSqm: number;
    deliveryDate: string;
    paymentPlan: PaymentPlan;
    image: string;
    nawyUrl: string;
    saleType: string;
    description: string;
    ai_valuation?: number;
    aiEstimate?: number;
}

// ── Image fallbacks ──────────────────────────────────────────
const FALLBACK_IMAGES = [
    'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200&h=800&fit=crop',
];

// ── Arabic location map ──────────────────────────────────────
const LOCATION_AR: Record<string, string> = {
    'new cairo': 'القاهرة الجديدة',
    'sheikh zayed': 'الشيخ زايد',
    '6th october': 'السادس من أكتوبر',
    'new capital': 'العاصمة الإدارية',
    'mostakbal city': 'مدينة المستقبل',
    'ain sokhna': 'العين السخنة',
    'north coast': 'الساحل الشمالي',
    'madinaty': 'مدينتي',
    'rehab': 'الرحاب',
    'maadi': 'المعادي',
    'zamalek': 'الزمالك',
    'heliopolis': 'مصر الجديدة',
    'golden square': 'الحي الذهبي',
};

const TYPE_AR: Record<string, string> = {
    'apartment': 'شقة',
    'villa': 'فيلا',
    'townhouse': 'تاون هاوس',
    'twin house': 'توين هاوس',
    'duplex': 'دوبلكس',
    'penthouse': 'بنتهاوس',
    'studio': 'ستوديو',
    'chalet': 'شاليه',
    'iVilla': 'آي فيلا',
};

function getLocationAr(location: string): string {
    const key = location.toLowerCase().trim();
    return LOCATION_AR[key] || location;
}

function getTypeAr(type: string): string {
    const key = type.toLowerCase().trim();
    return TYPE_AR[key] || type;
}

export default function PropertyDetailsPage() {
    const params = useParams();
    const { language, t } = useLanguage();
    const { isAuthenticated } = useAuth();
    const [property, setProperty] = useState<RawProperty | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isLiked, setIsLiked] = useState(false);
    const [imgError, setImgError] = useState(false);
    const [shareToast, setShareToast] = useState(false);

    const propertyId = params.id as string;

    // ── Fetch real property data from data.js ─────────────────
    const fetchProperty = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const res = await fetch('/assets/js/data.js');
            const txt = await res.text();
            const start = txt.indexOf('{');
            const end = txt.lastIndexOf('}');
            if (start === -1 || end === -1) throw new Error('Data parse error');

            const raw = JSON.parse(txt.substring(start, end + 1));
            const props = (raw.properties || []) as RawProperty[];
            const found = props.find(p => String(p.id) === propertyId);

            if (!found) {
                setError(language === 'ar' ? 'لم يتم العثور على العقار' : 'Property not found');
                return;
            }
            setProperty(found);
        } catch {
            setError(language === 'ar' ? 'فشل تحميل بيانات العقار' : 'Failed to load property data');
        } finally {
            setLoading(false);
        }
    }, [propertyId, language]);

    useEffect(() => {
        fetchProperty();
    }, [fetchProperty]);

    // ── Handlers ──────────────────────────────────────────────
    const handleToggleFavorite = async () => {
        if (!isAuthenticated) return;
        setIsLiked(!isLiked);
        try {
            await toggleFavorite(Number(propertyId) || 0);
        } catch {
            setIsLiked(prev => !prev);
        }
    };

    const handleShare = async () => {
        const url = window.location.href;
        const text = property ? `${property.title} — ${formatPrice(property.price)}` : 'Osool Property';
        if (navigator.share) {
            try { await navigator.share({ title: 'Osool', text, url }); } catch { /* cancelled */ }
        } else {
            await navigator.clipboard.writeText(url);
            setShareToast(true);
            setTimeout(() => setShareToast(false), 2000);
        }
    };

    const handleWhatsAppShare = () => {
        if (!property) return;
        const text = encodeURIComponent(
            `🏠 ${property.title}\n📍 ${property.compound}, ${property.location}\n💰 ${formatPrice(property.price)}\n🔗 ${window.location.href}`
        );
        window.open(`https://wa.me/?text=${text}`, '_blank');
    };

    // ── Formatters ────────────────────────────────────────────
    const formatPrice = (price: number) => {
        if (price >= 1_000_000) {
            const millions = price / 1_000_000;
            return language === 'ar'
                ? `${millions.toFixed(2)} مليون ج.م`
                : `EGP ${millions.toFixed(2)}M`;
        }
        return language === 'ar'
            ? `${price.toLocaleString('ar-EG')} ج.م`
            : `EGP ${price.toLocaleString()}`;
    };

    const formatInstallment = (amount: number) => {
        return language === 'ar'
            ? `${amount.toLocaleString('ar-EG')} ج.م/شهر`
            : `EGP ${amount.toLocaleString()}/mo`;
    };

    const getImage = () => {
        if (imgError || !property?.image) {
            const idx = propertyId.charCodeAt(propertyId.length - 1) % FALLBACK_IMAGES.length;
            return FALLBACK_IMAGES[idx];
        }
        return property.image;
    };

    // AI estimate: use backend value if available, otherwise don't show
    const aiEstimate = property ? (property.ai_valuation || property.aiEstimate || null) : null;
    const priceDiff = (property && aiEstimate) ? aiEstimate - property.price : 0;
    const priceDiffPercent = (property && aiEstimate && property.price) ? ((priceDiff / property.price) * 100).toFixed(1) : '0';

    const area = property ? (property.area || property.bua || property.size || property.sqm || 0) : 0;
    const decision = property ? propertyBrief({
        title: property.title,
        location: property.location,
        price: property.price,
        aiEstimate,
        bedrooms: property.bedrooms,
        bathrooms: property.bathrooms,
        area,
        type: property.type,
        developer: property.developer,
        saleType: property.saleType,
        pricePerSqm: property.pricePerSqm,
        paymentPlan: property.paymentPlan,
    }) : null;
    const advisorPrompt = property ? buildAdvisorPrompt({
        title: property.title,
        location: property.location,
        price: property.price,
        aiEstimate,
        bedrooms: property.bedrooms,
        bathrooms: property.bathrooms,
        area,
        type: property.type,
        developer: property.developer,
        saleType: property.saleType,
        pricePerSqm: property.pricePerSqm,
        paymentPlan: property.paymentPlan,
    }) : '';

    // ── Loading state ─────────────────────────────────────────
    if (loading) {
        return (
            <AppShell>
                <main className="h-full flex items-center justify-center bg-[var(--color-background)]">
                    <div className="flex flex-col items-center gap-4">
                        <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
                        <p className="text-[var(--color-text-muted)]">{t('common.loading')}</p>
                    </div>
                </main>
            </AppShell>
        );
    }

    // ── Error / not found state ───────────────────────────────
    if (error || !property) {
        return (
            <AppShell>
                <main className="h-full flex items-center justify-center bg-[var(--color-background)]">
                    <div className="flex flex-col items-center gap-4 text-center px-6">
                        <AlertCircle className="w-12 h-12 text-red-400" />
                        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
                            {error || (language === 'ar' ? 'لم يتم العثور على العقار' : 'Property not found')}
                        </h2>
                        <Link
                            href="/properties"
                            className="flex items-center gap-2 text-[var(--color-primary)] hover:underline"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            {language === 'ar' ? 'العودة للعقارات' : 'Back to Properties'}
                        </Link>
                    </div>
                </main>
            </AppShell>
        );
    }

    return (
        <AppShell>
        <main className="h-full overflow-y-auto bg-[var(--color-background)]">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {/* Breadcrumb */}
                <nav className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-6 flex-wrap">
                    <Link href="/" className="hover:text-[var(--color-primary)]">{t('nav.home')}</Link>
                    <span>/</span>
                    <Link href="/properties" className="hover:text-[var(--color-primary)]">{t('nav.properties')}</Link>
                    <span>/</span>
                    <span className="text-[var(--color-text-primary)] truncate max-w-[200px]">{property.title}</span>
                </nav>

                {decision && (
                    <section className="mb-8 grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
                        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
                            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
                                {decision.confidenceLabel}
                            </div>
                            <h1 className="mt-4 text-4xl font-semibold tracking-tight text-[var(--color-text-primary)]">{property.title}</h1>
                            <p className="mt-3 max-w-3xl text-base leading-7 text-[var(--color-text-secondary)]">
                                {decision.thesis}
                            </p>
                            <div className="mt-5 flex flex-wrap gap-3 text-sm text-[var(--color-text-muted)]">
                                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">
                                    {formatCompactPrice(property.price)}
                                </span>
                                {property.pricePerSqm > 0 && (
                                    <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">
                                        {Math.round(property.pricePerSqm).toLocaleString()} EGP/m²
                                    </span>
                                )}
                                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">
                                    {decision.priceSignal}
                                </span>
                            </div>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Best for</div>
                                <div className="mt-2 text-base font-semibold text-[var(--color-text-primary)]">{decision.bestFor}</div>
                            </div>
                            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Main watch-out</div>
                                <div className="mt-2 text-base font-semibold text-[var(--color-text-primary)]">{decision.risk}</div>
                            </div>
                        </div>
                    </section>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* ═══ Main Content ═══ */}
                    <div className="lg:col-span-2 space-y-6">

                        {/* Hero Image */}
                        <div className="relative rounded-2xl overflow-hidden">
                            <motion.img
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                src={getImage()}
                                alt={property.title}
                                onError={() => setImgError(true)}
                                className="w-full h-72 sm:h-96 lg:h-[500px] object-cover"
                            />

                            {/* Action Buttons */}
                            <div className="absolute top-4 right-4 flex gap-2">
                                <button
                                    onClick={handleToggleFavorite}
                                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                                        isLiked ? 'bg-red-500 hover:bg-red-600' : 'bg-white/90 hover:bg-white'
                                    }`}
                                >
                                    <Heart className={`w-5 h-5 ${isLiked ? 'fill-white text-white' : 'text-gray-600'}`} />
                                </button>
                                <button
                                    onClick={handleShare}
                                    className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition-colors"
                                >
                                    <Share2 className="w-5 h-5 text-gray-600" />
                                </button>
                            </div>

                            {/* Sale Type Badge */}
                            {property.saleType && (
                                <div className={`absolute top-4 left-4 flex items-center gap-2 px-4 py-2 rounded-full text-white text-sm font-semibold ${
                                    property.saleType.toLowerCase() === 'resale'
                                        ? 'bg-amber-500'
                                        : 'bg-green-500'
                                }`}>
                                    <Tag className="w-4 h-4" />
                                    {property.saleType.toLowerCase() === 'resale'
                                        ? (language === 'ar' ? 'إعادة بيع' : 'Resale')
                                        : (language === 'ar' ? 'من المطور' : 'Developer')
                                    }
                                </div>
                            )}

                            {/* Share Toast */}
                            <AnimatePresence>
                                {shareToast && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 20 }}
                                        className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-green-500 text-white text-sm font-medium"
                                    >
                                        {language === 'ar' ? 'تم نسخ الرابط ✓' : 'Link copied ✓'}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* ── Property Info Card ───────────────────── */}
                        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6">
                            <div className="flex items-start justify-between gap-4 mb-3">
                                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                                    {property.title}
                                </h1>
                                <span className="shrink-0 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                                    {language === 'ar' ? getTypeAr(property.type) : property.type}
                                </span>
                            </div>

                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[var(--color-text-secondary)] mb-6">
                                <span className="flex items-center gap-1.5">
                                    <MapPin className="w-4 h-4 text-[var(--color-primary)]" />
                                    {language === 'ar' ? getLocationAr(property.location) : property.location}
                                </span>
                                {property.compound && (
                                    <span className="flex items-center gap-1.5">
                                        <Home className="w-4 h-4 text-[var(--color-primary)]" />
                                        {property.compound}
                                    </span>
                                )}
                                {property.developer && property.developer !== 'Developer' && (
                                    <span className="flex items-center gap-1.5">
                                        <Building className="w-4 h-4 text-[var(--color-primary)]" />
                                        {property.developer}
                                    </span>
                                )}
                            </div>

                            {decision && (
                                <div className="mb-6 grid gap-3 sm:grid-cols-2">
                                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--color-text-muted)]">Decision angle</div>
                                        <div className="mt-2 text-sm font-semibold text-[var(--color-text-primary)]">{decision.thesis}</div>
                                    </div>
                                    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                        <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--color-text-muted)]">Why keep it on the board</div>
                                        <div className="mt-2 text-sm font-semibold text-[var(--color-text-primary)]">{decision.bestFor}</div>
                                    </div>
                                </div>
                            )}

                            {/* Key Specs */}
                            <div className="flex flex-wrap gap-6 pb-6 border-b border-[var(--color-border)]">
                                {property.bedrooms > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Bed className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {property.bedrooms} {t('property.bedrooms')}
                                        </span>
                                    </div>
                                )}
                                {property.bathrooms > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Bath className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {property.bathrooms} {t('property.bathrooms')}
                                        </span>
                                    </div>
                                )}
                                {area > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Maximize className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {area} {t('common.sqm')}
                                        </span>
                                    </div>
                                )}
                                {property.deliveryDate && (
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {language === 'ar' ? `تسليم ${property.deliveryDate}` : `Delivery ${property.deliveryDate}`}
                                        </span>
                                    </div>
                                )}
                                {property.pricePerSqm > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Ruler className="w-5 h-5 text-[var(--color-primary)]" />
                                        <span className="text-[var(--color-text-primary)] font-medium">
                                            {property.pricePerSqm.toLocaleString()} {language === 'ar' ? 'ج.م/م²' : 'EGP/sqm'}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Description */}
                            {property.description && (
                                <div className="py-6 border-b border-[var(--color-border)]">
                                    <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-3">
                                        {language === 'ar' ? 'الوصف' : 'Description'}
                                    </h3>
                                    <p className="text-[var(--color-text-secondary)] leading-relaxed">
                                        {property.description}
                                    </p>
                                </div>
                            )}

                            {/* Nawy Link */}
                            {property.nawyUrl && (
                                <div className="pt-6">
                                    <a
                                        href={property.nawyUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-2 text-[var(--color-primary)] hover:underline text-sm"
                                    >
                                        <ExternalLink className="w-4 h-4" />
                                        {language === 'ar' ? 'عرض على Nawy' : 'View on Nawy'}
                                    </a>
                                </div>
                            )}
                        </div>

                        {/* ── Payment Plan Card ────────────────────── */}
                        {property.paymentPlan && (
                            <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6">
                                <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-5 flex items-center gap-2">
                                    <CreditCard className="w-5 h-5 text-[var(--color-primary)]" />
                                    {language === 'ar' ? 'خطة الدفع' : 'Payment Plan'}
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                    {/* Down Payment */}
                                    <div className="rounded-xl bg-[var(--color-background)] p-4 text-center">
                                        <Percent className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-[var(--color-text-primary)]">
                                            {property.paymentPlan.downPayment}%
                                        </div>
                                        <div className="text-xs text-[var(--color-text-muted)] mt-1">
                                            {language === 'ar' ? 'مقدم' : 'Down Payment'}
                                        </div>
                                        <div className="text-sm text-[var(--color-text-secondary)] mt-1 font-medium">
                                            {formatPrice(Math.round(property.price * property.paymentPlan.downPayment / 100))}
                                        </div>
                                    </div>

                                    {/* Installment Years */}
                                    <div className="rounded-xl bg-[var(--color-background)] p-4 text-center">
                                        <Clock className="w-6 h-6 text-green-400 mx-auto mb-2" />
                                        <div className="text-2xl font-bold text-[var(--color-text-primary)]">
                                            {property.paymentPlan.installmentYears}
                                        </div>
                                        <div className="text-xs text-[var(--color-text-muted)] mt-1">
                                            {language === 'ar' ? 'سنوات التقسيط' : 'Years'}
                                        </div>
                                    </div>

                                    {/* Monthly Installment */}
                                    <div className="rounded-xl bg-[var(--color-background)] p-4 text-center">
                                        <Banknote className="w-6 h-6 text-amber-400 mx-auto mb-2" />
                                        <div className="text-xl font-bold text-[var(--color-text-primary)]">
                                            {formatInstallment(property.paymentPlan.monthlyInstallment)}
                                        </div>
                                        <div className="text-xs text-[var(--color-text-muted)] mt-1">
                                            {language === 'ar' ? 'القسط الشهري' : 'Monthly Installment'}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── WhatsApp Share ───────────────────────── */}
                        <button
                            onClick={handleWhatsAppShare}
                            className="w-full flex items-center justify-center gap-3 py-3.5 rounded-xl bg-[#25D366] hover:bg-[#20bd5a] text-white font-semibold transition-colors"
                        >
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                            {language === 'ar' ? 'شارك مع أهلك على واتساب' : 'Share with Family on WhatsApp'}
                        </button>
                    </div>

                    {/* ═══ Sidebar ═══ */}
                    <div className="space-y-6">
                        {/* Price Card */}
                        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-6 sticky top-24">
                            <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-1">
                                {formatPrice(property.price)}
                            </div>
                            {area > 0 && (
                                <div className="text-sm text-[var(--color-text-muted)] mb-4">
                                    {property.pricePerSqm.toLocaleString()} {language === 'ar' ? 'ج.م/م²' : 'EGP/sqm'}
                                </div>
                            )}

                            {decision && (
                                <div className="mb-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Decision summary</div>
                                    <div className="mt-2 text-sm font-semibold text-[var(--color-text-primary)]">{decision.confidenceLabel}</div>
                                    <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{decision.priceSignal}</div>
                                </div>
                            )}

                            {/* AI Estimate - only show if real valuation available */}
                            {aiEstimate && (
                            <div className="flex items-center gap-2 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 mb-6">
                                <Sparkles className="w-5 h-5 text-emerald-500" />
                                <div>
                                    <div className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">{t('property.aiEstimate')}</div>
                                    <div className="text-lg font-bold text-[var(--color-text-primary)]">{formatPrice(aiEstimate)}</div>
                                </div>
                                <div className={`ml-auto text-sm font-semibold ${priceDiff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                    <TrendingUp className="w-4 h-4 inline mr-1" />
                                    {priceDiff >= 0 ? '+' : ''}{priceDiffPercent}%
                                </div>
                            </div>
                            )}

                            {/* Quick Payment Summary */}
                            {property.paymentPlan && (
                                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 mb-6 text-sm">
                                    <div className="flex justify-between text-[var(--color-text-secondary)]">
                                        <span>{language === 'ar' ? 'مقدم' : 'Down'}</span>
                                        <span className="font-semibold text-[var(--color-text-primary)]">
                                            {formatPrice(Math.round(property.price * property.paymentPlan.downPayment / 100))}
                                        </span>
                                    </div>
                                    <div className="flex justify-between text-[var(--color-text-secondary)] mt-1.5">
                                        <span>{language === 'ar' ? 'قسط شهري' : 'Monthly'}</span>
                                        <span className="font-semibold text-[var(--color-text-primary)]">
                                            {formatInstallment(property.paymentPlan.monthlyInstallment)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between text-[var(--color-text-secondary)] mt-1.5">
                                        <span>{language === 'ar' ? 'مدة' : 'Duration'}</span>
                                        <span className="font-semibold text-[var(--color-text-primary)]">
                                            {property.paymentPlan.installmentYears} {language === 'ar' ? 'سنوات' : 'years'}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* Contact Buttons */}
                            <div className="space-y-3">
                                <button className="w-full btn-primary flex items-center justify-center gap-2">
                                    <Phone className="w-5 h-5" />
                                    {t('property.contactSeller')}
                                </button>
                                <Link
                                    href={`/chat?prompt=${encodeURIComponent(advisorPrompt)}&autostart=1`}
                                    className="w-full btn-secondary flex items-center justify-center gap-2"
                                >
                                    <Sparkles className="w-5 h-5" />
                                    {language === 'ar' ? 'اطلب تحليل هذا العقار من Osool' : 'Ask Osool to review this property'}
                                </Link>
                            </div>

                            {/* Developer Info */}
                            {property.developer && property.developer !== 'Developer' && (
                                <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
                                    <div className="flex items-center gap-3">
                                        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] flex items-center justify-center text-white font-bold">
                                            <Building className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <div className="font-semibold text-[var(--color-text-primary)]">{property.developer}</div>
                                            <div className="text-sm text-[var(--color-text-muted)]">
                                                {language === 'ar' ? 'المطور العقاري' : 'Developer'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </main>
        </AppShell>
    );
}
