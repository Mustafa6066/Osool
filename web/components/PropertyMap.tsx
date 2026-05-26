'use client';

import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Home, X, Bed, Maximize, ExternalLink } from 'lucide-react';
import Link from 'next/link';

// ── Coordinate mapping for Egyptian areas ──────────────────────────────────
const AREA_COORDS: Record<string, [number, number]> = {
    // New Cairo
    'new cairo':         [30.0131, 31.4555],
    '5th settlement':    [30.0074, 31.4325],
    'el patio':          [30.0280, 31.4680],
    'mivida':            [30.0090, 31.4400],
    'madinaty':          [30.1070, 31.6400],
    'rehab':             [30.0577, 31.4926],
    'mountain view':     [30.0200, 31.4700],
    'hyde park':         [30.0020, 31.4650],
    'katameya':          [30.0100, 31.4200],
    'palm hills':        [30.0150, 31.4500],
    // 6th October & Sheikh Zayed
    '6th october':       [29.9603, 31.0091],
    'sheikh zayed':      [30.0396, 31.0114],
    'smart village':     [30.0710, 30.9797],
    'zayed':             [30.0396, 31.0114],
    'beverly hills':     [30.0350, 31.0050],
    'allegria':          [30.0450, 31.0200],
    // Ain Sokhna
    'ain sokhna':        [29.5950, 32.3165],
    'sokhna':            [29.5950, 32.3165],
    // North Coast
    'north coast':       [31.0500, 28.5000],
    'sahel':             [31.0500, 28.8000],
    'ras el hikma':      [31.1000, 27.7000],
    'hacienda':          [31.0600, 28.5500],
    'marassi':           [31.0700, 28.3000],
    // New Capital
    'new capital':       [30.0200, 31.7600],
    'capital':           [30.0200, 31.7600],
    'new admin':         [30.0200, 31.7600],
    // Cairo – central areas
    'zamalek':           [30.0626, 31.2197],
    'maadi':             [29.9602, 31.2570],
    'heliopolis':        [30.0866, 31.3225],
    'cairo':             [30.0444, 31.2357],
    'nasr city':         [30.0500, 31.3500],
    'mohandessin':       [30.0560, 31.2050],
    'dokki':             [30.0380, 31.2120],
    'garden city':       [30.0350, 31.2310],
    'glen':              [30.0080, 31.4400],
    // Compounds
    'el shorouk':        [30.1120, 31.6150],
    'badr city':         [30.1300, 31.7200],
    'el obour':          [30.2200, 31.4800],
};

// Default center of Greater Cairo
const CAIRO_CENTER: [number, number] = [30.0444, 31.2357];

function geocodeFromLocation(locationStr: string): [number, number] {
    const loc = locationStr.toLowerCase();
    // Try to find a match in our coordinate list (longest match first for specificity)
    const sorted = Object.entries(AREA_COORDS).sort((a, b) => b[0].length - a[0].length);
    for (const [key, coords] of sorted) {
        if (loc.includes(key)) {
            // Add slight random jitter so pins don't overlap
            return [
                coords[0] + (Math.random() - 0.5) * 0.008,
                coords[1] + (Math.random() - 0.5) * 0.008,
            ];
        }
    }
    // Fallback: scatter around Cairo center
    return [
        CAIRO_CENTER[0] + (Math.random() - 0.5) * 0.05,
        CAIRO_CENTER[1] + (Math.random() - 0.5) * 0.05,
    ];
}

interface PropertyItem {
    id: string;
    title: string;
    titleAr: string;
    location: string;
    locationAr: string;
    price: number;
    bedrooms: number;
    area: number;
    type: string;
    image: string;
}

interface PropertyMapProps {
    properties: PropertyItem[];
    language: string;
    formatPrice: (price: number) => string;
}

type MapInstance = {
    remove: () => void;
    fitBounds: (...args: unknown[]) => unknown;
};

type MarkerInstance = {
    remove: () => void;
    on: (event: 'click', handler: () => void) => void;
};

export default function PropertyMap({ properties, language, formatPrice }: PropertyMapProps) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<MapInstance | null>(null);
    const markersRef = useRef<MarkerInstance[]>([]);
    const [selectedProperty, setSelectedProperty] = useState<PropertyItem | null>(null);
    const [mapReady, setMapReady] = useState(false);

    useEffect(() => {
        if (!mapRef.current || mapInstanceRef.current) return;

        // Dynamic import of Leaflet (client-only)
        import('leaflet').then((L) => {
            // Fix default marker icons for webpack/next
            delete (L.Icon.Default.prototype as { _getIconUrl?: unknown })._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
            });

            const map = L.map(mapRef.current!, {
                center: CAIRO_CENTER,
                zoom: 10,
                zoomControl: false,
            });

            // Add zoom control to top-right
            L.control.zoom({ position: 'topright' }).addTo(map);

            // Dark tile layer (CartoDB Dark Matter)
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19,
            }).addTo(map);

            mapInstanceRef.current = map as unknown as MapInstance;
            setMapReady(true);
        });

        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, []);

    // Place / update markers whenever properties or mapReady changes
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current) return;

        import('leaflet').then((L) => {
            const map = mapInstanceRef.current as unknown as { fitBounds: (...args: unknown[]) => unknown };
            const layerTarget = mapInstanceRef.current as unknown as Parameters<ReturnType<typeof L.marker>['addTo']>[0];

            // Remove old markers
            markersRef.current.forEach((m) => m.remove());
            markersRef.current = [];

            if (properties.length === 0) return;

            const bounds = L.latLngBounds([]);

            properties.forEach((prop) => {
                const [lat, lng] = geocodeFromLocation(prop.location);
                bounds.extend([lat, lng]);

                // Price label as divIcon
                const priceLabel = formatPrice(prop.price);
                const icon = L.divIcon({
                    className: 'osool-map-marker',
                    html: `<div style="
                        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
                        color: white;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 4px 10px;
                        border-radius: 20px;
                        white-space: nowrap;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
                        border: 2px solid rgba(255,255,255,0.25);
                        cursor: pointer;
                        transition: transform 0.15s;
                    ">${priceLabel}</div>`,
                    iconSize: [0, 0],
                    iconAnchor: [40, 16],
                });

                const marker = L.marker([lat, lng], { icon }).addTo(layerTarget);
                marker.on('click', () => setSelectedProperty(prop));
                markersRef.current.push(marker as unknown as MarkerInstance);
            });

            // Fit map to show all pins
            if (bounds.isValid()) {
                map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
            }
        });
    }, [properties, mapReady, formatPrice]);

    return (
        <div className="relative h-[600px] rounded-2xl overflow-hidden border border-[var(--color-border)]">
            {/* Leaflet CSS */}
            <link
                rel="stylesheet"
                href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                crossOrigin=""
            />

            {/* Map container */}
            <div ref={mapRef} className="w-full h-full z-0" />

            {/* Property count badge */}
            <div className="absolute top-4 left-4 z-[1000] bg-[var(--color-surface)]/90 backdrop-blur-md border border-[var(--color-border)] rounded-xl px-4 py-2 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-500" />
                <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {properties.length} {language === 'ar' ? 'عقار' : 'properties'}
                </span>
            </div>

            {/* Selected property popup card */}
            {selectedProperty && (
                <div className="absolute bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-[360px] z-[1000] animate-in slide-in-from-bottom-4 duration-300">
                    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-2xl overflow-hidden">
                        {/* Close button */}
                        <button
                            onClick={() => setSelectedProperty(null)}
                            aria-label={language === 'ar' ? 'إغلاق البطاقة' : 'Close property card'}
                            className="absolute top-3 right-3 z-10 w-11 h-11 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white hover:bg-black/70 transition-colors"
                        >
                            <X className="w-4 h-4" />
                        </button>

                        {/* Image */}
                        <div className="relative h-36 bg-gradient-to-br from-emerald-900/40 to-[var(--color-surface-elevated)]">
                            <img
                                src={selectedProperty.image}
                                alt={language === 'ar' ? selectedProperty.titleAr : selectedProperty.title}
                                loading="lazy"
                                decoding="async"
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = 'none';
                                }}
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                            <div className="absolute bottom-3 left-3 text-lg font-bold text-white">
                                {formatPrice(selectedProperty.price)}
                            </div>
                        </div>

                        {/* Info */}
                        <div className="p-4">
                            <h3 className="text-base font-bold text-[var(--color-text-primary)] mb-1 line-clamp-1">
                                {language === 'ar' ? selectedProperty.titleAr : selectedProperty.title}
                            </h3>
                            <div className="flex items-center gap-1.5 text-[var(--color-text-secondary)] text-sm mb-3">
                                <MapPin className="w-3.5 h-3.5 text-emerald-500" />
                                {language === 'ar' ? selectedProperty.locationAr || selectedProperty.location : selectedProperty.location}
                            </div>

                            <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)] mb-3">
                                {selectedProperty.bedrooms > 0 && (
                                    <span className="flex items-center gap-1">
                                        <Bed className="w-3.5 h-3.5" /> {selectedProperty.bedrooms}
                                    </span>
                                )}
                                {selectedProperty.area > 0 && (
                                    <span className="flex items-center gap-1">
                                        <Maximize className="w-3.5 h-3.5" /> {selectedProperty.area} {language === 'ar' ? 'م²' : 'sqm'}
                                    </span>
                                )}
                                <span className="capitalize px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 text-xs font-medium">
                                    {selectedProperty.type}
                                </span>
                            </div>

                            <Link
                                href={`/property/${selectedProperty.id}`}
                                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm transition-colors"
                            >
                                <ExternalLink className="w-4 h-4" />
                                {language === 'ar' ? 'عرض التفاصيل' : 'View Details'}
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
