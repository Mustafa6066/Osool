"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

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

interface VisualizationRendererProps {
    type: string;
    data: any;
    isRTL?: boolean;
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
    const hasContent = (obj: any, keys: string[]): boolean => {
        if (!obj) return false;
        return keys.some(key => {
            const val = obj[key];
            if (Array.isArray(val)) return val.length > 0;
            if (typeof val === 'object' && val !== null) return Object.keys(val).length > 0;
            return val !== undefined && val !== null && val !== '';
        });
    };

    // Route to appropriate component based on type
    switch (type) {
        // V4: New Wolf Brain visualizations
        case "inflation_killer":
            // Accept multiple valid data keys from backend
            if (!hasContent(data, ['projections', 'data_points', 'summary', 'summary_cards', 'initial_investment', 'property_value', 'years'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InflationKillerChart {...data} />
                </Suspense>
            );

        case "la2ta_alert":
        case "لقطة":
            if (!hasContent(data, ['properties']) || !data.properties?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <La2taAlert {...data} isRTL={isRTL} />
                </Suspense>
            );

        case "law_114_guardian":
            // Accept status key from backend (used when guardian is activated)
            if (!hasContent(data, ['capabilities', 'result', 'trust_badges', 'status', 'cta'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <Law114Guardian {...data} />
                </Suspense>
            );

        case "reality_check":
            if (!hasContent(data, ['alternatives', 'message_ar', 'message_en'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <RealityCheck {...data} isRTL={isRTL} />
                </Suspense>
            );

        case "certificates_vs_property":
            if (!hasContent(data, ['summary', 'data_points', 'verdict'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <CertificatesVsProperty {...data} isRTL={isRTL} />
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
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <AreaAnalysis {...areaData} />
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
                    <DeveloperAnalysis {...devData} />
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
                    <PropertyTypeAnalysis {...typeData} />
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
                    <PaymentPlanComparison {...planData} />
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
                    resale_ready: data.resale?.pros?.includes('جاهز للتسليم') || true,
                    developer_payment_plan: data.developer?.pros?.includes('تقسيط طويل') || true
                }
            };
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <ResaleVsDeveloper {...resaleData} />
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
                    <ROICalculator {...roiData} />
                </Suspense>
            );
        }

        case "price_heatmap":
            if (!data.locations?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PriceHeatmap {...data} />
                </Suspense>
            );

        // Legacy visualization types
        case "investment_scorecard":
            if (!data.property && !data.analysis) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InvestmentScorecard
                        property={data.property}
                        analysis={data.analysis}
                    />
                </Suspense>
            );

        case "comparison_matrix":
            if (!data.properties?.length) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <ComparisonMatrix
                        properties={data.properties}
                        bestValueId={data.best_value_id}
                        recommendedId={data.recommended_id}
                    />
                </Suspense>
            );

        case "payment_timeline":
            if (!data.property && !data.payment) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PaymentTimeline
                        property={data.property}
                        payment={data.payment}
                    />
                </Suspense>
            );

        case "market_trend_chart":
            if (!data.trend_data?.length && !data.price_growth_ytd) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <MarketTrendChart
                        location={data.location || "Market"}
                        data={{
                            historical: data.trend_data?.map((d: any) => ({
                                period: d.month,
                                avg_price: d.price_index * 1000,
                                volume: d.volume
                            })) || [],
                            current_price: data.trend_data?.[data.trend_data.length - 1]?.price_index * 1000 || 0,
                            trend: data.price_growth_ytd > 15 ? "Bullish" : data.price_growth_ytd > 8 ? "Stable" : "Bearish",
                            yoy_change: data.price_growth_ytd || 0,
                            momentum: data.demand_index || "Medium"
                        }}
                    />
                </Suspense>
            );

        // Bank vs Property comparison (alias for certificates_vs_property)
        case "bank_vs_property":
            if (!hasContent(data, ['data_points', 'summary', 'verdict', 'assumptions'])) return null;
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <CertificatesVsProperty {...data} isRTL={isRTL} />
                </Suspense>
            );

        // Market benchmark visualization (shows market segment data)
        case "market_benchmark": {
            if (!hasContent(data, ['market_segment', 'area_context', 'avg_price_sqm'])) return null;
            const currentPrice = data.avg_price_sqm || 0;
            const growthRate = data.growth_rate || 0.12;
            // Generate synthetic historical points when backend sends empty array
            const historical = (data.historical && data.historical.length > 0)
                ? data.historical
                : Array.from({ length: 6 }, (_, i) => ({
                    date: `${2020 + i}`,
                    price: Math.round(currentPrice / Math.pow(1 + growthRate, 5 - i))
                }));
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <MarketTrendChart
                        location={data.market_segment?.name_en || data.area_context?.name || "Market"}
                        data={{
                            historical,
                            current_price: currentPrice,
                            trend: growthRate > 0.15 ? "Bullish" : growthRate > 0.08 ? "Stable" : "Bearish",
                            yoy_change: growthRate * 100,
                            momentum: "Medium"
                        }}
                    />
                </Suspense>
            );
        }

        // Property cards are rendered by ChatMain.tsx via the properties field
        case "property_cards":
            return null;

        default:
            return null;
    }
}
