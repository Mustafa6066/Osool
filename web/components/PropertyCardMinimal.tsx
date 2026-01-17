"use client";

import React from 'react';
import Image from 'next/image';
import { PiBed, PiBathtub, PiRuler } from 'react-icons/pi';
import { HiOutlineLocationMarker } from 'react-icons/hi';

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
    };
    onClick?: () => void;
}

/**
 * PropertyCardMinimal - Compact, clean property card for list views
 * 
 * Design Philosophy:
 * - Mobile-first with responsive layout
 * - Key information at-a-glance
 * - Egyptian market focus (price in EGP, locations)
 * - Subtle hover effects for premium feel
 */
export default function PropertyCardMinimal({
    property,
    onClick
}: PropertyCardMinimalProps) {

    const {
        id,
        title,
        location,
        compound,
        price,
        size_sqm,
        bedrooms,
        bathrooms,
        image_url,
        type
    } = property;

    // Format price with Egyptian locale (e.g., "2,500,000 EGP")
    const formatPrice = (value: number): string => {
        return new Intl.NumberFormat('en-EG', {
            style: 'currency',
            currency: 'EGP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value).replace('EGP', '').trim() + ' EGP';
    };

    // Calculate price per sqm
    const pricePerSqm = Math.round(price / size_sqm);

    return (
        <div
            onClick={onClick}
            className="group relative bg-white dark:bg-gray-800 rounded-xl overflow-hidden 
                 border border-gray-200 dark:border-gray-700
                 hover:shadow-xl hover:border-purple-400 dark:hover:border-purple-600
                 transition-all duration-300 cursor-pointer
                 hover:-translate-y-1"
        >
            {/* Image Section */}
            <div className="relative h-48 w-full overflow-hidden bg-gray-100 dark:bg-gray-900">
                {image_url ? (
                    <Image
                        src={image_url}
                        alt={title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        <HiOutlineLocationMarker className="w-16 h-16 opacity-30" />
                    </div>
                )}

                {/* Property Type Badge */}
                {type && (
                    <div className="absolute top-3 left-3">
                        <span className="px-3 py-1 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm 
                           rounded-full text-xs font-medium text-gray-700 dark:text-gray-300
                           border border-gray-200 dark:border-gray-600">
                            {type}
                        </span>
                    </div>
                )}
            </div>

            {/* Content Section */}
            <div className="p-4 space-y-3">
                {/* Price - Hero Element */}
                <div className="space-y-1">
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {formatPrice(price)}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                        {pricePerSqm.toLocaleString()} EGP/m²
                    </p>
                </div>

                {/* Title */}
                <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-1 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                    {title}
                </h3>

                {/* Location */}
                <div className="flex items-start gap-1.5 text-sm text-gray-600 dark:text-gray-400">
                    <HiOutlineLocationMarker className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <div className="flex flex-col">
                        <span className="font-medium">{location}</span>
                        {compound && (
                            <span className="text-xs text-gray-500 dark:text-gray-500">{compound}</span>
                        )}
                    </div>
                </div>

                {/* Specs - Clean horizontal layout */}
                <div className="flex items-center gap-4 pt-3 border-t border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300">
                        <PiBed className="w-5 h-5 text-gray-400" />
                        <span className="font-medium">{bedrooms}</span>
                    </div>

                    {bathrooms && (
                        <div className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300">
                            <PiBathtub className="w-5 h-5 text-gray-400" />
                            <span className="font-medium">{bathrooms}</span>
                        </div>
                    )}

                    <div className="flex items-center gap-1.5 text-sm text-gray-700 dark:text-gray-300">
                        <PiRuler className="w-5 h-5 text-gray-400" />
                        <span className="font-medium">{size_sqm.toLocaleString()} m²</span>
                    </div>
                </div>

                {/* CTA Hint (visible on hover) */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 pt-2">
                    <p className="text-xs text-purple-600 dark:text-purple-400 font-medium text-center">
                        عرض التفاصيل • View Details →
                    </p>
                </div>
            </div>
        </div>
    );
}
