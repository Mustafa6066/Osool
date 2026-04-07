/**
 * Visualization Registry — Registry pattern for 25+ visualization types.
 *
 * Instead of a giant switch statement, each visualization is registered
 * with its component loader, data validator, and optional data transformer.
 *
 * Inspired by src/tools/tools.ts polymorphic tool registry pattern.
 */

import dynamic from 'next/dynamic';
import type { ComponentType } from 'react';

// ─── Types ───────────────────────────────────────────────

export interface VisualizationEntry {
  /** Lazy-loaded component */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  component: ComponentType<any>;
  /** Return true if data has enough content to render */
  validate: (data: Record<string, unknown>) => boolean;
  /** Optional: transform raw backend data into component props */
  transformProps?: (data: Record<string, unknown>, isRTL: boolean) => Record<string, unknown>;
}

// ─── Helpers ─────────────────────────────────────────────

/** Check if data has meaningful content for any of the given keys */
function hasContent(obj: Record<string, unknown> | null | undefined, keys: string[]): boolean {
  if (!obj) return false;
  return keys.some((key) => {
    const val = obj[key];
    if (Array.isArray(val)) return val.length > 0;
    if (typeof val === 'object' && val !== null) return Object.keys(val).length > 0;
    return val !== undefined && val !== null && val !== '';
  });
}

/** Check if value is a valid non-NaN number > 0 */
function isValidNum(v: unknown): boolean {
  return typeof v === 'number' && isFinite(v) && v > 0;
}

interface ProjectionPoint {
  cash?: number;
  cash_real_value?: number;
  property?: number;
  property_total?: number;
}

// ─── Registry ────────────────────────────────────────────

const registry = new Map<string, VisualizationEntry>();

export function registerVisualization(types: string | string[], entry: VisualizationEntry) {
  const typeList = Array.isArray(types) ? types : [types];
  for (const t of typeList) {
    registry.set(t, entry);
  }
}

export function getVisualization(type: string): VisualizationEntry | undefined {
  return registry.get(type);
}

export function getRegisteredTypes(): string[] {
  return Array.from(registry.keys());
}

// ─── Register all visualizations ─────────────────────────

// V4: Wolf Brain
registerVisualization('inflation_killer', {
  component: dynamic(() => import('./InflationKillerChart'), { ssr: false }),
  validate: (data) => {
    if (!hasContent(data, ['projections', 'data_points', 'summary', 'summary_cards', 'initial_investment', 'property_value', 'years'])) return false;
    if (data.projections && Array.isArray(data.projections) && data.projections.length > 0) {
      return data.projections.some((point) => {
        const p = typeof point === 'object' && point !== null ? (point as ProjectionPoint) : undefined;
        return isValidNum(p?.cash) || isValidNum(p?.cash_real_value) || isValidNum(p?.property) || isValidNum(p?.property_total);
      });
    }
    return true;
  },
});

registerVisualization(['la2ta_alert', 'لقطة'], {
  component: dynamic(() => import('./La2taAlert'), { ssr: false }),
  validate: (data) => hasContent(data, ['properties']) && Array.isArray(data.properties) && data.properties.length > 0,
  transformProps: (data, isRTL) => ({ ...data, isRTL }),
});

registerVisualization('law_114_guardian', {
  component: dynamic(() => import('./Law114Guardian'), { ssr: false }),
  validate: (data) => hasContent(data, ['capabilities', 'result', 'trust_badges', 'status', 'cta']),
});

registerVisualization('reality_check', {
  component: dynamic(() => import('./RealityCheck'), { ssr: false }),
  validate: (data) => hasContent(data, ['alternatives', 'message_ar', 'message_en']),
  transformProps: (data, isRTL) => ({ ...data, isRTL }),
});

registerVisualization(['certificates_vs_property', 'bank_vs_property'], {
  component: dynamic(() => import('./CertificatesVsProperty'), { ssr: false }),
  validate: (data) => hasContent(data, ['summary', 'data_points', 'verdict', 'assumptions']),
  transformProps: (data, isRTL) => ({ ...data, isRTL }),
});

// V6: Advanced Analytics
registerVisualization('area_analysis', {
  component: dynamic(() => import('./AreaAnalysis'), { ssr: false }),
  validate: (data) => {
    const areas = data.areas as Array<Record<string, unknown>> | undefined;
    const area = (areas?.[0] || data.area) as Record<string, unknown> | undefined;
    if (!area) return false;
    const aPrice = (area.avg_price_per_sqm || area.avg_price_sqm || 0) as number;
    return !!(area.name && (isValidNum(aPrice) || area.demand_level || (Array.isArray(area.best_for) && area.best_for.length)));
  },
  transformProps: (data) => {
    const areas = data.areas as Array<Record<string, unknown>> | undefined;
    return {
      area: areas?.[0] || data.area || null,
      comparison: data.comparison,
      heatmap: data.price_heatmap || data.heatmap,
    };
  },
});

registerVisualization('developer_analysis', {
  component: dynamic(() => import('./DeveloperAnalysis'), { ssr: false }),
  validate: (data) => {
    const devs = data.developers as Array<Record<string, unknown>> | undefined;
    return !!(devs?.[0] || data.developer);
  },
  transformProps: (data) => ({
    developer: (data.developers as Array<Record<string, unknown>> | undefined)?.[0] || data.developer || null,
    rankings: data.ranking || data.rankings,
  }),
});

registerVisualization('property_type_analysis', {
  component: dynamic(() => import('./PropertyTypeAnalysis'), { ssr: false }),
  validate: (data) => {
    const types = data.types as Array<Record<string, unknown>> | undefined;
    return !!(types?.[0] || data.analysis);
  },
  transformProps: (data) => ({
    analysis: (data.types as Array<Record<string, unknown>> | undefined)?.[0] || data.analysis || null,
    comparison: data.price_comparison || data.comparison,
  }),
});

registerVisualization(['payment_plan_comparison', 'payment_plan_analysis'], {
  component: dynamic(() => import('./PaymentPlanComparison'), { ssr: false }),
  validate: (data) => {
    const plans = data.plans as unknown[] | undefined;
    return Array.isArray(plans) && plans.length > 0;
  },
  transformProps: (data) => {
    const bestPlans = data.best_plans as Record<string, unknown> | undefined;
    return {
      plans: data.plans || [],
      best_down_payment: bestPlans?.lowest_down_payment || data.best_down_payment,
      longest_installment: bestPlans?.longest_installment || data.longest_installment,
      lowest_monthly: bestPlans?.lowest_monthly || data.lowest_monthly,
    };
  },
});

registerVisualization('resale_vs_developer', {
  component: dynamic(() => import('./ResaleVsDeveloper'), { ssr: false }),
  validate: () => true, // always renders if type matches
  transformProps: (data) => {
    const resale = data.resale as Record<string, unknown> | undefined;
    const developer = data.developer as Record<string, unknown> | undefined;
    return {
      recommendation: data.recommendation || { recommendation: resale ? 'resale' : 'developer', reason_ar: '', reason_en: '' },
      resale_discount: data.price_difference_percent || data.resale_discount || 0,
      comparison: {
        resale_count: resale?.count || 0,
        developer_count: developer?.count || 0,
        resale_avg_price: resale?.avg_price || 0,
        developer_avg_price: developer?.avg_price || 0,
        resale_avg_price_per_sqm: resale?.avg_price_per_sqm || 0,
        developer_avg_price_per_sqm: developer?.avg_price_per_sqm || 0,
        resale_ready: (resale?.pros as unknown[])?.includes('جاهز للتسليم') || true,
        developer_payment_plan: (developer?.pros as unknown[])?.includes('تقسيط طويل') || true,
      },
    };
  },
});

registerVisualization('roi_calculator', {
  component: dynamic(() => import('./ROICalculator'), { ssr: false }),
  validate: (data) => {
    const props = data.properties as Array<Record<string, unknown>> | undefined;
    return !!(props?.[0] || data.roi);
  },
  transformProps: (data) => ({
    roi: (data.properties as Array<Record<string, unknown>> | undefined)?.[0] || data.roi || null,
    comparisons: data.comparison || data.comparisons,
  }),
});

registerVisualization('price_heatmap', {
  component: dynamic(() => import('./PriceHeatmap'), { ssr: false }),
  validate: (data) => Array.isArray(data.locations) && data.locations.length > 0,
});

// Legacy types
registerVisualization('investment_scorecard', {
  component: dynamic(() => import('./InvestmentScorecard'), { ssr: false }),
  validate: (data) => !!(data.property || data.analysis),
  transformProps: (data) => ({ property: data.property, analysis: data.analysis }),
});

registerVisualization('comparison_matrix', {
  component: dynamic(() => import('./ComparisonMatrix'), { ssr: false }),
  validate: (data) => Array.isArray(data.properties) && data.properties.length > 0,
  transformProps: (data) => ({ properties: data.properties, bestValueId: data.best_value_id, recommendedId: data.recommended_id }),
});

registerVisualization('payment_timeline', {
  component: dynamic(() => import('./PaymentTimeline'), { ssr: false }),
  validate: (data) => !!(data.property || data.payment),
  transformProps: (data) => ({ property: data.property, payment: data.payment }),
});

interface TrendDataPoint {
  month?: string;
  price_index?: number;
  volume?: number;
}

registerVisualization('market_trend_chart', {
  component: dynamic(() => import('./MarketTrendChart'), { ssr: false }),
  validate: (data) => {
    const trendData = data.trend_data as TrendDataPoint[] | undefined;
    return (Array.isArray(trendData) && trendData.length > 0) || isValidNum(data.price_growth_ytd);
  },
  transformProps: (data) => {
    const trendData = data.trend_data as TrendDataPoint[] | undefined;
    return {
      location: data.location || 'Market',
      data: {
        historical: trendData?.map((d) => ({
          period: d.month,
          avg_price: (d.price_index ?? 0) * 1000,
          volume: d.volume,
        })) || [],
        current_price: (trendData?.[trendData.length - 1]?.price_index ?? 0) * 1000 || 0,
        trend: ((data.price_growth_ytd as number) ?? 0) > 15 ? 'Bullish' : ((data.price_growth_ytd as number) ?? 0) > 8 ? 'Stable' : 'Bearish',
        yoy_change: data.price_growth_ytd || 0,
        momentum: data.demand_index || 'Medium',
      },
    };
  },
});

// V9: Price Growth Chart
registerVisualization('price_growth_chart', {
  component: dynamic(() => import('./PriceGrowthChart'), { ssr: false }),
  validate: (data) => {
    const pts = data.data_points as unknown[] | undefined;
    return Array.isArray(pts) && pts.length >= 2;
  },
});

// V8: Market Benchmark
registerVisualization('market_benchmark', {
  component: dynamic(() => import('./MarketBenchmarkChart'), { ssr: false }),
  validate: (data) => {
    if (!hasContent(data, ['market_segment', 'area_context', 'avg_price_sqm'])) return false;
    const ctx = data.area_context as Record<string, unknown> | undefined;
    return isValidNum(data.avg_price_sqm) || isValidNum(ctx?.avg_price_sqm);
  },
  transformProps: (data, isRTL) => ({ ...data, isRTL }),
});

// property_cards — rendered by ChatMain.tsx, not here
registerVisualization('property_cards', {
  component: (() => null) as unknown as ComponentType<any>,
  validate: () => false,
});

// V10: Data Tables
registerVisualization(['data_table', 'table'], {
  component: dynamic(() => import('./DataTable').then((mod) => mod.default), { ssr: false }),
  validate: (data) => Array.isArray(data.columns) && Array.isArray(data.data),
  transformProps: (data, isRTL) => ({
    title: data.title,
    subtitle: data.subtitle,
    columns: data.columns,
    data: data.data,
    isRTL,
    colorScheme: data.colorScheme || 'neutral',
    icon: data.icon,
    maxHeight: data.maxHeight,
    onRowClick: data.onRowClick,
  }),
});

registerVisualization(['financial_comparison_table', 'comparison_table'], {
  component: dynamic(() => import('./FinancialComparisonTable').then((mod) => mod.default), { ssr: false }),
  validate: (data) => Array.isArray(data.rows) && data.rows.length > 0,
  transformProps: (data, isRTL) => ({
    title: data.title || 'المقارنة المالية',
    subtitle: data.subtitle,
    rows: data.rows,
    isRTL,
    colorScheme: data.colorScheme || 'info',
    showTrends: data.showTrends !== false,
  }),
});

registerVisualization('bank_vs_property_table', {
  component: dynamic(
    () => import('./FinancialComparisonTable').then((mod) => mod.BankVsPropertyComparisonTable),
    { ssr: false },
  ),
  validate: (data) => !!(data.bankMonthly && data.propertyMonthly),
  transformProps: (data, isRTL) => ({
    bankMonthly: data.bankMonthly,
    bankActual: data.bankActual || data.bankMonthly,
    propertyMonthly: data.propertyMonthly,
    propertyActual: data.propertyActual || data.propertyMonthly,
    isRTL,
  }),
});
