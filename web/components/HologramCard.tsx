"use client";

import { Bed, Bath, Scaling } from "lucide-react";
import { motion } from "framer-motion";

interface PropertyProps {
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    bathrooms?: number;
    wolf_score?: number;
    is_available?: boolean;
    image_url?: string;
    compound?: string;
    onSelect?: () => void;
}

export default function HologramCard({ property, onSelect }: { property: PropertyProps; onSelect?: () => void }) {
    // Map Wolf Score (0-100) to 5-star scale
    const starRating = (property.wolf_score || 70) / 20;

    const defaultImage = "https://images.unsplash.com/photo-1600596542815-e328d4de4bf7?w=500&h=300&fit=crop";

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.5 }}
            onClick={onSelect}
            className="relative w-full max-w-sm cursor-pointer group"
        >
            <div className="relative glass-panel rounded-2xl p-5 hover:border-[var(--color-primary)] transition-colors duration-300">
                {/* Node Glow Decoration */}
                <div className="absolute top-1/2 -right-1 w-2 h-2 bg-[var(--color-tertiary)] rounded-full node-glow blur-[1px] opacity-60"></div>
                <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[var(--color-primary)] opacity-60 rounded-tl-lg"></div>

                {/* Image Section */}
                <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-[var(--color-surface-dark)]">
                    <img
                        alt={property.title}
                        className="w-full h-full object-cover opacity-90 group-hover:opacity-100 hologram-img"
                        src={property.image_url || defaultImage}
                    />
                    {(property.wolf_score || 0) > 80 && (
                        <div className="absolute top-3 left-3 px-3 py-1 bg-[var(--color-surface-dark)]/40 border border-white/20 text-[var(--color-text-off-white)] text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">
                            Top Pick
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="space-y-3">
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-[var(--color-text-off-white)] font-sans line-clamp-1">
                                {property.compound || property.title}
                            </h3>
                            <p className="text-xs text-slate-500 dark:text-gray-400 mt-1 font-display uppercase tracking-wide">
                                {property.location}
                            </p>
                        </div>
                        <div className="flex items-center gap-1 text-[var(--color-tertiary)]">
                            <span className="material-symbols-outlined text-sm">star</span>
                            <span className="text-sm font-bold">{starRating.toFixed(1)}</span>
                        </div>
                    </div>

                    <div className="text-2xl font-light text-[var(--color-primary)] font-display">
                        {(property.price / 1000000).toLocaleString()}M <span className="text-base text-slate-500">EGP</span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                        <div className="text-center">
                            <Bed size={14} className="mx-auto text-slate-400 mb-1" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-gray-300">{property.bedrooms} Bed</p>
                        </div>
                        <div className="text-center">
                            <Bath size={14} className="mx-auto text-slate-400 mb-1" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-gray-300">{property.bathrooms || 2} Bath</p>
                        </div>
                        <div className="text-center">
                            <Scaling size={14} className="mx-auto text-slate-400 mb-1" />
                            <p className="text-xs font-semibold text-slate-600 dark:text-gray-300">{property.size_sqm}m²</p>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
