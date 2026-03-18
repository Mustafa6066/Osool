"use client";

import React from "react";
import {
  Building2,
  CalendarClock,
  TrendingUp,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Award,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  CircleDot,
  Brain,
  Layers,
} from "lucide-react";
import type { DeveloperPayload, ProjectRecord } from "./TerminalCore";

/* ── i18n labels ─────────────────────────────────── */
const L = {
  en: {
    devProfile: "DEVELOPER PROFILE",
    verified: "VERIFIED",
    partial: "PARTIAL",
    unverified: "UNVERIFIED",
    founded: "FOUNDED",
    projects: "PROJECTS",
    delivered: "DELIVERED",
    wolfScore: "WOLF SCORE",
    marketRank: "MARKET RANK",
    deliveryPerf: "DELIVERY PERFORMANCE",
    avgDelay: "AVG DELAY",
    months: "MO",
    onTimeRate: "ON-TIME RATE",
    roiTracker: "ROI TRACK RECORD",
    overallRoi: "OVERALL ROI",
    yearlyTrend: "YEARLY TREND",
    projectMatrix: "PROJECT HEALTH MATRIX",
    project: "PROJECT",
    location: "LOCATION",
    launch: "LAUNCH",
    promised: "PROMISED",
    actual: "ACTUAL",
    delay: "DELAY",
    status: "STATUS",
    roi: "ROI",
    sold: "SOLD",
    riskRadar: "RISK ASSESSMENT",
    deliveryRisk: "DELIVERY",
    financialRisk: "FINANCIAL",
    marketRisk: "MARKET",
    legalRisk: "LEGAL",
    reputationRisk: "REPUTATION",
    aiConfidence: "AI CONFIDENCE",
    analysisNote: "ANALYSIS BASED ON",
    dataPoints: "DATA POINTS",
    marketPosition: "MARKET POSITION",
    outOf: "OF",
    topPercentile: "TOP PERCENTILE",
    riskTier: "RISK TIER",
    priceGrowth: "PRICE GROWTH",
    launchPrice: "LAUNCH ₱/SQM",
    currentPrice: "CURRENT ₱/SQM",
    growth: "GROWTH",
    delivered_s: "DELIVERED",
    onTrack: "ON TRACK",
    delayed_s: "DELAYED",
    severelyDelayed: "SEVERELY DELAYED",
    na: "N/A",
    units: "UNITS",
  },
  ar: {
    devProfile: "ملف المطوّر",
    verified: "موثّق",
    partial: "جزئي",
    unverified: "غير موثّق",
    founded: "التأسيس",
    projects: "المشاريع",
    delivered: "المسلّمة",
    wolfScore: "تقييم وولف",
    marketRank: "الترتيب",
    deliveryPerf: "أداء التسليم",
    avgDelay: "متوسط التأخير",
    months: "شهر",
    onTimeRate: "معدل الالتزام",
    roiTracker: "سجل عائد الاستثمار",
    overallRoi: "العائد الكلي",
    yearlyTrend: "الاتجاه السنوي",
    projectMatrix: "مصفوفة صحة المشاريع",
    project: "المشروع",
    location: "الموقع",
    launch: "الإطلاق",
    promised: "الموعد",
    actual: "الفعلي",
    delay: "التأخير",
    status: "الحالة",
    roi: "العائد",
    sold: "مباع",
    riskRadar: "تقييم المخاطر",
    deliveryRisk: "التسليم",
    financialRisk: "المالية",
    marketRisk: "السوق",
    legalRisk: "القانونية",
    reputationRisk: "السمعة",
    aiConfidence: "ثقة الذكاء الاصطناعي",
    analysisNote: "التحليل مبني على",
    dataPoints: "نقطة بيانات",
    marketPosition: "الموقع السوقي",
    outOf: "من",
    topPercentile: "أعلى نسبة مئوية",
    riskTier: "مستوى المخاطر",
    priceGrowth: "نمو الأسعار",
    launchPrice: "سعر الإطلاق/م²",
    currentPrice: "السعر الحالي/م²",
    growth: "النمو",
    delivered_s: "تم التسليم",
    onTrack: "في الموعد",
    delayed_s: "متأخر",
    severelyDelayed: "تأخر شديد",
    na: "غ/م",
    units: "وحدات",
  },
};

/* ── Helper formatters ───────────────────────────── */
function fmtNum(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}K` : n.toFixed(0);
}

function fmtPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
}

function riskColor(score: number): string {
  if (score >= 70) return "text-rose-500";
  if (score >= 45) return "text-yellow-500";
  return "text-lime-400";
}

function riskBarColor(score: number): string {
  if (score >= 70) return "bg-rose-500";
  if (score >= 45) return "bg-yellow-500";
  return "bg-lime-400";
}

function tierColor(tier: string): string {
  switch (tier) {
    case "LOW":
      return "text-lime-400 border-lime-400/30";
    case "MEDIUM":
      return "text-yellow-500 border-yellow-500/30";
    case "HIGH":
      return "text-rose-500 border-rose-500/30";
    case "CRITICAL":
      return "text-rose-600 border-rose-600/50 animate-pulse";
    default:
      return "text-[#555] border-[#333]";
  }
}

function statusIcon(status: ProjectRecord["status"]) {
  switch (status) {
    case "delivered":
      return <CheckCircle2 className="h-3.5 w-3.5 text-lime-400" />;
    case "on-track":
      return <CircleDot className="h-3.5 w-3.5 text-blue-400" />;
    case "delayed":
      return <Clock className="h-3.5 w-3.5 text-yellow-500" />;
    case "severely-delayed":
      return <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />;
  }
}

function statusLabel(
  status: ProjectRecord["status"],
  t: (typeof L)["en"]
): string {
  switch (status) {
    case "delivered":
      return t.delivered_s;
    case "on-track":
      return t.onTrack;
    case "delayed":
      return t.delayed_s;
    case "severely-delayed":
      return t.severelyDelayed;
  }
}

function statusColor(status: ProjectRecord["status"]): string {
  switch (status) {
    case "delivered":
      return "text-lime-400";
    case "on-track":
      return "text-blue-400";
    case "delayed":
      return "text-yellow-500";
    case "severely-delayed":
      return "text-rose-500";
  }
}

/* ═══════════════════════════════════════════════════
   BENTO CARD WRAPPER
   ═══════════════════════════════════════════════════ */
function Card({
  children,
  className = "",
  span = "",
}: {
  children: React.ReactNode;
  className?: string;
  span?: string;
}) {
  return (
    <div
      className={`rounded-2xl border border-[#222] bg-[#0a0a0a] p-4 ${span} ${className}`}
    >
      {children}
    </div>
  );
}

function CardHeader({
  icon: Icon,
  label,
  badge,
}: {
  icon: React.ElementType;
  label: string;
  badge?: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-lime-400" />
        <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-[#888]">
          {label}
        </span>
      </div>
      {badge}
    </div>
  );
}

/* ═══════════════════════════════════════════════════
   MAIN: DEVELOPER ANALYSIS BENTO GRID
   ═══════════════════════════════════════════════════ */
interface Props {
  data: DeveloperPayload;
  lang: "en" | "ar";
  isRTL: boolean;
}

export default function DeveloperAnalysis({ data, lang, isRTL }: Props) {
  const t = L[lang] || L.en;

  // Computed
  const percentile = Math.round(
    ((data.marketTotal - data.marketRank + 1) / data.marketTotal) * 100
  );
  const totalDataPoints =
    data.projects.length * 8 + data.yearlyRoi.length + 5;

  return (
    <div dir={isRTL ? "rtl" : "ltr"} className="p-3 sm:p-4 lg:p-6">
      {/* ══ METRICS STRIP (full width) ══ */}
      <div className="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
        <MetricChip
          label={t.wolfScore}
          value={data.wolfScore.toFixed(1)}
          suffix="/10"
          positive={data.wolfScore >= 7}
        />
        <MetricChip
          label={t.overallRoi}
          value={fmtPct(data.overallRoi)}
          positive={data.overallRoi >= 15}
        />
        <MetricChip
          label={t.onTimeRate}
          value={`${(data.onTimeRate * 100).toFixed(0)}%`}
          positive={data.onTimeRate >= 0.5}
        />
        <MetricChip
          label={t.avgDelay}
          value={`${data.avgDelayMonths.toFixed(1)}`}
          suffix={` ${t.months}`}
          positive={data.avgDelayMonths < 6}
        />
        <MetricChip
          label={t.marketRank}
          value={`#${data.marketRank}`}
          suffix={` / ${data.marketTotal}`}
          positive={data.marketRank <= 10}
          className="hidden sm:flex"
        />
        <MetricChip
          label={t.riskTier}
          value={data.riskTier}
          positive={data.riskTier === "LOW"}
          className="hidden lg:flex"
        />
      </div>

      {/* ══ BENTO GRID ══ */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
        {/* ── Developer Profile (col-span-1 or 2 on lg) ── */}
        <Card span="lg:col-span-1">
          <CardHeader
            icon={Building2}
            label={t.devProfile}
            badge={
              <span
                className={`rounded-md border px-2 py-0.5 font-mono text-[9px] font-bold uppercase ${
                  data.verificationStatus === "VERIFIED"
                    ? "border-lime-400/30 text-lime-400"
                    : data.verificationStatus === "PARTIAL"
                      ? "border-yellow-500/30 text-yellow-500"
                      : "border-rose-500/30 text-rose-500"
                }`}
              >
                {data.verificationStatus === "VERIFIED"
                  ? t.verified
                  : data.verificationStatus === "PARTIAL"
                    ? t.partial
                    : t.unverified}
              </span>
            }
          />

          <div className="mb-4">
            <h3 className="text-xl font-bold text-white">
              {lang === "ar" ? data.nameAr : data.name}
            </h3>
            <p className="mt-0.5 font-mono text-[11px] text-[#555]">
              {lang === "ar" ? data.name : data.nameAr}
            </p>
          </div>

          <div className="space-y-2.5">
            <ProfileRow label={t.founded} value={String(data.founded)} />
            <ProfileRow
              label={t.projects}
              value={String(data.totalProjects)}
            />
            <ProfileRow
              label={t.delivered}
              value={`${data.deliveredProjects} / ${data.totalProjects}`}
            />
            <ProfileRow
              label={t.wolfScore}
              value={data.wolfScore.toFixed(1)}
              highlight={data.wolfScore >= 7}
            />
          </div>
        </Card>

        {/* ── Delivery Performance (col-span-2 on lg) ── */}
        <Card span="lg:col-span-2">
          <CardHeader icon={CalendarClock} label={t.deliveryPerf} />

          {/* Visual timeline */}
          <div className="mb-4 flex items-end gap-1">
            {data.projects.map((p, i) => {
              const maxDelay = Math.max(
                ...data.projects.map((x) => x.delayMonths),
                1
              );
              const height = p.delayMonths
                ? Math.max((p.delayMonths / maxDelay) * 80, 8)
                : 4;
              const bg =
                p.status === "delivered" && p.delayMonths === 0
                  ? "bg-lime-400"
                  : p.status === "on-track"
                    ? "bg-blue-400"
                    : p.status === "severely-delayed"
                      ? "bg-rose-500"
                      : p.delayMonths > 0
                        ? "bg-yellow-500"
                        : "bg-lime-400/40";
              return (
                <div
                  key={i}
                  className="group relative flex flex-1 flex-col items-center"
                >
                  <div
                    className={`w-full rounded-t ${bg} transition-all hover:opacity-80`}
                    style={{ height: `${height}px` }}
                  />
                  <span className="mt-1 font-mono text-[8px] text-[#444]">
                    {String.fromCharCode(65 + i)}
                  </span>
                  {/* Tooltip */}
                  <div className="pointer-events-none absolute -top-16 z-10 hidden rounded-lg border border-[#333] bg-[#111] px-2 py-1 text-center group-hover:block">
                    <p className="whitespace-nowrap font-mono text-[9px] text-white">
                      {p.name}
                    </p>
                    <p className="font-mono text-[9px] text-[#888]">
                      {p.delayMonths > 0
                        ? `${p.delayMonths} ${t.months} ${t.delay.toLowerCase()}`
                        : t.onTrack}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Aggregate stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-[#222] bg-black p-3 text-center">
              <p className="font-mono text-[10px] uppercase text-[#555]">
                {t.avgDelay}
              </p>
              <p
                className={`mt-1 font-mono text-lg font-bold ${data.avgDelayMonths > 12 ? "text-rose-500" : data.avgDelayMonths > 6 ? "text-yellow-500" : "text-lime-400"}`}
              >
                {data.avgDelayMonths.toFixed(1)}
              </p>
              <p className="font-mono text-[9px] text-[#444]">{t.months}</p>
            </div>
            <div className="rounded-xl border border-[#222] bg-black p-3 text-center">
              <p className="font-mono text-[10px] uppercase text-[#555]">
                {t.onTimeRate}
              </p>
              <p
                className={`mt-1 font-mono text-lg font-bold ${data.onTimeRate >= 0.5 ? "text-lime-400" : "text-rose-500"}`}
              >
                {(data.onTimeRate * 100).toFixed(0)}%
              </p>
              <p className="font-mono text-[9px] text-[#444]">
                {data.deliveredProjects} {t.delivered.toLowerCase()}
              </p>
            </div>
            <div className="rounded-xl border border-[#222] bg-black p-3 text-center">
              <p className="font-mono text-[10px] uppercase text-[#555]">
                {t.delivered}
              </p>
              <p className="mt-1 font-mono text-lg font-bold text-white">
                {data.deliveredProjects}
              </p>
              <p className="font-mono text-[9px] text-[#444]">
                / {data.totalProjects}
              </p>
            </div>
          </div>
        </Card>

        {/* ── AI Confidence + Market Position (stacked, col-span-1 on lg) ── */}
        <div className="flex flex-col gap-3 lg:col-span-1">
          {/* AI Confidence */}
          <Card>
            <CardHeader icon={Brain} label={t.aiConfidence} />
            <div className="flex flex-col items-center py-2">
              <div className="relative h-24 w-24">
                <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke="#222"
                    strokeWidth="6"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke={
                      data.aiConfidence >= 90
                        ? "#a3e635"
                        : data.aiConfidence >= 70
                          ? "#eab308"
                          : "#f43f5e"
                    }
                    strokeWidth="6"
                    strokeDasharray={`${(data.aiConfidence / 100) * 264} 264`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span
                    className={`font-mono text-lg font-bold ${data.aiConfidence >= 90 ? "text-lime-400" : data.aiConfidence >= 70 ? "text-yellow-500" : "text-rose-500"}`}
                  >
                    {data.aiConfidence.toFixed(1)}%
                  </span>
                </div>
              </div>
              <p className="mt-2 font-mono text-[9px] text-[#555]">
                {t.analysisNote} {totalDataPoints} {t.dataPoints}
              </p>
            </div>
          </Card>

          {/* Market Position */}
          <Card>
            <CardHeader icon={Award} label={t.marketPosition} />
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-3xl font-bold text-white">
                #{data.marketRank}
              </span>
              <span className="font-mono text-sm text-[#555]">
                {t.outOf} {data.marketTotal}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase text-[#555]">
                {t.topPercentile}:
              </span>
              <span className="font-mono text-sm font-bold text-lime-400">
                {percentile}%
              </span>
            </div>
            {/* Rank bar */}
            <div className="mt-3 h-2 w-full rounded-full bg-[#222]">
              <div
                className="h-2 rounded-full bg-lime-400 transition-all"
                style={{ width: `${percentile}%` }}
              />
            </div>
          </Card>
        </div>

        {/* ── ROI Track Record (col-span-2 on lg) ── */}
        <Card span="lg:col-span-2">
          <CardHeader
            icon={TrendingUp}
            label={t.roiTracker}
            badge={
              <span
                className={`font-mono text-sm font-bold ${data.overallRoi >= 15 ? "text-lime-400" : "text-rose-500"}`}
              >
                {fmtPct(data.overallRoi)}
              </span>
            }
          />

          {/* Bar chart */}
          <div className="mb-3 flex items-end gap-2" style={{ height: 100 }}>
            {data.yearlyRoi.map((yr, i) => {
              const maxRoi = Math.max(...data.yearlyRoi.map((y) => y.roi), 1);
              const height = Math.max((yr.roi / maxRoi) * 90, 4);
              return (
                <div
                  key={i}
                  className="group relative flex flex-1 flex-col items-center justify-end"
                  style={{ height: "100%" }}
                >
                  <div
                    className={`w-full rounded-t transition-all ${yr.roi >= 20 ? "bg-lime-400" : yr.roi >= 10 ? "bg-lime-400/60" : "bg-yellow-500/60"} group-hover:opacity-80`}
                    style={{ height: `${height}%` }}
                  />
                  <span className="absolute top-0 font-mono text-[9px] font-bold text-white opacity-0 transition-opacity group-hover:opacity-100">
                    {yr.roi.toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex gap-2">
            {data.yearlyRoi.map((yr, i) => (
              <div key={i} className="flex-1 text-center">
                <span className="font-mono text-[9px] text-[#555]">
                  {yr.year}
                </span>
              </div>
            ))}
          </div>

          {/* ROI summary row */}
          <div className="mt-3 flex items-center justify-between rounded-xl border border-[#222] bg-black px-3 py-2">
            <span className="font-mono text-[10px] uppercase text-[#555]">
              {t.yearlyTrend}
            </span>
            {data.yearlyRoi.length >= 2 && (
              <span
                className={`flex items-center gap-1 font-mono text-xs font-bold ${
                  data.yearlyRoi[data.yearlyRoi.length - 1].roi >=
                  data.yearlyRoi[data.yearlyRoi.length - 2].roi
                    ? "text-lime-400"
                    : "text-rose-500"
                }`}
              >
                {data.yearlyRoi[data.yearlyRoi.length - 1].roi >=
                data.yearlyRoi[data.yearlyRoi.length - 2].roi ? (
                  <ArrowUpRight className="h-3 w-3" />
                ) : (
                  <ArrowDownRight className="h-3 w-3" />
                )}
                {fmtPct(
                  data.yearlyRoi[data.yearlyRoi.length - 1].roi -
                    data.yearlyRoi[data.yearlyRoi.length - 2].roi
                )}{" "}
                YoY
              </span>
            )}
          </div>
        </Card>

        {/* ── Risk Assessment (col-span-2 on lg) ── */}
        <Card span="lg:col-span-2">
          <CardHeader
            icon={ShieldAlert}
            label={t.riskRadar}
            badge={
              <span
                className={`rounded-md border px-2 py-0.5 font-mono text-[9px] font-bold uppercase ${tierColor(data.riskTier)}`}
              >
                {data.riskTier}
              </span>
            }
          />

          <div className="space-y-3">
            {(
              [
                ["deliveryRisk", t.deliveryRisk],
                ["financialRisk", t.financialRisk],
                ["marketRisk", t.marketRisk],
                ["legalRisk", t.legalRisk],
                ["reputationRisk", t.reputationRisk],
              ] as [keyof DeveloperPayload["riskFactors"], string][]
            ).map(([key, label]) => {
              const score = data.riskFactors[key];
              return (
                <div key={key}>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="font-mono text-[10px] uppercase text-[#666]">
                      {label}
                    </span>
                    <span
                      className={`font-mono text-xs font-bold ${riskColor(score)}`}
                    >
                      {score}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-[#222]">
                    <div
                      className={`h-1.5 rounded-full transition-all ${riskBarColor(score)}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* ── Project Health Matrix (full width) ── */}
        <Card span="md:col-span-2 lg:col-span-4">
          <CardHeader icon={Layers} label={t.projectMatrix} />

          {/* Scrollable table */}
          <div className="-mx-4 overflow-x-auto px-4">
            <table className="w-full min-w-[700px]">
              <thead>
                <tr className="border-b border-[#222]">
                  {[
                    t.project,
                    t.location,
                    t.launch,
                    t.promised,
                    t.actual,
                    t.delay,
                    t.status,
                    t.roi,
                    t.priceGrowth,
                  ].map((h) => (
                    <th
                      key={h}
                      className="pb-2 text-start font-mono text-[9px] font-bold uppercase tracking-wider text-[#555]"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.projects.map((p, i) => {
                  const growth =
                    p.pricePerSqmAtLaunch > 0
                      ? ((p.currentPricePerSqm - p.pricePerSqmAtLaunch) /
                          p.pricePerSqmAtLaunch) *
                        100
                      : 0;
                  return (
                    <tr
                      key={i}
                      className="border-b border-[#111] transition-colors hover:bg-[#111]"
                    >
                      <td className="py-2 pe-3 font-mono text-xs text-white">
                        {p.name}
                      </td>
                      <td className="py-2 pe-3 font-mono text-[11px] text-[#888]">
                        {p.location}
                      </td>
                      <td className="py-2 pe-3 font-mono text-[11px] text-[#888]">
                        {p.launchYear}
                      </td>
                      <td className="py-2 pe-3 font-mono text-[11px] text-[#888]">
                        {p.promisedDelivery}
                      </td>
                      <td className="py-2 pe-3 font-mono text-[11px] text-[#888]">
                        {p.actualDelivery ?? (
                          <Minus className="h-3 w-3 text-[#444]" />
                        )}
                      </td>
                      <td className="py-2 pe-3">
                        <span
                          className={`font-mono text-[11px] font-bold ${p.delayMonths > 12 ? "text-rose-500" : p.delayMonths > 0 ? "text-yellow-500" : "text-lime-400"}`}
                        >
                          {p.delayMonths > 0
                            ? `${p.delayMonths} ${t.months}`
                            : "—"}
                        </span>
                      </td>
                      <td className="py-2 pe-3">
                        <span
                          className={`inline-flex items-center gap-1 font-mono text-[10px] font-bold uppercase ${statusColor(p.status)}`}
                        >
                          {statusIcon(p.status)}
                          {statusLabel(p.status, t)}
                        </span>
                      </td>
                      <td className="py-2 pe-3">
                        {p.roiPercent != null ? (
                          <span
                            className={`font-mono text-xs font-bold ${p.roiPercent >= 15 ? "text-lime-400" : p.roiPercent >= 0 ? "text-yellow-500" : "text-rose-500"}`}
                          >
                            {fmtPct(p.roiPercent)}
                          </span>
                        ) : (
                          <span className="font-mono text-[11px] text-[#444]">
                            {t.na}
                          </span>
                        )}
                      </td>
                      <td className="py-2">
                        <span
                          className={`inline-flex items-center gap-1 font-mono text-[11px] font-bold ${growth >= 20 ? "text-lime-400" : growth >= 0 ? "text-yellow-500" : "text-rose-500"}`}
                        >
                          {growth >= 0 ? (
                            <ArrowUpRight className="h-3 w-3" />
                          ) : (
                            <ArrowDownRight className="h-3 w-3" />
                          )}
                          {growth.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-3 flex flex-wrap items-center gap-4 border-t border-[#222] pt-3">
            {(
              [
                ["delivered", t.delivered_s, "bg-lime-400"],
                ["on-track", t.onTrack, "bg-blue-400"],
                ["delayed", t.delayed_s, "bg-yellow-500"],
                ["severely-delayed", t.severelyDelayed, "bg-rose-500"],
              ] as [string, string, string][]
            ).map(([, label, bg]) => (
              <span
                key={label}
                className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-[#555]"
              >
                <span className={`h-2 w-2 rounded-full ${bg}`} />
                {label}
              </span>
            ))}
          </div>
        </Card>
      </div>

      {/* ══ ANALYSIS TIMESTAMP ══ */}
      <div className="mt-3 flex items-center justify-between px-1">
        <span className="font-mono text-[9px] text-[#333]">
          {data.analysisTimestamp}
        </span>
        <span className="font-mono text-[9px] text-[#333]">
          OSOOL CORE — DEVELOPER DEEP-DIVE TELEMETRY
        </span>
      </div>
    </div>
  );
}

/* ── Metric Chip (top strip) ─────────────────────── */
function MetricChip({
  label,
  value,
  suffix,
  positive,
  className = "",
}: {
  label: string;
  value: string;
  suffix?: string;
  positive: boolean;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center rounded-xl border border-[#222] bg-[#0a0a0a] px-3 py-2 ${className}`}
    >
      <span className="font-mono text-[9px] uppercase tracking-wider text-[#555]">
        {label}
      </span>
      <span
        className={`mt-0.5 font-mono text-sm font-bold ${positive ? "text-lime-400" : "text-rose-500"}`}
      >
        {value}
        {suffix && (
          <span className="text-[10px] text-[#666]">{suffix}</span>
        )}
      </span>
    </div>
  );
}

/* ── Profile Row ─────────────────────────────────── */
function ProfileRow({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="font-mono text-[10px] uppercase text-[#555]">
        {label}
      </span>
      <span
        className={`font-mono text-xs font-bold ${highlight ? "text-lime-400" : "text-white"}`}
      >
        {value}
      </span>
    </div>
  );
}
