'use client';

/**
 * Osool Analytics Rules Engine
 * Client-side query detection system for triggering real estate analytics
 *
 * Detects user intent from natural language queries and triggers
 * appropriate visualizations and analytics components.
 */

// ============================================
// TYPE DEFINITIONS
// ============================================

export type VisualizationType =
    | 'area_analysis'
    | 'price_heatmap'
    | 'developer_analysis'
    | 'property_type_analysis'
    | 'payment_plan_comparison'
    | 'resale_vs_developer'
    | 'roi_calculator'
    | 'market_trend_chart'
    | 'investment_scorecard'
    | 'comparison_matrix';

export interface AnalyticsRule {
    id: string;
    name: string;
    nameAr: string;
    description: string;
    triggers: {
        arabic: string[];
        english: string[];
    };
    visualizations: VisualizationType[];
    priority: number;
    extractors?: {
        areas?: boolean;
        developers?: boolean;
        propertyTypes?: boolean;
        priceRange?: boolean;
    };
}

export interface AnalyticsMatch {
    rule: AnalyticsRule;
    matchedTriggers: string[];
    confidence: number;
    extractedContext: ExtractedContext;
}

export interface ExtractedContext {
    areas: string[];
    developers: string[];
    propertyTypes: string[];
    priceRange?: { min?: number; max?: number };
    keywords: string[];
}

// ============================================
// ANALYTICS RULES DEFINITIONS
// ============================================

const ANALYTICS_RULES: AnalyticsRule[] = [
    {
        id: 'area_analysis',
        name: 'Area Analysis',
        nameAr: 'تحليل المنطقة',
        description: 'Triggers area analysis when user mentions specific locations',
        triggers: {
            arabic: [
                'التجمع', 'التجمع الخامس', 'القاهرة الجديدة', 'مدينتي', 'الرحاب',
                'الشيخ زايد', 'زايد', 'السادس من اكتوبر', '6 اكتوبر', 'اكتوبر',
                'العاصمة الإدارية', 'العاصمه الاداريه', 'المستقبل', 'مستقبل سيتي',
                'الشروق', 'بدر', 'العبور', 'المعادي', 'مصر الجديدة', 'هليوبوليس',
                'الساحل الشمالي', 'الساحل', 'العين السخنة', 'السخنة', 'الجونة',
                'سهل حشيش', 'راس سدر', 'العلمين', 'مرسى مطروح',
                'في منطقة', 'بمنطقة', 'منطقة', 'في حي', 'بحي'
            ],
            english: [
                'new cairo', 'fifth settlement', 'madinaty', 'rehab', 'el rehab',
                'sheikh zayed', 'zayed', '6th october', 'sixth october', 'october city',
                'new capital', 'administrative capital', 'mostakbal', 'mostakbal city',
                'el shorouk', 'shorouk', 'badr city', 'obour', 'maadi', 'heliopolis',
                'north coast', 'sahel', 'ain sokhna', 'sokhna', 'el gouna',
                'sahl hasheesh', 'ras sudr', 'alamein', 'marsa matrouh',
                'in area', 'at location', 'near'
            ]
        },
        visualizations: ['area_analysis', 'price_heatmap'],
        priority: 1,
        extractors: { areas: true }
    },
    {
        id: 'developer_analysis',
        name: 'Developer Analysis',
        nameAr: 'تحليل المطور',
        description: 'Triggers developer analysis when user mentions developers',
        triggers: {
            arabic: [
                'طلعت مصطفى', 'مجموعة طلعت مصطفى', 'TMG',
                'بالم هيلز', 'بالم هيلز للتعمير',
                'سوديك', 'SODIC',
                'ماونتن فيو', 'ماونتين فيو',
                'اعمار', 'إعمار', 'اعمار مصر',
                'حسن علام', 'حسن علام العقارية',
                'لافيستا', 'لا فيستا',
                'المراسم', 'المراسم للتنمية',
                'اورا', 'أورا', 'اورا للتطوير',
                'سيتي ايدج', 'city edge',
                'مدينة نصر للاسكان', 'MNHD',
                'الأهلي صبور', 'الاهلي صبور',
                'تطوير مصر', 'Tatweer Misr',
                'مشاريع', 'مشروعات', 'من مطور', 'المطور'
            ],
            english: [
                'talaat moustafa', 'tmg', 'talaat mostafa',
                'palm hills', 'palmhills',
                'sodic', 'solidere',
                'mountain view', 'mountainview', 'mv',
                'emaar', 'emaar misr',
                'hassan allam', 'hassanallam',
                'la vista', 'lavista',
                'al marasem', 'marasem',
                'ora developers', 'ora',
                'city edge',
                'madinet nasr housing', 'mnhd',
                'al ahly sabbour', 'sabbour',
                'tatweer misr',
                'developer', 'projects by', 'developed by'
            ]
        },
        visualizations: ['developer_analysis'],
        priority: 2,
        extractors: { developers: true }
    },
    {
        id: 'property_type_analysis',
        name: 'Property Type Analysis',
        nameAr: 'تحليل نوع العقار',
        description: 'Triggers property type analysis when comparing types',
        triggers: {
            arabic: [
                'فيلا', 'فيلات', 'الفيلا', 'الفيلات',
                'تاون هاوس', 'تاونهاوس', 'تاون هاوز',
                'توين هاوس', 'توينهاوس', 'توين هاوز',
                'شقة', 'شقق', 'الشقة', 'الشقق',
                'بنتهاوس', 'بنت هاوس',
                'دوبلكس', 'دوبليكس',
                'ستوديو', 'استوديو',
                'روف', 'رووف',
                'الفرق بين', 'مقارنة بين', 'ايه الفرق',
                'افضل نوع', 'أفضل نوع', 'انواع العقارات'
            ],
            english: [
                'villa', 'villas',
                'townhouse', 'town house', 'townhouses',
                'twin house', 'twinhouse',
                'apartment', 'apartments', 'flat', 'flats',
                'penthouse', 'penthouses',
                'duplex', 'duplexes',
                'studio', 'studios',
                'roof', 'rooftop',
                'difference between', 'compare', 'comparison',
                'best type', 'property types', 'which type'
            ]
        },
        visualizations: ['property_type_analysis'],
        priority: 3,
        extractors: { propertyTypes: true }
    },
    {
        id: 'payment_plan_analysis',
        name: 'Payment Plan Analysis',
        nameAr: 'تحليل خطط السداد',
        description: 'Triggers payment plan analysis for installment queries',
        triggers: {
            arabic: [
                'مقدم', 'المقدم', 'اقل مقدم', 'أقل مقدم',
                'أقساط', 'اقساط', 'قسط', 'تقسيط',
                'سنوات', 'سنين', 'شهري', 'شهريا',
                'دفعة', 'دفعات', 'الدفعات',
                'خطة سداد', 'خطط السداد', 'نظام السداد',
                'فائدة', 'بدون فوائد', 'بفوائد',
                'كاش', 'نقدي', 'نقدا',
                'استلام', 'موعد الاستلام', 'التسليم'
            ],
            english: [
                'down payment', 'downpayment', 'deposit',
                'installment', 'installments', 'monthly payment',
                'years', 'months', 'monthly',
                'payment', 'payments',
                'payment plan', 'payment plans', 'payment schedule',
                'interest', 'interest free', 'no interest',
                'cash', 'full payment',
                'delivery', 'handover', 'delivery date'
            ]
        },
        visualizations: ['payment_plan_comparison'],
        priority: 4
    },
    {
        id: 'resale_vs_developer',
        name: 'Resale vs Developer',
        nameAr: 'ريسيل مقابل المطور',
        description: 'Triggers resale vs developer comparison',
        triggers: {
            arabic: [
                'ريسيل', 'ريسال', 'إعادة البيع', 'اعادة البيع',
                'من المطور', 'من المالك', 'مباشر',
                'ثانوي', 'سوق ثانوي', 'الثانوي',
                'جديد', 'جديدة', 'اول ساكن',
                'اشتري ريسيل', 'اشتري من المطور',
                'ريسيل ولا', 'من المطور ولا',
                'الفرق بين الريسيل', 'مميزات الريسيل'
            ],
            english: [
                'resale', 're-sale', 'resell',
                'from developer', 'primary', 'direct',
                'secondary', 'secondary market',
                'new', 'brand new', 'first owner',
                'buy resale', 'buy from developer',
                'resale or', 'developer or',
                'resale vs', 'primary vs secondary'
            ]
        },
        visualizations: ['resale_vs_developer'],
        priority: 5
    },
    {
        id: 'investment_roi',
        name: 'ROI Calculator',
        nameAr: 'حاسبة العائد الاستثماري',
        description: 'Triggers ROI calculator for investment queries',
        triggers: {
            arabic: [
                'استثمار', 'استثمر', 'عايز استثمر',
                'عائد', 'العائد', 'عائد الاستثمار',
                'ROI', 'ربح', 'الربح', 'مكسب',
                'دخل إيجار', 'دخل ايجار', 'إيجار',
                'عائد سنوي', 'عائد شهري',
                'افضل استثمار', 'أفضل استثمار',
                'فلوس', 'فلوسي', 'راس المال',
                'عقار استثماري', 'للاستثمار',
                'ايه الأفضل للاستثمار', 'احسن استثمار'
            ],
            english: [
                'investment', 'invest', 'investing',
                'return', 'returns', 'return on investment',
                'ROI', 'profit', 'profits', 'gain',
                'rental income', 'rent', 'rental',
                'annual return', 'monthly return', 'yearly return',
                'best investment', 'good investment',
                'money', 'capital', 'budget',
                'investment property', 'for investment',
                'what to invest', 'where to invest'
            ]
        },
        visualizations: ['roi_calculator', 'investment_scorecard'],
        priority: 6
    }
];

// ============================================
// CONTEXT EXTRACTORS
// ============================================

const KNOWN_AREAS = [
    // Cairo
    { ar: 'التجمع الخامس', en: 'New Cairo' },
    { ar: 'التجمع', en: 'Fifth Settlement' },
    { ar: 'القاهرة الجديدة', en: 'New Cairo' },
    { ar: 'مدينتي', en: 'Madinaty' },
    { ar: 'الرحاب', en: 'Rehab' },
    { ar: 'الشروق', en: 'El Shorouk' },
    { ar: 'العبور', en: 'Obour' },
    { ar: 'بدر', en: 'Badr City' },
    // Giza
    { ar: 'الشيخ زايد', en: 'Sheikh Zayed' },
    { ar: 'السادس من اكتوبر', en: '6th October' },
    { ar: '6 اكتوبر', en: '6th October' },
    // New Capital
    { ar: 'العاصمة الإدارية', en: 'New Capital' },
    { ar: 'المستقبل', en: 'Mostakbal City' },
    // Coastal
    { ar: 'الساحل الشمالي', en: 'North Coast' },
    { ar: 'العين السخنة', en: 'Ain Sokhna' },
    { ar: 'الجونة', en: 'El Gouna' },
    { ar: 'العلمين', en: 'Alamein' },
];

const KNOWN_DEVELOPERS = [
    { ar: 'طلعت مصطفى', en: 'Talaat Moustafa Group' },
    { ar: 'بالم هيلز', en: 'Palm Hills' },
    { ar: 'سوديك', en: 'SODIC' },
    { ar: 'ماونتن فيو', en: 'Mountain View' },
    { ar: 'إعمار', en: 'Emaar Misr' },
    { ar: 'حسن علام', en: 'Hassan Allam' },
    { ar: 'لافيستا', en: 'La Vista' },
    { ar: 'المراسم', en: 'Al Marasem' },
    { ar: 'أورا', en: 'Ora Developers' },
    { ar: 'سيتي ايدج', en: 'City Edge' },
    { ar: 'تطوير مصر', en: 'Tatweer Misr' },
    { ar: 'الأهلي صبور', en: 'Al Ahly Sabbour' },
];

const KNOWN_PROPERTY_TYPES = [
    { ar: 'فيلا', en: 'Villa' },
    { ar: 'تاون هاوس', en: 'Townhouse' },
    { ar: 'توين هاوس', en: 'Twin House' },
    { ar: 'شقة', en: 'Apartment' },
    { ar: 'بنتهاوس', en: 'Penthouse' },
    { ar: 'دوبلكس', en: 'Duplex' },
    { ar: 'ستوديو', en: 'Studio' },
    { ar: 'روف', en: 'Roof' },
];

// ============================================
// ANALYTICS RULES ENGINE CLASS
// ============================================

export class AnalyticsRulesEngine {
    private rules: AnalyticsRule[];

    constructor() {
        this.rules = ANALYTICS_RULES;
    }

    /**
     * Normalize text for matching (lowercase, remove diacritics)
     */
    private normalize(text: string): string {
        return text
            .toLowerCase()
            .replace(/[\u064B-\u065F]/g, '') // Remove Arabic diacritics
            .replace(/[أإآ]/g, 'ا') // Normalize Arabic alef
            .replace(/[ة]/g, 'ه') // Normalize Arabic taa marbuta
            .replace(/[ى]/g, 'ي') // Normalize Arabic yaa
            .trim();
    }

    /**
     * Calculate confidence score for a match
     */
    private calculateConfidence(query: string, trigger: string, matchCount: number): number {
        const normalizedQuery = this.normalize(query);
        const normalizedTrigger = this.normalize(trigger);

        // Base confidence from exact match
        let confidence = 0.5;

        // Boost for exact word match
        const words = normalizedQuery.split(/\s+/);
        if (words.includes(normalizedTrigger)) {
            confidence += 0.3;
        }

        // Boost for multiple trigger matches
        confidence += Math.min(matchCount * 0.1, 0.2);

        // Boost for longer triggers (more specific)
        if (trigger.length > 6) {
            confidence += 0.1;
        }

        return Math.min(confidence, 1.0);
    }

    /**
     * Extract areas mentioned in the query
     */
    private extractAreas(query: string): string[] {
        const normalizedQuery = this.normalize(query);
        const areas: string[] = [];

        for (const area of KNOWN_AREAS) {
            if (normalizedQuery.includes(this.normalize(area.ar)) ||
                normalizedQuery.includes(this.normalize(area.en))) {
                areas.push(area.en);
            }
        }

        return [...new Set(areas)];
    }

    /**
     * Extract developers mentioned in the query
     */
    private extractDevelopers(query: string): string[] {
        const normalizedQuery = this.normalize(query);
        const developers: string[] = [];

        for (const dev of KNOWN_DEVELOPERS) {
            if (normalizedQuery.includes(this.normalize(dev.ar)) ||
                normalizedQuery.includes(this.normalize(dev.en))) {
                developers.push(dev.en);
            }
        }

        return [...new Set(developers)];
    }

    /**
     * Extract property types mentioned in the query
     */
    private extractPropertyTypes(query: string): string[] {
        const normalizedQuery = this.normalize(query);
        const types: string[] = [];

        for (const type of KNOWN_PROPERTY_TYPES) {
            if (normalizedQuery.includes(this.normalize(type.ar)) ||
                normalizedQuery.includes(this.normalize(type.en))) {
                types.push(type.en);
            }
        }

        return [...new Set(types)];
    }

    /**
     * Extract price range from query (if mentioned)
     */
    private extractPriceRange(query: string): { min?: number; max?: number } | undefined {
        const priceRange: { min?: number; max?: number } = {};

        // Match patterns like "من 2 مليون" or "under 3 million"
        const millionPattern = /(\d+(?:\.\d+)?)\s*(?:مليون|million)/gi;
        const matches = query.match(millionPattern);

        if (matches && matches.length > 0) {
            const numbers = matches.map(m => {
                const num = parseFloat(m.match(/\d+(?:\.\d+)?/)?.[0] || '0');
                return num * 1000000;
            });

            if (query.includes('من') || query.includes('from') || query.includes('above')) {
                priceRange.min = Math.min(...numbers);
            }
            if (query.includes('إلى') || query.includes('to') || query.includes('under') || query.includes('below')) {
                priceRange.max = Math.max(...numbers);
            }

            // If just one number mentioned, use as max
            if (numbers.length === 1 && !priceRange.min && !priceRange.max) {
                priceRange.max = numbers[0];
            }
        }

        return Object.keys(priceRange).length > 0 ? priceRange : undefined;
    }

    /**
     * Main detection method - analyzes query and returns matched analytics
     */
    detectAnalytics(query: string): AnalyticsMatch[] {
        const normalizedQuery = this.normalize(query);
        const matches: AnalyticsMatch[] = [];

        for (const rule of this.rules) {
            const allTriggers = [...rule.triggers.arabic, ...rule.triggers.english];
            const matchedTriggers: string[] = [];

            for (const trigger of allTriggers) {
                if (normalizedQuery.includes(this.normalize(trigger))) {
                    matchedTriggers.push(trigger);
                }
            }

            if (matchedTriggers.length > 0) {
                // Extract context based on rule extractors
                const extractedContext: ExtractedContext = {
                    areas: rule.extractors?.areas ? this.extractAreas(query) : [],
                    developers: rule.extractors?.developers ? this.extractDevelopers(query) : [],
                    propertyTypes: rule.extractors?.propertyTypes ? this.extractPropertyTypes(query) : [],
                    priceRange: this.extractPriceRange(query),
                    keywords: matchedTriggers,
                };

                matches.push({
                    rule,
                    matchedTriggers,
                    confidence: this.calculateConfidence(query, matchedTriggers[0], matchedTriggers.length),
                    extractedContext,
                });
            }
        }

        // Sort by confidence (highest first), then by priority
        return matches.sort((a, b) => {
            if (b.confidence !== a.confidence) {
                return b.confidence - a.confidence;
            }
            return a.rule.priority - b.rule.priority;
        });
    }

    /**
     * Get visualization types to trigger based on detected analytics
     */
    getVisualizationsToTrigger(matches: AnalyticsMatch[]): VisualizationType[] {
        const visualizations: Set<VisualizationType> = new Set();

        for (const match of matches) {
            for (const viz of match.rule.visualizations) {
                visualizations.add(viz);
            }
        }

        return Array.from(visualizations);
    }

    /**
     * Build context data for API request
     */
    buildAnalyticsContext(matches: AnalyticsMatch[]): Record<string, any> {
        const context: Record<string, any> = {
            detected_intents: matches.map(m => m.rule.id),
            visualizations_requested: this.getVisualizationsToTrigger(matches),
            areas: [],
            developers: [],
            property_types: [],
            price_range: null,
        };

        // Merge extracted context from all matches
        for (const match of matches) {
            context.areas.push(...match.extractedContext.areas);
            context.developers.push(...match.extractedContext.developers);
            context.property_types.push(...match.extractedContext.propertyTypes);

            if (match.extractedContext.priceRange) {
                context.price_range = match.extractedContext.priceRange;
            }
        }

        // Deduplicate
        context.areas = [...new Set(context.areas)];
        context.developers = [...new Set(context.developers)];
        context.property_types = [...new Set(context.property_types)];

        return context;
    }

    /**
     * Get all available rules
     */
    getRules(): AnalyticsRule[] {
        return this.rules;
    }

    /**
     * Get a specific rule by ID
     */
    getRule(id: string): AnalyticsRule | undefined {
        return this.rules.find(r => r.id === id);
    }
}

// Export singleton instance for convenience
export const analyticsEngine = new AnalyticsRulesEngine();

// Export default for module usage
export default AnalyticsRulesEngine;
