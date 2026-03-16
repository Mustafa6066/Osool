'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { fetchNotifications as fetchOrchestratorNotifications, type OrchestratorNotification } from '@/lib/orchestrator';

interface Notification {
  id: string;
  type: string;
  title: string;
  titleAr: string | null;
  body: string;
  bodyAr: string | null;
  read: boolean;
  priority: number;
  createdAt: string;
  data?: Record<string, unknown>;
}

export default function NotificationBell() {
  const { user, isAuthenticated } = useAuth();
  const { language } = useLanguage();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated || !user?.id) return;
    try {
      // Fetch from both Platform backend and Orchestrator in parallel
      const [backendRes, orchestratorNotifs] = await Promise.allSettled([
        fetch(`/api/orchestrator/notifications/${user.id}?limit=20`).then(r => r.ok ? r.json() : { notifications: [] }),
        fetchOrchestratorNotifications(String(user.id), 10),
      ]);

      const backendNotifs: Notification[] = backendRes.status === 'fulfilled'
        ? (backendRes.value?.notifications ?? [])
        : [];

      // Convert orchestrator notifications to unified format
      const orchNotifs: Notification[] = orchestratorNotifs.status === 'fulfilled'
        ? orchestratorNotifs.value.map((n: OrchestratorNotification) => ({
            id: n.id,
            type: n.type,
            title: n.title,
            titleAr: n.titleAr || null,
            body: n.body,
            bodyAr: n.bodyAr || null,
            read: n.read,
            priority: n.type === 'market_pulse' ? 2 : 1,
            createdAt: n.createdAt,
            data: n.data,
          }))
        : [];

      // Merge and deduplicate by ID, sort by createdAt desc
      const allNotifs = [...backendNotifs, ...orchNotifs];
      const seen = new Set<string>();
      const deduped = allNotifs.filter((n) => {
        if (seen.has(n.id)) return false;
        seen.add(n.id);
        return true;
      });
      deduped.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

      setNotifications(deduped.slice(0, 20));
      setUnreadCount(deduped.filter((n) => !n.read).length);
    } catch {
      // Silently fail — notifications are non-critical
    }
  }, [isAuthenticated, user?.id]);

  // Poll every 60s
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60_000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handle = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [open]);

  const markAsRead = async (id: string) => {
    try {
      await fetch(`/api/orchestrator/notifications/${id}/read`, { method: 'PATCH' });
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // Ignore
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen(!open)}
        aria-label={language === 'ar' ? 'الإشعارات' : 'Notifications'}
        aria-expanded={open}
        className="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors relative"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -end-0.5 w-4 h-4 rounded-full bg-emerald-500 text-white text-[9px] font-bold flex items-center justify-center leading-none">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="absolute end-0 top-full mt-2 w-80 max-h-96 overflow-y-auto bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-xl shadow-black/10 z-50"
          >
            <div className="px-4 py-3 border-b border-[var(--color-border)]">
              <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                {language === 'ar' ? 'الإشعارات' : 'Notifications'}
              </div>
            </div>

            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-[var(--color-text-muted)]">
                {language === 'ar' ? 'لا يوجد إشعارات' : 'No notifications yet'}
              </div>
            ) : (
              <div className="py-1">
                {notifications.map((notif) => (
                  <button
                    key={notif.id}
                    onClick={() => !notif.read && markAsRead(notif.id)}
                    className={`w-full text-start px-4 py-3 hover:bg-[var(--color-surface-elevated)] transition-colors ${
                      !notif.read ? 'bg-emerald-500/5' : ''
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {!notif.read && (
                        <span className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-[var(--color-text-primary)]">
                          {language === 'ar' ? (notif.titleAr || notif.title) : notif.title}
                        </div>
                        <div className="text-xs text-[var(--color-text-muted)] mt-0.5 line-clamp-2">
                          {language === 'ar' ? (notif.bodyAr || notif.body) : notif.body}
                        </div>
                        <div className="text-[10px] text-[var(--color-text-muted)] mt-1">
                          {formatRelativeTime(notif.createdAt, language)}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function formatRelativeTime(dateStr: string, lang: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return lang === 'ar' ? 'الآن' : 'Just now';
  if (mins < 60) return lang === 'ar' ? `منذ ${mins} دقيقة` : `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return lang === 'ar' ? `منذ ${hours} ساعة` : `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return lang === 'ar' ? `منذ ${days} يوم` : `${days}d ago`;
}
