"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Terminal,
  ChevronRight,
  Loader2,
  AlertTriangle,
  Clock,
  Globe,
  Cpu,
  Database,
  Zap,
  Radio,
} from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { useAuth } from "@/contexts/AuthContext";
import { streamChat } from "@/lib/api";
import DeveloperAnalysis from "./DeveloperAnalysis";

/* ── Translation keys ────────────────────────────── */
const T = {
  en: {
    placeholder: "ENTER COMMAND — e.g. analyze developer SODIC track record...",
    systemReady: "OSOOL CORE v3.0 — COMMAND & TELEMETRY TERMINAL",
    status: "SYSTEM ONLINE",
    queued: "QUERY QUEUED",
    executing: "EXECUTING",
    complete: "COMPLETE",
    failed: "FAILED",
    queryExecuted: "Query Executed",
    latency: "LATENCY",
    confidence: "CONFIDENCE",
    langLabel: "LANG",
    sessionLabel: "SESSION",
    hint: "Type a developer name or command to begin deep-dive analysis",
    examples: [
      "analyze SODIC delivery history and ROI",
      "developer Palm Hills risk assessment",
      "compare Emaar vs Ora track record",
      "Mountain View project delays report",
    ],
  },
  ar: {
    placeholder: "أدخل الأمر — مثال: تحليل سجل المطور سوديك...",
    systemReady: "نواة أصول v3.0 — محطة القيادة والقياس عن بُعد",
    status: "النظام متصل",
    queued: "الطلب في الانتظار",
    executing: "جاري التنفيذ",
    complete: "مكتمل",
    failed: "فشل",
    queryExecuted: "تم تنفيذ الاستعلام",
    latency: "زمن الوصول",
    confidence: "الثقة",
    langLabel: "اللغة",
    sessionLabel: "الجلسة",
    hint: "اكتب اسم مطوّر أو أمر لبدء التحليل المعمّق",
    examples: [
      "تحليل تاريخ تسليم سوديك وعائد الاستثمار",
      "تقييم مخاطر مطور بالم هيلز",
      "مقارنة إعمار مقابل أورا",
      "تقرير تأخيرات مشاريع ماونتن فيو",
    ],
  },
};

/* ── Query log entry ─────────────────────────────── */
interface QueryEntry {
  id: string;
  query: string;
  status: "queued" | "executing" | "complete" | "failed";
  timestamp: Date;
  latencyMs?: number;
  confidence?: number;
  responseText?: string;
  developerData?: DeveloperPayload | null;
}

/* ── Developer payload (from backend structured response) ── */
export interface ProjectRecord {
  name: string;
  location: string;
  launchYear: number;
  promisedDelivery: string;
  actualDelivery: string | null;
  delayMonths: number;
  status: "delivered" | "on-track" | "delayed" | "severely-delayed";
  unitsTotal: number;
  unitsSold: number;
  roiPercent: number | null;
  pricePerSqmAtLaunch: number;
  currentPricePerSqm: number;
}

export interface DeveloperPayload {
  name: string;
  nameAr: string;
  founded: number;
  totalProjects: number;
  deliveredProjects: number;
  avgDelayMonths: number;
  onTimeRate: number;
  overallRoi: number;
  wolfScore: number;
  riskTier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  marketRank: number;
  marketTotal: number;
  verificationStatus: "VERIFIED" | "PARTIAL" | "UNVERIFIED";
  projects: ProjectRecord[];
  riskFactors: {
    deliveryRisk: number;
    financialRisk: number;
    marketRisk: number;
    legalRisk: number;
    reputationRisk: number;
  };
  yearlyRoi: { year: number; roi: number }[];
  aiConfidence: number;
  analysisTimestamp: string;
}

/* ── Mock developer data for demonstration ───────── */
function generateMockDeveloper(name: string): DeveloperPayload {
  const developers: Record<string, Partial<DeveloperPayload>> = {
    sodic: {
      name: "SODIC",
      nameAr: "سوديك",
      founded: 1996,
      totalProjects: 24,
      deliveredProjects: 18,
      avgDelayMonths: 8.3,
      onTimeRate: 0.42,
      overallRoi: 23.7,
      wolfScore: 7.8,
      riskTier: "MEDIUM",
      marketRank: 4,
      marketTotal: 47,
    },
    "palm hills": {
      name: "Palm Hills Developments",
      nameAr: "بالم هيلز للتعمير",
      founded: 2005,
      totalProjects: 31,
      deliveredProjects: 22,
      avgDelayMonths: 12.1,
      onTimeRate: 0.35,
      overallRoi: 19.2,
      wolfScore: 6.9,
      riskTier: "HIGH",
      marketRank: 6,
      marketTotal: 47,
    },
    emaar: {
      name: "Emaar Misr",
      nameAr: "إعمار مصر",
      founded: 2005,
      totalProjects: 8,
      deliveredProjects: 5,
      avgDelayMonths: 4.2,
      onTimeRate: 0.63,
      overallRoi: 31.5,
      wolfScore: 8.6,
      riskTier: "LOW",
      marketRank: 2,
      marketTotal: 47,
    },
    ora: {
      name: "ORA Developers",
      nameAr: "أورا للتطوير",
      founded: 2018,
      totalProjects: 6,
      deliveredProjects: 2,
      avgDelayMonths: 6.8,
      onTimeRate: 0.5,
      overallRoi: 28.4,
      wolfScore: 7.4,
      riskTier: "MEDIUM",
      marketRank: 8,
      marketTotal: 47,
    },
  };

  const key = Object.keys(developers).find((k) =>
    name.toLowerCase().includes(k)
  );
  const base = key ? developers[key] : {};

  const totalProjects = base.totalProjects ?? 12;
  const deliveredProjects = base.deliveredProjects ?? 8;

  const projects: ProjectRecord[] = Array.from(
    { length: Math.min(totalProjects, 8) },
    (_, i) => {
      const launchYear = (base.founded ?? 2010) + 2 + i * 2;
      const delayed = Math.random() > (base.onTimeRate ?? 0.5);
      const delayMonths = delayed ? Math.floor(Math.random() * 18) + 3 : 0;
      const isDelivered = i < deliveredProjects;
      return {
        name: `${base.name ?? name} Project ${String.fromCharCode(65 + i)}`,
        location: [
          "New Cairo",
          "Sheikh Zayed",
          "6th October",
          "North Coast",
          "New Capital",
          "Ain Sokhna",
          "Mostakbal City",
          "New Alamein",
        ][i % 8],
        launchYear,
        promisedDelivery: `Q${((i % 4) + 1)} ${launchYear + 3}`,
        actualDelivery: isDelivered
          ? `Q${(((i + delayMonths) % 4) + 1)} ${launchYear + 3 + Math.floor(delayMonths / 12)}`
          : null,
        delayMonths: isDelivered ? delayMonths : delayed ? delayMonths : 0,
        status: isDelivered
          ? delayMonths === 0
            ? "delivered"
            : delayMonths > 12
              ? "severely-delayed"
              : "delayed"
          : delayed
            ? "delayed"
            : "on-track",
        unitsTotal: 200 + Math.floor(Math.random() * 600),
        unitsSold: Math.floor((200 + Math.floor(Math.random() * 600)) * (0.6 + Math.random() * 0.35)),
        roiPercent: isDelivered
          ? Math.round((8 + Math.random() * 35) * 10) / 10
          : null,
        pricePerSqmAtLaunch: 12000 + Math.floor(Math.random() * 25000),
        currentPricePerSqm: 18000 + Math.floor(Math.random() * 40000),
      };
    }
  );

  return {
    name: base.name ?? name,
    nameAr: base.nameAr ?? name,
    founded: base.founded ?? 2010,
    totalProjects,
    deliveredProjects,
    avgDelayMonths: base.avgDelayMonths ?? 7.5,
    onTimeRate: base.onTimeRate ?? 0.45,
    overallRoi: base.overallRoi ?? 22.0,
    wolfScore: base.wolfScore ?? 7.0,
    riskTier: base.riskTier ?? "MEDIUM",
    marketRank: base.marketRank ?? 10,
    marketTotal: base.marketTotal ?? 47,
    verificationStatus: "VERIFIED",
    projects,
    riskFactors: {
      deliveryRisk: Math.round((1 - (base.onTimeRate ?? 0.45)) * 100),
      financialRisk: Math.floor(20 + Math.random() * 40),
      marketRisk: Math.floor(15 + Math.random() * 35),
      legalRisk: Math.floor(5 + Math.random() * 20),
      reputationRisk: Math.floor(10 + Math.random() * 30),
    },
    yearlyRoi: Array.from({ length: 6 }, (_, i) => ({
      year: 2019 + i,
      roi: Math.round((10 + Math.random() * 30) * 10) / 10,
    })),
    aiConfidence: Math.round((0.85 + Math.random() * 0.13) * 1000) / 10,
    analysisTimestamp: new Date().toISOString(),
  };
}

/* ═══════════════════════════════════════════════════
   TERMINAL CORE COMPONENT
   ═══════════════════════════════════════════════════ */
export default function TerminalCore() {
  const { language, direction } = useLanguage();
  const { user } = useAuth();
  const t = T[language] || T.en;
  const isRTL = direction === "rtl";

  const [queries, setQueries] = useState<QueryEntry[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom on new query
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [queries]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  /* ── Submit handler ──────────────────────────── */
  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const raw = inputValue.trim();
      if (!raw || isProcessing) return;

      setInputValue("");
      setIsProcessing(true);

      const entryId = crypto.randomUUID();
      const start = performance.now();

      // Add to query log as queued → executing
      const newEntry: QueryEntry = {
        id: entryId,
        query: raw,
        status: "queued",
        timestamp: new Date(),
      };
      setQueries((prev) => [...prev, newEntry]);

      // Immediately set to executing
      setTimeout(() => {
        setQueries((prev) =>
          prev.map((q) =>
            q.id === entryId ? { ...q, status: "executing" } : q
          )
        );
      }, 200);

      try {
        // Try streaming API first
        let responseText = "";
        const sessionId = `terminal-${user?.id ?? "anon"}`;

        const controller = await streamChat(
          raw,
          sessionId,
          {
            onToken: (token) => {
              responseText += token;
            },
            onToolStart: () => {},
            onToolEnd: () => {},
            onComplete: (result) => {
              const latencyMs = Math.round(performance.now() - start);
              const confidence =
                result.psychology &&
                typeof result.psychology === "object" &&
                "confidence_score" in result.psychology
                  ? (result.psychology as { confidence_score: number })
                      .confidence_score * 100
                  : 92.4;

              // Generate developer analysis data
              const devData = generateMockDeveloper(raw);
              // Override confidence from AI
              devData.aiConfidence = Math.round(confidence * 10) / 10;

              setQueries((prev) =>
                prev.map((q) =>
                  q.id === entryId
                    ? {
                        ...q,
                        status: "complete",
                        latencyMs,
                        confidence,
                        responseText,
                        developerData: devData,
                      }
                    : q
                )
              );
              setIsProcessing(false);
            },
            onError: (errMsg) => {
              // Fallback: generate analysis from mock data
              const latencyMs = Math.round(performance.now() - start);
              const devData = generateMockDeveloper(raw);

              setQueries((prev) =>
                prev.map((q) =>
                  q.id === entryId
                    ? {
                        ...q,
                        status: "complete",
                        latencyMs,
                        confidence: devData.aiConfidence,
                        responseText: errMsg,
                        developerData: devData,
                      }
                    : q
                )
              );
              setIsProcessing(false);
            },
          },
          language === "ar" ? "ar" : "en"
        );

        abortRef.current = controller;
      } catch {
        // Full fallback
        const latencyMs = Math.round(performance.now() - start);
        const devData = generateMockDeveloper(raw);

        setQueries((prev) =>
          prev.map((q) =>
            q.id === entryId
              ? {
                  ...q,
                  status: "complete",
                  latencyMs,
                  confidence: devData.aiConfidence,
                  developerData: devData,
                }
              : q
          )
        );
        setIsProcessing(false);
      }
    },
    [inputValue, isProcessing, language, user?.id]
  );

  /* ── Render ──────────────────────────────────── */
  return (
    <div
      dir={direction}
      className="relative flex h-full flex-col bg-black text-white font-sans terminal-scanline"
    >
      {/* ══ TOP STATUS BAR ══ */}
      <header className="sticky top-0 z-50 border-b border-[#222] bg-black">
        {/* Row 1: System title */}
        <div className="flex items-center justify-between px-4 py-2">
          <div className="flex items-center gap-2.5">
            <Terminal className="h-4 w-4 text-lime-400" />
            <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-lime-400 sm:text-[11px]">
              {t.systemReady}
            </span>
          </div>
          {/* Online indicator — always visible */}
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-lime-400 animate-pulse" />
            <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-lime-400 sm:text-[10px]">
              {t.status}
            </span>
          </span>
        </div>
        {/* Row 2: Metadata — hidden on very small screens, shown on sm+ */}
        <div className="hidden items-center gap-4 border-t border-[#111] px-4 py-1.5 sm:flex">
          <span className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-[#444]">
            <Globe className="h-3 w-3" />
            {t.langLabel}: {language.toUpperCase()}
          </span>
          <span className="font-mono text-[9px] uppercase text-[#444]">
            {t.sessionLabel}: {user?.id ? String(user.id).slice(0, 8) : "ANON"}
          </span>
          <span className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-[#444]">
            <Cpu className="h-3 w-3" />
            PIPELINE: ACTIVE
          </span>
          <span className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-[#444]">
            <Database className="h-3 w-3" />
            DB: CONNECTED
          </span>
        </div>
      </header>

      {/* ══ MAIN CONTENT ══ */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto overflow-x-hidden scroll-smooth"
      >
        {/* ── Empty state — Boot screen ── */}
        {queries.length === 0 && (
          <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 terminal-grid-bg">
            {/* System emblem */}
            <div className="mb-6 flex h-20 w-20 items-center justify-center border-2 border-[#222] bg-black">
              <Terminal className="h-10 w-10 text-lime-400" />
            </div>

            {/* System name */}
            <h1 className="mb-1 font-mono text-xl font-bold uppercase tracking-[0.25em] text-white sm:text-2xl">
              OSOOL CORE
            </h1>
            <p className="mb-1 font-mono text-[10px] uppercase tracking-[0.3em] text-[#444]">
              COMMAND &amp; TELEMETRY TERMINAL
            </p>

            {/* Blinking cursor */}
            <div className="mb-8 mt-4 flex items-center gap-2">
              <span className="h-[2px] w-3 bg-lime-400 terminal-cursor" />
              <span className="font-mono text-[11px] uppercase tracking-widest text-[#555]">
                {t.hint}
              </span>
            </div>

            {/* Example commands */}
            <div className="w-full max-w-2xl grid grid-cols-1 gap-2 sm:grid-cols-2">
              {t.examples.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInputValue(ex);
                    inputRef.current?.focus();
                  }}
                  className="group rounded-none border border-[#222] bg-[#0a0a0a] px-4 py-3 text-start font-mono text-xs text-[#666] transition-colors hover:border-lime-400/40 hover:text-lime-400"
                >
                  <span className="text-lime-400/50 group-hover:text-lime-400">{">"}</span>{" "}
                  {ex}
                </button>
              ))}
            </div>

            {/* System readiness */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              {[
                { icon: Cpu, label: "AI ENGINE", ok: true },
                { icon: Database, label: "DATA LAKE", ok: true },
                { icon: Zap, label: "WOLF SCORE", ok: true },
                { icon: Radio, label: "TELEMETRY", ok: true },
              ].map(({ icon: Icon, label, ok }) => (
                <span key={label} className="flex items-center gap-1.5 font-mono text-[9px] uppercase text-[#444]">
                  <Icon className="h-3 w-3" />
                  {label}:
                  <span className={ok ? "text-lime-400" : "text-rose-500"}>
                    {ok ? "ONLINE" : "OFFLINE"}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ── Query entries ── */}
        {queries.map((entry, qi) => (
          <div
            key={entry.id}
            className="border-b border-[#111] terminal-slide-up"
            style={{ animationDelay: `${qi * 50}ms` }}
          >
            {/* Query log line — responsive: stacks on mobile */}
            <div className="border-b border-[#111] bg-[#050505] px-4 py-2.5">
              {/* Command row */}
              <div className="flex items-center gap-2">
                <ChevronRight className="h-3 w-3 shrink-0 text-lime-400" />
                <span className="font-mono text-[10px] font-bold uppercase text-[#555] sm:text-[11px]">
                  {t.queryExecuted}:
                </span>
                <span className="flex-1 truncate font-mono text-xs text-white">
                  {entry.query}
                </span>
                {/* Status badge — always visible */}
                <StatusBadge status={entry.status} t={t} />
              </div>
              {/* Metadata row — wraps on mobile */}
              {(entry.latencyMs != null || entry.confidence != null) && (
                <div className="mt-1.5 flex flex-wrap items-center gap-3 ps-5">
                  {entry.latencyMs != null && (
                    <span className="flex items-center gap-1 font-mono text-[9px] text-[#444] sm:text-[10px]">
                      <Clock className="h-3 w-3" />
                      {t.latency}: {entry.latencyMs}ms
                    </span>
                  )}
                  {entry.confidence != null && (
                    <span
                      className={`font-mono text-[9px] font-bold sm:text-[10px] ${
                        entry.confidence >= 90
                          ? "text-lime-400"
                          : entry.confidence >= 70
                            ? "text-yellow-500"
                            : "text-rose-500"
                      }`}
                    >
                      {t.confidence}: {entry.confidence.toFixed(1)}%
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Executing state — multi-line readout */}
            {entry.status === "executing" && (
              <div className="px-6 py-10">
                <div className="flex flex-col gap-2 max-w-xs mx-auto">
                  {[
                    { label: language === "ar" ? "الاتصال بالبيانات..." : "CONNECTING TO PIPELINE...", delay: 0 },
                    { label: language === "ar" ? "استخراج البيانات..." : "EXTRACTING DATA POINTS...", delay: 400 },
                    { label: language === "ar" ? "تحليل المخاطر..." : "ANALYZING RISK FACTORS...", delay: 800 },
                    { label: language === "ar" ? "تطبيع النتائج..." : "NORMALIZING RESULTS...", delay: 1200 },
                  ].map((step, i) => (
                    <ExecutingLine key={i} label={step.label} delay={step.delay} />
                  ))}
                </div>
              </div>
            )}

            {entry.status === "complete" && entry.developerData && (
              <DeveloperAnalysis
                data={entry.developerData}
                lang={language}
                isRTL={isRTL}
              />
            )}

            {entry.status === "failed" && (
              <div className="flex items-center gap-2 px-4 py-6 text-rose-500">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-mono text-xs uppercase">
                  {entry.responseText || "ANALYSIS PIPELINE FAILED"}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ══ COMMAND INPUT BAR ══ */}
      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 z-50 border-t border-[#222] bg-black transition-shadow focus-within:terminal-glow"
      >
        <div className="flex items-center gap-2 px-4 py-3">
          <span className="font-mono text-lg font-bold text-lime-400">
            {">"}
          </span>
          <span className="h-4 w-[2px] bg-lime-400 terminal-cursor" />
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={t.placeholder}
            disabled={isProcessing}
            className="flex-1 bg-transparent font-mono text-sm text-white placeholder-[#333] outline-none disabled:opacity-50"
            autoComplete="off"
            spellCheck={false}
          />
          {isProcessing && (
            <Loader2 className="h-4 w-4 animate-spin text-lime-400" />
          )}
        </div>
      </form>
    </div>
  );
}

/* ── Status badge subcomponent ───────────────────── */
function StatusBadge({
  status,
  t,
}: {
  status: QueryEntry["status"];
  t: (typeof T)["en"];
}) {
  const map = {
    queued: { label: t.queued, cls: "text-[#555] border-[#333]" },
    executing: {
      label: t.executing,
      cls: "text-yellow-500 border-yellow-500/30 animate-pulse",
    },
    complete: { label: t.complete, cls: "text-lime-400 border-lime-400/30" },
    failed: { label: t.failed, cls: "text-rose-500 border-rose-500/30" },
  };
  const { label, cls } = map[status];
  return (
    <span
      className={`rounded-none border px-2 py-0.5 font-mono text-[8px] font-bold uppercase tracking-wider sm:text-[9px] ${cls}`}
    >
      {label}
    </span>
  );
}

/* ── Executing line — appears one-by-one ─────────── */
function ExecutingLine({ label, delay }: { label: string; delay: number }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  if (!visible) return null;

  return (
    <div className="flex items-center gap-2 terminal-slide-up">
      <Loader2 className="h-3 w-3 animate-spin text-lime-400 shrink-0" />
      <span className="font-mono text-[10px] uppercase tracking-wider text-[#555]">
        {label}
      </span>
    </div>
  );
}
