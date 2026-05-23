/**
 * types.ts
 * ─────────────────────────────────────────────────────────────────
 * Shared type definitions for the dynamic_ui primitive library.
 *
 * All financial quantities are denominated in Egyptian Pounds (EGP).
 * Percentage values are expressed as fractions in [0, 1] unless the
 * field name includes the suffix `Pct` in which case it is 0–100.
 */

// ── Financial Metrics ─────────────────────────────────────────────

export interface FinancialMetrics {
  /** Cash-equivalent NPV in EGP, discounted at the CBE corridor rate */
  cashNpvEgp: number;
  /** Nominal advertised asking price in EGP (sticker) */
  nominalPriceEgp: number;
  /** Implied cash discount versus nominal (EGP) */
  discountEgp: number;
  /** Discount depth as a fraction of nominal price (0–1) */
  discountPct: number;
  /** Normalised price per sqm after NPV + feature adjustments (EGP/sqm) */
  normalizedPricePerSqmEgp: number;
  /** Raw feature score multiplier — 1.0 represents a neutral baseline */
  featureMultiplier: number;
  /** Effective multiplier after delivery-lag penalty is applied */
  effectiveMultiplier: number;
  /** Delivery-lag penalty subtracted from the feature multiplier (pp) */
  deliveryLagPenaltyPp: number;
  /** CBE annual corridor rate that was used in the NPV calculation (0–1) */
  cbeRatePct: number;
  /** True when the listing is algorithmically flagged as a La2ta anomaly */
  isLa2ta: boolean;
  /**
   * Discount depth relative to the compound secondary-market mean (0–1).
   * Present and ≥ 0.15 when `isLa2ta` is true.
   */
  la2taDepthPct?: number;
  /** ISO-8601 timestamp of the most recent ingestion event */
  ingestedAt?: string;
}

// ── Asset Listing Data ────────────────────────────────────────────

export interface AssetStreamData {
  listingId: string;
  compoundId: string;
  geographicZone: string;
  totalPriceEgp: number;
  sizeSqm: number;
  floorLevel: number;
  viewOrientation: string;
  deliveryYear: number;
  isSecondaryMarket: boolean;
  hasPrivateGarden: boolean;
}

// ── Stream Lifecycle ──────────────────────────────────────────────

/** Reactive fetch lifecycle states for OsoolAssetStream */
export type StreamState = 'idle' | 'loading' | 'success' | 'error';

export interface AssetStreamContextValue {
  state: StreamState;
  data: AssetStreamData | null;
  financialMetrics: FinancialMetrics | null;
  error: string | null;
  /** Imperatively re-trigger the data fetch */
  refetch: () => void;
}

// ── Agent Layout Blueprint (JSON Grid Matrix Schema) ──────────────

/**
 * Primitive component identifiers that the AgentCustomLayoutEngine
 * recognises and can render inside the grid matrix.
 */
export type PrimitiveComponentId =
  | 'NPVMarginWidget'
  | 'StructuralVarianceTable'
  | 'La2taSignalBadge';

/** Number of column tracks for a row: 1 | 2 | 3 | 4 */
export type GridCols = 1 | 2 | 3 | 4;

/** Semantic gap scale between grid cells */
export type GridGap = 'sm' | 'md' | 'lg';

/** Column span override for a cell: 1 | 2 | 3 | 4 */
export type ColSpan = 1 | 2 | 3 | 4;

/** Row span override for a cell: 1 | 2 */
export type RowSpan = 1 | 2;

/** A single positioned cell in the agent-generated grid */
export interface LayoutCell {
  /** Which primitive to mount in this cell */
  componentId: PrimitiveComponentId;
  /** Column span — must not exceed the parent row's `cols` (default: 1) */
  colSpan?: ColSpan;
  /** Row span (default: 1) */
  rowSpan?: RowSpan;
  /**
   * Arbitrary prop overrides forwarded to the primitive at render time.
   * Only properties that the target primitive declares as optional overrides
   * will be respected; unknown keys are silently dropped.
   */
  props?: Record<string, unknown>;
}

/** A horizontal band of one or more cells sharing the same column grid */
export interface LayoutRow {
  /** Total column track count — governs `grid-cols-N` class selection */
  cols: GridCols;
  /** Gap between cells in this row (default: 'md') */
  gap?: GridGap;
  /** Ordered array of cells to place within the row */
  cells: LayoutCell[];
}

/**
 * Top-level JSON grid matrix schema emitted by an AI agent and parsed
 * by AgentCustomLayoutEngine.
 *
 * Example:
 * ```json
 * {
 *   "version": "1.0",
 *   "title": "La2ta Deal Snapshot",
 *   "rows": [
 *     {
 *       "cols": 3,
 *       "gap": "md",
 *       "cells": [
 *         { "componentId": "La2taSignalBadge", "colSpan": 1 },
 *         { "componentId": "NPVMarginWidget",  "colSpan": 2 }
 *       ]
 *     },
 *     {
 *       "cols": 1,
 *       "gap": "sm",
 *       "cells": [
 *         { "componentId": "StructuralVarianceTable", "colSpan": 1 }
 *       ]
 *     }
 *   ]
 * }
 * ```
 */
export interface LayoutBlueprint {
  /** Schema version identifier — must equal "1.0" */
  version: '1.0';
  /** Optional section heading rendered above the layout grid */
  title?: string;
  /** Ordered list of horizontal row descriptors */
  rows: LayoutRow[];
}
