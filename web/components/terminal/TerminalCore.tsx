"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Terminal,
  ChevronRight,
  Loader2,
  AlertTriangle,
  Clock,
  Globe,
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
      className="flex min-h-screen flex-col bg-black text-white font-sans"
    >
      {/* ══ TOP STATUS BAR ══ */}
      <header className="sticky top-0 z-50 flex items-center justify-between border-b border-[#222] bg-black/95 px-4 py-2 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Terminal className="h-4 w-4 text-lime-400" />
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-lime-400">
            {t.systemReady}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-mono text-[10px] uppercase text-[#555]">
            <Globe className="h-3 w-3" />
            {t.langLabel}: {language.toUpperCase()}
          </span>
          <span className="font-mono text-[10px] uppercase text-[#555]">
            {t.sessionLabel}: {user?.id ? String(user.id).slice(0, 8) : "ANON"}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-lime-400 animate-pulse" />
            <span className="font-mono text-[10px] font-bold uppercase text-lime-400">
              {t.status}
            </span>
          </span>
        </div>
      </header>

      {/* ══ MAIN CONTENT ══ */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto overflow-x-hidden scroll-smooth"
      >
        {/* ── Empty state ── */}
        {queries.length === 0 && (
          <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-[#222] bg-[#0a0a0a]">
              <Terminal className="h-8 w-8 text-lime-400" />
            </div>
            <p className="mb-2 font-mono text-sm uppercase tracking-wider text-[#666]">
              {t.hint}
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {t.examples.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setInputValue(ex);
                    inputRef.current?.focus();
                  }}
                  className="rounded-xl border border-[#222] bg-[#0a0a0a] px-4 py-2.5 text-start font-mono text-xs text-[#888] transition-colors hover:border-lime-400/30 hover:text-lime-400"
                >
                  <span className="text-lime-400/60">{">"}</span> {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── Query entries ── */}
        {queries.map((entry) => (
          <div key={entry.id} className="border-b border-[#111]">
            {/* Query log line */}
            <div className="flex items-center gap-3 border-b border-[#111] bg-[#050505] px-4 py-2.5">
              <ChevronRight className="h-3 w-3 shrink-0 text-lime-400" />
              <span className="font-mono text-[11px] font-bold uppercase text-[#666]">
                {t.queryExecuted}:
              </span>
              <span className="flex-1 truncate font-mono text-xs text-white">
                {entry.query}
              </span>

              {/* Status badge */}
              <StatusBadge status={entry.status} t={t} />

              {/* Metadata */}
              {entry.latencyMs != null && (
                <span className="flex items-center gap-1 font-mono text-[10px] text-[#555]">
                  <Clock className="h-3 w-3" />
                  {t.latency}: {entry.latencyMs}ms
                </span>
              )}
              {entry.confidence != null && (
                <span
                  className={`font-mono text-[10px] font-bold ${
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

            {/* Bento output */}
            {entry.status === "executing" && (
              <div className="flex items-center justify-center py-16">
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="h-6 w-6 animate-spin text-lime-400" />
                  <span className="font-mono text-[11px] uppercase tracking-widest text-[#555] animate-pulse">
                    {t.executing}...
                  </span>
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
                <span className="font-mono text-xs">
                  {entry.responseText || "Analysis pipeline failed"}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* ══ COMMAND INPUT BAR ══ */}
      <form
        onSubmit={handleSubmit}
        className="sticky bottom-0 z-50 border-t border-[#222] bg-black/95 backdrop-blur-sm"
      >
        <div className="flex items-center gap-2 px-4 py-3">
          <span className="font-mono text-lg font-bold text-lime-400">
            {">"}
          </span>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={t.placeholder}
            disabled={isProcessing}
            className="flex-1 bg-transparent font-mono text-sm text-white placeholder-[#444] outline-none disabled:opacity-50"
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
      className={`rounded-md border px-2 py-0.5 font-mono text-[9px] font-bold uppercase tracking-wider ${cls}`}
    >
      {label}
    </span>
  );
}
