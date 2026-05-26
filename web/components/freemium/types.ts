export interface CompoundBenchmarkSummary {
  compound_id: string;
  secondary_market_listing_count: number;
  compound_mean_normalized_sqm: number;
  compound_min_normalized_sqm: number;
  compound_max_normalized_sqm: number;
}

export interface ArbitrageAlternative {
  listing_id: string;
  compound_id: string;
  geographic_zone: string;
  total_price_egp: number;
  size_sqm: number;
  floor_level: number;
  view_orientation: string;
  delivery_year: number;
  is_secondary_market: boolean;
  cash_npv_egp: number;
  normalized_cash_price_sqm: number;
  savings_vs_offer_pct: number;
  discount_vs_compound_mean_pct: number;
  broker_direct_contact: string;
  building_number: string;
  exact_unit_id: string;
}

export interface RealityCheckResult {
  compound_id: string;
  offer_normalized_price_sqm: number;
  offer_cash_npv_egp: number;
  overpay_delta_pct: number;
  is_offer_la2ta: boolean;
  compound_benchmark: CompoundBenchmarkSummary;
  la2ta_alternatives_found: number;
  alternatives: ArbitrageAlternative[];
  is_premium_response: boolean;
  rate_limit_remaining: number | null;
  valuation_note: string;
}
