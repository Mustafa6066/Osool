'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Calendar,
  ChevronRight,
  Loader2,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Target,
  Users,
} from 'lucide-react';
import AdminShell from '@/components/AdminShell';
import api from '@/lib/api';

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

const STAGES = ['new', 'engaged', 'hot', 'converted', 'lost'] as const;

const STAGE_LABELS: Record<string, string> = {
  new: 'New',
  engaged: 'Engaged',
  hot: 'Hot',
  converted: 'Converted',
  lost: 'Lost',
};

const STAGE_TONES: Record<string, string> = {
  new: 'border-blue-500/20 bg-blue-500/10 text-blue-600 dark:text-blue-300',
  engaged: 'border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300',
  hot: 'border-red-500/20 bg-red-500/10 text-red-500',
  converted: 'border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
  lost: 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-muted)]',
};

function formatBudget(value: number): string {
  return new Intl.NumberFormat('en-EG').format(Math.round(value));
}

export default function LeadsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [stageFilter, setStageFilter] = useState<string>('');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [updatingLeadId, setUpdatingLeadId] = useState<number | null>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = stageFilter ? `?stage=${stageFilter}` : '';
      const [leadResponse, statsResponse] = await Promise.all([
        api.get(`/api/leads${params}`).catch(() => ({ data: [] })),
        api.get('/api/leads/stats').catch(() => ({ data: null })),
      ]);

      const nextLeads = leadResponse.data || [];
      setLeads(nextLeads);
      setSelectedLead((current) => nextLeads.find((lead: Lead) => lead.id === current?.id) || nextLeads[0] || null);

      if (statsResponse.data) {
        const raw = statsResponse.data;
        const byStage = raw.by_stage || {};
        setStats({
          total: raw.total_leads ?? 0,
          new: byStage.new ?? 0,
          engaged: byStage.engaged ?? 0,
          hot: byStage.hot ?? 0,
          converted: byStage.converted ?? 0,
          lost: byStage.lost ?? 0,
        });
      } else {
        setStats(null);
      }
    } catch (loadError) {
      console.error(loadError);
      setError('Lead data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, [stageFilter]);

  useEffect(() => {
    void fetchLeads();
  }, [fetchLeads]);

  const updateStage = async (leadId: number, nextStage: string) => {
    setUpdatingLeadId(leadId);
    try {
      await api.patch(`/api/leads/${leadId}`, { stage: nextStage });
      setLeads((current) => current.map((lead) => (lead.id === leadId ? { ...lead, stage: nextStage } : lead)));
      setSelectedLead((current) => (current?.id === leadId ? { ...current, stage: nextStage } : current));
    } catch (updateError) {
      console.error(updateError);
      setError('Lead stage could not be updated.');
    } finally {
      setUpdatingLeadId(null);
    }
  };

  const visibleSummary = useMemo(() => {
    return {
      visible: leads.length,
      active: leads.filter((lead) => ['new', 'engaged', 'hot'].includes(lead.stage)).length,
    };
  }, [leads]);

  return (
    <AdminShell
      eyebrow="Admin leads"
      title="Manage the lead pipeline with actual context, not just counts."
      subtitle="Review stage movement, inspect buyer context, and update the pipeline without leaving the admin workspace."
      actions={
        <button
          onClick={() => void fetchLeads()}
          className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh leads
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
          {stats && (
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <PipelineCard label="New" value={stats.new} active={stageFilter === 'new'} onClick={() => setStageFilter(stageFilter === 'new' ? '' : 'new')} />
              <PipelineCard label="Engaged" value={stats.engaged} active={stageFilter === 'engaged'} onClick={() => setStageFilter(stageFilter === 'engaged' ? '' : 'engaged')} />
              <PipelineCard label="Hot" value={stats.hot} active={stageFilter === 'hot'} onClick={() => setStageFilter(stageFilter === 'hot' ? '' : 'hot')} />
              <PipelineCard label="Converted" value={stats.converted} active={stageFilter === 'converted'} onClick={() => setStageFilter(stageFilter === 'converted' ? '' : 'converted')} />
              <PipelineCard label="Lost" value={stats.lost} active={stageFilter === 'lost'} onClick={() => setStageFilter(stageFilter === 'lost' ? '' : 'lost')} />
            </section>
          )}

          <section className="grid gap-6 lg:grid-cols-[1fr_0.95fr]">
            <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="flex flex-col gap-3 border-b border-[var(--color-border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Lead inbox</div>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Visible leads</h2>
                </div>
                <div className="text-sm text-[var(--color-text-secondary)]">
                  {visibleSummary.visible} visible, {visibleSummary.active} active pipeline leads
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {leads.length ? (
                  leads.map((lead) => (
                    <button
                      key={lead.id}
                      type="button"
                      onClick={() => setSelectedLead(lead)}
                      className={`w-full rounded-[24px] border p-5 text-left transition-colors ${
                        selectedLead?.id === lead.id
                          ? 'border-emerald-500/30 bg-emerald-500/5'
                          : 'border-[var(--color-border)] bg-[var(--color-background)] hover:border-emerald-500/20'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${STAGE_TONES[lead.stage] || STAGE_TONES.new}`}>
                              {STAGE_LABELS[lead.stage] || lead.stage}
                            </span>
                            {lead.interaction_count ? (
                              <span className="text-xs text-[var(--color-text-muted)]">{lead.interaction_count} interactions</span>
                            ) : null}
                          </div>
                          <h3 className="mt-3 text-lg font-semibold text-[var(--color-text-primary)]">{lead.email || `Lead #${lead.id}`}</h3>
                          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--color-text-muted)]">
                            <span>#{lead.id}</span>
                            {lead.created_at && <span>{new Date(lead.created_at).toLocaleDateString()}</span>}
                            {lead.timeline && <span>{lead.timeline}</span>}
                          </div>
                        </div>
                        <ChevronRight className="mt-1 h-4 w-4 text-[var(--color-text-muted)]" />
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="rounded-[24px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-8 text-center text-sm text-[var(--color-text-secondary)]">
                    No leads match the current filter.
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">
                  <Users className="h-4 w-4" />
                  Lead detail
                </div>
                {selectedLead ? (
                  <>
                    <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">{selectedLead.email || `Lead #${selectedLead.id}`}</h2>
                    <div className="mt-6 space-y-4 text-sm text-[var(--color-text-secondary)]">
                      {selectedLead.email && (
                        <div className="flex items-center gap-3">
                          <Mail className="h-4 w-4 text-[var(--color-text-muted)]" />
                          <span>{selectedLead.email}</span>
                        </div>
                      )}
                      {selectedLead.phone && (
                        <div className="flex items-center gap-3">
                          <Phone className="h-4 w-4 text-[var(--color-text-muted)]" />
                          <span>{selectedLead.phone}</span>
                        </div>
                      )}
                      {selectedLead.budget_min && selectedLead.budget_max && (
                        <div className="flex items-center gap-3">
                          <Target className="h-4 w-4 text-[var(--color-text-muted)]" />
                          <span>EGP {formatBudget(selectedLead.budget_min / 1_000_000)}M - {formatBudget(selectedLead.budget_max / 1_000_000)}M</span>
                        </div>
                      )}
                      {selectedLead.timeline && (
                        <div className="flex items-center gap-3">
                          <Calendar className="h-4 w-4 text-[var(--color-text-muted)]" />
                          <span>{selectedLead.timeline}</span>
                        </div>
                      )}
                      {selectedLead.preferred_areas?.length ? (
                        <div className="flex items-start gap-3">
                          <MapPin className="mt-1 h-4 w-4 text-[var(--color-text-muted)]" />
                          <div className="flex flex-wrap gap-2">
                            {selectedLead.preferred_areas.map((area) => (
                              <span key={area} className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-2.5 py-1 text-xs font-medium text-[var(--color-text-primary)]">
                                {area}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <div className="mt-6 border-t border-[var(--color-border)] pt-6">
                      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Move stage</div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {STAGES.map((stage) => (
                          <button
                            key={stage}
                            type="button"
                            onClick={() => void updateStage(selectedLead.id, stage)}
                            disabled={updatingLeadId === selectedLead.id}
                            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                              selectedLead.stage === stage
                                ? 'bg-[var(--color-text-primary)] text-[var(--color-background)]'
                                : 'border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-primary)]'
                            }`}
                          >
                            {STAGE_LABELS[stage]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="mt-4 rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-6 text-sm text-[var(--color-text-secondary)]">
                    Select a lead to inspect its context and update the stage.
                  </div>
                )}
              </div>

              <div className="rounded-[32px] border border-[var(--color-border)] bg-emerald-500/10 p-6">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Pipeline note</div>
                <div className="mt-3 text-sm leading-6 text-[var(--color-text-secondary)]">
                  Keep the stage honest. A smaller accurate hot list is more useful than a larger inflated pipeline.
                </div>
              </div>
            </div>
          </section>
        </div>
      )}
    </AdminShell>
  );
}

function PipelineCard({
  label,
  value,
  active,
  onClick,
}: {
  label: string;
  value: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-[24px] border p-5 text-left transition-colors ${
        active
          ? 'border-emerald-500/30 bg-emerald-500/10'
          : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/20'
      }`}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{value}</div>
    </button>
  );
}
