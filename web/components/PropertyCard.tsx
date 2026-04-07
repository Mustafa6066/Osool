"use client";

import { MapPin, Bed, Ruler, ArrowRight, Heart, Share2, ExternalLink, TrendingUp, Calendar } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import api from "@/lib/api";
import WhatsAppHandoffModal from "./WhatsAppHandoffModal";

interface PropertyProps {
    id?: number;
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    is_available?: boolean;
    image_url?: string;
    price_per_sqm?: number;
    developer?: string;
    delivery_date?: string;
    property_type?: string;
    url?: string;
}

export default function PropertyCard({ property }: { property: PropertyProps }) {
    const [isFavorite, setIsFavorite] = useState(false);
    const [imageError, setImageError] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [showWhatsApp, setShowWhatsApp] = useState(false);

    const handleToggleFavorite = async () => {
        const next = !isFavorite;
        setIsFavorite(next); // optimistic update
        try {
            if (property.id) {
                await api.post(`/api/gamification/favorite/${property.id}`);
            }
        } catch {
            setIsFavorite(!next); // revert on failure
        }
    };

    const handleContact = () => {
        setShowWhatsApp(true);
    };

    const handleShare = async () => {
        if (navigator.share && property.url) {
            try {
                await navigator.share({
                    title: property.title,
                    text: `Check out this property: ${property.title} - ${property.price.toLocaleString()} EGP`,
                    url: property.url
                });
            } catch (err) {
                console.error("Error sharing:", err);
            }
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(property.url || window.location.href);
            alert("Property link copied to clipboard!");
        }
    };

    const defaultImage = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=250&fit=crop";
    const imageUrl = imageError ? defaultImage : (property.image_url || defaultImage);

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="group max-w-sm overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-primary)] shadow-sm transition-all hover:-translate-y-0.5 hover:border-emerald-500/30 hover:shadow-lg"
        >
            {/* Image Section */}
            <div className="relative h-48 overflow-hidden bg-[var(--color-surface-elevated)]">
                {!imageLoaded && (
                    <div className="absolute inset-0 animate-pulse bg-[var(--color-surface-elevated)]" />
                )}
                <Image
                    src={imageUrl}
                    alt={property.title}
                    fill
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 384px"
                    onError={() => setImageError(true)}
                    onLoad={() => setImageLoaded(true)}
                    className={`object-cover group-hover:scale-110 transition-transform duration-500 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                    placeholder="blur"
                    blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjI1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMWEyMTJkIi8+PC9zdmc+"
                />

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />

                {/* Status Badge */}
                {property.is_available !== false && (
                    <div className="absolute top-3 left-3 flex items-center gap-1 rounded-full border border-emerald-500/25 bg-emerald-500/12 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400 shadow-sm">
                        <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                        Available now
                    </div>
                )}

                {/* Action Buttons */}
                <div className="absolute top-3 right-3 flex gap-2">
                    <button
                        onClick={handleToggleFavorite}
                        aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
                        className="rounded-full border border-white/25 bg-black/25 p-2 text-white backdrop-blur-sm transition-colors hover:bg-black/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/40"
                    >
                        <Heart
                            size={16}
                            className={`${isFavorite ? "fill-red-500 text-red-500" : "text-white"} transition-colors`}
                        />
                    </button>
                    <button
                        onClick={handleShare}
                        aria-label="Share property"
                        className="rounded-full border border-white/25 bg-black/25 p-2 text-white backdrop-blur-sm transition-colors hover:bg-black/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/40"
                    >
                        <Share2 size={16} className="text-white" />
                    </button>
                </div>

                {/* Price Tag */}
                <div className="absolute bottom-3 left-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]/95 px-3 py-2 shadow-md backdrop-blur-sm">
                    <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                        {(property.price / 1000000).toFixed(2)}M EGP
                    </div>
                    {property.price_per_sqm && (
                        <div className="text-xs text-[var(--color-text-secondary)]">
                            {property.price_per_sqm.toLocaleString()} EGP/m²
                        </div>
                    )}
                </div>
            </div>

            {/* Content Section */}
            <div className="p-4">
                {/* Title */}
                <h4 className="mb-2 line-clamp-2 text-lg font-bold text-[var(--color-text-primary)] transition-colors group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                    {property.title}
                </h4>

                {/* Location */}
                <div className="mb-3 flex items-center text-sm text-[var(--color-text-secondary)]">
                    <MapPin size={14} className="mr-1.5 text-emerald-500" />
                    {property.location}
                </div>

                {/* Property Details Grid */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="flex flex-col items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-2 text-center">
                        <Bed size={16} className="mb-1 text-emerald-500" />
                        <span className="text-sm font-semibold text-[var(--color-text-primary)]">{property.bedrooms}</span>
                        <span className="text-xs text-[var(--color-text-muted)]">Beds</span>
                    </div>
                    <div className="flex flex-col items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-2 text-center">
                        <Ruler size={16} className="mb-1 text-teal-500" />
                        <span className="text-sm font-semibold text-[var(--color-text-primary)]">{property.size_sqm}</span>
                        <span className="text-xs text-[var(--color-text-muted)]">m²</span>
                    </div>
                    {property.property_type && (
                        <div className="flex flex-col items-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-2 text-center">
                            <TrendingUp size={16} className="mb-1 text-emerald-500" />
                            <span className="line-clamp-1 text-xs font-semibold text-[var(--color-text-primary)]">{property.property_type}</span>
                            <span className="text-xs text-[var(--color-text-muted)]">Type</span>
                        </div>
                    )}
                </div>

                {/* Developer and Delivery */}
                {(property.developer || property.delivery_date) && (
                    <div className="mb-4 space-y-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] p-3">
                        {property.developer && (
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-[var(--color-text-muted)]">Developer:</span>
                                <span className="font-semibold text-[var(--color-text-primary)]">{property.developer}</span>
                            </div>
                        )}
                        {property.delivery_date && (
                            <div className="flex items-center justify-between text-xs">
                                <span className="flex items-center gap-1 text-[var(--color-text-muted)]">
                                    <Calendar size={12} />
                                    Delivery:
                                </span>
                                <span className="font-semibold text-emerald-600 dark:text-emerald-400">{property.delivery_date}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={() => {
                            if (!property.url) return;
                            window.open(property.url, '_blank', 'noopener,noreferrer');
                        }}
                        disabled={!property.url}
                        className="flex items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/40 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        Open listing
                        <ExternalLink size={14} />
                    </button>
                    <button
                        className="flex items-center justify-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-elevated)] py-2.5 text-sm font-semibold text-[var(--color-text-primary)] transition-colors hover:border-emerald-500/35 hover:bg-emerald-500/8 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/40"
                        onClick={handleContact}
                    >
                        Talk to advisor
                        <ArrowRight size={14} />
                    </button>
                </div>
            </div>

            <WhatsAppHandoffModal
                isOpen={showWhatsApp}
                onClose={() => setShowWhatsApp(false)}
                context={{
                    propertyTitle: property.title,
                    propertyLocation: property.location,
                    propertyPrice: `${(property.price / 1_000_000).toFixed(2)}M EGP`,
                }}
            />
        </motion.div>
    );
}
