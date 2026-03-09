'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  TrendingUp,
  Users,
  Target,
  Mail,
  BarChart3,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';

/* ── Types ───────────────────────────────────────────────── */

interface DashboardKPIs {
  total_leads: number;
  new_leads_7d: number;
  hot_leads: number;
  total_intents: number;
  emails_sent: number;
  emails_opened: number;
  open_rate: number;
  avg_confidence: number;
}

interface FunnelStage {
  stage: string;
  count: number;
}

interface IntentTrend {
  date: string;
  SEARCH: number;
  COMPARE: number;
  PURCHASE: number;
  VALUATION: number;
  GENERAL: number;
}

interface MarketSnapshot {
  top_areas: { area: string; count: number }[];
  avg_budget_min: number;
  avg_budget_max: number;
  top_intent: string;
  total_interactions: number;
}

/* ── Main Component ──────────────────────────────────────── */

export default function AnalyticsDashboard() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [funnel, setFunnel] = useState<FunnelStage[]>([]);
  const [trends, setTrends] = useState<IntentTrend[]>([]);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [kRes, fRes, tRes, mRes] = await Promise.all([
        api.get('/api/analytics/dashboard').catch(() => ({ data: null })),
        api.get('/api/analytics/funnel').catch(() => ({ data: [] })),
        api.get('/api/analytics/intent-trends?days=30').catch(() => ({ data: [] })),
        api.get('/api/analytics/market-snapshot').catch(() => ({ data: null })),
      ]);
      setKpis(kRes.data);
      setFunnel(fRes.data);
      setTrends(tRes.data);
      setMarket(mRes.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      router.push('/');
      return;
    }
    fetchAll();
  }, [authLoading, isAuthenticated, router, fetchAll]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    );
  }

  const fmt = (n: number) => new Intl.NumberFormat('en-EG').format(Math.round(n));
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/admin')}
              className="p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold">Dual-Engine Analytics</h1>
              <p className="text-sm text-[var(--color-text-muted)]">
                Lead intelligence, intent trends, and marketing performance
              </p>
            </div>
          </div>
          <button
            onClick={fetchAll}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-emerald-500/50 transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* KPI Cards */}
        {kpis && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <KPICard icon={Users} label="Total Leads" value={fmt(kpis.total_leads)} sub={`+${kpis.new_leads_7d} this week`} />
            <KPICard icon={Target} label="Hot Leads" value={String(kpis.hot_leads)} color="text-red-500" />
            <KPICard icon={BarChart3} label="Total Intents" value={fmt(kpis.total_intents)} sub={`${pct(kpis.avg_confidence)} avg confidence`} />
            <KPICard icon={Mail} label="Emails Sent" value={fmt(kpis.emails_sent)} sub={`${pct(kpis.open_rate)} open rate`} />
          </div>
        )}

        {/* Lead Funnel */}
        {funnel.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-500" /> Lead Funnel
            </h2>
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="space-y-3">
                {funnel.map((s) => {
                  const max = Math.max(...funnel.map((f) => f.count), 1);
                  const width = (s.count / max) * 100;
                  return (
                    <div key={s.stage}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="capitalize font-medium">{s.stage}</span>
                        <span className="text-[var(--color-text-muted)]">{s.count}</span>
                      </div>
                      <div className="h-3 rounded-full bg-[var(--color-border)]/50 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* Intent Trends Table */}
        {trends.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Intent Trends (30 days)</h2>
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--color-surface)]">
                  <tr>
                    <th className="p-3 text-left font-medium">Date</th>
                    <th className="p-3 text-right font-medium">Search</th>
                    <th className="p-3 text-right font-medium">Compare</th>
                    <th className="p-3 text-right font-medium">Purchase</th>
                    <th className="p-3 text-right font-medium">Valuation</th>
                    <th className="p-3 text-right font-medium">General</th>
                  </tr>
                </thead>
                <tbody>
                  {trends.slice(-14).map((t) => (
                    <tr key={t.date} className="border-t border-[var(--color-border)]">
                      <td className="p-3">{t.date}</td>
                      <td className="p-3 text-right font-mono">{t.SEARCH}</td>
                      <td className="p-3 text-right font-mono">{t.COMPARE}</td>
                      <td className="p-3 text-right font-mono text-emerald-500 font-bold">{t.PURCHASE}</td>
                      <td className="p-3 text-right font-mono">{t.VALUATION}</td>
                      <td className="p-3 text-right font-mono text-[var(--color-text-muted)]">{t.GENERAL}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Market Snapshot */}
        {market && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold mb-4">Market Snapshot</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <h3 className="text-sm font-medium text-[var(--color-text-muted)] mb-3">Top Searched Areas</h3>
                <div className="space-y-2">
                  {market.top_areas.map((a, i) => (
                    <div key={a.area} className="flex items-center justify-between text-sm">
                      <span>
                        <span className="text-[var(--color-text-muted)] mr-2">{i + 1}.</span>
                        {a.area}
                      </span>
                      <span className="font-mono text-emerald-500">{a.count}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Average Budget Range</p>
                  <p className="text-lg font-bold">
                    EGP {fmt(market.avg_budget_min / 1_000_000)}M – {fmt(market.avg_budget_max / 1_000_000)}M
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Top Intent Type</p>
                  <p className="text-lg font-bold text-emerald-500">{market.top_intent}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Total Interactions</p>
                  <p className="text-lg font-bold">{fmt(market.total_interactions)}</p>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────── */

function KPICard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color || 'text-emerald-500'}`} />
        <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${color || ''}`}>{value}</p>
      {sub && <p className="text-xs text-[var(--color-text-muted)] mt-1">{sub}</p>}
    </div>
  );
}
