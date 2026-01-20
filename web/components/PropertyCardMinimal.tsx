"use client";

import React from 'react';
import Image from 'next/image';
import { PiBed, PiBathtub, PiRuler } from 'react-icons/pi';
import { Building2, Home, Briefcase, Factory, Map as MapIcon, Store } from 'lucide-react';

interface PropertyCardMinimalProps {
    property: {
        id: number;
        title: string;
        location: string;
        compound?: string;
        price: number;
        size_sqm: number;
        bedrooms: number;
        bathrooms?: number;
        image_url?: string;
        type?: string;
        wolf_score?: number;
    };
    onClick?: () => void;
}

/**
 * PropertyCardMinimal - Hologram Style
 * Matches the "Neural Synapse" design system.
 */
export default function PropertyCardMinimal({
    property,
    onClick
}: PropertyCardMinimalProps) {

    const {
        title,
        location,
        compound,
        price,
        size_sqm,
        bedrooms,
        bathrooms,
        image_url,
        type,
        wolf_score
    } = property;

    return (
        <div
            onClick={onClick}
            className="group relative glass-panel rounded-2xl p-5 hover:border-[var(--color-primary)]/30 transition-all duration-300 cursor-pointer overflow-hidden transform hover:scale-[1.02]"
        >
            {/* Holographic Nodes */}
            <div className="absolute top-1/2 -right-1 w-2 h-2 bg-[var(--color-tertiary)]/60 rounded-full node-glow blur-[1px]"></div>
            <div className="absolute -top-[1px] -left-[1px] w-4 h-4 border-t border-l border-[var(--color-primary)]/60 rounded-tl-lg"></div>

            {/* Image Section */}
            <div className="relative overflow-hidden rounded-xl mb-4 h-44 bg-surface-dark/50">
                {image_url ? (
                    <Image
                        src={image_url}
                        alt={title}
                        fill
                        className="object-cover hologram-img group-hover:opacity-100 opacity-90"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 bg-gradient-to-br from-slate-100 to-slate-200 dark:from-white/5 dark:to-white/10 group-hover:scale-105 transition-transform duration-500">
                        <div className="p-4 rounded-full bg-[var(--color-background)]/50 backdrop-blur-sm border border-[var(--color-primary)]/20 shadow-inner mb-2 group-hover:border-[var(--color-primary)]/50 transition-colors">
                            {(() => {
                                const t = (type || '').toLowerCase();
                                if (t.includes('villa') || t.includes('house')) return <Home className="w-8 h-8 text-[var(--color-primary)]" />;
                                if (t.includes('office') || t.includes('admin')) return <Briefcase className="w-8 h-8 text-[var(--color-secondary)]" />;
                                if (t.includes('retail') || t.includes('store') || t.includes('shop')) return <Store className="w-8 h-8 text-[var(--color-tertiary)]" />;
                                if (t.includes('land') || t.includes('plot')) return <MapIcon className="w-8 h-8 text-emerald-600" />;
                                if (t.includes('factory') || t.includes('warehouse')) return <Factory className="w-8 h-8 text-slate-500" />;
                                return <Building2 className="w-8 h-8 text-[var(--color-primary)]/80" />;
                            })()}
                        </div>
                        <span className="text-[10px] uppercase tracking-widest font-semibold opacity-60 font-display">
                            {type || 'Property'}
                        </span>
                    </div>
                )}

                {/* Type Badge */}
                <div className="absolute top-3 left-3 px-3 py-1 bg-surface-dark/40 border border-white/20 text-white text-[10px] font-bold uppercase rounded-md backdrop-blur-md tracking-wider">
                    {type || 'Property'}
                </div>

                {/* Wolf Score Badge (if exists) */}
                {wolf_score && (
                    <div className="absolute bottom-3 right-3 px-2 py-0.5 bg-[var(--color-primary)]/90 text-white text-[10px] font-bold rounded flex items-center gap-1 shadow-lg shadow-[var(--color-primary)]/20">
                        <span className="material-symbols-outlined text-[10px]">star</span>
                        <span>{wolf_score}</span>
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="space-y-3">
                <div className="flex justify-between items-start">
                    <div>
                        <h3 className="text-lg font-medium leading-tight text-slate-800 dark:text-slate-100 font-sans line-clamp-1">{title}</h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-display uppercase tracking-wide truncate">
                            {compound ? `${compound} • ` : ''}{location}
                        </p>
                    </div>
                </div>

                <div className="text-2xl font-light text-[var(--color-primary)] font-display tracking-tight">
                    {price.toLocaleString()} <span className="text-base text-slate-500">EGP</span>
                </div>

                {/* Specs Grid */}
                <div className="grid grid-cols-3 gap-2 mt-4 pt-4 border-t border-slate-200 dark:border-white/5">
                    <div className="text-center">
                        <PiBed className="text-slate-400 text-lg mb-1 mx-auto" />
                        <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{bedrooms} Bed</p>
                    </div>
                    <div className="text-center border-l border-slate-200 dark:border-white/5">
                        <PiBathtub className="text-slate-400 text-lg mb-1 mx-auto" />
                        <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{bathrooms || 1} Bath</p>
                    </div>
                    <div className="text-center border-l border-slate-200 dark:border-white/5">
                        <PiRuler className="text-slate-400 text-lg mb-1 mx-auto" />
                        <p className="text-xs font-semibold text-slate-600 dark:text-slate-300">{size_sqm}m²</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
