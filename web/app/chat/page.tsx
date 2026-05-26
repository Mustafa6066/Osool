'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';

import { useAuth } from '@/contexts/AuthContext';
import api, { sendChatMessage, getUserChatSessions, type ChatSession } from '@/lib/api';
import {
  getOrCreateSessionId,
  loadFromStorage,
  saveToStorage,
  STORAGE_KEYS,
} from '@/lib/chat-utils';
import OsoolAvatar from '@/components/osool/OsoolAvatar';
import {
  IconCalc,
  IconChevDown,
  IconGlobe,
  IconMessageSquare,
  IconMic,
  IconMoon,
  IconPanelLeft,
  IconPaperclip,
  IconPlus,
  IconSearch,
  IconShare,
  IconShield,
  IconSpark,
  IconStop,
  IconSun,
  IconTrending,
  IconUp,
} from '@/components/osool/Icons';

import './chat.css';

/**
 * Osool Chat — editorial surface from the claude.ai/design handoff,
 * now wired to the real backend.
 *
 *   Send       → POST /api/chat        (sendChatMessage)
 *   Sessions   → GET  /api/chat/history (getUserChatSessions)
 *   Resume     → GET  /api/chat/history/{session_id}
 *
 * No mock data: every message comes from the API, every conversation in
 * the sidebar is real, session ID persists via getOrCreateSessionId.
 *
 * The legacy AgentInterface lives at /chat-legacy for reference until
 * we're confident this surface covers every flow.
 */

type Lang = 'en' | 'ar';
type Theme = 'light' | 'dark';
type DemoTier = 'free' | 'paid';

const DEMO_TIER_KEY = 'osool.demoTier';

/**
 * Hard-coded admin email allowlist — fallback for cases where the JWT
 * `role` claim isn't propagating correctly. Matches the backend admin
 * recognition in app/api/email_endpoints.py.
 */
const ADMIN_EMAILS = new Set([
  'mustafa@osool.com',
  'mustafa@osool.eg',
  'hani@osool.com',
  'hani@osool.eg',
]);

function isAdminUser(user: { role?: string; email?: string } | null): boolean {
  if (!user) return false;
  const role = (user.role ?? '').toLowerCase().trim();
  if (role === 'admin') return true;
  const email = (user.email ?? '').toLowerCase().trim();
  return ADMIN_EMAILS.has(email);
}

interface UserMessage {
  role: 'user';
  content: string;
}

interface PropertyCard {
  id?: string | number;
  name: string;
  loc: string;
  price: string;
  score: number | null;
  beds: number | null;
  size: string;
  imageUrl?: string | null;
}

interface AiMessage {
  role: 'ai';
  text: string;
  properties?: PropertyCard[];
  pending?: boolean;
  error?: string;
}

type Message = UserMessage | AiMessage;

interface HistoryMessage {
  role: string;
  content: string;
  properties_json?: string | null;
  created_at?: string;
}

/* ─── Translations ──────────────────────────────────────────────── */

type Translations = {
  newConv: string;
  search: string;
  placeholder: string;
  greeting: string;
  greetingSub: string;
  attach: string;
  voice: string;
  yourPlan: string;
  guest: string;
  disclaimer: string;
  talkAdvisor: string;
  stopGen: string;
  conv1Title: string;
  noConvs: string;
  errorSend: string;
  thinkingLabel: string;
};

const T_EN: Translations = {
  newConv: 'New conversation',
  search: 'Search conversations',
  placeholder: 'Ask Osool anything about real estate in Egypt…',
  greeting: 'How can Osool help today?',
  greetingSub:
    'Ask anything about the Egyptian property market — listings, valuation, contracts. Arabic or English.',
  attach: 'Attach a file',
  voice: 'Voice input',
  yourPlan: 'Free plan',
  guest: 'Guest',
  disclaimer: 'Osool can be wrong about prices. Verify against the registry.',
  talkAdvisor: 'Talk to a licensed advisor instead',
  stopGen: 'Stop generating',
  conv1Title: 'New conversation',
  noConvs: 'No conversations yet',
  errorSend: 'Could not reach Osool. Check your connection and try again.',
  thinkingLabel: 'Thinking…',
};

const T_AR: Translations = {
  newConv: 'محادثة جديدة',
  search: 'ابحث في المحادثات',
  placeholder: 'اسأل أصول أي شيء عن العقارات في مصر…',
  greeting: 'كيف يمكن لأصول مساعدتك اليوم؟',
  greetingSub: 'اسأل عن السوق المصري — وحدات، تقييم، عقود. بالعربية أو الإنجليزية.',
  attach: 'إرفاق ملف',
  voice: 'إدخال صوتي',
  yourPlan: 'الباقة المجانية',
  guest: 'ضيف',
  disclaimer: 'قد يخطئ أصول في الأسعار. تحقق من السجل العقاري.',
  talkAdvisor: 'تحدث إلى مستشار مرخص',
  stopGen: 'إيقاف التوليد',
  conv1Title: 'محادثة جديدة',
  noConvs: 'لا توجد محادثات بعد',
  errorSend: 'تعذر الوصول إلى أصول. تحقق من الاتصال وحاول مرة أخرى.',
  thinkingLabel: 'يفكر…',
};

/* ─── Mapping helpers ───────────────────────────────────────────── */

type Json = Record<string, unknown>;

function readNum(o: Json, ...keys: string[]): number | null {
  for (const k of keys) {
    const v = o[k];
    if (typeof v === 'number' && Number.isFinite(v)) return v;
    if (typeof v === 'string') {
      const n = Number(v);
      if (Number.isFinite(n)) return n;
    }
  }
  return null;
}

function readStr(o: Json, ...keys: string[]): string | undefined {
  for (const k of keys) {
    const v = o[k];
    if (typeof v === 'string' && v.length > 0) return v;
  }
  return undefined;
}

function formatEgp(amount: number, lang: Lang): string {
  if (amount >= 1_000_000) {
    const m = amount / 1_000_000;
    const rounded = m.toFixed(m >= 10 ? 1 : 2).replace(/\.?0+$/, '');
    return lang === 'ar' ? `${rounded} مليون جنيه` : `${rounded}M EGP`;
  }
  if (amount >= 1_000) {
    const k = Math.round(amount / 1_000);
    return lang === 'ar' ? `${k} ألف جنيه` : `${k.toLocaleString('en-US')} EGP`;
  }
  return lang === 'ar' ? `${Math.round(amount).toLocaleString('ar-EG')} جنيه` : `${Math.round(amount).toLocaleString('en-US')} EGP`;
}

function toPropertyCard(raw: unknown, lang: Lang): PropertyCard | null {
  if (!raw || typeof raw !== 'object') return null;
  const p = raw as Json;
  const name = readStr(p, 'title', 'name', 'compound') ?? 'Property';
  const compound = readStr(p, 'compound');
  const area = readStr(p, 'location', 'area', 'city');
  const loc = [compound, area].filter(Boolean).join(' · ') || (lang === 'ar' ? 'الموقع غير محدد' : 'Location unspecified');
  const priceNum = readNum(p, 'price', 'resale_price', 'developer_price', 'amount');
  const price = priceNum !== null ? formatEgp(priceNum, lang) : (readStr(p, 'price_label', 'price_str') ?? '—');
  const score = readNum(p, 'score', 'investment_score', 'osool_score');
  const beds = readNum(p, 'bedrooms', 'beds', 'rooms');
  const sizeNum = readNum(p, 'size_sqm', 'size', 'area_sqm', 'bua');
  const size = sizeNum !== null ? `${Math.round(sizeNum)}m²` : (readStr(p, 'size_str') ?? '');
  const id = (typeof p.id === 'string' || typeof p.id === 'number') ? p.id : (readStr(p, 'property_id', 'listing_id') ?? `${name}-${loc}`);
  const imageUrl = readStr(p, 'image_url', 'imageUrl', 'thumbnail', 'mirrored_image_url') ?? null;
  return { id, name, loc, price, score, beds, size, imageUrl };
}

/* ─── Top-level page ────────────────────────────────────────────── */

export default function ChatPage() {
  const { user, isAuthenticated } = useAuth();
  const isAdmin = isAdminUser(user);

  const [lang, setLang] = useState<Lang>('en');
  const [theme, setTheme] = useState<Theme>('light');
  const [collapsed, setCollapsed] = useState(false);
  const [tier, setTier] = useState<DemoTier>('paid');
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [historyLoading, setHistoryLoading] = useState(true);

  const threadRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const T = lang === 'ar' ? T_AR : T_EN;

  // Restore the admin's demo-tier choice from localStorage on first mount.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem(DEMO_TIER_KEY);
    if (saved === 'free' || saved === 'paid') setTier(saved);
  }, []);

  // Persist tier choice so demos survive reload.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(DEMO_TIER_KEY, tier);
  }, [tier]);

  const switchTier = (next: DemoTier) => {
    if (next === tier) return;
    setTier(next);
  };

  // Apply theme/dir at the document level so reveals + ambient pick it up.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    return () => {
      document.documentElement.removeAttribute('data-theme');
      document.documentElement.setAttribute('dir', 'ltr');
      document.documentElement.setAttribute('lang', 'en');
    };
  }, [theme, lang]);

  // Resolve session id + restore in-flight messages from sessionStorage on mount.
  // We do NOT fetch /api/chat/history/{sid} here — the backend 404s on sessions
  // it has never seen (which is the normal case for a freshly minted ID), and
  // querying it produces noise in the console. History from the server is
  // only loaded when the user explicitly clicks a session in the sidebar.
  useEffect(() => {
    const sid = getOrCreateSessionId();
    setSessionId(sid);
    const restored = loadFromStorage<Message[]>(STORAGE_KEYS.MESSAGES, []);
    if (Array.isArray(restored) && restored.length > 0) setMessages(restored);
    setHistoryLoading(false);
  }, []);

  // Persist messages to sessionStorage so a tab reload mid-conversation
  // doesn't lose context. Same key the legacy AgentInterface used.
  useEffect(() => {
    if (messages.length > 0) saveToStorage(STORAGE_KEYS.MESSAGES, messages);
  }, [messages]);

  // Fetch user's session list for the sidebar (auth only).
  useEffect(() => {
    if (!isAuthenticated) {
      setSessions([]);
      return;
    }
    let cancelled = false;
    getUserChatSessions()
      .then((list) => {
        if (!cancelled) setSessions(list);
      })
      .catch(() => {
        /* Surface silently — sidebar just shows the current session. */
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, sessionId]);

  // Auto-scroll on new messages.
  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  const onScroll = () => {
    const el = threadRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 200);
  };

  const scrollDown = () => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' });
  };

  // ── Real send → backend ────────────────────────────────────────
  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || streaming || !sessionId) return;

      const userMsg: UserMessage = { role: 'user', content: trimmed };
      const pending: AiMessage = { role: 'ai', text: '', pending: true };
      setMessages((m) => [...m, userMsg, pending]);
      setStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      (async () => {
        try {
          const data = await sendChatMessage(trimmed, sessionId, lang === 'ar' ? 'ar' : lang === 'en' ? 'en' : 'auto');
          if (controller.signal.aborted) return;

          const properties = Array.isArray(data.properties)
            ? data.properties
                .map((p) => toPropertyCard(p, lang))
                .filter((p): p is PropertyCard => p !== null)
            : undefined;

          const reply: AiMessage = {
            role: 'ai',
            text: data.response ?? '',
            properties: properties && properties.length > 0 ? properties : undefined,
          };

          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = reply;
            return copy;
          });
        } catch (err: unknown) {
          if (controller.signal.aborted) return;
          if (axios.isCancel?.(err)) return;
          const fallback: AiMessage = { role: 'ai', text: '', error: T.errorSend };
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = fallback;
            return copy;
          });
        } finally {
          if (!controller.signal.aborted) setStreaming(false);
          if (abortRef.current === controller) abortRef.current = null;
        }
      })();
    },
    [lang, sessionId, streaming, T.errorSend],
  );

  const onStop = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
    // Remove the dangling pending bubble.
    setMessages((m) => (m.length && (m[m.length - 1] as AiMessage).pending ? m.slice(0, -1) : m));
  };

  const startNewConversation = () => {
    const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, newId);
    sessionStorage.removeItem(STORAGE_KEYS.MESSAGES);
    setSessionId(newId);
    setMessages([]);
  };

  const selectSession = useCallback(
    async (sid: string) => {
      if (sid === sessionId) return;
      setHistoryLoading(true);
      try {
        const res = await api.get(`/api/chat/history/${sid}`);
        const history: HistoryMessage[] = Array.isArray(res.data)
          ? res.data
          : (res.data?.messages ?? []);
        const mapped = history
          .map((m): Message | null => {
            if (m.role === 'user') return { role: 'user', content: m.content };
            if (m.role === 'assistant' || m.role === 'ai') {
              let properties: PropertyCard[] | undefined;
              if (m.properties_json) {
                try {
                  const arr = JSON.parse(m.properties_json) as unknown;
                  if (Array.isArray(arr)) {
                    properties = arr
                      .map((p) => toPropertyCard(p, lang))
                      .filter((p): p is PropertyCard => p !== null);
                    if (properties.length === 0) properties = undefined;
                  }
                } catch {
                  /* ignore */
                }
              }
              return { role: 'ai', text: m.content, properties };
            }
            return null;
          })
          .filter((m): m is Message => m !== null);
        sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sid);
        setSessionId(sid);
        setMessages(mapped);
      } catch {
        /* leave UI unchanged on failure */
      } finally {
        setHistoryLoading(false);
      }
    },
    [lang, sessionId],
  );

  return (
    <div className="osool-chat-root">
      <div className="ambient" />
      <div className="shell" data-sidebar={collapsed ? 'collapsed' : 'expanded'}>
        <Sidebar
          T={T}
          collapsed={collapsed}
          lang={lang}
          sessions={sessions}
          currentSessionId={sessionId}
          onSelectSession={selectSession}
          onNewConversation={startNewConversation}
          user={user ? { name: user.full_name ?? user.email ?? T.guest, email: user.email ?? '' } : null}
        />
        <main className="main">
          <Topbar
            T={T}
            theme={theme}
            lang={lang}
            tier={tier}
            showDemoToggle={isAdmin}
            onSwitchTier={switchTier}
            onToggleSidebar={() => setCollapsed((v) => !v)}
            onToggleLang={() => setLang((l) => (l === 'ar' ? 'en' : 'ar'))}
            onToggleTheme={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
          />

          {messages.length === 0 && !historyLoading ? (
            <>
              <EmptyState T={T} lang={lang} onPick={send} />
              <Composer T={T} isStreaming={streaming} onSend={send} onStop={onStop} />
            </>
          ) : (
            <>
              <div className="thread" ref={threadRef} onScroll={onScroll}>
                <div className="thread-inner">
                  {messages.map((m, i) =>
                    m.role === 'user' ? (
                      <UserBubble key={i} content={m.content} />
                    ) : m.pending ? (
                      <Typing key={i} T={T} />
                    ) : (
                      <AiBubble key={i} msg={m} tier={tier} lang={lang} />
                    ),
                  )}
                </div>
              </div>
              <button
                type="button"
                className={'scroll-bottom' + (showScrollBtn ? ' visible' : '')}
                onClick={scrollDown}
                aria-label="Scroll to bottom"
              >
                <IconChevDown size={16} />
              </button>
              <Composer T={T} isStreaming={streaming} onSend={send} onStop={onStop} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}

/* ─── Sidebar ───────────────────────────────────────────────────── */

interface SidebarProps {
  T: Translations;
  collapsed: boolean;
  lang: Lang;
  sessions: ChatSession[];
  currentSessionId: string;
  onSelectSession: (sid: string) => void;
  onNewConversation: () => void;
  user: { name: string; email: string } | null;
}

function Sidebar({
  T,
  collapsed,
  lang,
  sessions,
  currentSessionId,
  onSelectSession,
  onNewConversation,
  user,
}: SidebarProps) {
  const [q, setQ] = useState('');

  const grouped = useMemo(() => groupSessions(sessions, lang), [sessions, lang]);
  const filtered = useMemo(() => {
    if (!q.trim()) return grouped;
    const needle = q.trim().toLowerCase();
    return grouped
      .map((g) => ({
        ...g,
        items: g.items.filter((s) => (s.preview ?? '').toLowerCase().includes(needle)),
      }))
      .filter((g) => g.items.length > 0);
  }, [grouped, q]);

  const initial = user?.name?.[0]?.toUpperCase() ?? 'G';

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <OsoolAvatar size={26} animated />
        </div>
        {!collapsed && <div className="brand-name">Osool</div>}
      </div>

      <button type="button" className="new-conv" onClick={onNewConversation}>
        <IconPlus size={15} />
        {!collapsed && <span className="new-conv-text">{T.newConv}</span>}
      </button>

      {!collapsed && (
        <div className="sb-search">
          <IconSearch size={13} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={T.search}
            type="text"
          />
        </div>
      )}

      <div className="sb-scroll">
        {!collapsed && filtered.length === 0 && (
          <div className="sb-group-label" style={{ opacity: 0.7 }}>
            {T.noConvs}
          </div>
        )}
        {!collapsed &&
          filtered.map((group) => (
            <div key={group.label}>
              <div className="sb-group-label">{group.label}</div>
              {group.items.map((s) => (
                <button
                  type="button"
                  key={s.session_id}
                  className={'sb-item' + (s.session_id === currentSessionId ? ' active' : '')}
                  onClick={() => onSelectSession(s.session_id)}
                  title={s.preview ?? undefined}
                >
                  <span className="sb-item-text">
                    {s.preview?.trim() || T.conv1Title}
                  </span>
                </button>
              ))}
            </div>
          ))}
      </div>

      <div className="profile">
        <div className="avatar-circle">{initial}</div>
        {!collapsed && (
          <div className="profile-text">
            <div className="profile-name">{user?.name ?? T.guest}</div>
            <div className="profile-mail">{user?.email || T.yourPlan}</div>
          </div>
        )}
      </div>
    </aside>
  );
}

/* ─── Session grouping ──────────────────────────────────────────── */

interface SidebarGroup {
  label: string;
  items: ChatSession[];
}

function groupSessions(sessions: ChatSession[], lang: Lang): SidebarGroup[] {
  if (sessions.length === 0) return [];
  const now = Date.now();
  const todayCut = now - 86_400_000;
  const yesterdayCut = now - 2 * 86_400_000;
  const weekCut = now - 7 * 86_400_000;

  const buckets: Record<string, ChatSession[]> = {
    today: [],
    yesterday: [],
    week: [],
    older: [],
  };

  for (const s of sessions) {
    const ts = s.last_message_at ? Date.parse(s.last_message_at) : 0;
    if (ts >= todayCut) buckets.today.push(s);
    else if (ts >= yesterdayCut) buckets.yesterday.push(s);
    else if (ts >= weekCut) buckets.week.push(s);
    else buckets.older.push(s);
  }

  const labels =
    lang === 'ar'
      ? { today: 'اليوم', yesterday: 'أمس', week: 'آخر ٧ أيام', older: 'سابقًا' }
      : { today: 'Today', yesterday: 'Yesterday', week: 'Last 7 days', older: 'Older' };

  return (['today', 'yesterday', 'week', 'older'] as const)
    .filter((k) => buckets[k].length > 0)
    .map((k) => ({ label: labels[k], items: buckets[k] }));
}

/* ─── Topbar ────────────────────────────────────────────────────── */

function Topbar({
  T,
  theme,
  lang,
  tier,
  showDemoToggle,
  onSwitchTier,
  onToggleSidebar,
  onToggleLang,
  onToggleTheme,
}: {
  T: Translations;
  theme: Theme;
  lang: Lang;
  tier: DemoTier;
  showDemoToggle: boolean;
  onSwitchTier: (next: DemoTier) => void;
  onToggleSidebar: () => void;
  onToggleLang: () => void;
  onToggleTheme: () => void;
}) {
  const labelFree = lang === 'ar' ? 'مجاني' : 'Free';
  const labelPaid = lang === 'ar' ? 'مدفوع' : 'Paid';
  const labelTag = lang === 'ar' ? 'وضع العرض' : 'Demo';

  return (
    <header className="topbar">
      <button type="button" className="icon-btn" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        <IconPanelLeft size={16} />
      </button>
      <div className="topbar-title">
        <b>{lang === 'ar' ? T.conv1Title : 'Osool'}</b>
      </div>
      {showDemoToggle && (
        <div
          className="demo-toggle"
          role="group"
          aria-label={lang === 'ar' ? 'تبديل وضع العرض' : 'Demo path toggle'}
        >
          <span className="demo-toggle-label">{labelTag}</span>
          <button
            type="button"
            className={tier === 'free' ? 'active' : ''}
            onClick={() => onSwitchTier('free')}
            aria-pressed={tier === 'free'}
          >
            {labelFree}
          </button>
          <button
            type="button"
            className={tier === 'paid' ? 'active' : ''}
            onClick={() => onSwitchTier('paid')}
            aria-pressed={tier === 'paid'}
          >
            {labelPaid}
          </button>
        </div>
      )}
      <button type="button" className="icon-btn" onClick={onToggleLang} aria-label="Language">
        <IconGlobe size={16} />
      </button>
      <button type="button" className="icon-btn" onClick={onToggleTheme} aria-label="Theme">
        {theme === 'dark' ? <IconSun size={16} /> : <IconMoon size={16} />}
      </button>
      <button type="button" className="icon-btn" aria-label="Share">
        <IconShare size={16} />
      </button>
    </header>
  );
}

/* ─── User bubble ───────────────────────────────────────────────── */

function UserBubble({ content }: { content: string }) {
  return <div className="msg-user">{content}</div>;
}

/* ─── AI bubble ─────────────────────────────────────────────────── */

function AiBubble({
  msg,
  tier,
  lang,
}: {
  msg: AiMessage;
  tier: DemoTier;
  lang: Lang;
}) {
  const isFree = tier === 'free';

  return (
    <div className="msg-ai">
      <div className="ai-label">
        <span className="ai-label-mark">
          <OsoolAvatar size={20} animated />
        </span>
        <b>Osool</b>
      </div>

      <div className="ai-body">
        {msg.error ? (
          <p style={{ color: 'var(--osool-accent)' }}>{msg.error}</p>
        ) : (
          <AiText text={msg.text} />
        )}

        {msg.properties && msg.properties.length > 0 && (
          <>
            <div className="section-label">
              {msg.properties.length === 1
                ? lang === 'ar'
                  ? 'صفقة مرجعية'
                  : 'Reference comp'
                : lang === 'ar'
                  ? `أفضل ${msg.properties.length}`
                  : `Top ${msg.properties.length} picks`}
            </div>
            <div className="carousel-shell">
              <div className="carousel">
                {msg.properties.map((p, i) => (
                  <article key={`${p.id ?? i}`} className="prop-card">
                    <div
                      className="prop-img"
                      style={
                        p.imageUrl
                          ? {
                              backgroundImage: `url(${p.imageUrl})`,
                              backgroundSize: 'cover',
                              backgroundPosition: 'center',
                            }
                          : undefined
                      }
                    />
                    <div className="prop-body">
                      <h5 className="prop-name">{p.name}</h5>
                      <div className="prop-loc">{p.loc}</div>
                      <div className="prop-row1">
                        <span className={'prop-price' + (isFree ? ' masked' : '')}>
                          {isFree ? (lang === 'ar' ? '— مغلق —' : '— locked —') : p.price}
                        </span>
                        {p.score !== null && !isFree && (
                          <span className="prop-score-num">
                            <b>{Math.round(p.score)}</b>
                          </span>
                        )}
                      </div>
                      {(p.beds !== null || p.size) && (
                        <div className="prop-specs">
                          {p.beds !== null && <span>{p.beds} BR</span>}
                          {p.beds !== null && p.size && <span>·</span>}
                          {p.size && <span>{p.size}</span>}
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </>
        )}

        {isFree && msg.properties && msg.properties.length > 0 && (
          <div className="upgrade-cta">
            <div className="upgrade-cta-head">
              <span className="upgrade-cta-eyebrow">
                {lang === 'ar' ? 'افتح الإجابة الكاملة' : 'Unlock the full answer'}
              </span>
            </div>
            <h4>
              {lang === 'ar'
                ? 'كل صفقة، كل أداة، كل سيناريو'
                : 'See every comp, every lever, every script.'}
            </h4>
            <p>
              {lang === 'ar'
                ? 'الباقة المدفوعة تفتح جدول الصفقات الكامل، أدوات التفاوض (خصم الكاش، عمولة السمسار، فارق التقسيط)، ونص مساومة ثنائي اللغة.'
                : 'Premium opens the full comp table, negotiation levers (cash discount, broker commission, payment-plan markup), and a bilingual haggle script you can use straight with the seller.'}
            </p>
            <div className="upgrade-cta-skus">
              <button type="button" className="upgrade-sku">
                <span className="upgrade-sku-price">EGP 99</span>
                <span className="upgrade-sku-label">
                  {lang === 'ar' ? 'هذا الكمبوند · 30 يوم' : 'This compound · 30 days'}
                </span>
              </button>
              <button type="button" className="upgrade-sku">
                <span className="upgrade-sku-price">EGP 299/mo</span>
                <span className="upgrade-sku-label">
                  {lang === 'ar' ? 'كل الكمبوندات · بلا حدود' : 'All compounds · unlimited'}
                </span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/** Render plain text with paragraph breaks preserved. */
function AiText({ text }: { text: string }) {
  if (!text) return null;
  const paragraphs = text.split(/\n\s*\n/);
  return (
    <>
      {paragraphs.map((p, i) => (
        <p key={i} style={{ whiteSpace: 'pre-wrap' }}>
          {p}
        </p>
      ))}
    </>
  );
}

function Typing({ T }: { T: Translations }) {
  return (
    <div className="msg-ai">
      <div className="ai-label">
        <span className="ai-label-mark">
          <OsoolAvatar size={20} animated state="thinking" />
        </span>
        <b>Osool</b>
        <span style={{ color: 'var(--muted)', marginInlineStart: 8 }}>{T.thinkingLabel}</span>
      </div>
      <div className="ai-body">
        <div className="typing">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}

/* ─── Empty state ───────────────────────────────────────────────── */

function EmptyState({
  T,
  lang,
  onPick,
}: {
  T: Translations;
  lang: Lang;
  onPick: (q: string) => void;
}) {
  type Card = { t: string; s: string; Icon: typeof IconTrending; q: string };
  const cards: Card[] =
    lang === 'ar'
      ? [
          {
            t: 'اتجاهات السوق',
            s: 'أسعار القاهرة الجديدة هذا الشهر',
            Icon: IconTrending,
            q: 'ما تحليل السوق الحالي للقاهرة الجديدة؟',
          },
          {
            t: 'احسب العائد',
            s: 'توقع عوائد ٥ سنوات على ٢ مليون',
            Icon: IconCalc,
            q: 'احسب العائد لاستثمار ٢ مليون ج.م في الساحل الشمالي',
          },
          {
            t: 'افحص عقدًا',
            s: 'ابحث عن المخاطر وفق القانون المصري',
            Icon: IconShield,
            q: 'ابحث عن المخاطر في عقد Mivida القياسي',
          },
          {
            t: 'هل السعر عادل؟',
            s: 'تقييم بالذكاء الاصطناعي',
            Icon: IconSpark,
            q: 'هل ٨٫٤ مليون ج.م سعر عادل لفيلا ١٥٢م في Mountain View؟',
          },
        ]
      : [
          {
            t: 'Explore market trends',
            s: 'New Cairo prices, this month',
            Icon: IconTrending,
            q: 'Show me the current market analysis for New Cairo',
          },
          {
            t: 'Calculate ROI',
            s: '5-year forecast on 2M EGP',
            Icon: IconCalc,
            q: 'Calculate 5-year ROI for a 2M EGP investment in North Coast',
          },
          {
            t: 'Review a contract',
            s: 'Spot risks under Egyptian law',
            Icon: IconShield,
            q: 'Find risks in the standard Mivida purchase contract',
          },
          {
            t: 'Is this price fair?',
            s: 'AI valuation against comps',
            Icon: IconSpark,
            q: 'Is 8.4M EGP a fair price for a 152m Mountain View villa?',
          },
        ];

  return (
    <div className="empty">
      <div className="empty-mark">
        <OsoolAvatar size={64} animated />
      </div>
      <h1>{T.greeting}</h1>
      <p>{T.greetingSub}</p>
      <div className="suggestions">
        {cards.map((c) => (
          <button key={c.t} type="button" className="suggestion" onClick={() => onPick(c.q)}>
            <span className="suggestion-icon">
              <c.Icon size={16} />
            </span>
            <span className="suggestion-text">
              <b>{c.t}</b>
              <small>{c.s}</small>
            </span>
          </button>
        ))}
      </div>
      <button type="button" className="advisor-cta">
        <IconMessageSquare size={13} />
        {T.talkAdvisor}
      </button>
    </div>
  );
}

/* ─── Composer ──────────────────────────────────────────────────── */

function Composer({
  T,
  isStreaming,
  onSend,
  onStop,
}: {
  T: Translations;
  isStreaming: boolean;
  onSend: (v: string) => void;
  onStop: () => void;
}) {
  const [val, setVal] = useState('');
  const [voice, setVoice] = useState(false);
  const taRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    if (!val.trim() || isStreaming) return;
    onSend(val.trim());
    setVal('');
    if (taRef.current) taRef.current.style.height = 'auto';
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setVal(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  };

  return (
    <div className="composer">
      <div className="composer-inner">
        {isStreaming && (
          <div className="stop-btn-wrap">
            <button type="button" className="stop-btn" onClick={onStop}>
              <IconStop size={10} /> {T.stopGen}
            </button>
          </div>
        )}
        <div className="composer-box">
          <button type="button" className="composer-attach" title={T.attach} aria-label={T.attach}>
            <IconPaperclip size={17} />
          </button>
          <textarea
            ref={taRef}
            className="composer-input"
            rows={1}
            value={val}
            onChange={onInput}
            onKeyDown={onKey}
            placeholder={T.placeholder}
            dir="auto"
          />
          <button
            type="button"
            className={'voice-orb' + (voice ? ' active' : '')}
            onClick={() => setVoice((v) => !v)}
            title={T.voice}
            aria-label={T.voice}
          >
            <IconMic size={15} />
          </button>
          <button
            type="button"
            className="send-btn"
            onClick={submit}
            disabled={!val.trim() || isStreaming}
            aria-label="Send"
          >
            <IconUp size={15} />
          </button>
        </div>
        <div className="composer-foot">
          <span>{T.disclaimer}</span>
        </div>
      </div>
    </div>
  );
}
