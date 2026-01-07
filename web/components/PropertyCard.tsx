import { MapPin, Bed, Ruler, ArrowRight } from "lucide-react";

interface PropertyProps {
    title: string;
    location: string;
    price: number;
    size_sqm: number;
    bedrooms: number;
    is_available?: boolean;
}

export default function PropertyCard({ property }: { property: PropertyProps }) {
    return (
        <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:bg-white/10 transition-all group max-w-sm mt-2 mb-2">
            <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                    <h4 className="text-white font-bold truncate pr-2">{property.title}</h4>
                    <span className="bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded-full font-mono">
                        {property.price.toLocaleString()} EGP
                    </span>
                </div>

                <div className="flex items-center text-gray-400 text-xs mb-3">
                    <MapPin size={12} className="mr-1" />
                    {property.location}
                </div>

                <div className="grid grid-cols-2 gap-2 mb-3">
                    <div className="flex items-center text-gray-300 text-xs bg-white/5 p-1.5 rounded">
                        <Bed size={12} className="mr-1.5 text-blue-400" />
                        {property.bedrooms} Beds
                    </div>
                    <div className="flex items-center text-gray-300 text-xs bg-white/5 p-1.5 rounded">
                        <Ruler size={12} className="mr-1.5 text-purple-400" />
                        {property.size_sqm}m²
                    </div>
                </div>

                <button className="w-full bg-blue-600/20 hover:bg-blue-600 hover:text-white text-blue-400 text-xs py-2 rounded-lg transition-colors flex items-center justify-center gap-1 group-hover:bg-blue-600 group-hover:text-white">
                    View Details <ArrowRight size={12} />
                </button>
            </div>
        </div>
    );
}
