"use client";

/**
 * PriceValuation Component
 * 
 * Standalone AI valuation tool.
 * Users enter property details and get fair price + market insights.
 */

import { useState } from "react";
import { API_URL } from "@/lib/contract";

interface ValuationResult {
    predicted_price: number;
    price_per_sqm?: number;
    market_status: string;
    reasoning_bullets: string[];
    investment_advice?: string;
    source?: string;
    error?: string;
}

const LOCATIONS = [
    "New Cairo",
    "Sheikh Zayed",
    "New Capital",
    "Mostakbal City",
    "6th of October",
    "Maadi",
    "Nasr City",
    "Heliopolis"
];

const FINISHING_OPTIONS = [
    { value: 0, label: "تشطيب شل" },
    { value: 1, label: "نصف تشطيب" },
    { value: 2, label: "تشطيب كامل" },
    { value: 3, label: "سوبر لوكس" },
];

export default function PriceValuation() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<ValuationResult | null>(null);

    const [formData, setFormData] = useState({
        location: "New Cairo",
        size: 150,
        finishing: 2,
        floor: 5,
        is_compound: 1,
    });

    const getValuation = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/ai/hybrid-valuation`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Valuation failed", error);
            setResult({
                error: "Service unavailable",
                predicted_price: 0,
                market_status: "Unknown",
                reasoning_bullets: []
            });
        } finally {
            setLoading(false);
        }
    };

    const getMarketStatusColor = (status: string) => {
        if (status === "Hot") return "text-red-600 bg-red-100";
        if (status === "Stable") return "text-blue-600 bg-blue-100";
        return "text-green-600 bg-green-100";
    };

    return (
        <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="p-8">
                {/* Header */}
                <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">
                        📊 تقييم العقار بالذكاء الاصطناعي
                    </h2>
                    <p className="text-gray-500 mt-2">
                        XGBoost + GPT-4o = تقييم دقيق + تحليل السوق
                    </p>
                </div>

                {/* Form */}
                <div className="space-y-4">
                    {/* Location */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">الموقع</label>
                        <select
                            className="w-full border-2 border-gray-200 rounded-lg p-3 focus:border-blue-500"
                            value={formData.location}
                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                        >
                            {LOCATIONS.map(loc => (
                                <option key={loc} value={loc}>{loc}</option>
                            ))}
                        </select>
                    </div>

                    {/* Size */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            المساحة (متر مربع)
                        </label>
                        <input
                            type="number"
                            className="w-full border-2 border-gray-200 rounded-lg p-3"
                            value={formData.size}
                            onChange={(e) => setFormData({ ...formData, size: parseInt(e.target.value) || 0 })}
                        />
                    </div>

                    {/* Finishing */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">التشطيب</label>
                        <select
                            className="w-full border-2 border-gray-200 rounded-lg p-3"
                            value={formData.finishing}
                            onChange={(e) => setFormData({ ...formData, finishing: parseInt(e.target.value) })}
                        >
                            {FINISHING_OPTIONS.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Floor */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">الطابق</label>
                        <input
                            type="number"
                            className="w-full border-2 border-gray-200 rounded-lg p-3"
                            value={formData.floor}
                            onChange={(e) => setFormData({ ...formData, floor: parseInt(e.target.value) || 0 })}
                        />
                    </div>

                    {/* Compound */}
                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="compound"
                            className="mr-2 h-5 w-5"
                            checked={formData.is_compound === 1}
                            onChange={(e) => setFormData({ ...formData, is_compound: e.target.checked ? 1 : 0 })}
                        />
                        <label htmlFor="compound" className="text-sm text-gray-700">داخل كمباوند</label>
                    </div>
                </div>

                {/* Submit Button */}
                <button
                    onClick={getValuation}
                    disabled={loading}
                    className={`mt-6 w-full py-4 rounded-xl font-bold text-lg transition-all
            ${loading
                            ? "bg-gray-400 cursor-not-allowed"
                            : "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700"
                        }`}
                >
                    {loading ? "جاري التقييم..." : "🔍 احسب السعر العادل"}
                </button>

                {/* Results */}
                {result && !result.error && (
                    <div className="mt-6 space-y-4">
                        {/* Price */}
                        <div className="p-6 rounded-xl bg-gradient-to-r from-green-50 to-blue-50 text-center">
                            <p className="text-sm text-gray-600">السعر العادل</p>
                            <p className="text-4xl font-bold text-gray-900 mt-2">
                                {result.predicted_price.toLocaleString()}
                            </p>
                            <p className="text-lg text-gray-600">جنيه مصري</p>
                            {result.price_per_sqm && (
                                <p className="text-sm text-gray-500 mt-2">
                                    {result.price_per_sqm.toLocaleString()} جنيه/م²
                                </p>
                            )}
                        </div>

                        {/* Market Status */}
                        <div className="flex justify-center">
                            <span className={`px-4 py-2 rounded-full font-bold ${getMarketStatusColor(result.market_status)}`}>
                                السوق: {result.market_status === "Hot" ? "ساخن 🔥" : result.market_status === "Stable" ? "مستقر 📊" : "هادئ ❄️"}
                            </span>
                        </div>

                        {/* Reasoning */}
                        {result.reasoning_bullets && result.reasoning_bullets.length > 0 && (
                            <div className="p-4 rounded-xl bg-gray-50">
                                <p className="font-bold text-gray-700 mb-2">💡 لماذا هذا السعر:</p>
                                <ul className="space-y-2">
                                    {result.reasoning_bullets.map((r, i) => (
                                        <li key={i} className="text-gray-600 text-sm">• {r}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Source */}
                        {result.source && (
                            <p className="text-xs text-center text-gray-400">
                                المصدر: {result.source}
                            </p>
                        )}
                    </div>
                )}

                {result?.error && (
                    <div className="mt-4 p-4 bg-red-100 rounded-xl text-red-700">
                        خطأ: {result.error}
                    </div>
                )}
            </div>
        </div>
    );
}
