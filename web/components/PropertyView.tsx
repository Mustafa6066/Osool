"use client";

/**
 * PropertyView Component
 * 
 * Handles the "EGP Payment" flow:
 * 1. User pays via InstaPay/Fawry (not crypto)
 * 2. User enters payment reference
 * 3. Backend verifies payment
 * 4. Backend updates blockchain status
 * 5. User receives TX hash as proof
 * 
 * This keeps Osool compliant with CBE Law 194/2020.
 */

import { useState } from "react";
import { useActiveAccount } from "thirdweb/react";
import { API_URL } from "@/lib/contract";

interface PropertyViewProps {
    propertyId?: number;
    title?: string;
    location?: string;
    price?: number;
    reservationFee?: number;
}

export default function PropertyView({
    propertyId = 1,
    title = "شقة فاخرة - التجمع الخامس",
    location = "New Cairo",
    price = 5000000,
    reservationFee = 50000,
}: PropertyViewProps) {
    const account = useActiveAccount();
    const [loading, setLoading] = useState(false);
    const [instaPayRef, setInstaPayRef] = useState("");
    const [txHash, setTxHash] = useState<string | null>(null);
    const [aiFeedback, setAiFeedback] = useState<any>(null);

    // ==============================================================
    // AI Price Check - Ask if price is fair
    // ==============================================================
    const checkPriceWithAI = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/ai/hybrid-valuation`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    location: location,
                    size: 150,
                    finishing: 2,
                    floor: 5,
                    is_compound: 1
                }),
            });
            const data = await response.json();

            // Compare AI price to asking price
            const isHigh = price > data.predicted_price * 1.1;
            setAiFeedback({
                fairPrice: data.predicted_price,
                marketStatus: data.market_status,
                reasoning: data.reasoning_bullets,
                isOverpriced: isHigh
            });
        } catch (error) {
            console.error("AI is offline", error);
            setAiFeedback({ error: "AI service unavailable" });
        } finally {
            setLoading(false);
        }
    };

    // ==============================================================
    // Reserve Property - After EGP Payment
    // ==============================================================
    const handleReservation = async () => {
        if (!account) return alert("الرجاء تسجيل الدخول أولاً");
        if (!instaPayRef || instaPayRef.length < 8) {
            return alert("الرجاء إدخال رقم مرجع الدفع (8 أرقام على الأقل)");
        }

        setLoading(true);
        try {
            // Call YOUR Backend (Not the Blockchain directly)
            const response = await fetch(`${API_URL}/api/reserve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    property_id: propertyId,
                    user_address: account.address,
                    payment_reference: instaPayRef,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setTxHash(data.tx_hash);
                alert(`🎉 تم حجز الوحدة بنجاح!\nإثبات البلوكتشين: ${data.tx_hash}`);
            } else {
                alert("❌ فشل الحجز: " + data.detail);
            }
        } catch (error) {
            console.error("Reservation Error", error);
            alert("خطأ في النظام. يرجى التواصل مع الدعم.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
            <div className="p-8">
                {/* Property Header */}
                <div className="text-sm text-green-600 font-semibold tracking-wide uppercase">
                    ✓ موثق بالبلوكتشين • {location}
                </div>
                <h1 className="mt-2 text-2xl font-bold text-gray-900">{title}</h1>

                {/* Price Display */}
                <div className="mt-6 bg-gradient-to-r from-gray-50 to-gray-100 p-4 rounded-xl">
                    <p className="text-sm text-gray-600 mb-1">السعر</p>
                    <p className="text-3xl font-bold text-gray-900">
                        {price.toLocaleString()} <span className="text-lg">جنيه</span>
                    </p>
                </div>

                {/* AI Price Check */}
                <button
                    onClick={checkPriceWithAI}
                    disabled={loading}
                    className="mt-4 w-full bg-purple-100 text-purple-700 font-semibold py-3 rounded-lg hover:bg-purple-200 transition"
                >
                    🤖 هل السعر عادل؟ (تحليل AI)
                </button>

                {/* AI Feedback Display */}
                {aiFeedback && !aiFeedback.error && (
                    <div className={`mt-4 p-4 rounded-lg ${aiFeedback.isOverpriced ? "bg-red-50 border border-red-200" : "bg-green-50 border border-green-200"}`}>
                        <p className="font-bold text-gray-900">
                            السعر العادل: {(aiFeedback.fairPrice || 0).toLocaleString()} جنيه
                        </p>
                        <p className="text-sm mt-1">
                            حالة السوق: <span className="font-semibold">{aiFeedback.marketStatus}</span>
                        </p>
                        {aiFeedback.isOverpriced && (
                            <p className="text-red-600 mt-2">⚠️ السعر أعلى من السوق بأكثر من 10%</p>
                        )}
                        {aiFeedback.reasoning && (
                            <ul className="mt-2 text-sm text-gray-600">
                                {aiFeedback.reasoning.map((r: string, i: number) => (
                                    <li key={i}>• {r}</li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {/* Reservation Fee */}
                <div className="mt-6 bg-green-50 p-4 rounded-xl border border-green-200">
                    <p className="text-sm text-gray-600 mb-1">مقدم الحجز</p>
                    <p className="text-2xl font-bold text-green-700">
                        {reservationFee.toLocaleString()} <span className="text-base">جنيه</span>
                    </p>
                </div>

                {/* Payment Instructions */}
                <div className="mt-6 space-y-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-sm font-medium text-blue-800">
                            الخطوة 1: حوّل عبر InstaPay إلى
                        </p>
                        <p className="text-lg font-bold text-blue-900 mt-1">osool@instapay</p>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            الخطوة 2: أدخل رقم المرجع
                        </label>
                        <input
                            type="text"
                            className="w-full border-2 border-gray-200 rounded-lg p-3 focus:border-green-500 focus:outline-none text-lg"
                            placeholder="مثال: 12345678"
                            value={instaPayRef}
                            onChange={(e) => setInstaPayRef(e.target.value)}
                        />
                    </div>
                </div>

                {/* Reserve Button */}
                <button
                    onClick={handleReservation}
                    disabled={loading || !account}
                    className={`mt-6 w-full py-4 px-4 rounded-xl shadow-lg font-bold text-lg transition-all
            ${loading || !account
                            ? "bg-gray-400 cursor-not-allowed text-gray-200"
                            : "bg-gradient-to-r from-green-600 to-green-700 text-white hover:from-green-700 hover:to-green-800 transform hover:scale-[1.02]"
                        }`}
                >
                    {loading ? "جاري التحقق..." : !account ? "سجل دخولك أولاً" : "✅ تأكيد الحجز"}
                </button>

                {/* Success State */}
                {txHash && (
                    <div className="mt-4 p-4 bg-green-100 rounded-lg">
                        <p className="text-green-800 font-bold">🎉 تم الحجز بنجاح!</p>
                        <p className="text-sm text-green-700 mt-1">إثبات البلوكتشين:</p>
                        <a
                            href={`https://amoy.polygonscan.com/tx/${txHash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 text-sm break-all hover:underline"
                        >
                            {txHash}
                        </a>
                    </div>
                )}

                <p className="mt-4 text-xs text-center text-gray-400">
                    مدعوم بتقنية Polygon Blockchain
                </p>
            </div>
        </div>
    );
}
