'use client';

/**
 * PriorityHandoff — Contextual Lead-to-Advisor Handoff
 * -------------------------------------------------------
 * Appears when a user's lead score reaches "warm" or "hot" tier.
 * Shows personalized action buttons based on their analyzed interests.
 *
 * Hot lead (85+):  "Priority Callback" + "Direct WhatsApp to Expert"
 * Warm lead (60+): "Schedule a Call" + interest summary
 */

import { useState } from 'react';
import { useLeadScore } from '@/contexts/LeadScoreContext';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

const WHATSAPP_NUMBER = '201000000000'; // Osool expert line

export default function PriorityHandoff() {
    const { isWarmLead, isHotLead, leadScore, preferredDevelopers, preferredAreas, tier, icpSegment } = useLeadScore();
    const { user } = useAuth();
    const { language } = useLanguage();
    const [dismissed, setDismissed] = useState(false);
    const [callbackRequested, setCallbackRequested] = useState(false);

    if (!isWarmLead || dismissed) return null;

    // Build personalized interest summary with ICP context
    const interestParts: string[] = [];
    if (preferredAreas.length > 0) {
        interestParts.push(
            language === 'ar'
                ? `مناطق: ${preferredAreas.slice(0, 3).join('، ')}`
                : `Areas: ${preferredAreas.slice(0, 3).join(', ')}`,
        );
    }
    if (preferredDevelopers.length > 0) {
        interestParts.push(
            language === 'ar'
                ? `مطورين: ${preferredDevelopers.slice(0, 3).join('، ')}`
                : `Developers: ${preferredDevelopers.slice(0, 3).join(', ')}`,
        );
    }

    // Translate ICP segment to user-friendly label
    const segmentLabels: Record<string, { en: string; ar: string }> = {
        expat_investor: { en: 'Expat Investment Advisory', ar: 'استشارات استثمار المغتربين' },
        domestic_hnw: { en: 'Premium Investment Advisory', ar: 'استشارات استثمار بريميوم' },
        institutional: { en: 'Institutional Support', ar: 'دعم مؤسسات' },
        first_time_buyer: { en: 'First-Time Buyer Support', ar: 'دعم المشترين الجدد' },
    };
    const segmentLabel = segmentLabels[icpSegment]?.[language === 'ar' ? 'ar' : 'en'] ?? '';

    const interestSummary = interestParts.join(' · ');

    // Build WhatsApp message with pre-filled context
    const whatsappMessage = encodeURIComponent(
        language === 'ar'
            ? `مرحباً، أنا مهتم بالعقارات في ${preferredAreas.slice(0, 2).join(' و ')}. هل ممكن تساعدوني؟`
            : `Hi, I'm interested in properties in ${preferredAreas.slice(0, 2).join(' and ')}. Can you help me?`,
    );
    const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${whatsappMessage}`;

    const handleRequestCallback = async () => {
        setCallbackRequested(true);
        try {
            await fetch('/api/leads/callback-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userId: user?.id,
                    preferredAreas,
                    preferredDevelopers,
                    leadScore,
                }),
            });
        } catch {
            // Silent
        }
    };

    return (
        <div className="fixed bottom-4 end-4 z-40 max-w-sm animate-in slide-in-from-bottom-4 fade-in duration-500">
            <div className={`rounded-2xl border p-4 shadow-2xl ${
                isHotLead
                    ? 'border-amber-500/30 bg-gradient-to-br from-amber-950/90 to-zinc-900/95 shadow-amber-500/10'
                    : 'border-emerald-500/20 bg-zinc-900/95 shadow-emerald-500/5'
            }`}>
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                        {isHotLead ? (
                            <span className="text-amber-400 text-lg">🔥</span>
                        ) : (
                            <span className="text-emerald-400 text-lg">✨</span>
                        )}
                        <h4 className="text-sm font-semibold text-white">
                            {isHotLead
                                ? (language === 'ar' ? 'مستشار متاح لك الآن' : 'Expert Available Now')
                                : (language === 'ar' ? 'هل تحتاج مساعدة؟' : 'Need Expert Help?')}
                        </h4>
                    </div>
                    <button
                        onClick={() => setDismissed(true)}
                        className="text-zinc-500 hover:text-zinc-300 transition-colors p-1"
                        aria-label="Dismiss"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>

                {/* Interest summary */}
                {interestSummary && (
                    <p className="text-xs text-zinc-400 mb-3 leading-relaxed">
                        {language === 'ar'
                            ? `شايفين أنك مهتم بـ ${interestSummary}`
                            : `We see you're exploring ${interestSummary}`}
                    </p>
                )}
                {segmentLabel && (
                    <p className="text-[10px] text-zinc-500 mb-2 uppercase tracking-wider font-medium">
                        {segmentLabel}
                    </p>
                )}

                {/* Action buttons */}
                <div className="flex flex-col gap-2">
                    {isHotLead && (
                        <a
                            href={whatsappUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 rounded-xl bg-green-600 hover:bg-green-500 px-4 py-2.5 text-sm font-medium text-white transition-colors"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                            </svg>
                            {language === 'ar' ? 'واتساب مع خبير' : 'WhatsApp Expert'}
                        </a>
                    )}

                    {!callbackRequested ? (
                        <button
                            onClick={handleRequestCallback}
                            className={`flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-colors ${
                                isHotLead
                                    ? 'bg-amber-600 hover:bg-amber-500 text-white'
                                    : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                            }`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                            {isHotLead
                                ? (language === 'ar' ? 'اطلب مكالمة أولوية' : 'Priority Callback')
                                : (language === 'ar' ? 'جدول مكالمة' : 'Schedule a Call')}
                        </button>
                    ) : (
                        <div className="flex items-center justify-center gap-2 rounded-xl bg-zinc-800 px-4 py-2.5 text-sm text-emerald-400">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            {language === 'ar' ? 'تم! هنتصل بيك قريب' : 'Done! We\'ll call you soon'}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
