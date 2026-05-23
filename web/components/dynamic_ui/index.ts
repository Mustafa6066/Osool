/**
 * dynamic_ui/index.ts
 * ─────────────────────────────────────────────────────────────────
 * Barrel export for the Osool dynamic UI primitive library.
 *
 * Consumers can import any subset:
 *
 *   import {
 *     OsoolAssetStream, useAssetStream,
 *     NPVMarginWidget, StructuralVarianceTable, La2taSignalBadge,
 *     AgentCustomLayoutEngine,
 *   } from '@/components/dynamic_ui';
 *
 *   import type { FinancialMetrics, LayoutBlueprint } from '@/components/dynamic_ui';
 */

// ── Orchestrator ──────────────────────────────────────────────────
export { OsoolAssetStream, useAssetStream } from './OsoolAssetStream';
export type { OsoolAssetStreamProps } from './OsoolAssetStream';

// ── Context re-export for deep consumers ──────────────────────────
// Consumers that need to read context without re-importing the full orchestrator.
// The context object itself is not re-exported to avoid misuse;
// use `useAssetStream()` hook instead.

// ── Standalone atoms ──────────────────────────────────────────────
export { NPVMarginWidget }         from './NPVMarginWidget';
export { StructuralVarianceTable } from './StructuralVarianceTable';
export { La2taSignalBadge }        from './La2taSignalBadge';

export type { NPVMarginWidgetProps }        from './NPVMarginWidget';
export type { StructuralVarianceTableProps } from './StructuralVarianceTable';
export type { La2taSignalBadgeProps }       from './La2taSignalBadge';

// ── Layout engine ─────────────────────────────────────────────────
export { AgentCustomLayoutEngine } from './AgentCustomLayoutEngine';
export type { AgentCustomLayoutEngineProps } from './AgentCustomLayoutEngine';

// ── Shared types ──────────────────────────────────────────────────
export type {
  // Domain models
  FinancialMetrics,
  AssetStreamData,
  // Stream state
  StreamState,
  AssetStreamContextValue,
  // Blueprint schema
  LayoutBlueprint,
  LayoutRow,
  LayoutCell,
  // Primitive tokens
  PrimitiveComponentId,
  GridCols,
  GridGap,
  ColSpan,
  RowSpan,
} from './types';
