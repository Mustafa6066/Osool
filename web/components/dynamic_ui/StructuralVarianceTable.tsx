'use client';

/**
 * StructuralVarianceTable.tsx
 * ─────────────────────────────────────────────────────────────────
 * Standalone UI atom that presents a colour-coded breakdown of all
 * structural factors contributing to a property's effective feature
 * multiplier and normalised price per sqm.
 *
 * Visual anatomy
 * ──────────────
 *  ┌─────────────────────────────────────────────────────────────┐
 *  │  Structural Valuation Factors                               │
 *  │ ─────────────────────────────────────────────────────────── │
 *  │  Factor                  Value         Signal               │
 *  │  View Orientation        Pool (+15pp)   🟢 Premium          │
 *  │  Floor Bonus             +5 pp          🟢 Elevated         │
 *  │  Garden Premium          +12 pp         🟢 Active           │
 *  │  Delivery Lag Penalty    −6.0 pp        🔴 1yr off-plan     │
 *  │  ─────────────────────────────────────────────────────────  │
 *  │  Feature Multiplier      1.20 ×         🟢                  │
 *  │  Effective Multiplier    1.14 ×         🟢                  │
 *  │  Normalised Price / sqm  52,400 EGP     —                   │
 *  └─────────────────────────────────────────────────────────────┘
 *
 * Props
 * ─────
 * featureMultiplier        — Raw structural score (1.0 = neutral).
 * effectiveMultiplier      — After delivery-lag deduction.
 * deliveryLagPenaltyPp     — Penalty subtracted (percentage points).
 * normalizedPricePerSqmEgp — Final EGP/sqm after all adjustments.
 * viewOrientation          — Enum string from PropertyListing.
 * floorLevel               — Floor number (0 = ground).
 * hasPrivateGarden         — Whether the unit has a garden.
 * deliveryYear             — Contractual delivery year.
 * currentYear              — Reference year for lag calc (default 2026).
 * animate                  — Entrance animation flag (default: true).
 * className                — Extra classes for the root element.
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Building2, TreePine, Eye, Calendar, TrendingUp, TrendingDown,
  Minus, BarChart3,
} from 'lucide-react';
import type { FinancialMetrics, AssetStreamData } from './types';

// ── Prop definition ───────────────────────────────────────────────

export interface StructuralVarianceTableProps
  extends Pick<
    FinancialMetrics,
    | 'featureMultiplier'
    | 'effectiveMultiplier'
    | 'deliveryLagPenaltyPp'
    | 'normalizedPricePerSqmEgp'
  >,
  Partial<Pick<
    AssetStreamData,
    | 'viewOrientation'
    | 'floorLevel'
    | 'hasPrivateGarden'
    | 'deliveryYear'
  >> {
  currentYear?: number;
  animate?: boolean;
  className?: string;
  /** Override prop forwarded from AgentCustomLayoutEngine */
  _overrides?: Record<string, unknown>;
}

// ── Formatters ────────────────────────────────────────────────────

const EGP = new Intl.NumberFormat('en-EG', {
  style: 'currency',
  currency: 'EGP',
  maximumFractionDigits: 0,
});

function fmtPP(pp: number, alwaysSign = true): string {
  const sign = pp > 0 ? '+' : '';
  const display = alwaysSign ? `${sign}${pp.toFixed(1)} pp` : `${pp.toFixed(1)} pp`;
  return display;
}

function fmtMultiplier(m: number): string {
  return `${m.toFixed(2)} ×`;
}

// ── Signal classifications ────────────────────────────────────────
// All Tailwind class strings are complete literals — no template concatenation.

type SignalKind = 'positive' | 'negative' | 'neutral' | 'warning';

const SIGNAL_ROW_BG: Record<SignalKind, string> = {
  positive: 'bg-emerald-500/5 hover:bg-emerald-500/8',
  negative: 'bg-rose-500/5 hover:bg-rose-500/8',
  warning:  'bg-amber-400/5 hover:bg-amber-400/8',
  neutral:  'hover:bg-[var(--color-surface-hover)]',
};

const SIGNAL_VALUE_CLASS: Record<SignalKind, string> = {
  positive: 'text-emerald-500 font-semibold',
  negative: 'text-rose-500 font-semibold',
  warning:  'text-amber-500 font-semibold',
  neutral:  'text-[var(--color-text-primary)] font-medium',
};

const SIGNAL_ICON_CLASS: Record<SignalKind, string> = {
  positive: 'text-emerald-500',
  negative: 'text-rose-500',
  warning:  'text-amber-500',
  neutral:  'text-[var(--color-text-muted)]',
};

const SIGNAL_DOT_CLASS: Record<SignalKind, string> = {
  positive: 'bg-emerald-400',
  negative: 'bg-rose-400',
  warning:  'bg-amber-400',
  neutral:  'bg-[var(--color-border)]',
};

// ── View orientation labels ───────────────────────────────────────

const VIEW_LABEL: Record<string, { label: string; pp: number }> = {
  premium_pool:     { label: 'Pool view', pp: 15 },
  open_landscape:   { label: 'Landscape view', pp: 8 },
  side_street:      { label: 'Street view', pp: 0 },
  rear_view:        { label: 'Rear view', pp: -10 },
};

function viewSignal(view: string | undefined): SignalKind {
  if (!view) return 'neutral';
  const entry = VIEW_LABEL[view];
  if (!entry) return 'neutral';
  if (entry.pp > 0) return 'positive';
  if (entry.pp < 0) return 'negative';
  return 'neutral';
}

// ── Row descriptor ────────────────────────────────────────────────

interface TableRow {
  icon: React.ComponentType<{ size: number; strokeWidth: number; className?: string }>;
  factor: string;
  value: string;
  signal: SignalKind;
  note?: string;
  isDivider?: boolean;
}

// ── Build rows from props ─────────────────────────────────────────

function buildRows(props: StructuralVarianceTableProps): TableRow[] {
  const {
    viewOrientation,
    floorLevel,
    hasPrivateGarden,
    deliveryYear,
    currentYear = 2026,
    deliveryLagPenaltyPp,
    featureMultiplier,
    effectiveMultiplier,
    normalizedPricePerSqmEgp,
  } = props;

  const rows: TableRow[] = [];

  // ── View orientation
  if (viewOrientation !== undefined) {
    const viewEntry = VIEW_LABEL[viewOrientation] ?? { label: viewOrientation, pp: 0 };
    rows.push({
      icon: Eye,
      factor: 'View Orientation',
      value: viewEntry.pp !== 0
        ? `${viewEntry.label} (${fmtPP(viewEntry.pp)})`
        : viewEntry.label,
      signal: viewSignal(viewOrientation),
    });
  }

  // ── Floor bonus
  if (floorLevel !== undefined) {
    const isGround = floorLevel === 0;
    const isElevated = floorLevel > 5;
    rows.push({
      icon: Building2,
      factor: 'Floor Level',
      value: isGround
        ? `Ground floor (${fmtPP(12)})`
        : isElevated
          ? `Floor ${floorLevel} (${fmtPP(5)})`
          : `Floor ${floorLevel} (±0 pp)`,
      signal: isGround || isElevated ? 'positive' : 'neutral',
    });
  }

  // ── Garden premium
  if (hasPrivateGarden !== undefined) {
    rows.push({
      icon: TreePine,
      factor: 'Private Garden',
      value: hasPrivateGarden ? `Active (${fmtPP(12)})` : 'None (±0 pp)',
      signal: hasPrivateGarden ? 'positive' : 'neutral',
    });
  }

  // ── Delivery lag penalty
  const lagYears =
    deliveryYear !== undefined ? Math.max(0, deliveryYear - currentYear) : undefined;

  rows.push({
    icon: Calendar,
    factor: 'Delivery Lag Penalty',
    value: lagYears !== undefined
      ? lagYears === 0
        ? 'Ready now (0.0 pp)'
        : `${lagYears}yr off-plan (−${(lagYears * 6).toFixed(1)} pp)`
      : `−${deliveryLagPenaltyPp.toFixed(1)} pp`,
    signal: deliveryLagPenaltyPp > 0 ? 'negative' : 'neutral',
    note: lagYears !== undefined && lagYears > 0
      ? `Delivery: ${deliveryYear}`
      : undefined,
  });

  // ── Divider row before computed totals
  rows.push({ icon: Minus, factor: '', value: '', signal: 'neutral', isDivider: true });

  // ── Feature multiplier
  const fmSig: SignalKind =
    featureMultiplier >= 1.1 ? 'positive' :
    featureMultiplier >= 0.9 ? 'neutral' : 'warning';

  rows.push({
    icon: TrendingUp,
    factor: 'Feature Multiplier',
    value: fmtMultiplier(featureMultiplier),
    signal: fmSig,
    note: 'Raw structural score',
  });

  // ── Effective multiplier
  const emSig: SignalKind =
    effectiveMultiplier >= 1.0 ? 'positive' :
    effectiveMultiplier >= 0.8 ? 'neutral' : 'warning';

  rows.push({
    icon: TrendingDown,
    factor: 'Effective Multiplier',
    value: fmtMultiplier(effectiveMultiplier),
    signal: emSig,
    note: 'After lag penalty',
  });

  // ── Normalised price / sqm
  rows.push({
    icon: BarChart3,
    factor: 'Normalised Price / sqm',
    value: EGP.format(normalizedPricePerSqmEgp),
    signal: 'neutral',
    note: 'EGP per sqm',
  });

  return rows;
}

// ── Row animation ─────────────────────────────────────────────────

const rowVariants = {
  hidden: { opacity: 0, x: -6 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { duration: 0.3, delay: i * 0.05, ease: [0.16, 1, 0.3, 1] },
  }),
};

// ── Component ─────────────────────────────────────────────────────

export function StructuralVarianceTable(props: StructuralVarianceTableProps) {
  const { animate = true, className = '' } = props;
  const rows = useMemo(() => buildRows(props), [
    props.viewOrientation,
    props.floorLevel,
    props.hasPrivateGarden,
    props.deliveryYear,
    props.deliveryLagPenaltyPp,
    props.featureMultiplier,
    props.effectiveMultiplier,
    props.normalizedPricePerSqmEgp,
    props.currentYear,
  ]);

  let dataRowIndex = 0;

  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={[
        'rounded-2xl border border-[var(--color-border)] overflow-hidden',
        'bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)]',
        className,
      ].filter(Boolean).join(' ')}
      style={{ boxShadow: 'var(--glass-shadow)' }}
    >
      {/* ── Table header ─────────────────────────────────────── */}
      <div className="px-5 py-3.5 border-b border-[var(--color-border)] flex items-center justify-between">
        <p className="text-[12px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Structural Valuation Factors
        </p>
        <BarChart3 size={14} strokeWidth={2} className="text-[var(--color-text-muted)]" aria-hidden />
      </div>

      {/* ── Column labels ────────────────────────────────────── */}
      <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 px-5 py-2 border-b border-[var(--color-border-light)]">
        <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
          Factor
        </span>
        <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] text-right">
          Value
        </span>
        <span className="text-[10px] font-medium uppercase tracking-wider text-[var(--color-text-muted)] w-4" />
      </div>

      {/* ── Data rows ────────────────────────────────────────── */}
      <div>
        {rows.map((row, i) => {
          if (row.isDivider) {
            return (
              <div
                key={`divider-${i}`}
                className="h-px bg-[var(--color-border)] mx-4 my-0.5"
                role="separator"
              />
            );
          }

          const rowIdx = dataRowIndex++;
          const Icon = row.icon;

          return (
            <motion.div
              key={`${row.factor}-${i}`}
              custom={rowIdx}
              initial={animate ? 'hidden' : false}
              animate="visible"
              variants={rowVariants}
              className={[
                'grid grid-cols-[1fr_auto_auto] gap-x-4',
                'items-center px-5 py-3 transition-colors duration-150',
                SIGNAL_ROW_BG[row.signal],
              ].join(' ')}
            >
              {/* Factor label + icon */}
              <div className="flex items-center gap-2 min-w-0">
                <Icon
                  size={13}
                  strokeWidth={2}
                  className={SIGNAL_ICON_CLASS[row.signal]}
                  aria-hidden
                />
                <div className="min-w-0">
                  <span className="text-[13px] text-[var(--color-text-secondary)] truncate block">
                    {row.factor}
                  </span>
                  {row.note && (
                    <span className="text-[10px] text-[var(--color-text-muted)]">
                      {row.note}
                    </span>
                  )}
                </div>
              </div>

              {/* Value */}
              <span className={['text-[13px] tabular-nums text-right whitespace-nowrap', SIGNAL_VALUE_CLASS[row.signal]].join(' ')}>
                {row.value}
              </span>

              {/* Signal dot */}
              <span
                className={['w-1.5 h-1.5 rounded-full shrink-0', SIGNAL_DOT_CLASS[row.signal]].join(' ')}
                aria-hidden
              />
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}

export default StructuralVarianceTable;
