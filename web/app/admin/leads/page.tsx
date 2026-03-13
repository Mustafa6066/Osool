'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Users,
  Loader2,
  RefreshCw,
  ChevronRight,
  Phone,
  Mail,
  Calendar,
  Target,
  MapPin,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';

/* ── Types ─────────────────────────────────────────────── */

interface Lead {
  id: number;
  user_id: number;
  email?: string;
  phone?: string;
  stage: string;
  budget_min?: number;
  budget_max?: number;
  preferred_areas?: string[];
  preferred_types?: string[];
  timeline?: string;
  interaction_count?: number;
  created_at?: string;
  updated_at?: string;
}

interface PipelineStats {
  total: number;
  new: number;
  engaged: number;
  hot: number;
  converted: number;
  lost: number;
}

// The backend /api/leads/stats returns a different shape — map it here
interface StatsApiResponse {
  total_leads: number;
  hot_leads: number;
  by_stage: Record<string, number>;
}

/* ── Stages ─────────────────────────────────────────────── */

const STAGES = ['new', 'engaged', 'hot', 'converted', 'lost'] as const;

const STAGE_COLORS: Record<string, string> = {
  new: 'bg-blue-500/10 text-blue-600',
  engaged: 'bg-yellow-500/10 text-yellow-600',
  hot: 'bg-red-500/10 text-red-600',
  converted: 'bg-emerald-500/10 text-emerald-600',
  lost: 'bg-gray-500/10 text-gray-500',
};

/* ── Main Component ───────────────────────────────────── */

export default function LeadsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [stageFilter, setStageFilter] = useState<string>('');
  const [selected, setSelected] = useState<Lead | null>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = stageFilter ? `?stage=${stageFilter}` : '';
      const [lRes, sRes] = await Promise.all([
        api.get(`/api/leads${params}`).catch(() => ({ data: [] })),
        api.get('/api/leads/stats').catch(() => ({ data: null })),
      ]);
      setLeads(lRes.data);
      const raw: StatsApiResponse | null = sRes.data;
      if (raw) {
        const by = raw.by_stage ?? {};
        setStats({
          total: raw.total_leads ?? 0,
          new: by.new ?? 0,
          engaged: by.engaged ?? 0,
          hot: by.hot ?? 0,
          converted: by.converted ?? 0,
          lost: by.lost ?? 0,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [stageFilter]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.push('/'); return; }
    fetchLeads();
  }, [authLoading, isAuthenticated, router, fetchLeads]);

  const updateStage = async (leadId: number, newStage: string) => {
    try {
      await api.patch(`/api/leads/${leadId}`, { stage: newStage });
      setLeads((prev) =>
        prev.map((l) => (l.id === leadId ? { ...l, stage: newStage } : l))
      );
      if (selected?.id === leadId) setSelected({ ...selected, stage: newStage });
    } catch {
      // silent
    }
  };

  const fmt = (n: number) => new Intl.NumberFormat('en-EG').format(Math.round(n));

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push('/admin')}
              title="Back to admin"
              className="p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Users className="w-6 h-6 text-emerald-500" /> Lead Pipeline
              </h1>
              <p className="text-sm text-[var(--color-text-muted)]">
                Manage leads from chat conversations
              </p>
            </div>
          </div>
          <button
            onClick={fetchLeads}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-emerald-500/50 transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* Pipeline Stats */}
        {stats && (
          <div className="grid grid-cols-5 gap-3 mb-6">
            {STAGES.map((s) => (
              <button
                key={s}
                onClick={() => setStageFilter(stageFilter === s ? '' : s)}
                className={`p-3 rounded-xl border transition-all text-center ${
                  stageFilter === s
                    ? 'border-emerald-500 bg-emerald-500/10'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/30'
                }`}
              >
                <p className="text-xs text-[var(--color-text-muted)] capitalize">{s}</p>
                <p className="text-xl font-bold">
                  {stats[s as keyof PipelineStats] ?? 0}
                </p>
              </button>
            ))}
          </div>
        )}

        {/* Lead List + Detail Split */}
        <div className="grid lg:grid-cols-5 gap-4">
          {/* Lead List */}
          <div className="lg:col-span-3 space-y-2">
            {leads.length === 0 && (
              <p className="text-sm text-[var(--color-text-muted)] p-4">No leads found.</p>
            )}
            {leads.map((lead) => (
              <button
                key={lead.id}
                onClick={() => setSelected(lead)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selected?.id === lead.id
                    ? 'border-emerald-500 bg-emerald-500/5'
                    : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/30'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-sm">{lead.email || `Lead #${lead.id}`}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${STAGE_COLORS[lead.stage] || ''}`}>
                        {lead.stage}
                      </span>
                      {lead.interaction_count && (
                        <span className="text-[10px] text-[var(--color-text-muted)]">
                          {lead.interaction_count} interactions
                        </span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />
                </div>
              </button>
            ))}
          </div>

          {/* Lead Detail */}
          <div className="lg:col-span-2">
            {selected ? (
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sticky top-8">
                <h3 className="font-semibold mb-4">Lead #{selected.id}</h3>

                <div className="space-y-3 text-sm">
                  {selected.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-[var(--color-text-muted)]" />
                      {selected.email}
                    </div>
                  )}
                  {selected.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-[var(--color-text-muted)]" />
                      {selected.phone}
                    </div>
                  )}
                  {selected.budget_min && selected.budget_max && (
                    <div className="flex items-center gap-2">
                      <Target className="w-4 h-4 text-[var(--color-text-muted)]" />
                      EGP {fmt(selected.budget_min / 1_000_000)}M – {fmt(selected.budget_max / 1_000_000)}M
                    </div>
                  )}
                  {selected.preferred_areas && selected.preferred_areas.length > 0 && (
                    <div className="flex items-start gap-2">
                      <MapPin className="w-4 h-4 text-[var(--color-text-muted)] mt-0.5" />
                      <div className="flex flex-wrap gap-1">
                        {selected.preferred_areas.map((a) => (
                          <span key={a} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--color-border)]/50">
                            {a}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {selected.timeline && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-[var(--color-text-muted)]" />
                      {selected.timeline}
                    </div>
                  )}
                </div>

                {/* Stage Selector */}
                <div className="mt-4 pt-4 border-t border-[var(--color-border)]">
                  <p className="text-xs text-[var(--color-text-muted)] mb-2">Move to stage:</p>
                  <div className="flex flex-wrap gap-1">
                    {STAGES.map((s) => (
                      <button
                        key={s}
                        onClick={() => updateStage(selected.id, s)}
                        className={`text-xs px-3 py-1 rounded-full transition-all ${
                          selected.stage === s
                            ? 'bg-emerald-500 text-white'
                            : 'bg-[var(--color-border)]/50 hover:bg-emerald-500/20'
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-center text-sm text-[var(--color-text-muted)]">
                Select a lead to view details
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
