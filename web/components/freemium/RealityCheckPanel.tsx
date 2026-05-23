'use client';

/**
 * RealityCheckPanel.tsx
 * ─────────────────────────────────────────────────────────────────
 * Interactive pre-subscription property intelligence panel.
 *
 * Panel phases
 * ────────────
 *   form     → Clean entry form capturing broker-offer parameters.
 *   loading  → Spinner with progress messaging while API evaluates.
 *   results  → Animated metrics (gauge + cards) + gated alternatives grid.
 *   error    → Contextual error with recovery actions.
 *
 * Gating contract
 * ───────────────
 *   When the backend returns alternatives with broker_direct_contact ===
 *   "[GATED_PREMIUM_ACCESS]", the entire alternatives grid is blurred and
 *   overlaid with a premium conversion card. All numeric savings metrics
 *   remain readable to demonstrate value — only identification fields
 *   (contact, building, unit ID) are hidden.
 *
 * Motion contract
 * ───────────────
 *   All animations respect prefers-reduced-motion via the `reducedMotion`
 *   Framer Motion global config. Durations collapse to ≤50 ms in that mode.
 *   Spring configurations are chosen to feel snappy without being jarring.
 */

import React, {
  useCallback,
  useId,
  useReducer,
  useRef,
  useState,
} from 'react';
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useSpring,
  useTransform,
  LazyMotion,
  domAnimation,
} from 'framer-motion';
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  ChevronDown,
  Crown,
  Loader2,
  Lock,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

// ─────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────

const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
).replace(/\/$/, '');

const GATED_SENTINEL = '[GATED_PREMIUM_ACCESS]';

/** Gauge arc geometry */
const GAUGE = {
  cx: 100,
  cy: 100,
  r: 80,
  strokeWidth: 12,
} as const;

const GAUGE_ARC_LENGTH = Math.PI * GAUGE.r; // half-circle

// ─────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────

interface CompoundBenchmarkSummary {
  compound_id: string;
  secondary_market_listing_count: number;
  compound_mean_normalized_sqm: number;
  compound_min_normalized_sqm: number;
  compound_max_normalized_sqm: number;
}

interface ArbitrageAlternative {
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

interface RealityCheckResult {
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

interface FormValues {
  compound_id: string;
  stated_total_price: string;
  space_sqm: string;
  down_payment: string;
  installment_years: string;
  annual_installments_count: string;
}

interface FormErrors {
  compound_id?: string;
  stated_total_price?: string;
  space_sqm?: string;
  down_payment?: string;
  installment_years?: string;
}

type PanelPhase = 'form' | 'loading' | 'results' | 'error';

// ─────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────

const EGP = new Intl.NumberFormat('en-EG', {
  style: 'currency',
  currency: 'EGP',
  maximumFractionDigits: 0,
});

function fmt(n: number): string {
  return n.toLocaleString('en-EG', { maximumFractionDigits: 0 });
}

/** Map overpay delta % to a 0–1 risk score for the gauge. */
function deltaToRisk(delta: number): number {
  // -15 % → 0 (great deal), 0 % → 0.33 (at market), +30 % → 1.0 (significant overpay)
  return Math.min(1, Math.max(0, (delta + 15) / 45));
}

/** Gauge needle endpoint for a given risk [0,1]. */
function gaugeNeedle(risk: number): { x: number; y: number } {
  const angle = Math.PI - risk * Math.PI; // π → 0 (left to right)
  return {
    x: GAUGE.cx + GAUGE.r * Math.cos(angle),
    y: GAUGE.cy - GAUGE.r * Math.sin(angle),
  };
}

/** Colour ramp for the gauge and delta badges. */
function riskColor(risk: number): string {
  if (risk < 0.33) return '#10B981'; // emerald — at or below market
  if (risk < 0.66) return '#F59E0B'; // amber — moderate overpay
  return '#EF4444'; // red — significant overpay
}

function riskLabel(risk: number): string {
  if (risk < 0.25) return 'Below Market';
  if (risk < 0.45) return 'Fair Value';
  if (risk < 0.66) return 'Slight Overpay';
  if (risk < 0.85) return 'Above Market';
  return 'Significant Overpay';
}

function validateForm(v: FormValues): FormErrors {
  const errors: FormErrors = {};
  const total = parseFloat(v.stated_total_price);
  const down = parseFloat(v.down_payment);

  const compoundClean = v.compound_id.trim();
  if (!compoundClean) {
    errors.compound_id = 'Compound name is required.';
  } else if (compoundClean.length > 128) {
    errors.compound_id = 'Maximum 128 characters.';
  } else if (!/^[\w\-\. ]+$/.test(compoundClean)) {
    errors.compound_id = 'Only letters, numbers, hyphens, dots, and spaces.';
  }

  if (!v.stated_total_price) {
    errors.stated_total_price = 'Required.';
  } else if (isNaN(total) || total <= 0) {
    errors.stated_total_price = 'Must be a positive number.';
  }

  if (!v.space_sqm) {
    errors.space_sqm = 'Required.';
  } else if (isNaN(parseFloat(v.space_sqm)) || parseFloat(v.space_sqm) <= 0) {
    errors.space_sqm = 'Must be positive.';
  }

  if (!v.down_payment) {
    errors.down_payment = 'Required.';
  } else if (isNaN(down) || down <= 0) {
    errors.down_payment = 'Must be positive.';
  } else if (!isNaN(total) && down >= total) {
    errors.down_payment = 'Must be less than total price.';
  }

  if (!v.installment_years) {
    errors.installment_years = 'Required.';
  } else {
    const yr = parseInt(v.installment_years, 10);
    if (isNaN(yr) || yr < 1 || yr > 30) {
      errors.installment_years = '1 – 30 years.';
    }
  }

  return errors;
}

function isGated(value: string): boolean {
  return value === GATED_SENTINEL;
}

// ─────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────

// ── FormField ──────────────────────────────────────────────────────

interface FormFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: 'text' | 'number';
  placeholder?: string;
  suffix?: string;
  error?: string;
  hint?: string;
  min?: number;
  max?: number;
}

function FormField({
  id,
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  suffix,
  error,
  hint,
  min,
  max,
}: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-400 dark:text-zinc-500"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          min={min}
          max={max}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          className={[
            'w-full rounded-xl border bg-zinc-950/70 dark:bg-zinc-950/80 px-4 py-3 text-[15px]',
            'text-zinc-100 placeholder:text-zinc-600',
            'transition-all duration-150 outline-none',
            suffix ? 'pr-14' : '',
            error
              ? 'border-red-500/60 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'
              : 'border-white/8 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/20',
          ]
            .filter(Boolean)
            .join(' ')}
        />
        {suffix && (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-[12px] font-medium text-zinc-500">
            {suffix}
          </span>
        )}
      </div>
      {error && (
        <p
          id={`${id}-error`}
          role="alert"
          className="flex items-center gap-1.5 text-[12px] text-red-400"
        >
          <AlertCircle className="h-3 w-3 shrink-0" aria-hidden="true" />
          {error}
        </p>
      )}
      {!error && hint && (
        <p id={`${id}-hint`} className="text-[11px] text-zinc-600">
          {hint}
        </p>
      )}
    </div>
  );
}

// ── SelectField ────────────────────────────────────────────────────

interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
  hint?: string;
}

function SelectField({ id, label, value, onChange, options, hint }: SelectFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={id}
        className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-400 dark:text-zinc-500"
      >
        {label}
      </label>
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none rounded-xl border border-white/8 bg-zinc-950/70 px-4 py-3 pr-10 text-[15px] text-zinc-100 outline-none transition-all duration-150 focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/20"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value} className="bg-zinc-900">
              {o.label}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
          aria-hidden="true"
        />
      </div>
      {hint && <p className="text-[11px] text-zinc-600">{hint}</p>}
    </div>
  );
}

// ── OverpayGauge ───────────────────────────────────────────────────

interface OverpayGaugeProps {
  overpayDeltaPct: number;
  isLa2ta: boolean;
}

function OverpayGauge({ overpayDeltaPct, isLa2ta }: OverpayGaugeProps) {
  const risk = deltaToRisk(overpayDeltaPct);
  const color = riskColor(risk);
  const label = riskLabel(risk);

  // Animate fill length
  const motionRisk = useMotionValue(0);
  const springRisk = useSpring(motionRisk, { stiffness: 80, damping: 18 });

  React.useEffect(() => {
    motionRisk.set(risk);
  }, [risk, motionRisk]);

  const fillLength = useTransform(springRisk, (r) => r * GAUGE_ARC_LENGTH);

  // SVG arc path for the half-circle (180°)
  // M 20,100 A 80,80,0,0,1,180,100  ← left to right, bottom plane
  const trackPath = `M ${GAUGE.cx - GAUGE.r},${GAUGE.cy} A ${GAUGE.r},${GAUGE.r},0,0,1,${GAUGE.cx + GAUGE.r},${GAUGE.cy}`;

  // Needle
  const needle = gaugeNeedle(risk);
  const motionNeedleX = useTransform(springRisk, (r) => gaugeNeedle(r).x);
  const motionNeedleY = useTransform(springRisk, (r) => gaugeNeedle(r).y);

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Label */}
      <div className="flex items-center gap-2">
        <BarChart3 className="h-4 w-4 text-zinc-400" aria-hidden="true" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-400">
          Overpay Risk Index
        </span>
      </div>

      {/* SVG gauge */}
      <div className="relative w-full max-w-[220px]" role="img" aria-label={`Overpay risk: ${label}, ${overpayDeltaPct.toFixed(1)}% delta`}>
        <svg viewBox="0 0 200 115" fill="none" className="w-full overflow-visible">
          {/* Zone gradient definitions */}
          <defs>
            <linearGradient id="gaugeZoneGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%"   stopColor="#10B981" stopOpacity="0.25" />
              <stop offset="40%"  stopColor="#F59E0B" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#EF4444" stopOpacity="0.25" />
            </linearGradient>
          </defs>

          {/* Background track */}
          <path
            d={trackPath}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={GAUGE.strokeWidth}
            strokeLinecap="round"
          />

          {/* Colored fill arc — animated */}
          <motion.path
            d={trackPath}
            fill="none"
            stroke={color}
            strokeWidth={GAUGE.strokeWidth}
            strokeLinecap="round"
            style={{
              pathLength: 0,           // reset; we drive via strokeDasharray
              strokeDasharray: `${GAUGE_ARC_LENGTH} ${GAUGE_ARC_LENGTH}`,
              strokeDashoffset: useTransform(
                springRisk,
                (r) => GAUGE_ARC_LENGTH - r * GAUGE_ARC_LENGTH
              ),
            }}
            transition={{ type: 'spring', stiffness: 80, damping: 18 }}
          />

          {/* Animated needle line */}
          <motion.line
            x1={GAUGE.cx}
            y1={GAUGE.cy}
            x2={motionNeedleX}
            y2={motionNeedleY}
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            opacity={0.8}
          />

          {/* Center dot */}
          <circle cx={GAUGE.cx} cy={GAUGE.cy} r="5" fill="white" opacity={0.9} />

          {/* Needle tip dot */}
          <motion.circle
            cx={motionNeedleX}
            cy={motionNeedleY}
            r="4"
            fill={color}
          />

          {/* Zone labels */}
          <text x="22" y="114" fontSize="9" fill="#10B981" opacity="0.7" textAnchor="middle">Low</text>
          <text x="100" y="28" fontSize="9" fill="#F59E0B" opacity="0.7" textAnchor="middle">Mid</text>
          <text x="178" y="114" fontSize="9" fill="#EF4444" opacity="0.7" textAnchor="middle">High</text>
        </svg>

        {/* Center numeric display */}
        <div className="absolute inset-x-0 bottom-3 flex flex-col items-center">
          <motion.span
            key={overpayDeltaPct.toFixed(1)}
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            className="text-2xl font-bold tabular-nums leading-none"
            style={{ color }}
          >
            {overpayDeltaPct > 0 ? '+' : ''}{overpayDeltaPct.toFixed(1)}%
          </motion.span>
          <span className="mt-0.5 text-[11px] font-medium text-zinc-400">{label}</span>
        </div>
      </div>

      {/* La2ta badge */}
      <AnimatePresence>
        {isLa2ta && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-4 py-1.5"
          >
            <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" aria-hidden="true" />
            <span className="text-[12px] font-semibold text-emerald-400">
              La2ta Signal — This offer is a market anomaly
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── MetricCard ─────────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: string;
  sub?: string;
  accent?: 'emerald' | 'amber' | 'red' | 'zinc';
  icon?: React.ReactNode;
}

function MetricCard({ label, value, sub, accent = 'zinc', icon }: MetricCardProps) {
  const accentMap: Record<string, string> = {
    emerald: 'text-emerald-400',
    amber:   'text-amber-400',
    red:     'text-red-400',
    zinc:    'text-zinc-100',
  };
  const borderMap: Record<string, string> = {
    emerald: 'border-emerald-500/20',
    amber:   'border-amber-500/20',
    red:     'border-red-500/20',
    zinc:    'border-white/8',
  };

  return (
    <div
      className={`flex flex-col gap-1 rounded-2xl border bg-zinc-900/50 p-4 ${borderMap[accent]}`}
    >
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-zinc-500" aria-hidden="true">{icon}</span>}
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
          {label}
        </span>
      </div>
      <span className={`text-[22px] font-bold tabular-nums leading-tight ${accentMap[accent]}`}>
        {value}
      </span>
      {sub && <span className="text-[11px] text-zinc-500">{sub}</span>}
    </div>
  );
}

// ── AlternativeCard ────────────────────────────────────────────────

interface AlternativeCardProps {
  alt: ArbitrageAlternative;
  offerNormSqm: number;
}

function AlternativeCard({ alt, offerNormSqm }: AlternativeCardProps) {
  const savingsEgp = (offerNormSqm - alt.normalized_cash_price_sqm) * alt.size_sqm;
  const savingsPct = alt.savings_vs_offer_pct;

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/8 bg-zinc-900/60 p-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col">
          <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
            {alt.geographic_zone}
          </span>
          <span className="mt-0.5 text-[13px] font-semibold text-zinc-100">
            {alt.compound_id}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-1 rounded-full bg-emerald-500/12 border border-emerald-500/25 px-2.5 py-1">
          <span className="text-[11px] font-bold text-emerald-400">
            −{savingsPct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Primary savings callout */}
      {savingsEgp > 0 && (
        <div className="rounded-xl bg-emerald-500/8 border border-emerald-500/15 px-3 py-2.5">
          <p className="text-[13px] font-semibold text-emerald-300">
            Save {EGP.format(Math.round(savingsEgp))} on Cash Terms
          </p>
          <p className="text-[11px] text-zinc-500">vs. evaluated broker offer</p>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 text-[12px]">
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">Size</span>
          <span className="font-semibold text-zinc-200">{alt.size_sqm.toFixed(0)} sqm</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">Floor</span>
          <span className="font-semibold text-zinc-200">{alt.floor_level}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">NPV Price</span>
          <span className="font-semibold text-zinc-200">{EGP.format(alt.cash_npv_egp)}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">Delivery</span>
          <span className="font-semibold text-zinc-200">{alt.delivery_year}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">Norm. Price/sqm</span>
          <span className="font-semibold text-zinc-200">
            {EGP.format(alt.normalized_cash_price_sqm)}/m²
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-zinc-600">vs Compound Mean</span>
          <span className="font-semibold text-emerald-400">
            −{alt.discount_vs_compound_mean_pct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Gated identification row */}
      <div className="grid grid-cols-1 gap-1 border-t border-white/6 pt-2.5 text-[11px]">
        {[
          { label: 'Unit ID',   value: alt.exact_unit_id },
          { label: 'Building',  value: alt.building_number },
          { label: 'Contact',   value: alt.broker_direct_contact },
        ].map(({ label, value: v }) => (
          <div key={label} className="flex items-center justify-between gap-2">
            <span className="text-zinc-600">{label}</span>
            {isGated(v) ? (
              <span className="flex items-center gap-1 text-zinc-600">
                <Lock className="h-2.5 w-2.5" aria-hidden="true" />
                <span className="text-[10px] tracking-wide">Subscriber Only</span>
              </span>
            ) : (
              <span className="font-mono text-emerald-300">{v}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── PremiumGateCard ────────────────────────────────────────────────

interface PremiumGateCardProps {
  alternativeCount: number;
  onUpgrade: () => void;
}

function PremiumGateCard({ alternativeCount, onUpgrade }: PremiumGateCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 160, damping: 22, delay: 0.15 }}
      className="relative mx-auto w-full max-w-sm rounded-3xl border border-white/12 bg-zinc-900/90 p-7 shadow-2xl backdrop-blur-xl"
      style={{
        background:
          'linear-gradient(145deg, rgba(16,185,129,0.06) 0%, rgba(9,9,11,0.92) 60%, rgba(124,58,237,0.04) 100%)',
        boxShadow: '0 0 40px rgba(16,185,129,0.12), 0 20px 60px rgba(0,0,0,0.5)',
      }}
    >
      {/* Crown icon */}
      <div className="mb-5 flex justify-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400/20 to-amber-600/10 ring-1 ring-amber-400/20">
          <Crown className="h-7 w-7 text-amber-400" aria-hidden="true" />
        </div>
      </div>

      {/* Copy */}
      <h3 className="text-center text-[17px] font-bold leading-snug text-zinc-50">
        Unlock Exact Unit Coordinates &amp; Direct Broker-Free Contact Links
      </h3>
      <p className="mx-auto mt-3 max-w-[280px] text-center text-[13px] leading-relaxed text-zinc-400">
        <strong className="text-emerald-400">{alternativeCount} verified below-market</strong>{' '}
        arbitrage units in this compound. Subscribe to{' '}
        <strong className="text-zinc-200">Osool Market Intelligence Engine</strong>{' '}
        to unlock building numbers, unit IDs, and direct contact channels.
      </p>

      {/* Feature bullets */}
      <ul className="mt-5 flex flex-col gap-2">
        {[
          'Full unit coordinates (building + exact unit ID)',
          'Direct broker contact — no intermediaries',
          'Unlimited evaluations per day',
          'La2ta alert notifications for your compounds',
        ].map((feat) => (
          <li key={feat} className="flex items-start gap-2.5 text-[12px] text-zinc-300">
            <CheckCircle2
              className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400"
              aria-hidden="true"
            />
            {feat}
          </li>
        ))}
      </ul>

      {/* CTA */}
      <button
        type="button"
        onClick={onUpgrade}
        className="mt-6 flex w-full items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-3.5 text-[14px] font-semibold text-white shadow-lg transition-all duration-200 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-emerald-500/25 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
      >
        <Sparkles className="h-4 w-4" aria-hidden="true" />
        Subscribe to Market Intelligence
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </button>

      {/* Social proof */}
      <p className="mt-3 text-center text-[11px] text-zinc-600">
        Cancel anytime · Trusted by 2,400+ Egyptian investors
      </p>
    </motion.div>
  );
}

// ── PaymentRoutingSheet ────────────────────────────────────────────

interface PaymentSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

const PLANS = [
  {
    id: 'monthly',
    label: 'Monthly',
    price: 'EGP 199',
    period: '/month',
    badge: null,
  },
  {
    id: 'annual',
    label: 'Annual',
    price: 'EGP 1,590',
    period: '/year',
    badge: 'Save 33%',
  },
] as const;

function PaymentRoutingSheet({ isOpen, onClose }: PaymentSheetProps) {
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<'monthly' | 'annual'>('annual');
  const dialogRef = useRef<HTMLDivElement>(null);

  const handleSubscribe = useCallback(() => {
    onClose();
    router.push(`/upgrade?plan=${selectedPlan}`);
  }, [router, selectedPlan, onClose]);

  // Trap focus within sheet when open
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            key="sheet-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Sheet */}
          <motion.div
            key="sheet-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Upgrade to Osool Market Intelligence"
            ref={dialogRef}
            onKeyDown={handleKeyDown}
            initial={{ y: '100%', opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: '100%', opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 30 }}
            className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-lg rounded-t-3xl border border-white/10 bg-zinc-900 shadow-2xl"
            style={{ maxHeight: '92dvh', overflowY: 'auto' }}
          >
            {/* Handle */}
            <div className="flex justify-center pt-3">
              <div className="h-1 w-10 rounded-full bg-white/15" aria-hidden="true" />
            </div>

            {/* Close */}
            <button
              type="button"
              onClick={onClose}
              aria-label="Close payment sheet"
              className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-white/8 text-zinc-400 transition-colors hover:bg-white/15 hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/30"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>

            <div className="px-6 pb-10 pt-5">
              {/* Header */}
              <div className="mb-6 flex flex-col items-center gap-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-400/20 to-teal-500/10 ring-1 ring-emerald-400/20">
                  <Zap className="h-6 w-6 text-emerald-400" aria-hidden="true" />
                </div>
                <h2 className="text-[20px] font-bold text-zinc-50">
                  Osool Market Intelligence
                </h2>
                <p className="text-center text-[13px] text-zinc-400">
                  Full property intelligence with direct broker bypass
                </p>
              </div>

              {/* Plan selector */}
              <div className="mb-6 grid grid-cols-2 gap-3">
                {PLANS.map((plan) => (
                  <button
                    key={plan.id}
                    type="button"
                    onClick={() => setSelectedPlan(plan.id)}
                    aria-pressed={selectedPlan === plan.id}
                    className={[
                      'relative flex flex-col items-center gap-1 rounded-2xl border p-4 text-center transition-all duration-200',
                      selectedPlan === plan.id
                        ? 'border-emerald-500/50 bg-emerald-500/8 ring-1 ring-emerald-500/30'
                        : 'border-white/8 bg-zinc-900/60 hover:border-white/15',
                    ].join(' ')}
                  >
                    {plan.badge && (
                      <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-emerald-500 px-2.5 py-0.5 text-[10px] font-bold text-white">
                        {plan.badge}
                      </span>
                    )}
                    <span className="text-[12px] font-semibold uppercase tracking-widest text-zinc-400">
                      {plan.label}
                    </span>
                    <span className="text-[22px] font-bold text-zinc-50">{plan.price}</span>
                    <span className="text-[11px] text-zinc-500">{plan.period}</span>
                  </button>
                ))}
              </div>

              {/* Feature list */}
              <ul className="mb-6 flex flex-col gap-2.5">
                {[
                  { feat: 'Unlimited broker offer evaluations', premium: true },
                  { feat: 'Full unit coordinates & building numbers', premium: true },
                  { feat: 'Direct broker contact links', premium: true },
                  { feat: 'La2ta opportunity alerts (real-time)', premium: true },
                  { feat: 'Market pulse reports for all compounds', premium: true },
                  { feat: 'Priority AI CoInvestor responses', premium: true },
                ].map(({ feat }) => (
                  <li key={feat} className="flex items-center gap-3 text-[13px] text-zinc-200">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" aria-hidden="true" />
                    {feat}
                  </li>
                ))}
              </ul>

              {/* Subscribe button */}
              <button
                type="button"
                onClick={handleSubscribe}
                className="flex w-full items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-4 text-[15px] font-semibold text-white shadow-xl transition-all duration-200 hover:from-emerald-400 hover:to-teal-400 hover:shadow-emerald-500/30 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
              >
                <Crown className="h-5 w-5" aria-hidden="true" />
                Subscribe Now — {selectedPlan === 'annual' ? 'EGP 1,590/yr' : 'EGP 199/mo'}
              </button>

              <p className="mt-3 text-center text-[11px] text-zinc-600">
                Billed in EGP · Cancel anytime · Secure via Fawry / InstaPay
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// ─────────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────────

const INITIAL_FORM: FormValues = {
  compound_id: '',
  stated_total_price: '',
  space_sqm: '',
  down_payment: '',
  installment_years: '',
  annual_installments_count: '4',
};

const INSTALLMENT_OPTIONS: SelectOption[] = [
  { value: '1',  label: 'Annual (1× per year)' },
  { value: '2',  label: 'Semi-annual (2× per year)' },
  { value: '4',  label: 'Quarterly (4× per year)' },
  { value: '12', label: 'Monthly (12× per year)' },
];

const LOADING_MESSAGES = [
  'Running NPV normalisation…',
  'Querying compound benchmarks…',
  'Scoring La2ta opportunities…',
  'Composing market intelligence…',
];

/** Main exported component */
export default function RealityCheckPanel() {
  const [phase, setPhase] = useState<PanelPhase>('form');
  const [form, setForm] = useState<FormValues>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Partial<Record<keyof FormValues, true>>>({});
  const [result, setResult] = useState<RealityCheckResult | null>(null);
  const [apiError, setApiError] = useState<string>('');
  const [showPaymentSheet, setShowPaymentSheet] = useState(false);
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0);
  const loadingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const formId = useId();

  // Field updater — marks field as touched on change
  const setField = useCallback(
    (field: keyof FormValues) => (value: string) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      setTouched((prev) => ({ ...prev, [field]: true }));
      // Clear field error on change
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    },
    []
  );

  // Compute visible errors (only for touched fields, or all after first submit)
  const visibleErrors = (field: keyof FormErrors): string | undefined => {
    return touched[field] ? errors[field] : undefined;
  };

  const startLoadingCycle = useCallback(() => {
    setLoadingMsgIdx(0);
    if (loadingIntervalRef.current) clearInterval(loadingIntervalRef.current);
    loadingIntervalRef.current = setInterval(() => {
      setLoadingMsgIdx((i) => (i + 1) % LOADING_MESSAGES.length);
    }, 1400);
  }, []);

  const stopLoadingCycle = useCallback(() => {
    if (loadingIntervalRef.current) {
      clearInterval(loadingIntervalRef.current);
      loadingIntervalRef.current = null;
    }
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // Mark all fields as touched and validate
      const allTouched = Object.keys(form).reduce(
        (acc, k) => ({ ...acc, [k]: true }),
        {} as Partial<Record<keyof FormValues, true>>
      );
      setTouched(allTouched);

      const validationErrors = validateForm(form);
      setErrors(validationErrors);
      if (Object.keys(validationErrors).length > 0) return;

      setPhase('loading');
      startLoadingCycle();

      try {
        const token =
          typeof window !== 'undefined'
            ? localStorage.getItem('access_token')
            : null;

        const body = {
          compound_id:              form.compound_id.trim(),
          stated_total_price:       parseFloat(form.stated_total_price),
          space_sqm:                parseFloat(form.space_sqm),
          down_payment:             parseFloat(form.down_payment),
          installment_years:        parseInt(form.installment_years, 10),
          annual_installments_count: parseInt(form.annual_installments_count, 10),
        };

        const res = await fetch(`${API_BASE}/api/evaluate/reality-check`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const errJson = await res.json().catch(() => null);
          if (res.status === 429) {
            const retryAfter = res.headers.get('Retry-After');
            const hours = retryAfter ? Math.ceil(parseInt(retryAfter, 10) / 3600) : 24;
            setApiError(
              `You have reached the 3-evaluation limit for free accounts. ` +
              `Your allowance resets in approximately ${hours} hour${hours !== 1 ? 's' : ''}. ` +
              `Subscribe to Market Intelligence for unlimited access.`
            );
          } else if (res.status === 404) {
            setApiError(
              errJson?.detail?.message ??
              `No market data found for compound "${form.compound_id.trim()}". ` +
              `This compound may not yet be indexed — try another compound name.`
            );
          } else if (res.status === 422) {
            setApiError(
              'The submitted values are invalid. Please check your inputs and try again.'
            );
          } else {
            setApiError(
              errJson?.detail ?? `Analysis failed (HTTP ${res.status}). Please retry.`
            );
          }
          setPhase('error');
          return;
        }

        const data: RealityCheckResult = await res.json();
        setResult(data);
        setPhase('results');
      } catch {
        setApiError(
          'Unable to reach the analysis server. Check your connection and try again.'
        );
        setPhase('error');
      } finally {
        stopLoadingCycle();
      }
    },
    [form, startLoadingCycle, stopLoadingCycle]
  );

  const handleReset = useCallback(() => {
    setPhase('form');
    setResult(null);
    setApiError('');
    setErrors({});
    setTouched({});
  }, []);

  // Derived gating state
  const hasGatedAlternatives =
    result !== null &&
    result.alternatives.length > 0 &&
    result.alternatives.some((a) => isGated(a.broker_direct_contact));

  return (
    <LazyMotion features={domAnimation}>
      <div className="w-full text-zinc-100">
        {/* ── Loading phase ─────────────────────────────────────────── */}
        <AnimatePresence mode="wait">
          {phase === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex min-h-[320px] flex-col items-center justify-center gap-5 rounded-3xl border border-white/8 bg-zinc-900/50 p-10"
            >
              <div className="relative flex h-16 w-16 items-center justify-center">
                <div className="absolute inset-0 animate-ping rounded-full bg-emerald-500/15" />
                <Loader2
                  className="h-8 w-8 animate-spin text-emerald-400"
                  aria-hidden="true"
                />
              </div>
              <div className="flex flex-col items-center gap-1.5">
                <p className="text-[15px] font-semibold text-zinc-100">
                  Analysing broker offer…
                </p>
                <AnimatePresence mode="wait">
                  <motion.p
                    key={loadingMsgIdx}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.25 }}
                    className="text-[13px] text-zinc-500"
                    aria-live="polite"
                    aria-atomic="true"
                  >
                    {LOADING_MESSAGES[loadingMsgIdx]}
                  </motion.p>
                </AnimatePresence>
              </div>
            </motion.div>
          )}

          {/* ── Form phase ──────────────────────────────────────────── */}
          {phase === 'form' && (
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ type: 'spring', stiffness: 200, damping: 26 }}
            >
              {/* Panel header */}
              <div className="mb-6 flex flex-col gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/12 ring-1 ring-emerald-500/25">
                    <BarChart3 className="h-4.5 w-4.5 text-emerald-400" aria-hidden="true" />
                  </div>
                  <h2 className="text-[17px] font-bold text-zinc-50">
                    Broker Offer Reality Check
                  </h2>
                </div>
                <p className="text-[13px] leading-relaxed text-zinc-400">
                  Enter the offer details below. Our valuation engine will compute
                  the NPV-adjusted price, score it against the compound's secondary-market
                  mean, and surface La2ta arbitrage alternatives.
                </p>
              </div>

              {/* Form */}
              <form
                id={formId}
                onSubmit={handleSubmit}
                noValidate
                aria-label="Broker offer evaluation form"
              >
                <div className="rounded-3xl border border-white/8 bg-zinc-900/50 p-6">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {/* Compound name — full width */}
                    <div className="sm:col-span-2">
                      <FormField
                        id="compound_id"
                        label="Compound Name"
                        value={form.compound_id}
                        onChange={setField('compound_id')}
                        placeholder="e.g. Hyde Park New Cairo"
                        error={visibleErrors('compound_id')}
                        hint="Match the compound name as listed on Nawy or the developer's site."
                      />
                    </div>

                    <FormField
                      id="stated_total_price"
                      label="Stated Total Price"
                      value={form.stated_total_price}
                      onChange={setField('stated_total_price')}
                      type="number"
                      placeholder="5,200,000"
                      suffix="EGP"
                      error={visibleErrors('stated_total_price')}
                      min={0}
                    />

                    <FormField
                      id="space_sqm"
                      label="Unit Size"
                      value={form.space_sqm}
                      onChange={setField('space_sqm')}
                      type="number"
                      placeholder="130"
                      suffix="sqm"
                      error={visibleErrors('space_sqm')}
                      min={0}
                    />

                    <FormField
                      id="down_payment"
                      label="Down Payment"
                      value={form.down_payment}
                      onChange={setField('down_payment')}
                      type="number"
                      placeholder="1,040,000"
                      suffix="EGP"
                      error={visibleErrors('down_payment')}
                      min={0}
                    />

                    <FormField
                      id="installment_years"
                      label="Installment Tenure"
                      value={form.installment_years}
                      onChange={setField('installment_years')}
                      type="number"
                      placeholder="7"
                      suffix="yrs"
                      error={visibleErrors('installment_years')}
                      min={1}
                      max={30}
                    />

                    <div className="sm:col-span-2">
                      <SelectField
                        id="annual_installments_count"
                        label="Payment Frequency"
                        value={form.annual_installments_count}
                        onChange={setField('annual_installments_count')}
                        options={INSTALLMENT_OPTIONS}
                        hint="How many instalment payments are due per year."
                      />
                    </div>
                  </div>

                  {/* Submit */}
                  <div className="mt-6">
                    <button
                      type="submit"
                      form={formId}
                      className="flex w-full items-center justify-center gap-2.5 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-3.5 text-[15px] font-semibold text-white shadow-lg transition-all duration-200 hover:from-emerald-400 hover:to-emerald-500 hover:shadow-emerald-500/20 active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
                    >
                      Run Reality Check
                      <ArrowRight className="h-4.5 w-4.5" aria-hidden="true" />
                    </button>
                    <p className="mt-2.5 text-center text-[11px] text-zinc-600">
                      Free tier · 3 evaluations per 24 hours · No account required
                    </p>
                  </div>
                </div>
              </form>
            </motion.div>
          )}

          {/* ── Error phase ─────────────────────────────────────────── */}
          {phase === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 26 }}
              className="flex flex-col items-center gap-5 rounded-3xl border border-red-500/20 bg-zinc-900/50 p-8 text-center"
              role="alert"
            >
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 ring-1 ring-red-500/20">
                <AlertCircle className="h-7 w-7 text-red-400" aria-hidden="true" />
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="text-[16px] font-bold text-zinc-50">Evaluation Failed</h3>
                <p className="max-w-[360px] text-[13px] leading-relaxed text-zinc-400">
                  {apiError}
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleReset}
                  className="flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-800 px-4 py-2.5 text-[13px] font-semibold text-zinc-200 transition-colors hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
                >
                  <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
                  Try Again
                </button>
                {apiError.toLowerCase().includes('limit') && (
                  <button
                    type="button"
                    onClick={() => setShowPaymentSheet(true)}
                    className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-2.5 text-[13px] font-semibold text-white transition-all hover:from-emerald-400 hover:to-emerald-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
                  >
                    <Crown className="h-3.5 w-3.5" aria-hidden="true" />
                    Upgrade
                  </button>
                )}
              </div>
            </motion.div>
          )}

          {/* ── Results phase ───────────────────────────────────────── */}
          {phase === 'results' && result !== null && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-6"
            >
              {/* Results header */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex flex-col gap-0.5">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                    Reality Check Complete
                  </p>
                  <h2 className="text-[18px] font-bold text-zinc-50">
                    {result.compound_id}
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  aria-label="Run a new evaluation"
                  className="flex shrink-0 items-center gap-1.5 rounded-xl border border-white/10 bg-zinc-800 px-3 py-2 text-[12px] font-medium text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
                >
                  <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
                  New Check
                </button>
              </div>

              {/* Two-column layout: Gauge + Metrics | Arbitrage section */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_1.15fr]">

                {/* ── Left column: Gauge + Key metrics ──────────────── */}
                <div className="flex flex-col gap-5">

                  {/* Gauge panel */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ type: 'spring', stiffness: 180, damping: 24 }}
                    className="rounded-3xl border border-white/8 bg-zinc-900/60 p-6"
                  >
                    <OverpayGauge
                      overpayDeltaPct={result.overpay_delta_pct}
                      isLa2ta={result.is_offer_la2ta}
                    />
                  </motion.div>

                  {/* Metric cards */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                      type: 'spring',
                      stiffness: 180,
                      damping: 24,
                      delay: 0.06,
                    }}
                    className="grid grid-cols-2 gap-3"
                  >
                    <MetricCard
                      label="Offer Price/sqm"
                      value={`${fmt(result.offer_normalized_price_sqm)} EGP`}
                      sub="NPV-adjusted"
                      accent={
                        result.overpay_delta_pct > 10
                          ? 'red'
                          : result.overpay_delta_pct > 0
                          ? 'amber'
                          : 'emerald'
                      }
                      icon={
                        result.overpay_delta_pct > 0 ? (
                          <TrendingUp className="h-3.5 w-3.5" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5" />
                        )
                      }
                    />
                    <MetricCard
                      label="Compound Mean"
                      value={`${fmt(result.compound_benchmark.compound_mean_normalized_sqm)} EGP`}
                      sub={`${result.compound_benchmark.secondary_market_listing_count} comparables`}
                      accent="zinc"
                      icon={<BarChart3 className="h-3.5 w-3.5" />}
                    />
                    <MetricCard
                      label="Cash NPV"
                      value={EGP.format(result.offer_cash_npv_egp)}
                      sub="True cost of this deal"
                      accent="zinc"
                    />
                    <MetricCard
                      label="Compound Range"
                      value={`${fmt(result.compound_benchmark.compound_min_normalized_sqm)} – ${fmt(result.compound_benchmark.compound_max_normalized_sqm)}`}
                      sub="EGP/sqm min–max"
                      accent="zinc"
                    />
                  </motion.div>

                  {/* Valuation note */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.15 }}
                    className="rounded-2xl border border-white/6 bg-zinc-900/40 px-4 py-3"
                  >
                    <p className="text-[12px] leading-relaxed text-zinc-400">
                      {result.valuation_note}
                    </p>
                    {result.rate_limit_remaining !== null && (
                      <p className="mt-1.5 text-[11px] text-zinc-600">
                        Free evaluations remaining today:{' '}
                        <strong className="text-zinc-400">
                          {result.rate_limit_remaining}
                        </strong>
                      </p>
                    )}
                  </motion.div>
                </div>

                {/* ── Right column: Arbitrage alternatives ───────────── */}
                <motion.div
                  initial={{ opacity: 0, x: 16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    type: 'spring',
                    stiffness: 160,
                    damping: 24,
                    delay: 0.1,
                  }}
                  className="flex flex-col gap-4"
                >
                  {/* Section header */}
                  <div className="flex items-center gap-2.5">
                    <Building2 className="h-4.5 w-4.5 text-emerald-400" aria-hidden="true" />
                    <div className="flex flex-col">
                      <h3 className="text-[13px] font-bold text-zinc-100">
                        Verified Below-Market Arbitrage Units
                      </h3>
                      <p className="text-[11px] text-zinc-500">
                        Found Natively Inside This Compound
                      </p>
                    </div>
                    {result.la2ta_alternatives_found > 0 && (
                      <span className="ml-auto shrink-0 rounded-full bg-emerald-500/12 border border-emerald-500/25 px-2.5 py-0.5 text-[11px] font-bold text-emerald-400">
                        {result.la2ta_alternatives_found}
                      </span>
                    )}
                  </div>

                  {result.alternatives.length === 0 ? (
                    /* Empty state */
                    <div className="flex flex-col items-center gap-3 rounded-3xl border border-white/6 bg-zinc-900/40 p-8 text-center">
                      <CheckCircle2
                        className="h-8 w-8 text-zinc-600"
                        aria-hidden="true"
                      />
                      <p className="text-[13px] text-zinc-400">
                        No La2ta alternatives currently indexed for this compound.
                        Check back as new secondary-market listings are ingested.
                      </p>
                    </div>
                  ) : (
                    /* Alternatives grid with optional gating overlay */
                    <div className="relative">
                      {/* Card grid — blurred when gated */}
                      <div
                        aria-hidden={hasGatedAlternatives ? 'true' : undefined}
                        className={[
                          'flex flex-col gap-3',
                          hasGatedAlternatives
                            ? 'pointer-events-none select-none blur-md opacity-40'
                            : '',
                        ]
                          .filter(Boolean)
                          .join(' ')}
                      >
                        {result.alternatives.map((alt, i) => (
                          <motion.div
                            key={alt.listing_id}
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                              type: 'spring',
                              stiffness: 200,
                              damping: 28,
                              delay: 0.08 * i,
                            }}
                          >
                            <AlternativeCard
                              alt={alt}
                              offerNormSqm={result.offer_normalized_price_sqm}
                            />
                          </motion.div>
                        ))}
                      </div>

                      {/* Premium gate overlay */}
                      {hasGatedAlternatives && (
                        <div
                          className="absolute inset-0 flex items-center justify-center p-4"
                          aria-label="Premium content — upgrade required"
                        >
                          <PremiumGateCard
                            alternativeCount={result.la2ta_alternatives_found}
                            onUpgrade={() => setShowPaymentSheet(true)}
                          />
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Payment routing sheet ────────────────────────────────── */}
        <PaymentRoutingSheet
          isOpen={showPaymentSheet}
          onClose={() => setShowPaymentSheet(false)}
        />
      </div>
    </LazyMotion>
  );
}
