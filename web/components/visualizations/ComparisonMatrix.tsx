"use client";

import { motion } from "framer-motion";
import { Home, MapPin, DollarSign, Calendar, TrendingUp, Award, CheckCircle2 } from "lucide-react";

interface Property {
    id: number;
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    price_per_sqm: number;
    monthly_installment?: number;
    delivery_date?: string;
    roi_projection?: number;
    developer?: string;
}

interface ComparisonMatrixProps {
    properties: Property[];
    bestValueId?: number;
    recommendedId?: number;
}

export default function ComparisonMatrix({ properties, bestValueId, recommendedId }: ComparisonMatrixProps) {
    if (!properties || properties.length === 0) {
        return null;
    }

    // Find best values
    const lowestPricePerSqm = Math.min(...properties.map(p => p.price_per_sqm || 0));
    const highestROI = Math.max(...properties.map(p => p.roi_projection || 0));

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-[#1a1c2e] to-[#2d3748] rounded-2xl p-6 border border-white/10 shadow-2xl"
        >
            {/* Header */}
            <div className="mb-6">
                <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                    <Award className="w-5 h-5 text-yellow-400" />
                    Property Comparison
                </h3>
                <p className="text-gray-400 text-sm">
                    Side-by-side analysis of {properties.length} properties
                </p>
            </div>

            {/* Comparison Table */}
            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-white/10">
                            <th className="text-left py-3 px-2 text-gray-400 text-sm font-medium">Metric</th>
                            {properties.map((property, idx) => (
                                <th key={property.id} className="py-3 px-2 text-center">
                                    <motion.div
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="relative"
                                    >
                                        {property.id === recommendedId && (
                                            <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-blue-500 text-white text-[10px] rounded-full whitespace-nowrap">
                                                Recommended
                                            </div>
                                        )}
                                        {property.id === bestValueId && (
                                            <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 bg-green-500 text-white text-[10px] rounded-full whitespace-nowrap">
                                                Best Value
                                            </div>
                                        )}
                                        <div className="text-xs text-gray-400 mt-2">Property {idx + 1}</div>
                                    </motion.div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {/* Title */}
                        <tr className="border-b border-white/10">
                            <td className="py-4 px-2">
                                <div className="flex items-center gap-2 text-gray-300 text-sm">
                                    <Home className="w-4 h-4" />
                                    <span>Title</span>
                                </div>
                            </td>
                            {properties.map((property, idx) => (
                                <td key={property.id} className="py-4 px-2">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.2 + idx * 0.1 }}
                                        className="text-sm text-white text-center font-medium"
                                    >
                                        {property.title.length > 30
                                            ? property.title.substring(0, 30) + "..."
                                            : property.title}
                                    </motion.div>
                                </td>
                            ))}
                        </tr>

                        {/* Location */}
                        <tr className="border-b border-white/10 bg-white/5">
                            <td className="py-4 px-2">
                                <div className="flex items-center gap-2 text-gray-300 text-sm">
                                    <MapPin className="w-4 h-4" />
                                    <span>Location</span>
                                </div>
                            </td>
                            {properties.map((property, idx) => (
                                <td key={property.id} className="py-4 px-2">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.3 + idx * 0.1 }}
                                        className="text-sm text-gray-400 text-center"
                                    >
                                        {property.location}
                                    </motion.div>
                                </td>
                            ))}
                        </tr>

                        {/* Total Price */}
                        <tr className="border-b border-white/10">
                            <td className="py-4 px-2">
                                <div className="flex items-center gap-2 text-gray-300 text-sm">
                                    <DollarSign className="w-4 h-4" />
                                    <span>Total Price</span>
                                </div>
                            </td>
                            {properties.map((property, idx) => (
                                <td key={property.id} className="py-4 px-2">
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: 0.4 + idx * 0.1 }}
                                        className="text-center"
                                    >
                                        <div className="text-lg font-bold text-blue-400">
                                            {(property.price / 1000000).toFixed(1)}M
                                        </div>
                                        <div className="text-xs text-gray-500">EGP</div>
                                    </motion.div>
                                </td>
                            ))}
                        </tr>

                        {/* Price per sqm */}
                        <tr className="border-b border-white/10 bg-white/5">
                            <td className="py-4 px-2">
                                <div className="flex items-center gap-2 text-gray-300 text-sm">
                                    <TrendingUp className="w-4 h-4" />
                                    <span>Price/sqm</span>
                                </div>
                            </td>
                            {properties.map((property, idx) => (
                                <td key={property.id} className="py-4 px-2">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.5 + idx * 0.1 }}
                                        className="text-center"
                                    >
                                        <div className={`text-sm font-semibold ${
                                            property.price_per_sqm === lowestPricePerSqm
                                                ? "text-green-400"
                                                : "text-white"
                                        }`}>
                                            {(property.price_per_sqm || 0).toLocaleString()} EGP
                                        </div>
                                        {property.price_per_sqm === lowestPricePerSqm && (
                                            <div className="flex items-center justify-center gap-1 mt-1">
                                                <CheckCircle2 className="w-3 h-3 text-green-400" />
                                                <span className="text-[10px] text-green-400">Best Value</span>
                                            </div>
                                        )}
                                    </motion.div>
                                </td>
                            ))}
                        </tr>

                        {/* Size */}
                        <tr className="border-b border-white/10">
                            <td className="py-4 px-2">
                                <div className="flex items-center gap-2 text-gray-300 text-sm">
                                    <span className="w-4 h-4 flex items-center justify-center text-xs">📐</span>
                                    <span>Size</span>
                                </div>
                            </td>
                            {properties.map((property, idx) => (
                                <td key={property.id} className="py-4 px-2">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 0.6 + idx * 0.1 }}
                                        className="text-sm text-white text-center font-medium"
                                    >
                                        {property.size_sqm} sqm
                                        <div className="text-xs text-gray-500 mt-1">
                                            {property.bedrooms} bed
                                        </div>
                                    </motion.div>
                                </td>
                            ))}
                        </tr>

                        {/* Monthly Payment */}
                        {properties.some(p => p.monthly_installment) && (
                            <tr className="border-b border-white/10 bg-white/5">
                                <td className="py-4 px-2">
                                    <div className="flex items-center gap-2 text-gray-300 text-sm">
                                        <Calendar className="w-4 h-4" />
                                        <span>Monthly</span>
                                    </div>
                                </td>
                                {properties.map((property, idx) => (
                                    <td key={property.id} className="py-4 px-2">
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: 0.7 + idx * 0.1 }}
                                            className="text-center"
                                        >
                                            {property.monthly_installment ? (
                                                <>
                                                    <div className="text-sm font-semibold text-purple-400">
                                                        {(property.monthly_installment / 1000).toFixed(0)}K
                                                    </div>
                                                    <div className="text-xs text-gray-500">EGP/mo</div>
                                                </>
                                            ) : (
                                                <span className="text-xs text-gray-600">N/A</span>
                                            )}
                                        </motion.div>
                                    </td>
                                ))}
                            </tr>
                        )}

                        {/* ROI */}
                        {properties.some(p => p.roi_projection) && (
                            <tr className="border-b border-white/10">
                                <td className="py-4 px-2">
                                    <div className="flex items-center gap-2 text-gray-300 text-sm">
                                        <TrendingUp className="w-4 h-4 text-green-400" />
                                        <span>ROI</span>
                                    </div>
                                </td>
                                {properties.map((property, idx) => (
                                    <td key={property.id} className="py-4 px-2">
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: 0.8 + idx * 0.1 }}
                                            className="text-center"
                                        >
                                            {property.roi_projection ? (
                                                <>
                                                    <div className={`text-sm font-semibold ${
                                                        property.roi_projection === highestROI
                                                            ? "text-green-400"
                                                            : "text-white"
                                                    }`}>
                                                        {property.roi_projection.toFixed(1)}%
                                                    </div>
                                                    {property.roi_projection === highestROI && (
                                                        <div className="flex items-center justify-center gap-1 mt-1">
                                                            <CheckCircle2 className="w-3 h-3 text-green-400" />
                                                            <span className="text-[10px] text-green-400">Highest</span>
                                                        </div>
                                                    )}
                                                </>
                                            ) : (
                                                <span className="text-xs text-gray-600">N/A</span>
                                            )}
                                        </motion.div>
                                    </td>
                                ))}
                            </tr>
                        )}

                        {/* Delivery */}
                        {properties.some(p => p.delivery_date) && (
                            <tr className="border-b border-white/10 bg-white/5">
                                <td className="py-4 px-2">
                                    <div className="flex items-center gap-2 text-gray-300 text-sm">
                                        <Calendar className="w-4 h-4" />
                                        <span>Delivery</span>
                                    </div>
                                </td>
                                {properties.map((property, idx) => (
                                    <td key={property.id} className="py-4 px-2">
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: 0.9 + idx * 0.1 }}
                                            className="text-sm text-gray-400 text-center"
                                        >
                                            {property.delivery_date || "N/A"}
                                        </motion.div>
                                    </td>
                                ))}
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-white/10">
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span>Powered by AMR Hybrid AI Brain</span>
                </div>
            </div>
        </motion.div>
    );
}
