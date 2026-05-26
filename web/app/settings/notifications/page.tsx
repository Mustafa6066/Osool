'use client';

import { useState, useEffect } from 'react';
import { Bell, MessageCircle, Mail, Clock } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { trackUserMemoryUpdate } from '@/lib/orchestrator';

interface NotificationPrefs {
  in_app: boolean;
  whatsapp: boolean;
  email_digest: boolean;
  frequency: 'realtime' | 'daily' | 'weekly';
  whatsapp_number?: string;
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function NotificationSettingsPage() {
  const { user } = useAuth();
  const { t, direction } = useLanguage();
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const [prefs, setPrefs] = useState<NotificationPrefs>({
    in_app: true,
    whatsapp: false,
    email_digest: false,
    frequency: 'realtime',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [phone, setPhone] = useState('');

  useEffect(() => {
    if (!token) return;
    fetch(`${API}/api/user/notification-preferences`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data) {
          setPrefs(data);
          if (data.whatsapp_number) setPhone(data.whatsapp_number);
        }
      })
      .catch(() => {});
  }, [token]);

  async function save() {
    if (!token) return;
    setSaving(true);
    try {
      const body = { ...prefs, whatsapp_number: prefs.whatsapp ? phone : undefined };

      await fetch(`${API}/api/user/notification-preferences`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      // Forward to Orchestrator for lead preference sync
      if (user?.id) {
        trackUserMemoryUpdate({
          userId: String(user.id),
          anonymousId: '',
        });
      }

      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch {
      // Silent — non-critical
    } finally {
      setSaving(false);
    }
  }

  function Toggle({
    label,
    sublabel,
    icon: Icon,
    checked,
    onChange,
  }: {
    label: string;
    sublabel: string;
    icon: React.ElementType;
    checked: boolean;
    onChange: (v: boolean) => void;
  }) {
    return (
      <div className="flex items-center justify-between gap-4 p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-emerald-500" />
          <div>
            <div className="font-medium text-sm">{label}</div>
            <div className="text-xs text-[var(--color-text-muted)]">{sublabel}</div>
          </div>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          onClick={() => onChange(!checked)}
          className={`relative h-6 w-11 rounded-full transition-colors ${
            checked ? 'bg-emerald-500' : 'bg-[var(--color-border)]'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
              checked ? 'translate-x-5' : ''
            }`}
          />
        </button>
      </div>
    );
  }

  return (
    <AppShell>
      <main
        className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]"
        dir={direction}
      >
        <div className="mx-auto max-w-xl px-4 py-8">
          <h1 className="text-2xl font-semibold mb-2">Notification Preferences</h1>
          <p className="text-sm text-[var(--color-text-muted)] mb-6">
            Control how you receive market alerts and investment updates.
          </p>

          <div className="flex flex-col gap-3">
            <Toggle
              label="In-App Notifications"
              sublabel="Market alerts, price drops, and trending listings"
              icon={Bell}
              checked={prefs.in_app}
              onChange={(v) => setPrefs((p) => ({ ...p, in_app: v }))}
            />

            <Toggle
              label="WhatsApp Alerts"
              sublabel="Receive high-priority alerts on WhatsApp"
              icon={MessageCircle}
              checked={prefs.whatsapp}
              onChange={(v) => setPrefs((p) => ({ ...p, whatsapp: v }))}
            />

            {prefs.whatsapp && (
              <div className="ml-8 p-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
                <label className="text-xs font-medium text-[var(--color-text-muted)] mb-1 block">
                  WhatsApp Number (with country code)
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+20 10 xxxx xxxx"
                  className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-sm"
                />
              </div>
            )}

            <Toggle
              label="Email Digest"
              sublabel="Weekly summary of market movements and new listings"
              icon={Mail}
              checked={prefs.email_digest}
              onChange={(v) => setPrefs((p) => ({ ...p, email_digest: v }))}
            />

            <div className="p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]">
              <div className="flex items-center gap-3 mb-3">
                <Clock className="w-5 h-5 text-emerald-500" />
                <span className="font-medium text-sm">Alert Frequency</span>
              </div>
              <div className="flex gap-2">
                {(['realtime', 'daily', 'weekly'] as const).map((freq) => (
                  <button
                    key={freq}
                    onClick={() => setPrefs((p) => ({ ...p, frequency: freq }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      prefs.frequency === freq
                        ? 'bg-emerald-500 text-white'
                        : 'bg-[var(--color-background)] text-[var(--color-text-muted)] border border-[var(--color-border)]'
                    }`}
                  >
                    {freq === 'realtime' ? 'Real-time' : freq.charAt(0).toUpperCase() + freq.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            onClick={save}
            disabled={saving}
            className="mt-6 w-full py-3 rounded-xl bg-emerald-500 text-white font-semibold text-sm hover:bg-emerald-600 transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Preferences'}
          </button>
        </div>
      </main>
    </AppShell>
  );
}
