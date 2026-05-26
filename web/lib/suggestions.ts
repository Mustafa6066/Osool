import { Search, Shield, TrendingUp, BarChart2, Zap, Rocket, Star, History, LineChart, Flame } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface Suggestion {
    icon: any;
    label: string;
    prompt: string;
    type?: string;
}

export interface SuggestionWithSnippet extends Suggestion {
    snippet: string;
    snippetAr: string;
    trend: 'up' | 'down' | 'neutral';
}

const ADVANCED_EN = [
    { icon: LineChart, label: "Market Benchmark", prompt: "Benchmark top developers in New Cairo across the last 3 years", snippet: "Historical analysis", snippetAr: "تحليل تاريخي", trend: "up" as const },
    { icon: Zap, label: "Inflation Protection", prompt: "Compare real estate vs bank CDs after factoring in inflation", snippet: "Wealth preservation", snippetAr: "حماية الثروة", trend: "neutral" as const }
];

const ADVANCED_AR = [
    { icon: LineChart, label: "قياس أداء السوق", prompt: "قارن أداء أفضل المطورين في القاهرة الجديدة خلال 3 سنوات", snippet: "تحليل تاريخي", snippetAr: "تحليل تاريخي", trend: "up" as const },
    { icon: Zap, label: "الحماية من التضخم", prompt: "مقارنة العقارات بشهادات البنك بعد حساب التضخم", snippet: "حماية الثروة", snippetAr: "حماية الثروة", trend: "neutral" as const }
];

const BASIC_EN = [
    { icon: BarChart2, label: "Market Intelligence", prompt: "Analyze current market trends in New Cairo", snippet: "+2.4% avg EGP/m² this week", snippetAr: "+٢.٤٪ متوسط سعر المتر", trend: 'up' as const },
    { icon: Search, label: "Find Opportunities", prompt: "Find high ROI properties under 5M EGP", snippet: "12 new high-ROI listings", snippetAr: "١٢ وحدة عائد عالي", trend: 'up' as const },
];

const BASIC_AR = [
    { icon: BarChart2, label: "تحليل السوق", prompt: "حلل اتجاهات السوق الحالية في القاهرة الجديدة", snippet: "+2.4% avg EGP/m² this week", snippetAr: "+٢.٤٪ متوسط سعر المتر هذا الأسبوع", trend: 'up' as const },
    { icon: Search, label: "فرص استثمارية", prompt: "ابحث عن عقارات عائد مرتفع تحت 5 مليون جنيه", snippet: "12 new high-ROI listings", snippetAr: "١٢ وحدة عائد مرتفع جديدة", trend: 'up' as const },
];

const GENERAL_EN = [
    { icon: Shield, label: "Developer Audit", prompt: "Audit the delivery history of Palm Hills", snippet: "Palm Hills: 94% on-time", snippetAr: "بالم هيلز: ٩٤٪ ملتزمين", trend: 'neutral' as const },
    { icon: TrendingUp, label: "Price Comparison", prompt: "Compare price per sqm across New Cairo, Sheikh Zayed, and North Coast", snippet: "North Coast +5.1% this week", snippetAr: "الساحل +٥.١٪ هذا الأسبوع", trend: 'up' as const },
];

const GENERAL_AR = [
    { icon: Shield, label: "تدقيق المطور", prompt: "دقق في سجل تسليمات بالم هيلز", snippet: "Palm Hills: 94% on-time", snippetAr: "بالم هيلز: ٩٤٪ تسليم في الموعد", trend: 'neutral' as const },
    { icon: TrendingUp, label: "مقارنة الأسعار", prompt: "قارن أسعار المتر في القاهرة الجديدة والشيخ زايد والساحل", snippet: "North Coast +5.1% this week", snippetAr: "الساحل +٥.١٪ هذا الأسبوع", trend: 'up' as const },
];

const TRENDING_EN = { icon: Flame, label: "Trending Query", prompt: "Show me the top appreciating compounds in October", snippet: "Based on 500+ recent searches", snippetAr: "بناء على أكثر من 500 بحث متداول", trend: 'up' as const };
const TRENDING_AR = { icon: Flame, label: "الأكثر بحثاً", prompt: "أظهر لي أفضل الكمبوندات نمواً في أكتوبر", snippet: "Based on 500+ recent searches", snippetAr: "بناء على أكثر من 500 بحث متداول", trend: 'up' as const };

export function getSmartEmptyStateSuggestions(lang: string, gamificationLevel: string, favoritesCount: number = 0): SuggestionWithSnippet[] {
    const isAr = lang === 'ar';
    const isAdvanced = ['analyst', 'strategist', 'mogul'].includes(gamificationLevel?.toLowerCase());
    
    let base = isAr ? [...BASIC_AR, ...GENERAL_AR] : [...BASIC_EN, ...GENERAL_EN];
    
    // Substitute a basic one with an advanced one for experienced users
    if (isAdvanced) {
        base[0] = isAr ? ADVANCED_AR[0] : ADVANCED_EN[0];
        base[1] = isAr ? ADVANCED_AR[1] : ADVANCED_EN[1];
    }

    // Add trending context
    base[3] = isAr ? TRENDING_AR : TRENDING_EN;

    return base.slice(0, 4);
}
