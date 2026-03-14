"use client";

import dynamic from "next/dynamic";
import { Suspense, type ComponentProps } from "react";

// Lazy load visualization components for better performance
const InvestmentScorecard = dynamic(() => import("./InvestmentScorecard"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const ComparisonMatrix = dynamic(() => import("./ComparisonMatrix"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const PaymentTimeline = dynamic(() => import("./PaymentTimeline"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const MarketTrendChart = dynamic(() => import("./MarketTrendChart"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// V4: New Wolf Brain visualizations
const InflationKillerChart = dynamic(() => import("./InflationKillerChart"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const La2taAlert = dynamic(() => import("./La2taAlert"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const Law114Guardian = dynamic(() => import("./Law114Guardian"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const RealityCheck = dynamic(() => import("./RealityCheck"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const CertificatesVsProperty = dynamic(() => import("./CertificatesVsProperty"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// V6: Advanced Analytics Components
const AreaAnalysis = dynamic(() => import("./AreaAnalysis"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const DeveloperAnalysis = dynamic(() => import("./DeveloperAnalysis"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const PropertyTypeAnalysis = dynamic(() => import("./PropertyTypeAnalysis"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const PaymentPlanComparison = dynamic(() => import("./PaymentPlanComparison"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const ResaleVsDeveloper = dynamic(() => import("./ResaleVsDeveloper"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const ROICalculator = dynamic(() => import("./ROICalculator"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const PriceHeatmap = dynamic(() => import("./PriceHeatmap"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// V8: Market Benchmark (Analytics-First)
const MarketBenchmarkChart = dynamic(() => import("./MarketBenchmarkChart"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// V9: Price Growth Chart (Line chart — 2021-2026 trajectory)
const PriceGrowthChart = dynamic(() => import("./PriceGrowthChart"), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// V10: Data Tables
const DataTable = dynamic(() => import("./DataTable").then(mod => mod.default), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const FinancialComparisonTable = dynamic(() => import("./FinancialComparisonTable").then(mod => mod.default), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

const BankVsPropertyComparisonTable = dynamic(() => import("./FinancialComparisonTable").then(mod => mod.BankVsPropertyComparisonTable), {
    loading: () => <VisualizationSkeleton />,
    ssr: false,
});

// Loading skeleton
function VisualizationSkeleton() {
    return (
        <div className="animate-pulse bg-[var(--color-surface)] rounded-2xl p-6 border border-[var(--color-border)]">
            <div className="h-4 bg-[var(--color-surface-hover)] rounded w-1/3 mb-4"></div>
            <div className="h-32 bg-[var(--color-surface-hover)] rounded mb-4"></div>
            <div className="h-4 bg-[var(--color-surface-hover)] rounded w-2/3"></div>
        </div>
    );
}

export interface VisualizationRendererProps {
    type: string;
    data: VisualizationData;
    isRTL?: boolean;
}

interface ProjectionPoint {
    cash?: number;
    cash_real_value?: number;
    property?: number;
    property_total?: number;
}

interface TrendDataPoint {
    month?: string;
    price_index?: number;
    volume?: number;
}

interface AreaVisualizationData extends Record<string, unknown> {
    name?: string;
    avg_price_per_sqm?: number;
    avg_price_sqm?: number;
    demand_level?: string;
    best_for?: unknown[];
}

interface VisualizationData {
    projections?: unknown[];
    properties?: Array<Record<string, unknown>>;
    capabilities?: unknown;
    result?: unknown;
    trust_badges?: unknown;
    status?: unknown;
    cta?: unknown;
    summary?: unknown;
    data_points?: unknown[];
    verdict?: unknown;
    areas?: AreaVisualizationData[];
    area?: AreaVisualizationData | null;
    comparison?: unknown;
    price_heatmap?: unknown;
    heatmap?: unknown;
    developers?: Array<Record<string, unknown>>;
    developer?: Record<string, unknown> | null;
    metrics?: unknown;
    types?: unknown[];
    plans?: unknown[];
    recommendation?: unknown;
    assumptions?: unknown;
    trend_data?: TrendDataPoint[];
    price_growth_ytd?: number;
    location?: string;
    demand_index?: string;
    payment?: unknown;
    property?: Record<string, unknown> | null;
    best_value_id?: string | number;
    recommended_id?: string | number;
    best_plans?: Record<string, unknown>;
    resale?: Record<string, unknown>;
    locations?: Array<Record<string, unknown>>;
    area_context?: Record<string, unknown>;
    [key: string]: unknown;
}

/**
 * Dynamic Visualization Router
 *
 * Routes visualization types to their corresponding components.
 * Supports both legacy visualization types and new V4 Wolf Brain types.
 */
export default function VisualizationRenderer({ type, data, isRTL = true }: VisualizationRendererProps) {
    // Handle null/undefined data gracefully
    if (!data) {
        return null;
    }

    // Helper to check if data has meaningful content
    const hasContent = (obj: VisualizationData | null | undefined, keys: string[]): boolean => {
        if (!obj) return false;
        return keys.some(key => {
            const val = obj[key];
            if (Array.isArray(val)) return val.length > 0;
            if (typeof val === 'object' && val !== null) return Object.keys(val).length > 0;
            return val !== undefined && val !== null && val !== '';
        });
    };

    // Helper: check if value is a valid non-NaN number > 0
    const isValidNum = (v: unknown): boolean => typeof v === 'number' && isFinite(v) && v > 0;

    // Route to appropriate component based on type
    switch (type) {
        // V4: New Wolf Brain visualizations
        case "inflation_killer":
            // Accept multiple valid data keys from backend
            if (!hasContent(data, ['projections', 'data_points', 'summary', 'summary_cards', 'initial_investment', 'property_value', 'years'])) return null;
            // Extra guard: ensure projections have actual numeric values
            if (data.projections && data.projections.length > 0) {
                const hasRealData = data.projections.some((point) => {
                    const projection = typeof point === 'object' && point !== null ? point as ProjectionPoint : undefined;
                    return isValidNum(projection?.cash) || isValidNum(projection?.cash_real_value) || isValidNum(projection?.property) || isValidNum(projection?.property_total);
                });
                if (!hasRealData) return null;
            }
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InflationKillerChart {...(data as unknown as ComponentProps<typeof InflationKillerChart>)} />
                </Suspense>
            );

        case "la2ta_alert":
        case "لقطة":
            if (!hasContent(data, ['properties']) || !data.properties?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <La2taAlert {...(data as unknown as ComponentProps<typeof La2taAlert>)} isRTL={isRTL} />
                </Suspense>
            );

        case "law_114_guardian":
            // Accept status key from backend (used when guardian is activated)
            if (!hasContent(data, ['capabilities', 'result', 'trust_badges', 'status', 'cta'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <Law114Guardian {...(data as unknown as ComponentProps<typeof Law114Guardian>)} />
                </Suspense>
            );

        case "reality_check":
            if (!hasContent(data, ['alternatives', 'message_ar', 'message_en'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <RealityCheck {...(data as unknown as ComponentProps<typeof RealityCheck>)} isRTL={isRTL} />
                </Suspense>
            );

        case "certificates_vs_property":
            if (!hasContent(data, ['summary', 'data_points', 'verdict'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <CertificatesVsProperty {...(data as unknown as ComponentProps<typeof CertificatesVsProperty>)} isRTL={isRTL} />
                </Suspense>
            );

        // V6: Advanced Analytics visualizations
        // Map backend data structure to component props
        case "area_analysis": {
            const areaData = {
                area: data.areas?.[0] || data.area || null,
                comparison: data.comparison,
                heatmap: data.price_heatmap || data.heatmap
            };
            if (!areaData.area) return null;
            // Guard: don't render if area has no real numeric data
            const aPrice = areaData.area.avg_price_per_sqm || areaData.area.avg_price_sqm || 0;
            if (!areaData.area.name || (!isValidNum(aPrice) && !areaData.area.demand_level && !areaData.area.best_for?.length)) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <AreaAnalysis {...(areaData as unknown as ComponentProps<typeof AreaAnalysis>)} />
                </Suspense>
            );
        }

        case "developer_analysis": {
            const devData = {
                developer: data.developers?.[0] || data.developer || null,
                rankings: data.ranking || data.rankings
            };
            if (!devData.developer) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                        <DeveloperAnalysis {...(devData as unknown as ComponentProps<typeof DeveloperAnalysis>)} />
                </Suspense>
            );
        }

        case "property_type_analysis": {
            const typeData = {
                analysis: data.types?.[0] || data.analysis || null,
                comparison: data.price_comparison || data.comparison
            };
            if (!typeData.analysis) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                        <PropertyTypeAnalysis {...(typeData as unknown as ComponentProps<typeof PropertyTypeAnalysis>)} />
                </Suspense>
            );
        }

        case "payment_plan_comparison":
        case "payment_plan_analysis": {
            const planData = {
                plans: data.plans || [],
                best_down_payment: data.best_plans?.lowest_down_payment || data.best_down_payment,
                longest_installment: data.best_plans?.longest_installment || data.longest_installment,
                lowest_monthly: data.best_plans?.lowest_monthly || data.lowest_monthly
            };
            if (!planData.plans?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                        <PaymentPlanComparison {...(planData as unknown as ComponentProps<typeof PaymentPlanComparison>)} />
                </Suspense>
            );
        }

        case "resale_vs_developer": {
            // Backend sends: { resale: {...}, developer: {...}, recommendation: {...} }
            const resaleData = {
                recommendation: data.recommendation || { recommendation: data.resale ? 'resale' : 'developer', reason_ar: '', reason_en: '' },
                resale_discount: data.price_difference_percent || data.resale_discount || 0,
                comparison: {
                    resale_count: data.resale?.count || 0,
                    developer_count: data.developer?.count || 0,
                    resale_avg_price: data.resale?.avg_price || 0,
                    developer_avg_price: data.developer?.avg_price || 0,
                    resale_avg_price_per_sqm: data.resale?.avg_price_per_sqm || 0,
                    developer_avg_price_per_sqm: data.developer?.avg_price_per_sqm || 0,
                    resale_ready: (data.resale?.pros as unknown[] | undefined)?.includes('جاهز للتسليم') || true,
                    developer_payment_plan: (data.developer?.pros as unknown[] | undefined)?.includes('تقسيط طويل') || true
                }
            };
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                        <ResaleVsDeveloper {...(resaleData as unknown as ComponentProps<typeof ResaleVsDeveloper>)} />
                </Suspense>
            );
        }

        case "roi_calculator": {
            const roiData = {
                roi: data.properties?.[0] || data.roi || null,
                comparisons: data.comparison || data.comparisons
            };
            if (!roiData.roi) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                        <ROICalculator {...(roiData as unknown as ComponentProps<typeof ROICalculator>)} />
                </Suspense>
            );
        }

        case "price_heatmap":
            if (!data.locations?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PriceHeatmap {...(data as unknown as ComponentProps<typeof PriceHeatmap>)} />
                </Suspense>
            );

        // Legacy visualization types
        case "investment_scorecard":
            if (!data.property && !data.analysis) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InvestmentScorecard {...({ property: data.property, analysis: data.analysis } as unknown as ComponentProps<typeof InvestmentScorecard>)} />
                </Suspense>
            );

        case "comparison_matrix":
            if (!data.properties?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <ComparisonMatrix {...({ properties: data.properties, bestValueId: data.best_value_id, recommendedId: data.recommended_id } as unknown as ComponentProps<typeof ComparisonMatrix>)} />
                </Suspense>
            );

        case "payment_timeline":
            if (!data.property && !data.payment) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PaymentTimeline {...({ property: data.property, payment: data.payment } as unknown as ComponentProps<typeof PaymentTimeline>)} />
                </Suspense>
            );

        case "market_trend_chart": {
            if (!data.trend_data?.length && !data.price_growth_ytd) return null;
            const trendChartData = {
                location: data.location || "Market",
                data: {
                    historical: data.trend_data?.map((d) => ({
                        period: d.month,
                        avg_price: (d.price_index ?? 0) * 1000,
                        volume: d.volume
                    })) || [],
                    current_price: (data.trend_data?.[data.trend_data.length - 1]?.price_index ?? 0) * 1000 || 0,
                    trend: (data.price_growth_ytd ?? 0) > 15 ? "Bullish" : (data.price_growth_ytd ?? 0) > 8 ? "Stable" : "Bearish",
                    yoy_change: data.price_growth_ytd || 0,
                    momentum: data.demand_index || "Medium"
                }
            };
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <MarketTrendChart {...(trendChartData as unknown as ComponentProps<typeof MarketTrendChart>)} />
                </Suspense>
            );
        }

        // Bank vs Property comparison (alias for certificates_vs_property)
        case "bank_vs_property":
            if (!hasContent(data, ['data_points', 'summary', 'verdict', 'assumptions'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <CertificatesVsProperty {...(data as unknown as ComponentProps<typeof CertificatesVsProperty>)} isRTL={isRTL} />
                </Suspense>
            );

        // V9: Price Growth Chart (2021-2026 line chart)
        case "price_growth_chart": {
            if (!hasContent(data, ['data_points'])) return null;
            if (!data.data_points?.length || data.data_points.length < 2) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PriceGrowthChart {...(data as unknown as ComponentProps<typeof PriceGrowthChart>)} />
                </Suspense>
            );
        }

        // Market benchmark visualization (smart analytics chart)
        case "market_benchmark": {
            if (!hasContent(data, ['market_segment', 'area_context', 'avg_price_sqm'])) return null;
            // Guard: ensure actual price data exists
            const mbPrice = data.avg_price_sqm || data.area_context?.avg_price_sqm || 0;
            if (!isValidNum(mbPrice)) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <MarketBenchmarkChart {...(data as unknown as ComponentProps<typeof MarketBenchmarkChart>)} isRTL={isRTL} />
                </Suspense>
            );
        }

        // Property cards are rendered by ChatMain.tsx via the properties field
        case "property_cards":
            return null;

        // V10: Generic Data Table
        case "data_table":
        case "table": {
            if (!data.columns || !Array.isArray(data.columns) || !data.data || !Array.isArray(data.data)) {
                return null;
            }
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <DataTable {...({
                        title: data.title,
                        subtitle: data.subtitle,
                        columns: data.columns,
                        data: data.data,
                        isRTL,
                        colorScheme: data.colorScheme || 'neutral',
                        icon: data.icon,
                        maxHeight: data.maxHeight,
                        onRowClick: data.onRowClick
                    } as unknown as ComponentProps<typeof DataTable>)} />
                </Suspense>
            );
        }

        // V10: Financial Comparison Table (Bank vs Property, etc.)
        case "financial_comparison_table":
        case "comparison_table": {
            if (!data.rows || !Array.isArray(data.rows) || data.rows.length === 0) {
                return null;
            }
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <FinancialComparisonTable {...({
                        title: data.title || 'المقارنة المالية',
                        subtitle: data.subtitle,
                        rows: data.rows,
                        isRTL,
                        colorScheme: data.colorScheme || 'info',
                        showTrends: data.showTrends !== false
                    } as unknown as ComponentProps<typeof FinancialComparisonTable>)} />
                </Suspense>
            );
        }

        // Specific: Bank vs Property Comparison
        case "bank_vs_property_table": {
            if (!data.bankMonthly || !data.propertyMonthly) {
                return null;
            }
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <BankVsPropertyComparisonTable {...({
                        bankMonthly: data.bankMonthly,
                        bankActual: data.bankActual || data.bankMonthly,
                        propertyMonthly: data.propertyMonthly,
                        propertyActual: data.propertyActual || data.propertyMonthly,
                        isRTL
                    } as unknown as ComponentProps<typeof BankVsPropertyComparisonTable>)} />
                </Suspense>
            );
        }

        default:
            return null;
    }
}
