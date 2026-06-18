"use client";

/**
 * ForecastChart — scientific price-per-sqm forecast (per developer / compound / area).
 *
 * Consumes the /api/forecast/* response (lib/api PriceForecast). Renders two states:
 *   FREE  — present price + a single 12-month headline % + confidence pill + a
 *           blurred locked region with an upsell CTA (the curve/bands are premium).
 *   PAID  — the full 6/12/24-month curve with an indicative confidence band.
 *
 * DESIGN.md compliant: colours come ONLY from --osool-* tokens (via OSOOL_CHART);
 * Arabic via LanguageContext; prices via CurrencyContext (EGP↔USD). No raw hex,
 * no bleached white. Forecasts are always labelled indicative with a disclaimer.
 */
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, Lock } from "lucide-react";
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from "recharts";

import { OSOOL_CHART } from "@/lib/chart-theme";
import ArchFrame from "@/components/osool/ArchFrame";
import { useCurrency } from "@/contexts/CurrencyContext";
import { useLanguage } from "@/contexts/LanguageContext";
import type { PriceForecast } from "@/lib/api";

const CONFIDENCE_LABEL: Record<string, { en: string; ar: string }> = {
  high: { en: "High confidence", ar: "ثقة عالية" },
  moderate: { en: "Moderate confidence", ar: "ثقة متوسطة" },
  indicative: { en: "Indicative", ar: "استرشادي" },
};

const DIRECTION = {
  up: { Icon: TrendingUp, en: "Rising", ar: "صاعد", color: "var(--osool-nile)" },
  down: { Icon: TrendingDown, en: "Cooling", ar: "هابط", color: "var(--osool-accent)" },
  flat: { Icon: Minus, en: "Stable", ar: "مستقر", color: "var(--osool-muted)" },
} as const;

interface ForecastChartProps {
  forecast: PriceForecast;
}

export default function ForecastChart({ forecast }: ForecastChartProps) {
  const { language } = useLanguage();
  const { format } = useCurrency();
  const isAr = language === "ar";
  const t = (en: string, ar: string) => (isAr ? ar : en);

  const tier = forecast.tier;
  const confKey = (forecast.confidence_label || forecast.confidence_tier || "indicative").toLowerCase();
  const conf = CONFIDENCE_LABEL[confKey] || CONFIDENCE_LABEL.indicative;
  const dir = DIRECTION[(forecast.trend_direction as keyof typeof DIRECTION) || "flat"] || DIRECTION.flat;
  const base = forecast.base_price_per_m2 || 0;

  const title = t(
    `${forecast.entity} — price outlook`,
    `${forecast.entity} — توقع الأسعار`,
  );

  return (
    <ArchFrame className="osool-forecast-chart" style={{ borderRadius: 16 }}>
      <div style={{ padding: "1rem 1.25rem" }} dir={isAr ? "rtl" : "ltr"}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <dir.Icon size={18} style={{ color: dir.color, flexShrink: 0 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: "var(--osool-text)", margin: 0,
                         fontFamily: isAr ? "var(--osool-font-arabic)" : undefined }}>
              {title}
            </h3>
            <p style={{ fontSize: 11, color: "var(--osool-muted)", margin: 0 }}>
              {base ? `${format(base, { lang: language })} / m²` : t("Present price/m²", "سعر المتر الحالي")}
              {forecast.as_of ? ` · ${t("as of", "حتى")} ${forecast.as_of}` : ""}
            </p>
          </div>
          {/* Confidence pill */}
          <span style={{
            fontSize: 10, fontWeight: 700, padding: "3px 9px", borderRadius: 999,
            background: "var(--osool-border-2)", color: "var(--osool-text)", whiteSpace: "nowrap",
          }}>
            {isAr ? conf.ar : conf.en}
          </span>
        </div>

        {/* Headline 12-month outlook */}
        {forecast.headline_12mo_pct != null && (
          <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 24, fontWeight: 800, color: dir.color, fontVariantNumeric: "tabular-nums" }}>
              {forecast.headline_12mo_pct > 0 ? "+" : ""}{forecast.headline_12mo_pct}%
            </span>
            <span style={{ fontSize: 12, color: "var(--osool-muted)" }}>
              {t("projected 12-month change", "التغير المتوقع خلال 12 شهرًا")} · {isAr ? dir.ar : dir.en}
            </span>
          </div>
        )}

        {tier === "premium"
          ? <PaidBody forecast={forecast} base={base} format={format} language={language} t={t} />
          : <FreeBody forecast={forecast} t={t} isAr={isAr} />}

        {/* Disclaimer — always present */}
        {forecast.disclaimer && (
          <p style={{ fontSize: 10, color: "var(--osool-muted)", marginTop: 12, lineHeight: 1.4,
                      fontFamily: isAr ? "var(--osool-font-arabic)" : undefined }}>
            {isAr ? forecast.disclaimer.ar : forecast.disclaimer.en}
          </p>
        )}
      </div>
    </ArchFrame>
  );
}

// ── Paid: full curve + indicative band ────────────────────────────────────────
function PaidBody({ forecast, base, format, language, t }: {
  forecast: PriceForecast; base: number;
  format: (n: number, o?: { lang?: "en" | "ar" }) => string;
  language: "en" | "ar"; t: (en: string, ar: string) => string;
}) {
  const horizons = forecast.horizons || [];
  if (!base || horizons.length === 0) {
    return <p style={{ fontSize: 12, color: "var(--osool-muted)" }}>
      {t("Not enough data to chart a forecast yet.", "لا توجد بيانات كافية لرسم التوقع بعد.")}
    </p>;
  }
  const data = [
    { label: t("now", "الآن"), point: base, lower: base, upper: base },
    ...horizons.map((h) => ({
      label: `${h.horizon_months}${t("mo", "ش")}`,
      point: h.point, lower: h.lower, upper: h.upper,
    })),
  ];

  return (
    <div style={{ height: 220, width: "100%" }} dir="ltr">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 6, right: 10, left: 6, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={OSOOL_CHART.grid} opacity={0.5} />
          <XAxis dataKey="label" tick={{ fill: OSOOL_CHART.axis, fontSize: 11 }}
                 tickLine={false} axisLine={{ stroke: OSOOL_CHART.grid }} />
          <YAxis tick={{ fill: OSOOL_CHART.axis, fontSize: 10 }} tickLine={false} axisLine={false}
                 width={54} tickFormatter={(v: number) => format(v, { lang: language })} />
          <Tooltip content={<ForecastTooltip format={format} language={language} t={t} />} />
          {/* Indicative band: upper area then erase below lower with the surface colour */}
          <Area type="monotone" dataKey="upper" stroke="none" fill={OSOOL_CHART.primary} fillOpacity={0.14} isAnimationActive={false} />
          <Area type="monotone" dataKey="lower" stroke="none" fill={OSOOL_CHART.tooltipBg} fillOpacity={1} isAnimationActive={false} />
          {/* Forecast point line (dashed beyond 'now') */}
          <Line type="monotone" dataKey="point" stroke={OSOOL_CHART.secondary} strokeWidth={2.5}
                strokeDasharray="5 3" dot={{ r: 3, fill: OSOOL_CHART.secondary }} activeDot={{ r: 5 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function ForecastTooltip({ active, payload, label, format, language, t }:
  TooltipProps<number, string> & {
    format: (n: number, o?: { lang?: "en" | "ar" }) => string;
    language: "en" | "ar"; t: (en: string, ar: string) => string;
  }) {
  if (!active || !payload?.length) return null;
  const row = payload[0]?.payload as { point: number; lower: number; upper: number };
  return (
    <div style={{ background: OSOOL_CHART.tooltipBg, border: `1px solid ${OSOOL_CHART.tooltipBorder}`,
                  borderRadius: 12, padding: "8px 12px", fontSize: 12, color: OSOOL_CHART.text }}>
      <p style={{ fontWeight: 700, margin: "0 0 4px" }}>{label}</p>
      <p style={{ margin: 0 }}>{format(row.point, { lang: language })} / m²</p>
      {row.lower !== row.upper && (
        <p style={{ margin: "2px 0 0", color: OSOOL_CHART.axis, fontSize: 11 }}>
          {t("range", "النطاق")}: {format(row.lower, { lang: language })}–{format(row.upper, { lang: language })}
        </p>
      )}
    </div>
  );
}

// ── Free: locked teaser + upsell ──────────────────────────────────────────────
function FreeBody({ forecast, t, isAr }: {
  forecast: PriceForecast; t: (en: string, ar: string) => string; isAr: boolean;
}) {
  const up = forecast.upsell;
  return (
    <div style={{ position: "relative", borderRadius: 12, overflow: "hidden",
                  border: "1px dashed var(--osool-border)", padding: 16, marginTop: 4 }}>
      {/* Blurred faux-chart hint */}
      <div aria-hidden style={{ filter: "blur(6px)", opacity: 0.5, height: 70,
        background: "linear-gradient(90deg, var(--osool-border-2), var(--osool-surface))",
        borderRadius: 8 }} />
      {/* Lock overlay */}
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", gap: 8, textAlign: "center", padding: 12 }}>
        <Lock size={18} style={{ color: "var(--osool-accent)" }} />
        <p style={{ fontSize: 12, fontWeight: 600, color: "var(--osool-text)", margin: 0,
                    fontFamily: isAr ? "var(--osool-font-arabic)" : undefined }}>
          {up ? (isAr ? up.headline_ar : up.headline_en)
              : t("Unlock the full 6/12/24-month forecast.", "افتح التوقع الكامل لـ 6/12/24 شهرًا.")}
        </p>
        {up?.sku_options?.length ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center" }}>
            {up.sku_options.map((sku) => (
              <span key={sku.sku} style={{
                fontSize: 11, fontWeight: 700, padding: "5px 12px", borderRadius: 999,
                background: "var(--osool-accent)", color: "var(--osool-surface)",
              }}>
                {isAr ? sku.label_ar : sku.label_en}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
