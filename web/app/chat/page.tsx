'use client';

import { useEffect, useRef, useState } from 'react';

import { useAuth } from '@/contexts/AuthContext';
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
 * Osool Chat — visual prototype, now live at /chat.
 * Port of Osool Chat.html from the claude.ai/design handoff.
 *
 * Demo tiers:
 *   - "paid"  → full reply: thinking + summary strip + property carousel + levers
 *   - "free"  → fair-range teaser + one masked comp + upgrade CTA
 *
 * Admins see a topbar segmented toggle to flip between the two for live demos.
 * The chosen tier is persisted in localStorage under "osool.demoTier".
 * Non-admin users see the paid demo by default (legacy behaviour preserved).
 *
 * The production AgentInterface lives at /chat-legacy until backend wiring
 * for this new surface lands.
 */

type Lang = 'en' | 'ar';
type Theme = 'light' | 'dark';
type DemoTier = 'free' | 'paid';
const DEMO_TIER_KEY = 'osool.demoTier';

type Translations = {
  newConv: string;
  search: string;
  placeholder: string;
  greeting: string;
  greetingSub: string;
  attach: string;
  voice: string;
  yourPlan: string;
  disclaimer: string;
  talkAdvisor: string;
  stopGen: string;
  conv1Title: string;
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
  yourPlan: 'mustafa@osool.eg',
  disclaimer: 'Osool can be wrong about prices. Verify against the registry.',
  talkAdvisor: 'Talk to a licensed advisor instead',
  stopGen: 'Stop generating',
  conv1Title: 'Villas in New Cairo under 10M',
};

const T_AR: Translations = {
  newConv: 'محادثة جديدة',
  search: 'ابحث في المحادثات',
  placeholder: 'اسأل أصول أي شيء عن العقارات في مصر…',
  greeting: 'كيف يمكن لأصول مساعدتك اليوم؟',
  greetingSub: 'اسأل عن السوق المصري — وحدات، تقييم، عقود. بالعربية أو الإنجليزية.',
  attach: 'إرفاق ملف',
  voice: 'إدخال صوتي',
  yourPlan: 'mustafa@osool.eg',
  disclaimer: 'قد يخطئ أصول في الأسعار. تحقق من السجل العقاري.',
  talkAdvisor: 'أو تحدث إلى مستشار مرخص',
  stopGen: 'إيقاف التوليد',
  conv1Title: 'فيلات في القاهرة الجديدة بأقل من ١٠ مليون',
};

type Conversation = {
  group: 'Today' | 'Yesterday' | 'Last 7 days';
  items: Array<{ id: string; title: string; active?: boolean }>;
};

const CONVERSATIONS: Conversation[] = [
  {
    group: 'Today',
    items: [
      { id: 'c1', title: 'Villas in New Cairo under 10M', active: true },
      { id: 'c2', title: 'Hyde Park vs Mivida — ROI?' },
      { id: 'c3', title: 'Fair value: 8.4M Mountain View villa' },
    ],
  },
  {
    group: 'Yesterday',
    items: [
      { id: 'c4', title: 'Mountain View iCity clause 14' },
      { id: 'c5', title: 'Fawry escrow for 8M unit' },
    ],
  },
  {
    group: 'Last 7 days',
    items: [
      { id: 'c6', title: 'Madinaty resale trend 2026' },
      { id: 'c7', title: 'North Coast — Marassi vs Hacienda' },
      { id: 'c8', title: 'CBE rate impact on installments' },
    ],
  },
];

/* ─── Message data shapes ───────────────────────────────────────── */

interface UserMessage {
  role: 'user';
  content: string;
}

interface SummaryCell {
  label: string;
  value: string;
  trend?: string;
  direction?: 'up' | 'down';
}

interface PropertyCard {
  name: string;
  loc: string;
  price: string;
  score: number | '—';
  beds: number;
  size: string;
  badges?: Array<{ label: string; tone?: 'accent' | 'default' }>;
  /** When true, the closing price renders as a masked italic placeholder. */
  priceMasked?: boolean;
}

interface ThinkingStep {
  title: string;
  meta: string;
}

interface UpgradeCTA {
  eyebrow: string;
  headline: string;
  body: string;
  skus: Array<{ price: string; label: string }>;
}

interface AiMessage {
  role: 'ai';
  thinking?: ThinkingStep[];
  thinkingHeader?: string;
  body?: React.ReactNode;
  summary?: SummaryCell[];
  properties?: PropertyCard[];
  /** Free-tier ammunition card. Render at the end of the AI bubble. */
  upgradeCTA?: UpgradeCTA;
  pending?: boolean;
}

type Message = UserMessage | AiMessage;

/* ─── Sample seed conversations ─────────────────────────────────── */

/** Paid demo — full AI reply with thinking, summary strip, lever-rich carousel. */
const PAID_SEED_MESSAGES: Message[] = [
  {
    role: 'user',
    content:
      "I'm looking at apartments in New Cairo around 8M EGP — 3+ bedrooms. What's the smart pick right now?",
  },
  {
    role: 'ai',
    thinkingHeader: 'Reasoning · 4 steps · 1.8s',
    thinking: [
      { title: 'Pull registry-verified listings in New Cairo, 7-9M EGP band', meta: '412 candidates' },
      { title: 'Filter to 3+ BR, delivered or off-plan with ≤2y delivery', meta: '38 candidates' },
      { title: 'Score against compound dev/resale gap + delivery track record', meta: '12 final' },
      { title: 'Cross-check CBE FX, inflation deflator, comparable closings (90d)', meta: 'high confidence' },
    ],
    body: (
      <>
        <p>
          Here&apos;s a snapshot of the <strong>New Cairo</strong> submarket in your budget. The
          market is up <strong>6.4% YoY</strong> in EGP terms, but inflation-adjusted real growth is
          closer to <strong>2.1%</strong>.
        </p>
        <p>
          Three units lead on a registry + price-gap basis. <em>Mivida Lake Residence</em> stands out
          on developer track record (Emaar Misr, 92% on-time delivery), while{' '}
          <em>Mountain View iCity</em> wins on resale liquidity in the last 90 days.
        </p>
      </>
    ),
    summary: [
      { label: 'Median /m²', value: '54.2K', trend: '↑ 6.4%', direction: 'up' },
      { label: 'Avg yield', value: '5.8%', trend: '↑ 0.3pp', direction: 'up' },
      { label: 'Time on market', value: '62d', trend: '↓ 9d', direction: 'down' },
    ],
    properties: [
      {
        name: 'Mivida — Lake Residence',
        loc: 'EMAAR Misr · New Cairo',
        price: '9.2M EGP',
        score: 91,
        beds: 3,
        size: '188m²',
        badges: [{ label: 'Registry verified', tone: 'accent' }],
      },
      {
        name: 'Hyde Park — Garden',
        loc: 'Hyde Park · 5th Settlement',
        price: '6.9M EGP',
        score: 82,
        beds: 3,
        size: '162m²',
        badges: [{ label: 'Below market', tone: 'accent' }],
      },
      {
        name: 'Mountain View iCity',
        loc: 'Mountain View · New Cairo',
        price: '8.4M EGP',
        score: 87,
        beds: 4,
        size: '195m²',
      },
    ],
  },
];

/** Free demo — fair-range teaser, ONE masked comp, upgrade CTA. */
const FREE_SEED_MESSAGES: Message[] = [
  {
    role: 'user',
    content:
      "I'm looking at apartments in New Cairo around 8M EGP — 3+ bedrooms. What's the smart pick right now?",
  },
  {
    role: 'ai',
    thinkingHeader: 'Quick scan · 1.1s',
    thinking: [
      { title: 'Pull registry-verified listings in New Cairo, 7-9M EGP band', meta: '412 candidates' },
      { title: 'Filter to 3+ BR + compute fair-value range', meta: '12 final' },
    ],
    body: (
      <>
        <p>
          The honest answer for <strong>New Cairo, 3BR, ~8M EGP</strong>: the fair range is{' '}
          <strong>6.9M – 9.2M EGP</strong>, median <strong>8.1M</strong>. You&apos;re inside the
          band, but the picks worth offering on differ by 200-400K once you account for delivery
          track record and resale liquidity.
        </p>
        <p>
          One reference comp closed in April near the median. <em>Free path shows the headline.</em>
          {' '}Unlock the comp table, lever breakdown, and the bilingual haggle script to act on it.
        </p>
      </>
    ),
    summary: [
      { label: 'Fair range', value: '6.9M – 9.2M EGP', trend: 'Median 8.1M', direction: 'up' },
    ],
    properties: [
      {
        name: 'Comparable closing · April 2026',
        loc: 'New Cairo · 3 BR · 188 m²',
        price: 'Locked',
        score: '—',
        beds: 3,
        size: '188m²',
        priceMasked: true,
        badges: [{ label: 'Premium unlocks 9 more', tone: 'accent' }],
      },
    ],
    upgradeCTA: {
      eyebrow: 'Unlock the full answer',
      headline: 'See every comp, every lever, every script.',
      body:
        'Premium opens the full 10-comp table, negotiation-lever breakdown (cash discount, broker commission, payment-plan markup), a bilingual haggle script you can read straight to the seller, and the interactive coach.',
      skus: [
        { price: 'EGP 99', label: 'This compound · 30 days' },
        { price: 'EGP 299/mo', label: 'All compounds · unlimited' },
      ],
    },
  },
];

function seedFor(tier: DemoTier): Message[] {
  return tier === 'free' ? FREE_SEED_MESSAGES : PAID_SEED_MESSAGES;
}

/* ─── Top-level page ────────────────────────────────────────────── */

export default function ChatPreviewPage() {
  const { user } = useAuth();
  const isAdmin = (user?.role ?? '').toLowerCase() === 'admin';

  const [lang, setLang] = useState<Lang>('en');
  const [theme, setTheme] = useState<Theme>('light');
  const [collapsed, setCollapsed] = useState(false);
  const [tier, setTier] = useState<DemoTier>('paid');
  const [messages, setMessages] = useState<Message[]>(() => seedFor('paid'));
  const [streaming, setStreaming] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const threadRef = useRef<HTMLDivElement>(null);

  const T = lang === 'ar' ? T_AR : T_EN;

  // Restore admin's demo-tier choice from localStorage on first mount.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem(DEMO_TIER_KEY);
    if (saved === 'free' || saved === 'paid') {
      setTier(saved);
      setMessages(seedFor(saved));
    }
  }, []);

  // Persist tier changes and re-seed the thread so the demo reflects the choice.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(DEMO_TIER_KEY, tier);
  }, [tier]);

  const switchTier = (next: DemoTier) => {
    if (next === tier) return;
    setTier(next);
    setMessages(seedFor(next));
  };

  // Apply theme/dir at the document level so reveals + ambient pick it up.
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    return () => {
      // Restore defaults when leaving the preview
      document.documentElement.removeAttribute('data-theme');
      document.documentElement.setAttribute('dir', 'ltr');
      document.documentElement.setAttribute('lang', 'en');
    };
  }, [theme, lang]);

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

  const send = (text: string) => {
    if (!text.trim() || streaming) return;
    const userMsg: UserMessage = { role: 'user', content: text };
    const pending: AiMessage = { role: 'ai', pending: true };
    setMessages((m) => [...m, userMsg, pending]);
    setStreaming(true);

    setTimeout(() => {
      // Reply mirrors the current demo tier — admins flipping the toggle
      // change what future replies look like too, not just the seed thread.
      const seed = seedFor(tier);
      const aiSeed = seed.find((m): m is AiMessage => m.role === 'ai');
      if (!aiSeed) {
        setStreaming(false);
        return;
      }
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { ...aiSeed, role: 'ai' };
        return copy;
      });
      setStreaming(false);
    }, 1600);
  };

  return (
    <div className="osool-chat-root">
      <div className="ambient" />
      <div className="shell" data-sidebar={collapsed ? 'collapsed' : 'expanded'}>
        <Sidebar T={T} collapsed={collapsed} lang={lang} />
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

          {messages.length === 0 ? (
            <>
              <EmptyState T={T} lang={lang} onPick={send} />
              <Composer T={T} isStreaming={streaming} onSend={send} onStop={() => setStreaming(false)} />
            </>
          ) : (
            <>
              <div className="thread" ref={threadRef} onScroll={onScroll}>
                <div className="thread-inner">
                  {messages.map((m, i) =>
                    m.role === 'user' ? (
                      <UserBubble key={i} content={m.content} />
                    ) : m.pending ? (
                      <Typing key={i} />
                    ) : (
                      <AiBubble key={i} msg={m} />
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
              <Composer T={T} isStreaming={streaming} onSend={send} onStop={() => setStreaming(false)} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}

/* ─── Sidebar ───────────────────────────────────────────────────── */

function Sidebar({ T, collapsed, lang }: { T: Translations; collapsed: boolean; lang: Lang }) {
  const [q, setQ] = useState('');
  const groupLabel = (g: Conversation['group']) =>
    lang === 'ar'
      ? g === 'Today'
        ? 'اليوم'
        : g === 'Yesterday'
          ? 'أمس'
          : 'آخر ٧ أيام'
      : g;

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <OsoolAvatar size={26} animated />
        </div>
        {!collapsed && <div className="brand-name">Osool</div>}
      </div>

      <button type="button" className="new-conv">
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
        {!collapsed &&
          CONVERSATIONS.map((group) => (
            <div key={group.group}>
              <div className="sb-group-label">{groupLabel(group.group)}</div>
              {group.items.map((c) => (
                <button
                  type="button"
                  key={c.id}
                  className={'sb-item' + (c.active ? ' active' : '')}
                >
                  <span className="sb-item-text">
                    {c.active && lang === 'ar' ? T.conv1Title : c.title}
                  </span>
                </button>
              ))}
            </div>
          ))}
      </div>

      <div className="profile">
        <div className="avatar-circle">M</div>
        {!collapsed && (
          <div className="profile-text">
            <div className="profile-name">{lang === 'ar' ? 'مصطفى' : 'Mustafa A.'}</div>
            <div className="profile-mail">{T.yourPlan}</div>
          </div>
        )}
      </div>
    </aside>
  );
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
        <b>{lang === 'ar' ? T.conv1Title : 'Villas in New Cairo under 10M'}</b>
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

function AiBubble({ msg }: { msg: AiMessage }) {
  const [thinkingOpen, setThinkingOpen] = useState(false);

  return (
    <div className="msg-ai">
      <div className="ai-label">
        <span className="ai-label-mark">
          <OsoolAvatar size={20} animated />
        </span>
        <b>Osool</b>
      </div>

      {msg.thinking && msg.thinkingHeader && (
        <div>
          <button
            type="button"
            className="thinking-head"
            aria-expanded={thinkingOpen}
            onClick={() => setThinkingOpen((v) => !v)}
          >
            {msg.thinkingHeader}
            <IconChevDown size={12} className="chev" />
          </button>
          {thinkingOpen && (
            <div className="thinking-body">
              {msg.thinking.map((s, i) => (
                <div key={i} className="thinking-step">
                  <span>{s.title}</span>
                  <span className="meta">{s.meta}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="ai-body">
        {msg.body}

        {msg.summary && (
          <div className="summary-strip">
            {msg.summary.map((cell, i) => (
              <div key={i} className="summary-cell">
                <div className="summary-label">{cell.label}</div>
                <div className="summary-row">
                  <span className="summary-value">{cell.value}</span>
                  {cell.trend && (
                    <span className={'summary-trend ' + (cell.direction ?? '')}>{cell.trend}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {msg.properties && (
          <>
            <div className="section-label">
              {msg.properties.length === 1 ? 'Reference comp' : 'Top 3 picks'}
            </div>
            <div className="carousel-shell">
              <div className="carousel">
                {msg.properties.map((p) => (
                  <article key={p.name} className="prop-card">
                    <div className="prop-img">
                      <div className="prop-badges">
                        {(p.badges ?? []).map((b) => (
                          <span key={b.label} className={'badge ' + (b.tone ?? '')}>
                            {b.label}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="prop-body">
                      <h5 className="prop-name">{p.name}</h5>
                      <div className="prop-loc">{p.loc}</div>
                      <div className="prop-row1">
                        <span className={'prop-price' + (p.priceMasked ? ' masked' : '')}>
                          {p.priceMasked ? '— locked —' : p.price}
                        </span>
                        <span className="prop-score-num">
                          {p.score === '—' ? <b>—</b> : <b>{p.score}</b>}
                        </span>
                      </div>
                      <div className="prop-specs">
                        <span>{p.beds} BR</span>
                        <span>·</span>
                        <span>{p.size}</span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </>
        )}

        {msg.upgradeCTA && (
          <div className="upgrade-cta">
            <div className="upgrade-cta-head">
              <span className="upgrade-cta-eyebrow">{msg.upgradeCTA.eyebrow}</span>
            </div>
            <h4>{msg.upgradeCTA.headline}</h4>
            <p>{msg.upgradeCTA.body}</p>
            <div className="upgrade-cta-skus">
              {msg.upgradeCTA.skus.map((sku) => (
                <button key={sku.price} type="button" className="upgrade-sku">
                  <span className="upgrade-sku-price">{sku.price}</span>
                  <span className="upgrade-sku-label">{sku.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Typing() {
  return (
    <div className="msg-ai">
      <div className="ai-label">
        <span className="ai-label-mark">
          <OsoolAvatar size={20} animated state="thinking" />
        </span>
        <b>Osool</b>
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
