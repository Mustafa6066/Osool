'use client';

/**
 * La2taSignalBadge.tsx
 * ─────────────────────────────────────────────────────────────────
 * Standalone UI atom that communicates the La2ta (لقطة) anomaly
 * detection status of a property listing.
 *
 * When active (isLa2ta = true) the badge renders a pulsing terracotta
 * glow with the discount depth displayed in Arabic/English. When
 * inactive it renders a muted neutral chip.
 *
 * Props
 * ─────
 * isLa2ta        — Primary signal flag.
 * la2taDepthPct  — Fractional discount vs compound mean (0–1).
 *                  Displayed as a percentage when provided.
 * compoundId     — Optional compound label shown in the tooltip.
 * size           — 'sm' | 'md' | 'lg' (default: 'md').
 * showLabel      — Toggle extended text label (default: true).
 * className      — Additional class names forwarded to the root element.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, TrendingDown, Minus } from 'lucide-react';
import type { FinancialMetrics } from './types';

// ── Prop definition ───────────────────────────────────────────────

export interface La2taSignalBadgeProps
  extends Pick<FinancialMetrics, 'isLa2ta' | 'la2taDepthPct'> {
  compoundId?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
  /** Override prop forwarded from AgentCustomLayoutEngine */
  _overrides?: Record<string, unknown>;
}

// ── Static Tailwind class lookup maps (no dynamic concatenation) ──

const SIZE_BADGE_CLASS: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'px-2 py-0.5 text-[11px] gap-1',
  md: 'px-3 py-1 text-xs gap-1.5',
  lg: 'px-4 py-1.5 text-sm gap-2',
};

const SIZE_ICON_CLASS: Record<'sm' | 'md' | 'lg', number> = {
  sm: 10,
  md: 12,
  lg: 14,
};

const SIZE_PULSE_CLASS: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
};

// ── Helper ────────────────────────────────────────────────────────

function formatDepthPct(depth: number | undefined): string {
  if (depth === undefined) return '';
  return `${(depth * 100).toFixed(1)}%`;
}

function getDepthIntensity(depth: number | undefined): 'low' | 'mid' | 'high' {
  if (!depth) return 'low';
  if (depth >= 0.30) return 'high';
  if (depth >= 0.20) return 'mid';
  return 'low';
}

// Depth → ring colour lookup (terracotta brand glow; opacity tiers via rgba — Tailwind /opacity on an arbitrary var does not render)
const DEPTH_RING_STYLE: Record<'low' | 'mid' | 'high', string> = {
  low:  'rgba(201,100,66,0.40)',
  mid:  'rgba(201,100,66,0.60)',
  high: 'rgba(201,100,66,0.80)',
};

const DEPTH_GLOW_STYLE: Record<'low' | 'mid' | 'high', string> = {
  low:  '0 0 12px rgba(201,100,66,0.25)',
  mid:  '0 0 16px rgba(201,100,66,0.40)',
  high: '0 0 24px rgba(201,100,66,0.55)',
};

// ── Component ─────────────────────────────────────────────────────

export function La2taSignalBadge({
  isLa2ta,
  la2taDepthPct,
  compoundId,
  size = 'md',
  showLabel = true,
  className = '',
  _overrides,
}: La2taSignalBadgeProps) {
  // Merge any overrides forwarded by AgentCustomLayoutEngine
  const resolvedSize =
    (typeof _overrides?.size === 'string' &&
    ['sm', 'md', 'lg'].includes(_overrides.size as string)
      ? (_overrides.size as 'sm' | 'md' | 'lg')
      : size);

  const depth = la2taDepthPct;
  const intensity = getDepthIntensity(depth);
  const iconSize = SIZE_ICON_CLASS[resolvedSize];

  return (
    <AnimatePresence mode="wait">
      {isLa2ta ? (
        /* ── ACTIVE badge ─────────────────────────────────────── */
        <motion.div
          key="la2ta-active"
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.85 }}
          transition={{ type: 'spring', stiffness: 400, damping: 28 }}
          title={compoundId ? `La2ta deal — ${compoundId}` : 'La2ta anomaly detected'}
          className={[
            'inline-flex items-center font-semibold rounded-full',
            'bg-[var(--osool-accent-soft)] text-[var(--osool-accent)]',
            'ring-1',
            SIZE_BADGE_CLASS[resolvedSize],
            'select-none cursor-default',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
          style={{
            boxShadow: DEPTH_GLOW_STYLE[intensity],
            '--tw-ring-color': DEPTH_RING_STYLE[intensity],
          } as React.CSSProperties}
        >
          {/* Pulse dot */}
          <span className="relative flex shrink-0">
            <span
              className={[
                'absolute inline-flex rounded-full',
                'bg-[var(--osool-accent)] opacity-75 animate-ping',
                SIZE_PULSE_CLASS[resolvedSize],
              ].join(' ')}
            />
            <span
              className={[
                'relative inline-flex rounded-full bg-[var(--osool-accent)]',
                SIZE_PULSE_CLASS[resolvedSize],
              ].join(' ')}
            />
          </span>

          {/* Icon */}
          <Zap size={iconSize} strokeWidth={2.5} className="shrink-0" aria-hidden />

          {/* Label */}
          {showLabel && (
            <span dir="ltr">
              لقطة
              {depth !== undefined && (
                <span className="ml-1 opacity-80">
                  −{formatDepthPct(depth)}
                </span>
              )}
            </span>
          )}
        </motion.div>
      ) : (
        /* ── INACTIVE badge ───────────────────────────────────── */
        <motion.div
          key="la2ta-inactive"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          title="No La2ta anomaly detected"
          className={[
            'inline-flex items-center font-medium rounded-full',
            'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]',
            'ring-1 ring-[var(--color-border)]',
            SIZE_BADGE_CLASS[resolvedSize],
            'select-none cursor-default',
            className,
          ]
            .filter(Boolean)
            .join(' ')}
        >
          <Minus size={iconSize} strokeWidth={2} className="shrink-0" aria-hidden />
          {showLabel && <span>No La2ta</span>}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default La2taSignalBadge;
