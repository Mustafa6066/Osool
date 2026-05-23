'use client';

/**
 * AgentCustomLayoutEngine.tsx
 * ─────────────────────────────────────────────────────────────────
 * Accepts a declarative JSON `LayoutBlueprint` produced by an external
 * coding agent and reconstructs the page presentation on the fly from
 * the registered primitive library.
 *
 * Design invariants
 * ─────────────────
 * 1. ALL Tailwind utility classes are resolved through explicit static
 *    lookup tables. Dynamic template literals such as `grid-cols-${n}`
 *    are strictly forbidden — they would be purged in production builds.
 *
 * 2. Unknown `componentId` values cause a warn-and-skip (no crash).
 *
 * 3. The `layoutBlueprint` prop accepts either a pre-parsed object or a
 *    raw JSON string, simplifying agent-generated payloads.
 *
 * Blueprint JSON schema (v1.0)
 * ────────────────────────────
 * {
 *   "version": "1.0",
 *   "title": "Optional display title",
 *   "rows": [
 *     {
 *       "cols": 2,          // 1 | 2 | 3 | 4
 *       "gap": "md",        // "sm" | "md" | "lg"
 *       "cells": [
 *         {
 *           "componentId": "NPVMarginWidget",
 *           "colSpan": 1,   // 1 | 2 | 3 | 4
 *           "rowSpan": 1,   // 1 | 2
 *           "props": {}     // forwarded as _overrides
 *         }
 *       ]
 *     }
 *   ]
 * }
 *
 * Usage
 * ─────
 * ```tsx
 * const blueprint = {
 *   version: "1.0",
 *   rows: [{
 *     cols: 2, gap: "md",
 *     cells: [
 *       { componentId: "NPVMarginWidget" },
 *       { componentId: "La2taSignalBadge" }
 *     ]
 *   }]
 * };
 *
 * <AgentCustomLayoutEngine
 *   layoutBlueprint={blueprint}
 *   financialMetrics={metrics}
 *   data={assetData}
 * />
 * ```
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';
import type {
  AssetStreamData,
  ColSpan,
  FinancialMetrics,
  GridCols,
  GridGap,
  LayoutBlueprint,
  LayoutCell,
  PrimitiveComponentId,
  RowSpan,
} from './types';
import { NPVMarginWidget }          from './NPVMarginWidget';
import { StructuralVarianceTable }  from './StructuralVarianceTable';
import { La2taSignalBadge }         from './La2taSignalBadge';

// ── Tailwind class lookup tables ──────────────────────────────────
// Every value is a complete string literal — no template concatenation.

const GRID_COLS_CLASS: Record<GridCols, string> = {
  1: 'grid-cols-1',
  2: 'grid-cols-2',
  3: 'grid-cols-3',
  4: 'grid-cols-4',
};

const GRID_GAP_CLASS: Record<GridGap, string> = {
  sm: 'gap-3',
  md: 'gap-5',
  lg: 'gap-8',
};

const COL_SPAN_CLASS: Record<ColSpan, string> = {
  1: 'col-span-1',
  2: 'col-span-2',
  3: 'col-span-3',
  4: 'col-span-4',
};

const ROW_SPAN_CLASS: Record<RowSpan, string> = {
  1: 'row-span-1',
  2: 'row-span-2',
};

// ── Component registry ────────────────────────────────────────────
// Maps PrimitiveComponentId → the actual React component type.
// Add new primitives here; AgentCustomLayoutEngine picks them up automatically.

const COMPONENT_REGISTRY: Record<
  PrimitiveComponentId,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  React.ComponentType<any>
> = {
  NPVMarginWidget,
  StructuralVarianceTable,
  La2taSignalBadge,
};

const VALID_COMPONENT_IDS = new Set<string>(Object.keys(COMPONENT_REGISTRY));

// ── Props ─────────────────────────────────────────────────────────

export interface AgentCustomLayoutEngineProps {
  /** Parsed LayoutBlueprint object OR a raw JSON string representation of one. */
  layoutBlueprint: LayoutBlueprint | string;
  /** Financial metrics forwarded to all child atoms. */
  financialMetrics?: FinancialMetrics | null;
  /** Raw asset data forwarded to structural-variance atoms. */
  data?: AssetStreamData | null;
  /**
   * Called when the blueprint cannot be parsed or fails version validation.
   * Receives the thrown Error. Provides an escape hatch for logging / fallback UI.
   */
  onParseError?: (error: Error) => void;
  /** Extra classes for the outermost container. */
  className?: string;
}

// ── Blueprint validation ──────────────────────────────────────────

const VALID_GRID_COLS = new Set<number>([1, 2, 3, 4]);
const VALID_GRID_GAPS = new Set<string>(['sm', 'md', 'lg']);
const VALID_COL_SPANS = new Set<number>([1, 2, 3, 4]);
const VALID_ROW_SPANS = new Set<number>([1, 2]);

function parseBlueprint(raw: LayoutBlueprint | string): LayoutBlueprint {
  let obj: unknown;
  if (typeof raw === 'string') {
    try {
      obj = JSON.parse(raw);
    } catch {
      throw new Error('AgentCustomLayoutEngine: layoutBlueprint is not valid JSON.');
    }
  } else {
    obj = raw;
  }

  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) {
    throw new Error('AgentCustomLayoutEngine: layoutBlueprint must be a JSON object.');
  }

  const bp = obj as Record<string, unknown>;

  if (bp.version !== '1.0') {
    throw new Error(
      `AgentCustomLayoutEngine: unsupported blueprint version "${bp.version}". Expected "1.0".`
    );
  }

  if (!Array.isArray(bp.rows)) {
    throw new Error('AgentCustomLayoutEngine: layoutBlueprint.rows must be an array.');
  }

  return bp as unknown as LayoutBlueprint;
}

// ── Safe accessor helpers ─────────────────────────────────────────

function safeGridCols(v: unknown): GridCols {
  if (typeof v === 'number' && VALID_GRID_COLS.has(v)) return v as GridCols;
  return 1;
}

function safeGridGap(v: unknown): GridGap {
  if (typeof v === 'string' && VALID_GRID_GAPS.has(v)) return v as GridGap;
  return 'md';
}

function safeColSpan(v: unknown): ColSpan {
  if (typeof v === 'number' && VALID_COL_SPANS.has(v)) return v as ColSpan;
  return 1;
}

function safeRowSpan(v: unknown): RowSpan {
  if (typeof v === 'number' && VALID_ROW_SPANS.has(v)) return v as RowSpan;
  return 1;
}

// ── Cell renderer ─────────────────────────────────────────────────

interface CellRendererProps {
  cell: LayoutCell;
  financialMetrics: FinancialMetrics | null | undefined;
  data: AssetStreamData | null | undefined;
  cellKey: string;
}

function CellRenderer({ cell, financialMetrics, data, cellKey }: CellRendererProps) {
  const { componentId, colSpan, rowSpan, props: overrides } = cell;

  if (!VALID_COMPONENT_IDS.has(componentId)) {
    if (process.env.NODE_ENV !== 'production') {
      console.warn(
        `[AgentCustomLayoutEngine] Unknown componentId "${componentId}". Skipping cell.`
      );
    }
    return null;
  }

  const Component = COMPONENT_REGISTRY[componentId as PrimitiveComponentId];

  const colClass = COL_SPAN_CLASS[safeColSpan(colSpan)];
  const rowClass = ROW_SPAN_CLASS[safeRowSpan(rowSpan)];

  // Build merged prop set — financial metrics and data are base context;
  // cell-level overrides take precedence via _overrides.
  const mergedProps = {
    ...(financialMetrics ?? {}),
    ...(data ?? {}),
    _overrides: overrides ?? {},
  };

  return (
    <div key={cellKey} className={[colClass, rowClass].join(' ')}>
      <Component {...mergedProps} />
    </div>
  );
}

// ── Row animation ─────────────────────────────────────────────────

const rowVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, delay: i * 0.07, ease: [0.16, 1, 0.3, 1] },
  }),
};

// ── Component ─────────────────────────────────────────────────────

export function AgentCustomLayoutEngine({
  layoutBlueprint,
  financialMetrics,
  data,
  onParseError,
  className = '',
}: AgentCustomLayoutEngineProps) {
  const blueprint = useMemo<LayoutBlueprint | null>(() => {
    try {
      return parseBlueprint(layoutBlueprint);
    } catch (err) {
      onParseError?.(err as Error);
      return null;
    }
  }, [layoutBlueprint, onParseError]);

  if (!blueprint) {
    return (
      <div
        className="flex items-start gap-3 rounded-xl border border-amber-400/30
                   bg-amber-400/5 px-4 py-3"
        role="alert"
      >
        <AlertTriangle size={15} className="text-amber-500 shrink-0 mt-0.5" aria-hidden />
        <div className="space-y-0.5">
          <p className="text-sm font-semibold text-amber-600">Invalid layout blueprint</p>
          <p className="text-[12px] text-[var(--color-text-muted)]">
            The agent-provided blueprint could not be parsed. Check console for details.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={['space-y-5', className].filter(Boolean).join(' ')}
      aria-label={blueprint.title ?? 'Agent-generated layout'}
    >
      {/* Optional title */}
      {blueprint.title && (
        <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          {blueprint.title}
        </p>
      )}

      {/* Rows */}
      {blueprint.rows.map((row, rowIdx) => {
        const colsClass = GRID_COLS_CLASS[safeGridCols(row.cols)];
        const gapClass  = GRID_GAP_CLASS[safeGridGap(row.gap)];

        return (
          <motion.div
            key={`row-${rowIdx}`}
            custom={rowIdx}
            initial="hidden"
            animate="visible"
            variants={rowVariants}
            className={['grid', colsClass, gapClass].join(' ')}
          >
            {row.cells.map((cell, cellIdx) => (
              <CellRenderer
                key={`row-${rowIdx}-cell-${cellIdx}-${cell.componentId}`}
                cellKey={`row-${rowIdx}-cell-${cellIdx}`}
                cell={cell}
                financialMetrics={financialMetrics}
                data={data}
              />
            ))}
          </motion.div>
        );
      })}
    </div>
  );
}

export default AgentCustomLayoutEngine;
