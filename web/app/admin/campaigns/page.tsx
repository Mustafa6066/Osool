'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Loader2,
  RefreshCw,
  Plus,
  Megaphone,
  DollarSign,
  Eye,
  MousePointer,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import api from '@/lib/api';

/* ── Types ─────────────────────────────────────────────── */

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

/* ── Main Component ───────────────────────────────────── */

export default function CampaignsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: '',
    platform: 'meta',
    budget: '',
    target_areas: '',
    target_intents: '',
  });

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/campaigns');
      setCampaigns(res.data);
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) { router.push('/'); return; }
    fetchCampaigns();
  }, [authLoading, isAuthenticated, router, fetchCampaigns]);

  const createCampaign = async () => {
    if (!form.name || !form.budget) return;
    try {
      await api.post('/api/campaigns', {
        name: form.name,
        platform: form.platform,
        budget: parseFloat(form.budget),
        target_areas: form.target_areas ? form.target_areas.split(',').map((s) => s.trim()) : [],
        target_intents: form.target_intents ? form.target_intents.split(',').map((s) => s.trim()) : [],
      });
      setShowForm(false);
      setForm({ name: '', platform: 'meta', budget: '', target_areas: '', target_intents: '' });
      fetchCampaigns();
    } catch {
      // silent
    }
  };

  const toggleStatus = async (c: Campaign) => {
    const newStatus = c.status === 'active' ? 'paused' : 'active';
    try {
      await api.patch(`/api/campaigns/${c.id}`, { status: newStatus });
      setCampaigns((prev) =>
        prev.map((x) => (x.id === c.id ? { ...x, status: newStatus } : x))
      );
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
              className="p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Megaphone className="w-6 h-6 text-emerald-500" /> Ad Campaigns
              </h1>
              <p className="text-sm text-[var(--color-text-muted)]">
                Manage Meta & Google ad campaigns
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={fetchCampaigns}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-emerald-500/50 text-sm"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 transition-colors text-sm"
            >
              <Plus className="w-4 h-4" /> New Campaign
            </button>
          </div>
        </div>

        {/* Create Form */}
        {showForm && (
          <div className="rounded-xl border border-emerald-500/30 bg-[var(--color-surface)] p-5 mb-6">
            <h3 className="font-semibold mb-4">Create Campaign</h3>
            <div className="grid sm:grid-cols-2 gap-3">
              <input
                placeholder="Campaign name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="px-3 py-2 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-sm"
              />
              <select
                value={form.platform}
                onChange={(e) => setForm({ ...form, platform: e.target.value })}
                className="px-3 py-2 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-sm"
              >
                <option value="meta">Meta (Facebook/Instagram)</option>
                <option value="google">Google Ads</option>
                <option value="tiktok">TikTok</option>
              </select>
              <input
                placeholder="Budget (EGP)"
                type="number"
                value={form.budget}
                onChange={(e) => setForm({ ...form, budget: e.target.value })}
                className="px-3 py-2 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-sm"
              />
              <input
                placeholder="Target areas (comma sep)"
                value={form.target_areas}
                onChange={(e) => setForm({ ...form, target_areas: e.target.value })}
                className="px-3 py-2 rounded-lg bg-[var(--color-background)] border border-[var(--color-border)] text-sm"
              />
            </div>
            <div className="mt-3 flex justify-end">
              <button
                onClick={createCampaign}
                className="px-5 py-2 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 text-sm font-medium"
              >
                Create
              </button>
            </div>
          </div>
        )}

        {/* Campaigns Table */}
        {campaigns.length === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)] p-4">No campaigns yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--color-surface)]">
                <tr>
                  <th className="p-3 text-left font-medium">Campaign</th>
                  <th className="p-3 text-center font-medium">Platform</th>
                  <th className="p-3 text-center font-medium">Status</th>
                  <th className="p-3 text-right font-medium">Budget</th>
                  <th className="p-3 text-right font-medium">Spent</th>
                  <th className="p-3 text-right font-medium flex items-center justify-end gap-1">
                    <Eye className="w-3 h-3" /> Impr
                  </th>
                  <th className="p-3 text-right font-medium">
                    <MousePointer className="w-3 h-3 inline" /> Clicks
                  </th>
                  <th className="p-3 text-right font-medium">Conv</th>
                  <th className="p-3 text-center font-medium">Toggle</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.id} className="border-t border-[var(--color-border)]">
                    <td className="p-3 font-medium">{c.name}</td>
                    <td className="p-3 text-center">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-border)]/50">
                        {c.platform}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          c.status === 'active'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : 'bg-yellow-500/10 text-yellow-600'
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td className="p-3 text-right font-mono">{fmt(c.budget)}</td>
                    <td className="p-3 text-right font-mono">{fmt(c.spent)}</td>
                    <td className="p-3 text-right font-mono">{fmt(c.impressions)}</td>
                    <td className="p-3 text-right font-mono">{fmt(c.clicks)}</td>
                    <td className="p-3 text-right font-mono text-emerald-500">{c.conversions}</td>
                    <td className="p-3 text-center">
                      <button onClick={() => toggleStatus(c)} className="hover:text-emerald-500 transition-colors">
                        {c.status === 'active' ? (
                          <ToggleRight className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <ToggleLeft className="w-5 h-5 text-[var(--color-text-muted)]" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
