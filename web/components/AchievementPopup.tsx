'use client';

import React, { useEffect, useState } from 'react';
import {
    Award, Eye, ShieldCheck, TrendingUp, Building2, Flame, Gem,
    CheckCircle, Heart, Crown, MapPin
} from 'lucide-react';

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
    'award': Award,
    'eye': Eye,
    'shield-check': ShieldCheck,
    'trending-up': TrendingUp,
    'building-2': Building2,
    'flame': Flame,
    'gem': Gem,
    'check-circle': CheckCircle,
    'heart': Heart,
    'crown': Crown,
    'map-pin': MapPin,
};

const TIER_STYLES: Record<string, string> = {
    bronze: 'from-amber-700 to-amber-900 border-amber-600',
    silver: 'from-gray-300 to-gray-500 border-gray-400',
    gold: 'from-yellow-400 to-amber-500 border-yellow-300',
};

interface AchievementPopupProps {
    achievementKey: string;
    titleEn: string;
    titleAr: string;
    icon: string;
    tier: string;
    xpReward: number;
    language?: string;
    onDone?: () => void;
}

/**
 * Achievement Popup - Slide-in celebration on badge unlock
 * Professional, not intrusive — small toast with icon.
 */
export default function AchievementPopup({
    achievementKey, titleEn, titleAr, icon, tier, xpReward, language = 'en', onDone
}: AchievementPopupProps) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            onDone?.();
        }, 4000);
        return () => clearTimeout(timer);
    }, [onDone]);

    const IconComponent = ICON_MAP[icon] || Award;
    const tierStyle = TIER_STYLES[tier] || TIER_STYLES.bronze;
    const title = language === 'ar' ? titleAr : titleEn;

    if (!visible) return null;

    return (
        <div
            className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5
                        bg-[#1e1f20] border border-[#3d3d3d] rounded-2xl
                        shadow-2xl shadow-black/40 animate-achievement-slide
                        max-w-sm`}
            dir={language === 'ar' ? 'rtl' : 'ltr'}
        >
            {/* Badge Icon */}
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tierStyle}
                            flex items-center justify-center flex-shrink-0 shadow-lg`}>
                <IconComponent className="w-6 h-6 text-white" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="text-[10px] font-bold text-teal-400 uppercase tracking-widest mb-0.5">
                    {language === 'ar' ? 'إنجاز جديد!' : 'Achievement Unlocked!'}
                </div>
                <div className="text-sm font-medium text-white truncate">
                    {title}
                </div>
                <div className="text-xs text-gray-400">
                    +{xpReward} XP
                </div>
            </div>
        </div>
    );
}
