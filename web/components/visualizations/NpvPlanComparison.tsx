"use client";

// NpvPlanComparison (Fix 3) — installment-first comparison of multiple
// listings by cash-equivalent NPV ("cheapest in real money, not sticker"),
// plus a rent-vs-installment read per listing. Backend payload comes from
// wolf_orchestrator._build_payment_plan_comparison / /valuation/compare-plans.

import { motion } from "framer-motion";
import { Scale, TrendingDown, Home } from "lucide-react";

interface PlanRow {
  listing_id: string;
  label?: string | null;
  sticker_price: number;
  down_payment?: number | null;
  down_payment_pct?: number | null;
  monthly_installment?: number | null;
  years?: number | null;
  npv_today: number;
  npv_discount_pct: number;
  is_cash: boolean;
  rent_ratio?: number | null;
  avg_rent?: number | null;
  verdict_ar?: string | null;
  verdict_en?: string | null;
}

interface NpvPlanComparisonProps {
  rows: PlanRow[];
  cheapestListingId?: string | null;
  cbeRate?: number | null;
  isRTL?: boolean;
}

const fmtEGP = (v: number | null | undefined) => {
  if (v === null || v === undefined || !isFinite(v)) return "—";
  return new Intl.NumberFormat("en-EG", {
    style: "currency",
    currency: "EGP",
    maximumFractionDigits: 0,
  }).format(v);
};

export default function NpvPlanComparison({
  rows,
  cheapestListingId,
  cbeRate,
  isRTL = false,
}: NpvPlanComparisonProps) {
  if (!Array.isArray(rows) || rows.length === 0) return null;

  const t = (ar: string, en: string) => (isRTL ? ar : en);
  const cbePct = cbeRate ? (cbeRate * 100).toFixed(0) : null;

  return (
    <motion.div
      dir={isRTL ? "rtl" : "ltr"}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl overflow-hidden border border-[var(--color-border)] bg-gradient-to-br from-emerald-950/20 to-teal-950/10"
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-[var(--color-border)] bg-gradient-to-r from-emerald-600/15 to-teal-600/15">
        <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center">
          <Scale className="w-5 h-5 text-emerald-300" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">
            {t("مقارنة الأقساط بالقيمة الحالية", "Installment comparison — today's money")}
          </h3>
          <p className="text-[11px] text-white/60">
            {t(
              "السعر الحقيقي بعد خصم قيمة الوقت — مش سعر الكتالوج",
              "Real cost after discounting future payments — not the sticker",
            )}
            {cbePct ? t(` (خصم ${cbePct}%)`, ` (discounted at ${cbePct}%)`) : null}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-[12px] text-white/80">
          <thead>
            <tr className="text-white/50 text-[11px] uppercase tracking-wide">
              <th className="text-start font-medium px-4 py-2">{t("الوحدة", "Listing")}</th>
              <th className="text-end font-medium px-3 py-2">{t("السعر", "Sticker")}</th>
              <th className="text-end font-medium px-3 py-2">{t("المقدم", "Down")}</th>
              <th className="text-end font-medium px-3 py-2">{t("القسط/شهر", "Monthly")}</th>
              <th className="text-end font-medium px-3 py-2">{t("السنين", "Years")}</th>
              <th className="text-end font-medium px-3 py-2">{t("القيمة الحالية", "NPV today")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isCheapest = r.listing_id === cheapestListingId;
              const verdict = isRTL ? r.verdict_ar : r.verdict_en;
              return (
                <tr
                  key={r.listing_id || r.label || Math.random()}
                  className={`border-t border-[var(--color-border)] ${
                    isCheapest ? "bg-emerald-500/10" : ""
                  }`}
                >
                  <td className="px-4 py-3 align-top">
                    <div className="flex items-center gap-2">
                      {isCheapest && (
                        <span
                          className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 text-emerald-300 px-2 py-0.5 text-[10px] font-semibold"
                          title={t("الأرخص بالقيمة الحالية", "Cheapest in today's money")}
                        >
                          <TrendingDown className="w-3 h-3" />
                          {t("الأفضل", "Best")}
                        </span>
                      )}
                      <span className="text-white font-medium">{r.label || r.listing_id}</span>
                    </div>
                    {verdict && (
                      <div className="mt-1 flex items-center gap-1 text-[11px] text-white/55">
                        <Home className="w-3 h-3 shrink-0" />
                        <span>{verdict}</span>
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3 text-end whitespace-nowrap">{fmtEGP(r.sticker_price)}</td>
                  <td className="px-3 py-3 text-end whitespace-nowrap">
                    {r.down_payment ? (
                      <>
                        {fmtEGP(r.down_payment)}
                        {r.down_payment_pct != null && (
                          <span className="text-white/45"> ({r.down_payment_pct}%)</span>
                        )}
                      </>
                    ) : (
                      <span className="text-white/40">{t("كاش", "Cash")}</span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-end whitespace-nowrap">
                    {r.monthly_installment ? fmtEGP(r.monthly_installment) : "—"}
                  </td>
                  <td className="px-3 py-3 text-end">{r.years ?? "—"}</td>
                  <td className="px-3 py-3 text-end whitespace-nowrap">
                    <span className={isCheapest ? "text-emerald-300 font-semibold" : "text-white font-medium"}>
                      {fmtEGP(r.npv_today)}
                    </span>
                    {!r.is_cash && r.npv_discount_pct > 0 && (
                      <div className="text-[10px] text-emerald-400/70">
                        −{r.npv_discount_pct}% {t("مقابل الكتالوج", "vs sticker")}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
