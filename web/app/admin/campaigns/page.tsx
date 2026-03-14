'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Eye,
  Loader2,
  Megaphone,
  MousePointer,
  Plus,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import AdminShell from '@/components/AdminShell';
import api from '@/lib/api';

interface Campaign {
  id: number;
  name: string;
  platform: string;
  status: string;
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cpa?: number;
  created_at?: string;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-EG').format(Math.round(value));
}

export default function CampaignsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: '',
    platform: 'meta',
    budget: '',
    target_areas: '',
    target_intents: '',
  });

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/campaigns');
      setCampaigns(response.data || []);
    } catch (loadError) {
      console.error(loadError);
      setCampaigns([]);
      setError('Campaign data could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchCampaigns();
  }, [fetchCampaigns]);

  const createCampaign = async () => {
    if (!form.name || !form.budget) {
      return;
    }

    setCreating(true);
    try {
      await api.post('/api/campaigns', {
        name: form.name,
        platform: form.platform,
        budget: parseFloat(form.budget),
        target_areas: form.target_areas
          ? form.target_areas.split(',').map((item) => item.trim()).filter(Boolean)
          : [],
        target_intents: form.target_intents
          ? form.target_intents.split(',').map((item) => item.trim()).filter(Boolean)
          : [],
      });
      setShowForm(false);
      setForm({ name: '', platform: 'meta', budget: '', target_areas: '', target_intents: '' });
      await fetchCampaigns();
    } catch (createError) {
      console.error(createError);
      setError('Campaign could not be created.');
    } finally {
      setCreating(false);
    }
  };

  const toggleStatus = async (campaign: Campaign) => {
    const nextStatus = campaign.status === 'active' ? 'paused' : 'active';
    try {
      await api.patch(`/api/campaigns/${campaign.id}`, { status: nextStatus });
      setCampaigns((current) => current.map((item) => (item.id === campaign.id ? { ...item, status: nextStatus } : item)));
    } catch (toggleError) {
      console.error(toggleError);
      setError('Campaign status could not be updated.');
    }
  };

  const summary = useMemo(() => {
    return {
      active: campaigns.filter((campaign) => campaign.status === 'active').length,
      budget: campaigns.reduce((sum, campaign) => sum + (campaign.budget || 0), 0),
      spent: campaigns.reduce((sum, campaign) => sum + (campaign.spent || 0), 0),
      conversions: campaigns.reduce((sum, campaign) => sum + (campaign.conversions || 0), 0),
    };
  }, [campaigns]);

  return (
    <AdminShell
      eyebrow="Admin campaigns"
      title="Control acquisition without leaving the admin workspace."
      subtitle="Track campaign spend, monitor conversion signal, and open or pause campaigns from the same operating layer."
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => void fetchCampaigns()}
            className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3 text-sm font-semibold text-[var(--color-text-primary)]"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={() => setShowForm((current) => !current)}
            className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
          >
            <Plus className="h-4 w-4" />
            {showForm ? 'Close form' : 'New campaign'}
          </button>
        </div>
      }
    >
      {loading ? (
        <div className="flex items-center justify-center rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] py-24">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      ) : (
        <div className="space-y-6">
          {error ? <div className="rounded-[32px] border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-500">{error}</div> : null}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <SummaryCard label="Active campaigns" value={formatNumber(summary.active)} />
            <SummaryCard label="Allocated budget" value={`EGP ${formatNumber(summary.budget)}`} />
            <SummaryCard label="Spend to date" value={`EGP ${formatNumber(summary.spent)}`} />
            <SummaryCard label="Conversions" value={formatNumber(summary.conversions)} />
          </section>

          {showForm ? (
            <section className="rounded-[32px] border border-emerald-500/20 bg-emerald-500/5 p-6">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Campaign setup</div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Create a new campaign</h2>
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <input
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                  placeholder="Campaign name"
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none"
                />
                <select
                  value={form.platform}
                  onChange={(event) => setForm({ ...form, platform: event.target.value })}
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none"
                >
                  <option value="meta">Meta</option>
                  <option value="google">Google</option>
                  <option value="tiktok">TikTok</option>
                </select>
                <input
                  value={form.budget}
                  onChange={(event) => setForm({ ...form, budget: event.target.value })}
                  placeholder="Budget in EGP"
                  type="number"
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none"
                />
                <input
                  value={form.target_areas}
                  onChange={(event) => setForm({ ...form, target_areas: event.target.value })}
                  placeholder="Target areas, comma separated"
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none"
                />
                <input
                  value={form.target_intents}
                  onChange={(event) => setForm({ ...form, target_intents: event.target.value })}
                  placeholder="Target intents, comma separated"
                  className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-sm text-[var(--color-text-primary)] outline-none sm:col-span-2"
                />
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => void createCampaign()}
                  disabled={creating}
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)] disabled:opacity-60"
                >
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  Create campaign
                </button>
              </div>
            </section>
          ) : null}

          <section className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Campaign table</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-[var(--color-text-primary)]">Live acquisition inventory</h2>
            {campaigns.length ? (
              <div className="mt-6 overflow-x-auto rounded-2xl border border-[var(--color-border)]">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-background)]">
                    <tr>
                      <th className="p-3 text-left font-medium">Campaign</th>
                      <th className="p-3 text-center font-medium">Platform</th>
                      <th className="p-3 text-center font-medium">Status</th>
                      <th className="p-3 text-right font-medium">Budget</th>
                      <th className="p-3 text-right font-medium">Spent</th>
                      <th className="p-3 text-right font-medium">Impressions</th>
                      <th className="p-3 text-right font-medium">Clicks</th>
                      <th className="p-3 text-right font-medium">Conversions</th>
                      <th className="p-3 text-center font-medium">Toggle</th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaigns.map((campaign) => (
                      <tr key={campaign.id} className="border-t border-[var(--color-border)]">
                        <td className="p-3">
                          <div className="font-medium text-[var(--color-text-primary)]">{campaign.name}</div>
                          {campaign.created_at ? <div className="mt-1 text-xs text-[var(--color-text-muted)]">Created {new Date(campaign.created_at).toLocaleDateString()}</div> : null}
                        </td>
                        <td className="p-3 text-center">
                          <span className="inline-flex rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-2.5 py-1 text-xs font-medium">{campaign.platform}</span>
                        </td>
                        <td className="p-3 text-center">
                          <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${campaign.status === 'active' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300' : 'bg-amber-500/10 text-amber-600 dark:text-amber-300'}`}>
                            {campaign.status}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">{formatNumber(campaign.budget)}</td>
                        <td className="p-3 text-right font-mono">{formatNumber(campaign.spent)}</td>
                        <td className="p-3 text-right font-mono">{formatNumber(campaign.impressions)}</td>
                        <td className="p-3 text-right font-mono">{formatNumber(campaign.clicks)}</td>
                        <td className="p-3 text-right font-mono font-semibold text-emerald-600 dark:text-emerald-300">{formatNumber(campaign.conversions)}</td>
                        <td className="p-3 text-center">
                          <button onClick={() => void toggleStatus(campaign)} className="inline-flex items-center justify-center">
                            {campaign.status === 'active' ? <ToggleRight className="h-5 w-5 text-emerald-500" /> : <ToggleLeft className="h-5 w-5 text-[var(--color-text-muted)]" />}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="mt-6 rounded-[24px] border border-dashed border-[var(--color-border)] bg-[var(--color-background)] p-8 text-center text-sm text-[var(--color-text-secondary)]">
                No campaigns are available yet.
              </div>
            )}
          </section>

          <section className="grid gap-4 sm:grid-cols-3">
            <NoteCard icon={Megaphone} label="Platform mix" text="Use platform labels to keep spend visible across Meta, Google, and TikTok without switching tools." />
            <NoteCard icon={Eye} label="Impressions" text="High reach without clicks is a creative or targeting problem, not a scaling signal." />
            <NoteCard icon={MousePointer} label="Clicks" text="Clicks only matter if they continue into lead quality and downstream conversion." />
          </section>
        </div>
      )}
    </AdminShell>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-[var(--color-text-primary)]">{value}</div>
    </div>
  );
}

function NoteCard({
  icon: Icon,
  label,
  text,
}: {
  icon: typeof Megaphone;
  label: string;
  text: string;
}) {
  return (
    <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <Icon className="h-5 w-5 text-emerald-500" />
      <div className="mt-3 text-sm font-semibold text-[var(--color-text-primary)]">{label}</div>
      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{text}</div>
    </div>
  );
}
