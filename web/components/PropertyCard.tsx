"use client";

import { MapPin, Bed, Ruler, ArrowRight, Heart, Share2, ExternalLink, TrendingUp, Calendar } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";

interface PropertyProps {
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
            className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] border border-white/10 rounded-2xl overflow-hidden hover:border-blue-500/30 transition-all group shadow-xl hover:shadow-2xl hover:shadow-blue-500/20 max-w-sm"
        >
            {/* Image Section */}
            <div className="relative h-48 overflow-hidden bg-gray-800">
                <img
                    src={imageUrl}
                    alt={property.title}
                    onError={() => setImageError(true)}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                />

                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />

                {/* Status Badge */}
                {property.is_available !== false && (
                    <div className="absolute top-3 left-3 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1 shadow-lg">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                        Available
                    </div>
                )}

                {/* Action Buttons */}
                <div className="absolute top-3 right-3 flex gap-2">
                    <button
                        onClick={() => setIsFavorite(!isFavorite)}
                        className="p-2 rounded-full bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all"
                    >
                        <Heart
                            size={16}
                            className={`${isFavorite ? "fill-red-500 text-red-500" : "text-white"} transition-colors`}
                        />
                    </button>
                    <button
                        onClick={handleShare}
                        className="p-2 rounded-full bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all"
                    >
                        <Share2 size={16} className="text-white" />
                    </button>
                </div>

                {/* Price Tag */}
                <div className="absolute bottom-3 left-3 bg-white/95 backdrop-blur-md px-3 py-2 rounded-lg shadow-lg">
                    <div className="text-blue-600 font-bold text-lg">
                        {(property.price / 1000000).toFixed(2)}M EGP
                    </div>
                    {property.price_per_sqm && (
                        <div className="text-gray-600 text-xs">
                            {property.price_per_sqm.toLocaleString()} EGP/m²
                        </div>
                    )}
                </div>
            </div>

            {/* Content Section */}
            <div className="p-4">
                {/* Title */}
                <h4 className="text-white font-bold text-lg mb-2 line-clamp-2 group-hover:text-blue-400 transition-colors">
                    {property.title}
                </h4>

                {/* Location */}
                <div className="flex items-center text-gray-400 text-sm mb-3">
                    <MapPin size={14} className="mr-1.5 text-blue-400" />
                    {property.location}
                </div>

                {/* Property Details Grid */}
                <div className="grid grid-cols-3 gap-2 mb-4">
                    <div className="flex flex-col items-center text-center bg-white/5 p-2 rounded-lg border border-white/10">
                        <Bed size={16} className="text-blue-400 mb-1" />
                        <span className="text-white font-semibold text-sm">{property.bedrooms}</span>
                        <span className="text-gray-400 text-xs">Beds</span>
                    </div>
                    <div className="flex flex-col items-center text-center bg-white/5 p-2 rounded-lg border border-white/10">
                        <Ruler size={16} className="text-purple-400 mb-1" />
                        <span className="text-white font-semibold text-sm">{property.size_sqm}</span>
                        <span className="text-gray-400 text-xs">m²</span>
                    </div>
                    {property.property_type && (
                        <div className="flex flex-col items-center text-center bg-white/5 p-2 rounded-lg border border-white/10">
                            <TrendingUp size={16} className="text-green-400 mb-1" />
                            <span className="text-white font-semibold text-xs line-clamp-1">{property.property_type}</span>
                            <span className="text-gray-400 text-xs">Type</span>
                        </div>
                    )}
                </div>

                {/* Developer and Delivery */}
                {(property.developer || property.delivery_date) && (
                    <div className="space-y-2 mb-4 p-3 bg-white/5 rounded-lg border border-white/10">
                        {property.developer && (
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-400">Developer:</span>
                                <span className="text-white font-semibold">{property.developer}</span>
                            </div>
                        )}
                        {property.delivery_date && (
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-400 flex items-center gap-1">
                                    <Calendar size={12} />
                                    Delivery:
                                </span>
                                <span className="text-green-400 font-semibold">{property.delivery_date}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={() => window.open(property.url || "#", "_blank")}
                        className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-sm py-2.5 rounded-lg transition-all flex items-center justify-center gap-2 font-semibold shadow-lg shadow-blue-600/30"
                    >
                        View Details
                        <ExternalLink size={14} />
                    </button>
                    <button
                        className="bg-white/10 hover:bg-white/20 border border-white/20 hover:border-blue-500/50 text-white text-sm py-2.5 rounded-lg transition-all flex items-center justify-center gap-2 font-semibold"
                    >
                        Contact
                        <ArrowRight size={14} />
                    </button>
                </div>
            </div>
        </motion.div>
    );
}
