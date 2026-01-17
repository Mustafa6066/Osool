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
}

/**
 * Dynamic Visualization Router
 *
 * Routes visualization types to their corresponding components.
 * Supports both legacy visualization types and new V4 Wolf Brain types.
 */
export default function VisualizationRenderer({ type, data }: VisualizationRendererProps) {
    // Handle null/undefined data gracefully
    if (!data) {
        console.warn(`VisualizationRenderer: No data provided for type "${type}"`);
        return null;
    }

    // Route to appropriate component based on type
    switch (type) {
        // V4: New Wolf Brain visualizations
        case "inflation_killer":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InflationKillerChart {...data} />
                </Suspense>
            );

        case "la2ta_alert":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <La2taAlert {...data} />
                </Suspense>
            );

        case "law_114_guardian":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <Law114Guardian {...data} />
                </Suspense>
            );

        case "reality_check":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <RealityCheck {...data} />
                </Suspense>
            );

        // Legacy visualization types
        case "investment_scorecard":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <InvestmentScorecard
                        property={data.property}
                        analysis={data.analysis}
                    />
                </Suspense>
            );

        case "comparison_matrix":
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
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <PaymentTimeline
                        property={data.property}
                        payment={data.payment}
                    />
                </Suspense>
            );

        case "market_trend_chart":
            return (
                <Suspense fallback={<VisualizationSkeleton />}>
                    <MarketTrendChart
                        location={data.location}
                        data={data.data}
                    />
                </Suspense>
            );

        default:
            // Unknown visualization type - log warning but don't break
            console.warn(`VisualizationRenderer: Unknown visualization type "${type}"`);
            return null;
    }
}
