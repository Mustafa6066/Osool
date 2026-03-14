'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  Loader2,
  Mail,
  RefreshCw,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react';
import AdminShell from '@/components/AdminShell';
import api from '@/lib/api';

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

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-EG').format(Math.round(value));
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default function AnalyticsDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [funnel, setFunnel] = useState<FunnelStage[]>([]);
  const [trends, setTrends] = useState<IntentTrend[]>([]);
  const [market, setMarket] = useState<MarketSnapshot | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiResponse, funnelResponse, trendResponse, marketResponse] = await Promise.all([
        api.get('/api/analytics/dashboard').catch(() => ({ data: null })),
        api.get('/api/analytics/funnel').catch(() => ({ data: [] })),
        api.get('/api/analytics/intent-trends?days=30').catch(() => ({ data: [] })),
        api.get('/api/analytics/market-snapshot').catch(() => ({ data: null })),
      ]);

      setKpis(kpiResponse.data);
      setFunnel(funnelResponse.data || []);
      setTrends(trendResponse.data || []);
      setMarket(marketResponse.data);
    } catch (loadError) {
      console.error(loadError);
      setError('Analytics data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchAll();
  }, [fetchAll]);

  const latestPurchaseTrend = useMemo(() => {
    if (!trends.length) {
      return 0;
    }
    return trends.slice(-7).reduce((sum: number, item: IntentTrend) => sum + item.PURCHASE, 0);
  }, [trends]);

  return (
    <AdminShell
      eyebrow="Admin analytics"
      title="Read lead demand, funnel movement, and campaign signal in one place."
      subtitle="This route condenses lead generation, intent quality, and market demand into an operating view for the admin team."
      actions={
        <button
          onClick={() => void fetchAll()}
          className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh data
        </button>
      }
    >
      {loading ? (
        <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-24">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      ) : error ? (
        <div className="rounded-[32px] border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-500">{error}</div>
      ) : (
        <div className="space-y-6">
          {kpis && (
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard icon={Users} label="Total leads" value={formatNumber(kpis.total_leads)} detail={`+${kpis.new_leads_7d} in the last 7 days`} />
              <MetricCard icon={Target} label="Hot leads" value={formatNumber(kpis.hot_leads)} detail={`${formatPercent(kpis.avg_confidence)} average confidence`} />
              <MetricCard icon={BarChart3} label="Intent volume" value={formatNumber(kpis.total_intents)} detail={`${latestPurchaseTrend} purchase-intent events in the last 7 days`} />
              <MetricCard icon={Mail} label="Email performance" value={formatNumber(kpis.emails_sent)} detail={`${formatPercent(kpis.open_rate)} open rate`} />
            </section>
          )}

          <section className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Lead funnel</div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Where opportunities are actually progressing</h2>
              <div className="mt-6 space-y-4">
                {funnel.length ? (
                  funnel.map((stage: FunnelStage) => {
                    const max = Math.max(...funnel.map((item: FunnelStage) => item.count), 1);
                    const width = (stage.count / max) * 100;
                    return (
                      <div key={stage.stage}>
                        <div className="mb-2 flex items-center justify-between text-sm">
                          <span className="font-medium capitalize text-[var(--color-text-primary)]">{stage.stage}</span>
                          <span className="text-[var(--color-text-muted)]">{formatNumber(stage.count)}</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-[var(--color-background)]">
                          <div className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400" style={{ width: `${width}%` }} />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-sm text-[var(--color-text-secondary)]">No funnel data is available.</p>
                )}
              </div>
            </div>

            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Market signal</div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">What users are asking for right now</h2>
              {market ? (
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-2xl bg-[var(--color-background)] p-5">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Average budget</div>
                    <div className="mt-2 text-xl font-semibold text-[var(--color-text-primary)]">
                      EGP {formatNumber(market.avg_budget_min / 1_000_000)}M - {formatNumber(market.avg_budget_max / 1_000_000)}M
                    </div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-5">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Top intent</div>
                    <div className="mt-2 text-xl font-semibold text-emerald-600 dark:text-emerald-300">{market.top_intent || 'N/A'}</div>
                  </div>
                  <div className="rounded-2xl bg-[var(--color-background)] p-5 sm:col-span-2">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Top searched areas</div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      {market.top_areas?.length ? (
                        market.top_areas.map((area, index) => (
                          <div key={area.area} className="flex items-center justify-between rounded-xl border border-[var(--color-border)] px-4 py-3">
                            <div className="text-sm font-medium text-[var(--color-text-primary)]">{index + 1}. {area.area}</div>
                            <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-300">{formatNumber(area.count)}</div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-[var(--color-text-secondary)]">No area signal is available.</p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-6 text-sm text-[var(--color-text-secondary)]">No market snapshot is available.</p>
              )}
            </div>
          </section>

          <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
              <TrendingUp className="h-4 w-4" />
              Intent trends
            </div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Recent demand pattern by intent type</h2>
            {trends.length ? (
              <div className="mt-6 overflow-x-auto rounded-2xl border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-background)]">
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
                    {trends.slice(-14).map((trend) => (
                      <tr key={trend.date} className="border-t border-[var(--color-border)]">
                        <td className="p-3 text-[var(--color-text-primary)]">{trend.date}</td>
                        <td className="p-3 text-right font-mono">{trend.SEARCH}</td>
                        <td className="p-3 text-right font-mono">{trend.COMPARE}</td>
                        <td className="p-3 text-right font-mono font-semibold text-emerald-600 dark:text-emerald-300">{trend.PURCHASE}</td>
                        <td className="p-3 text-right font-mono">{trend.VALUATION}</td>
                        <td className="p-3 text-right font-mono text-[var(--color-text-muted)]">{trend.GENERAL}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-6 text-sm text-[var(--color-text-secondary)]">No trend data is available.</p>
            )}
          </section>
        </div>
      )}
    </AdminShell>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="flex items-center justify-between">
        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{label}</div>
        <Icon className="h-4 w-4 text-emerald-500" />
      </div>
      <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{value}</div>
      <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{detail}</div>
    </div>
  );
}
