'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

import OsoolAvatar from '@/components/osool/OsoolAvatar';
import OsoolNav from '@/components/osool/OsoolNav';
import OsoolFooter from '@/components/osool/OsoolFooter';
import ArchFrame from '@/components/osool/ArchFrame';
import Mashrabiya from '@/components/osool/Mashrabiya';
import { useAuth } from '@/contexts/AuthContext';
import {
  IconHome,
  IconPaperclip,
  IconMic,
  IconSpark,
  IconUp,
} from '@/components/osool/Icons';

/**
 * Osool — landing page.
 * Editorial + Cairene direction per DESIGN.md (2026-05-27 refresh).
 * Bilingual stacked hero (Newsreader italic + Cairo Display at 60%),
 * dossier-block proof sections instead of icon-grid pillars, Mashrabiya
 * watermark on the chat-preview section, Eastern-Arabic-numeral stat
 * accent in the hero, terracotta + Nile + ochre on warm paper.
 *
 * Copy rule (2026-06-19 honesty pass): every claim maps to a shipping
 * capability or a clearly-labelled beta statement. No deal counts, no
 * verified registry, no escrow, no contract feature, no accuracy figure,
 * no developer partnerships — none of those exist yet. Where Osool compares
 * prices it compares against what similar units are *listed* at.
 */
export default function LandingPage() {
  useReveal();

  return (
    <div className="osool-themed" style={{ background: 'var(--osool-bg)', color: 'var(--osool-text)' }}>
      <OsoolNav />
      <main>
        <Hero />
        <Pillars />
        <ChatPreview />
        <HowItWorks />
        <Numbers />
        <Developers />
        <ClosingCTA />
      </main>
      <OsoolFooter />
    </div>
  );
}

/* ─── Reveal-on-scroll hook ──────────────────────────────────────── */
function useReveal() {
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('in');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -60px 0px' },
    );
    document.querySelectorAll('.osool-reveal').forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, []);
}

/* ─── HERO ───────────────────────────────────────────────────────── */
function Hero() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [q, setQ] = useState('');

  const go = () => {
    const prompt = q.trim();
    // Logged-in users go straight to the chat with the prompt in the URL.
    // Logged-out users get their prompt stashed in localStorage and are
    // sent to signup. /chat re-submits the prompt after auth succeeds.
    if (!isAuthenticated) {
      if (prompt && typeof window !== 'undefined') {
        try {
          window.localStorage.setItem('osool:pending_chat_prompt', prompt);
        } catch {
          // localStorage may be unavailable (private mode); fall through.
        }
      }
      router.push('/signup?next=' + encodeURIComponent('/chat' + (prompt ? `?q=${encodeURIComponent(prompt)}` : '')));
      return;
    }
    const url = '/chat' + (prompt ? `?q=${encodeURIComponent(prompt)}` : '');
    router.push(url);
  };

  const chips: Array<{ t: string; Icon: typeof IconHome }> = [
    { t: 'Show apartments in New Cairo under 8M', Icon: IconHome },
    { t: 'Is 8.4M fair for a 3-bedroom in Sheikh Zayed?', Icon: IconSpark },
    { t: 'What are similar units in 5th Settlement listed at?', Icon: IconHome },
  ];

  return (
    <section className="osool-hero">
      <div className="osool-container">
        <div className="osool-hero-mark">
          <OsoolAvatar size={88} animated />
        </div>

        {/* Eyebrow — Eastern Arabic numerals as the page's single deliberate
            cultural marker. The number is true: Osool is in private beta in
            two neighbourhoods. */}
        <span className="osool-hero-eyebrow">
          <span className="osool-hero-eyebrow-dot" />
          <span className="osool-numeral-ar" aria-label="Two neighbourhoods">٢</span>
          <span style={{ marginInlineStart: 8 }}>neighbourhoods · private beta in Cairo</span>
        </span>

        {/* Bilingual stacked headline — Latin on top (sells to global
            investors), Arabic sibling below at 60% (signs the page as
            Cairo-native to Egyptian buyers). */}
        <div className="osool-bilingual">
          <h1>
            The honest way to <em>buy property</em> in Egypt.
          </h1>
          <p className="osool-display-ar" lang="ar">الطريقة الصادقة عشان تشتري عقار في مصر.</p>
        </div>

        <p>
          Ask about any property in Egypt, in Arabic or English. Osool compares the
          asking price against what similar units in the area are listed at, and tells
          you plainly whether it makes sense. No inflated promises, no numbers we
          can&apos;t stand behind.
        </p>

        {/* Signature shape: the composer sits inside an arch-top frame,
            echoing the OsoolAvatar doorway. Reserve this shape for
            high-attention surfaces only. */}
        <ArchFrame
          outline
          style={{
            maxWidth: 620,
            margin: '0 auto',
            padding: 0,
            background: 'transparent',
            border: 'none',
            overflow: 'visible',
          }}
        >
          <div className="osool-composer" style={{ marginTop: 12 }}>
            <span className="osool-ico">
              <IconPaperclip size={17} />
            </span>
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && go()}
              placeholder="Ask Osool about any property in Egypt…"
            />
            <span className="osool-ico">
              <IconMic size={16} />
            </span>
            <button type="button" className="osool-send" onClick={go} aria-label="Send">
              <IconUp size={15} />
            </button>
          </div>
        </ArchFrame>

        <div className="osool-hero-chips">
          {chips.map((c) => (
            <button key={c.t} type="button" className="osool-hero-chip" onClick={() => setQ(c.t)}>
              <c.Icon size={12} /> {c.t}
            </button>
          ))}
        </div>

        <div className="osool-hero-trust">
          <span className="osool-nile-pill">Prices in EGP</span>
          <span className="osool-nile-pill">Arabic &amp; English</span>
          <span className="osool-nile-pill">Built in Cairo, for Egypt</span>
          <span className="osool-nile-pill">Private beta</span>
        </div>
      </div>
    </section>
  );
}

/* ─── DOSSIERS (was: icon-grid Pillars) ─────────────────────────── */
function Pillars() {
  const items: Array<{
    title: string;
    body: string;
    number: string;
    numberLabel: string;
  }> = [
    {
      title: 'An honest read on price',
      body: 'Tell Osool the unit and the asking price. It compares against what similar units in the area are listed at, and tells you where this one sits — high, fair, or worth a second look. When the data is thin, it says so instead of inventing confidence.',
      number: 'Ranges',
      numberLabel: 'not false decimals',
    },
    {
      title: 'Speaks Egyptian',
      body: 'Ask in Egyptian Arabic or English — switch mid-sentence if you like. Prices are in EGP, the areas are the ones you actually search, and the market it knows is the Egyptian one. Not a foreign tool with Cairo bolted on.',
      number: 'EGP',
      numberLabel: 'native, not translated',
    },
    {
      title: 'Refuses to oversell',
      body: "Osool won't call a unit a once-in-a-lifetime deal, and it won't quote a number it can't trace. If it doesn't know, it tells you it doesn't know. That restraint is the product.",
      number: '0',
      numberLabel: 'made-up numbers',
    },
  ];

  return (
    <section className="osool-section" id="product">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal">
          <div>
            <div className="osool-eyebrow">What Osool actually does</div>
            <h2 className="osool-section-title">
              Three <em>honest</em> reasons to ask Osool first.
            </h2>
          </div>
          <p className="osool-section-lead">
            Property listings in Egypt are written to sell, not to inform. Osool gives
            you the other side of the conversation — straight, in your language, before
            you put money down.
          </p>
        </div>

        {/* Newspaper-rule dossier blocks. Each column reads like a print
            feature: serif title, body paragraph, hard number footer.
            Replaces the generic icon-in-circle SaaS grid pattern. */}
        <div className="osool-dossiers osool-reveal">
          {items.map((it) => (
            <article className="osool-dossier" key={it.title}>
              <h3>{it.title}</h3>
              <p>{it.body}</p>
              <div className="osool-dossier-number">
                <b>{it.number}</b>
                <span>{it.numberLabel}</span>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── CHAT PREVIEW ───────────────────────────────────────────────── */
function ChatPreview() {
  return (
    <section
      className="osool-section"
      id="trust"
      style={{ paddingTop: 32, position: 'relative', overflow: 'hidden' }}
    >
      {/* Mashrabiya watermark — Cairo geometric latticework at 5% opacity.
          Quiet cultural signature behind the chat preview. */}
      <Mashrabiya tile={72} />
      <div className="osool-container" style={{ position: 'relative', zIndex: 1 }}>
        <div className="osool-section-head osool-reveal">
          <div>
            <div className="osool-eyebrow">See how it answers</div>
            <h2 className="osool-section-title">
              A <em>straight</em> answer, in the time it takes to ask.
            </h2>
          </div>
          <p className="osool-section-lead">
            Real questions in plain language. When Osool gives you a number it tells you
            where it came from — and when the data is thin, it says that too.
          </p>
        </div>

        <div className="osool-preview osool-reveal">
          <div className="osool-preview-bar">
            <i />
            <i />
            <i />
            <span className="osool-preview-url">osool.eg/chat</span>
          </div>
          <div className="osool-preview-body">
            <aside className="osool-preview-side">
              <div className="osool-preview-label">Today</div>
              <div className="osool-preview-item active">Apartments in New Cairo under 8M</div>
              <div className="osool-preview-item">Sheikh Zayed vs New Cairo — price/m²</div>
              <div className="osool-preview-label">Earlier</div>
              <div className="osool-preview-item">Is this asking price fair?</div>
              <div className="osool-preview-item">3-bed near 90th Street</div>
            </aside>
            <div className="osool-preview-main">
              <div className="osool-preview-thread">
                <div className="osool-pv-user">
                  Looking at 3-bedroom apartments in New Cairo around 8M EGP. Where
                  should I be looking, and is 8M reasonable?
                </div>
                <div className="osool-pv-ai">
                  <div className="osool-pv-ai-label">
                    <OsoolAvatar size={20} animated />
                    <b>Osool</b>
                  </div>
                  <div className="osool-pv-ai-think">Comparing similar listings ▾</div>
                  <p>
                    Around <strong>8M</strong> in <strong>New Cairo</strong>, three-bedroom
                    apartments are realistic in several of the larger compounds, though
                    finished, ready-to-move units sit at the top of that budget. Asking
                    prices vary a lot by compound, finish, and delivery stage — so 8M is
                    reasonable for some and a stretch for others. Tell me the specific unit
                    and I&apos;ll give you a sharper read.
                  </p>
                  <div className="osool-pv-summary">
                    <div>
                      <div className="lbl">Budget</div>
                      <div className="val">~8M EGP</div>
                    </div>
                    <div>
                      <div className="lbl">Area</div>
                      <div className="val">New Cairo</div>
                    </div>
                    <div>
                      <div className="lbl">Read</div>
                      <div className="val">Reasonable, unit-dependent</div>
                    </div>
                  </div>
                  <div className="osool-pv-cards">
                    <PreviewCard title="Compound A" loc="New Cairo" price="from ~9M" note="Above your budget — finished units" />
                    <PreviewCard title="Compound B" loc="5th Settlement" price="~7M" note="Within budget, varies by phase" />
                    <PreviewCard title="Compound C" loc="New Cairo" price="~8M" note="Right at your number" />
                  </div>
                  <p style={{ fontSize: 11.5, color: 'var(--osool-muted)', marginTop: 10 }}>
                    Illustrative example — not live listings or quoted prices.
                  </p>
                </div>
              </div>
              <div className="osool-preview-composer">
                <div className="osool-preview-composer-box">
                  <span style={{ color: 'var(--osool-muted)', fontSize: 13.5, flex: 1 }}>
                    Ask about an area, a price, or a specific unit…
                  </span>
                  <button type="button" className="osool-send" style={{ width: 28, height: 28 }} aria-label="Send">
                    <IconUp size={13} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function PreviewCard({
  title,
  loc,
  price,
  note,
}: {
  title: string;
  loc: string;
  price: string;
  note: string;
}) {
  return (
    <div className="osool-pv-card">
      <div className="osool-pv-card-img" />
      <div className="osool-pv-card-body">
        <h5>{title}</h5>
        <div className="osool-pv-card-loc">{loc}</div>
        <div className="osool-pv-card-row">
          <span className="osool-pv-card-price">{price}</span>
          <span
            className="osool-pv-card-score"
            style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}
          >
            Illustrative
          </span>
        </div>
        <div className="osool-pv-card-loc" style={{ marginTop: 4 }}>{note}</div>
      </div>
    </div>
  );
}

/* ─── HOW IT WORKS ───────────────────────────────────────────────── */
function HowItWorks() {
  const steps = [
    {
      n: '01',
      t: 'Ask in your own words',
      b: "Budget, area, bedrooms — or paste a listing you're looking at. Type it in Arabic or English, whichever's easier.",
    },
    {
      n: '02',
      t: 'Get a straight read',
      b: 'Osool tells you where the asking price sits against similar units nearby, and what to watch for — in plain language, with the reasoning shown, not hidden.',
    },
    {
      n: '03',
      t: 'Decide with your eyes open',
      b: "Take the read into your own negotiation. Osool's job is to make sure you walk in knowing what's fair — the deal stays yours to make.",
    },
  ];

  return (
    <section className="osool-section tight" id="how">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal">
          <div>
            <div className="osool-eyebrow">How it works</div>
            <h2 className="osool-section-title">
              From <em>&ldquo;is this worth it&rdquo;</em> to a clear answer.
            </h2>
          </div>
        </div>
        <div className="osool-steps">
          {steps.map((s, i) => (
            <div
              className="osool-step osool-reveal"
              key={s.n}
              style={{ transitionDelay: `${i * 0.08}s` }}
            >
              <div className="osool-step-num">
                <b>{s.n}</b>
                <span>Step</span>
              </div>
              <h4>{s.t}</h4>
              <p>{s.b}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── NUMBERS BAND → anti-numbers statement of principle ─────────── */
function Numbers() {
  const stats = [
    { val: 'EGP', lbl: 'Every price, in pounds' },
    { val: 'AR/EN', lbl: 'Every question, either language' },
    { val: '2', lbl: 'Neighbourhoods — New Cairo & Sheikh Zayed, to start' },
    { val: '0', lbl: 'Fake numbers — ever' },
  ];

  return (
    <section className="osool-section dark">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal" style={{ marginBottom: 32 }}>
          <div>
            <div className="osool-eyebrow">Why we don&apos;t show a wall of numbers</div>
            <h2 className="osool-section-title">
              Most property sites lead with numbers. We won&apos;t show you ones we made up.
            </h2>
          </div>
          <p className="osool-section-lead">
            We&apos;re a private beta. We haven&apos;t closed deals, so we won&apos;t claim a
            deal count. We don&apos;t run a verified registry, so we won&apos;t pretend to.
            When Osool gives you a number, it&apos;s because the data is real — and when it
            isn&apos;t, we say nothing.
          </p>
        </div>
        <div className="osool-numbers osool-reveal">
          {stats.map((s) => (
            <div className="osool-number" key={s.lbl}>
              <div className="val">{s.val}</div>
              <div className="lbl">{s.lbl}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── DEVELOPERS STRIP ───────────────────────────────────────────── */
function Developers() {
  const devs = [
    'EMAAR Misr',
    'Mountain View',
    'Hyde Park',
    'Talaat Moustafa',
    'Palm Hills',
    'SODIC',
    'Madinaty',
  ];
  return (
    <section className="osool-devs-band" id="developers">
      <div className="osool-container">
        <div className="osool-devs-label">Osool reads public listings across Egypt&apos;s major compounds</div>
        <div style={{ fontSize: 11.5, color: 'var(--osool-muted)', marginTop: 6 }}>
          Public data, not partnerships.
        </div>
        <div className="osool-devs osool-reveal">
          {devs.map((d) => (
            <span key={d} className="osool-dev">
              {d}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── CLOSING CTA ────────────────────────────────────────────────── */
function ClosingCTA() {
  return (
    <section className="osool-cta-final">
      <div className="osool-container">
        <div className="osool-hero-mark" style={{ width: 64, height: 64, marginBottom: 18 }}>
          <OsoolAvatar size={56} animated />
        </div>
        <h2>Start with one honest question.</h2>
        <p>
          Ask about any property in Egypt, in Arabic or English. Osool is in private beta
          in New Cairo and Sheikh Zayed — invite-only for now.
        </p>
        <Link
          href="/signup"
          className="osool-btn osool-btn-primary"
          style={{ padding: '12px 24px', fontSize: 14.5 }}
        >
          Request an invite <IconUp size={14} style={{ transform: 'rotate(45deg)' }} />
        </Link>
        <div className="osool-cta-secondary">
          Or <Link href="/pricing">see where Osool is headed</Link>
        </div>
      </div>
    </section>
  );
}
