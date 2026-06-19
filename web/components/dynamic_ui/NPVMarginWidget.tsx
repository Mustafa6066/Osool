'use client';

/**
 * NPVMarginWidget.tsx
 * ─────────────────────────────────────────────────────────────────
 * Standalone UI atom that visualises the Net Present Value (NPV)
 * compression of an Egyptian property instalment plan versus its
 * nominal sticker price.
 *
 * Visual anatomy
 * ──────────────
 *  ┌─────────────────────────────────────────────┐
 *  │  NPV Cash Equivalent          CBE 22.0 %    │
 *  │  ───────────────────────────────────────── │
 *  │  4,250,000 EGP  ◄──────────── 6,000,000 EGP│
 *  │                                             │
 *  │  ████████████████████░░░░░░░  70.8 %        │
 *  │  ─────────────────────────────────────────  │
 *  │  Cash saving  ·  1,750,000 EGP  ·  29.2 %  │
 *  └─────────────────────────────────────────────┘
 *
 * Props
 * ─────
 * cashNpvEgp          — Discounted NPV (EGP).
 * nominalPriceEgp     — Sticker price (EGP).
 * discountEgp         — Savings vs nominal (EGP).
 * discountPct         — Savings fraction (0–1).
 * cbeRatePct          — CBE rate used (0–1).
 * compact             — Render a condensed single-line variant.
 * animate             — Enable entrance animation (default: true).
 * className           — Extra classes for the root element.
 */

import React, { useId } from 'react';
import { motion } from 'framer-motion';
import { TrendingDown, Info } from 'lucide-react';
import type { FinancialMetrics } from './types';

// ── Prop definition ───────────────────────────────────────────────

export interface NPVMarginWidgetProps
  extends Pick<
    FinancialMetrics,
    'cashNpvEgp' | 'nominalPriceEgp' | 'discountEgp' | 'discountPct' | 'cbeRatePct'
  > {
  compact?: boolean;
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

function fmt(value: number): string {
  return EGP.format(value);
}

function fmtPct(fraction: number, dp = 1): string {
  return `${(fraction * 100).toFixed(dp)} %`;
}

// ── Colour lookup for the compression bar fill ────────────────────
// Keyed by discount depth bucket — no dynamic class names.

type DepthBucket = 'deep' | 'moderate' | 'shallow' | 'none';

function depthBucket(discountPct: number): DepthBucket {
  if (discountPct >= 0.30) return 'deep';
  if (discountPct >= 0.15) return 'moderate';
  if (discountPct > 0)     return 'shallow';
  return 'none';
}

// Lookup tables — every class must be a complete string literal so
// Tailwind's static analyser includes them in the generated CSS.
const BAR_FILL_CLASS: Record<DepthBucket, string> = {
  deep:     'bg-emerald-500',
  moderate: 'bg-teal-500',
  shallow:  'bg-amber-400',
  none:     'bg-[var(--color-border)]',
};

const SAVING_TEXT_CLASS: Record<DepthBucket, string> = {
  deep:     'text-emerald-500',
  moderate: 'text-teal-500',
  shallow:  'text-amber-500',
  none:     'text-[var(--color-text-muted)]',
};

const BADGE_BG_CLASS: Record<DepthBucket, string> = {
  deep:     'bg-emerald-500/10 text-emerald-600 ring-emerald-400/30',
  moderate: 'bg-teal-500/10 text-teal-600 ring-teal-400/30',
  shallow:  'bg-amber-400/10 text-amber-600 ring-amber-400/30',
  none:     'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] ring-[var(--color-border)]',
};

// ── Bar animation variant ─────────────────────────────────────────

const barVariants = {
  hidden: { scaleX: 0, originX: 0 },
  visible: (pct: number) => ({
    scaleX: 1 - pct, // NPV share of nominal
    originX: 0,
    transition: {
      duration: 0.9,
      ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
      delay: 0.15,
    },
  }),
};

// ── Component ─────────────────────────────────────────────────────

export function NPVMarginWidget({
  cashNpvEgp,
  nominalPriceEgp,
  discountEgp,
  discountPct,
  cbeRatePct,
  compact = false,
  animate = true,
  className = '',
  _overrides,
}: NPVMarginWidgetProps) {
  const uid = useId();
  const bucket = depthBucket(discountPct);
  const npvShare = nominalPriceEgp > 0 ? cashNpvEgp / nominalPriceEgp : 1;
  const clampedNpvShare = Math.min(1, Math.max(0, npvShare));

  // ── Compact variant ──────────────────────────────────────────
  if (compact) {
    return (
      <motion.div
        initial={animate ? { opacity: 0, y: 4 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className={[
          'flex items-center gap-3 px-3 py-2 rounded-xl',
          'bg-[var(--color-surface)] border border-[var(--color-border)]',
          className,
        ].filter(Boolean).join(' ')}
      >
        <TrendingDown size={15} className="text-[var(--osool-accent)] shrink-0" />
        <span className="text-[13px] font-semibold text-[var(--color-text-primary)]">
          {fmt(cashNpvEgp)}
        </span>
        <span className="text-[11px] text-[var(--color-text-muted)]">NPV</span>
        <span
          className={[
            'ml-auto text-[11px] font-semibold px-1.5 py-0.5 rounded-full ring-1',
            BADGE_BG_CLASS[bucket],
          ].join(' ')}
        >
          −{fmtPct(discountPct)}
        </span>
      </motion.div>
    );
  }

  // ── Full variant ─────────────────────────────────────────────
  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className={[
        'rounded-2xl border border-[var(--color-border)]',
        'bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)]',
        'p-5 space-y-4',
        className,
      ].filter(Boolean).join(' ')}
      style={{ boxShadow: 'var(--glass-shadow)' }}
    >
      {/* ── Header row ─────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-0.5">
          <p className="text-[11px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
            NPV Cash Equivalent
          </p>
          <p className="text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">
            {fmt(cashNpvEgp)}
          </p>
        </div>

        {/* CBE rate pill */}
        <div
          className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold
                     bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]
                     ring-1 ring-[var(--color-border)] shrink-0"
          title="Central Bank of Egypt base corridor rate applied"
        >
          <Info size={10} strokeWidth={2.5} aria-hidden />
          CBE {fmtPct(cbeRatePct, 1)}
        </div>
      </div>

      {/* ── Compression bar ────────────────────────────────── */}
      <div className="space-y-2" aria-label={`NPV compression: ${fmtPct(discountPct)} discount`}>
        {/* Track */}
        <div
          id={`${uid}-track`}
          className="relative h-2.5 rounded-full overflow-hidden bg-[var(--color-surface-dark)]"
        >
          {/* NPV fill — animates from left */}
          <motion.div
            className={['absolute inset-y-0 left-0 rounded-full', BAR_FILL_CLASS[bucket]].join(' ')}
            initial={animate ? { width: 0 } : false}
            animate={{ width: `${clampedNpvShare * 100}%` }}
            transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          />
          {/* Nominal remainder (ghost track) */}
          <div
            className="absolute inset-y-0 right-0 rounded-r-full bg-[var(--color-border)]"
            style={{ width: `${(1 - clampedNpvShare) * 100}%` }}
          />
        </div>

        {/* Labels beneath the bar */}
        <div className="flex justify-between text-[11px] tabular-nums">
          <span className="text-[var(--color-text-muted)]">
            {fmt(cashNpvEgp)} NPV
          </span>
          <span className="text-[var(--color-text-muted)]">
            {fmt(nominalPriceEgp)} nominal
          </span>
        </div>
      </div>

      {/* ── Saving summary ──────────────────────────────────── */}
      <div
        className={[
          'flex items-center justify-between rounded-xl px-4 py-3',
          'bg-[var(--color-surface-hover)] border border-[var(--color-border-light)]',
        ].join(' ')}
      >
        <span className="text-[12px] text-[var(--color-text-muted)]">
          Cash saving
        </span>
        <div className="flex items-center gap-2">
          <span
            className={['text-sm font-bold tabular-nums', SAVING_TEXT_CLASS[bucket]].join(' ')}
          >
            {fmt(discountEgp)}
          </span>
          <span
            className={[
              'text-[11px] font-semibold px-2 py-0.5 rounded-full ring-1',
              BADGE_BG_CLASS[bucket],
            ].join(' ')}
          >
            −{fmtPct(discountPct)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}

export default NPVMarginWidget;
