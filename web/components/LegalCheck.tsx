"use client";

/**
 * LegalCheck Component
 * 
 * The "Killer Feature" - AI Legal Contract Analysis
 * Users can paste/upload contract text and get a risk analysis.
 * This is a premium feature worth 500 EGP.
 */

import { useState } from "react";
import { API_URL } from "@/lib/contract";

interface LegalResult {
    risk_score: number;
    contract_type?: string;
    verdict: string;
    red_flags: string[];
    missing_clauses: string[];
    recommendations?: string[];
    legal_summary_arabic?: string;
    error?: string;
}

export default function LegalCheck() {
    const [contractText, setContractText] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<LegalResult | null>(null);

    const analyzeContract = async () => {
        if (contractText.length < 100) {
            alert("الرجاء إدخال نص العقد (100 حرف على الأقل)");
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/ai/audit-contract`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: contractText }),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Analysis failed", error);
            setResult({ error: "Failed to analyze contract", risk_score: -1, verdict: "Error", red_flags: [], missing_clauses: [] });
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (score: number) => {
        if (score < 30) return "text-green-600 bg-green-100";
        if (score < 60) return "text-yellow-600 bg-yellow-100";
        return "text-red-600 bg-red-100";
    };

    const getVerdictColor = (verdict: string) => {
        if (verdict.includes("Safe")) return "bg-green-500";
        if (verdict.includes("Caution")) return "bg-yellow-500";
        return "bg-red-500";
    };

    return (
        <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="p-8">
                {/* Header */}
                <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">
                        🕵️ فحص العقد الذكي
                    </h2>
                    <p className="text-gray-500 mt-2">
                        تحليل العقود بالذكاء الاصطناعي وفقاً للقانون المصري
                    </p>
                </div>

                {/* Contract Input */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        الصق نص العقد هنا (عربي أو إنجليزي)
                    </label>
                    <textarea
                        className="w-full h-64 border-2 border-gray-200 rounded-xl p-4 text-sm focus:border-purple-500 focus:outline-none resize-none"
                        placeholder="عقد بيع ابتدائي...
            
انه في يوم ... الموافق ...
اتفق الطرف الاول (البائع) والطرف الثاني (المشتري) على بيع الشقة..."
                        value={contractText}
                        onChange={(e) => setContractText(e.target.value)}
                        dir="auto"
                    />
                </div>

                {/* Analyze Button */}
                <button
                    onClick={analyzeContract}
                    disabled={loading}
                    className={`w-full py-4 rounded-xl font-bold text-lg transition-all
            ${loading
                            ? "bg-gray-400 cursor-not-allowed"
                            : "bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700"
                        }`}
                >
                    {loading ? "جاري التحليل..." : "🔍 تحليل العقد"}
                </button>

                {/* Results */}
                {result && !result.error && (
                    <div className="mt-8 space-y-4">
                        {/* Risk Score */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">
                            <span className="font-medium text-gray-700">درجة المخاطر</span>
                            <span className={`px-4 py-2 rounded-full font-bold ${getRiskColor(result.risk_score)}`}>
                                {result.risk_score}/100
                            </span>
                        </div>

                        {/* Verdict */}
                        <div className={`p-4 rounded-xl text-white text-center font-bold ${getVerdictColor(result.verdict)}`}>
                            {result.verdict === "Safe to Sign" && "✅ آمن للتوقيع"}
                            {result.verdict === "Proceed with Caution" && "⚠️ تابع بحذر"}
                            {result.verdict === "DO NOT SIGN" && "🚫 لا توقع!"}
                        </div>

                        {/* Contract Type */}
                        {result.contract_type && (
                            <div className="p-4 rounded-xl bg-blue-50">
                                <span className="font-medium text-blue-800">نوع العقد: </span>
                                <span className="text-blue-900">{result.contract_type}</span>
                            </div>
                        )}

                        {/* Red Flags */}
                        {result.red_flags && result.red_flags.length > 0 && (
                            <div className="p-4 rounded-xl bg-red-50">
                                <p className="font-bold text-red-700 mb-2">🚩 علامات خطر:</p>
                                <ul className="space-y-2">
                                    {result.red_flags.map((flag, i) => (
                                        <li key={i} className="text-red-600 text-sm">• {flag}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Missing Clauses */}
                        {result.missing_clauses && result.missing_clauses.length > 0 && (
                            <div className="p-4 rounded-xl bg-yellow-50">
                                <p className="font-bold text-yellow-700 mb-2">📋 بنود ناقصة:</p>
                                <ul className="space-y-2">
                                    {result.missing_clauses.map((clause, i) => (
                                        <li key={i} className="text-yellow-600 text-sm">• {clause}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Arabic Summary */}
                        {result.legal_summary_arabic && (
                            <div className="p-4 rounded-xl bg-gray-100">
                                <p className="font-bold text-gray-700 mb-2">📝 الملخص:</p>
                                <p className="text-gray-600 text-sm" dir="rtl">
                                    {result.legal_summary_arabic}
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Error State */}
                {result?.error && (
                    <div className="mt-4 p-4 bg-red-100 rounded-xl text-red-700">
                        خطأ في التحليل: {result.error}
                    </div>
                )}

                <p className="mt-6 text-xs text-center text-gray-400">
                    التحليل مبني على القانون المدني المصري رقم 131 وقانون 114 لسنة 1946
                </p>
            </div>
        </div>
    );
}
