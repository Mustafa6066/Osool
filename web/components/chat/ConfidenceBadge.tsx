"use client";

import { useState } from "react";

export type ConfidenceTier = "high" | "moderate" | "indicative";

interface ConfidenceBadgeProps {
  tier: ConfidenceTier;
  /** Raw sample count — shown only to premium users */
  sampleCount?: number;
  isPremium?: boolean;
  /** ISO date string e.g. "2026-04-15" */
  dataAsOf?: string;
  isRtl?: boolean;
  className?: string;
}

const TIER_CONFIG = {
  high: {
    label: { ar: "موثوق", en: "High confidence" },
    /** solid terracotta pill with checkmark + slow pulse ring */
    badgeClass:
      "bg-[var(--color-primary)] text-white border-transparent",
    barClass: "",
    icon: "✓",
    pulse: true,
  },
  moderate: {
    label: { ar: "متوسط", en: "Moderate" },
    /** Nile outline pill, no fill */
    badgeClass:
      "bg-transparent border border-[var(--osool-nile)] text-[var(--osool-nile)]",
    barClass: "",
    icon: null,
    pulse: false,
  },
  indicative: {
    label: { ar: "أولي", en: "Indicative" },
    /** amber left-bar block */
    badgeClass:
      "bg-[#FEF3C7] text-[var(--color-warning-dark)] border-transparent rounded-sm",
    barClass:
      "absolute inset-y-0 start-0 w-1 rounded-s-sm bg-[var(--color-warning)]",
    icon: "⚠",
    pulse: false,
  },
} as const;


/**
 * Three-tier confidence badge for comparison results.
 *
 * - high        → solid terracotta pill + ✓ + pulse ring
 * - moderate    → Nile outline pill
 * - indicative  → amber block with left accent bar + ⚠
 *
 * Free users see a 🔒 N=? in place of raw sample count.
 * Tapping 🔒 fires the inline upgrade prompt.
 */
export function ConfidenceBadge({
  tier,
  sampleCount,
  isPremium = false,
  dataAsOf,
  isRtl = false,
  className = "",
}: ConfidenceBadgeProps) {
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);
  const config = TIER_CONFIG[tier];
  const lang = isRtl ? "ar" : "en";

  const label = config.label[lang];
  const dir = isRtl ? "rtl" : "ltr";

  const sampleDisplay =
    sampleCount !== undefined ? (
      isPremium ? (
        <span className="ms-1 text-xs opacity-70">N={sampleCount}</span>
      ) : (
        <button
          type="button"
          aria-label={isRtl ? "فتح الباقة المتقدمة" : "Unlock to see sample count"}
          className="ms-1 text-xs opacity-70 hover:opacity-100 transition-opacity focus:outline-none"
          onClick={(e) => {
            e.stopPropagation();
            setShowUpgradePrompt(true);
          }}
        >
          🔒 N=?
        </button>
      )
    ) : null;

  return (
    <div dir={dir} className={`inline-flex flex-col items-start gap-0.5 ${className}`}>
      {/* Badge pill / block */}
      <div
        className={`relative inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full select-none ${config.badgeClass}`}
      >
        {/* Left accent bar (indicative only) */}
        {config.barClass && <span aria-hidden className={config.barClass} />}

        {/* Pulse ring (high only) */}
        {config.pulse && (
          <span
            aria-hidden
            className="absolute inset-0 rounded-full animate-ping-slow bg-[var(--color-primary)] opacity-20"
          />
        )}

        {config.icon && (
          <span aria-hidden className={tier === "indicative" ? "ps-1" : ""}>
            {config.icon}
          </span>
        )}

        <span>{label}</span>
        {sampleDisplay}
      </div>

      {/* Data freshness line */}
      {dataAsOf && (
        <span className="text-[10px] text-gray-400 ms-1">
          {isRtl ? `بيانات حتى ${dataAsOf}` : `Data as of ${dataAsOf}`}
        </span>
      )}

      {/* Inline upgrade prompt (appears when free user taps 🔒) */}
      {showUpgradePrompt && !isPremium && (
        <div
          role="dialog"
          aria-label={isRtl ? "فتح الباقة المتقدمة" : "Unlock Premium"}
          className="mt-1 rounded-lg border border-[var(--color-primary)] bg-white p-3 text-xs shadow-md w-48"
          dir={dir}
        >
          <p className="mb-2 font-medium text-gray-800">
            {isRtl
              ? "افتح الباقة المتقدمة لرؤية عدد العينات الكاملة"
              : "Unlock Premium to see full sample counts"}
          </p>
          <button
            type="button"
            className="w-full rounded-md bg-[var(--color-primary)] px-3 py-1.5 text-white font-semibold hover:bg-[var(--color-primary-dark)] transition-colors"
            onClick={() => {
              setShowUpgradePrompt(false);
              // Bubble up to the chat layer's upgrade flow.
              window.dispatchEvent(new CustomEvent("osool:unlock-premium"));
            }}
          >
            {isRtl ? "فتح الآن" : "Unlock Now"}
          </button>
          <button
            type="button"
            className="mt-1 w-full text-center text-gray-400 hover:text-gray-600 transition-colors"
            onClick={() => setShowUpgradePrompt(false)}
          >
            {isRtl ? "إغلاق" : "Dismiss"}
          </button>
        </div>
      )}
    </div>
  );
}
