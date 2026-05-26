'use client';

import { useEffect, useRef, useState } from 'react';

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
 * Osool Chat — visual prototype.
 * Port of Osool Chat.html from the claude.ai/design handoff.
 *
 * Live at /chat-preview. The production chat at /chat (AgentInterface)
 * stays untouched until the team decides to swap. This route is a
 * stand-alone interactive design — sample messages, fake AI reply on send.
 */

type Lang = 'en' | 'ar';
type Theme = 'light' | 'dark';
type DemoState = 'empty' | 'results';

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
  score: number;
  beds: number;
  size: string;
  badges?: Array<{ label: string; tone?: 'accent' | 'default' }>;
}

interface ThinkingStep {
  title: string;
  meta: string;
}

interface AiMessage {
  role: 'ai';
  thinking?: ThinkingStep[];
  thinkingHeader?: string;
  body?: React.ReactNode;
  summary?: SummaryCell[];
  properties?: PropertyCard[];
  pending?: boolean;
}

type Message = UserMessage | AiMessage;

/* ─── Sample seed conversation ──────────────────────────────────── */

const SEED_MESSAGES: Message[] = [
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

/* ─── Top-level page ────────────────────────────────────────────── */

export default function ChatPreviewPage() {
  const [lang, setLang] = useState<Lang>('en');
  const [theme, setTheme] = useState<Theme>('light');
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState<Message[]>(SEED_MESSAGES);
  const [streaming, setStreaming] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  const threadRef = useRef<HTMLDivElement>(null);

  const T = lang === 'ar' ? T_AR : T_EN;

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
      const reply = {
        ...SEED_MESSAGES[1],
        role: 'ai' as const,
      };
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = reply;
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
  onToggleSidebar,
  onToggleLang,
  onToggleTheme,
}: {
  T: Translations;
  theme: Theme;
  lang: Lang;
  onToggleSidebar: () => void;
  onToggleLang: () => void;
  onToggleTheme: () => void;
}) {
  return (
    <header className="topbar">
      <button type="button" className="icon-btn" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        <IconPanelLeft size={16} />
      </button>
      <div className="topbar-title">
        <b>{lang === 'ar' ? T.conv1Title : 'Villas in New Cairo under 10M'}</b>
      </div>
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
            <div className="section-label">Top 3 picks</div>
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
                        <span className="prop-price">{p.price}</span>
                        <span className="prop-score-num"><b>{p.score}</b></span>
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
