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
  IconShield,
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
    { t: 'Show villas in New Cairo under 10M', Icon: IconHome },
    { t: 'Is 8.4M EGP fair for a Mountain View villa?', Icon: IconSpark },
    { t: 'Review the standard Mivida contract', Icon: IconShield },
  ];

  return (
    <section className="osool-hero">
      <div className="osool-container">
        <div className="osool-hero-mark">
          <OsoolAvatar size={88} animated />
        </div>

        {/* Operator-energy eyebrow stat — Eastern Arabic numerals as the
            page's single deliberate cultural marker. The Latin gloss
            keeps non-Arabic readers oriented. */}
        <span className="osool-hero-eyebrow">
          <span className="osool-hero-eyebrow-dot" />
          <span className="osool-numeral-ar" aria-label="412 deals closed">٤١٢</span>
          <span style={{ marginInlineStart: 8 }}>deals closed · live in Cairo</span>
        </span>

        {/* Bilingual stacked headline — Latin on top (sells to global
            investors), Arabic sibling below at 60% (signs the page as
            Cairo-native to Egyptian buyers). */}
        <div className="osool-bilingual">
          <h1>
            The honest way to <em>buy property</em> in Egypt.
          </h1>
          <p className="osool-display-ar" lang="ar">الطريقة الصادقة لشراء العقار في مصر.</p>
        </div>

        <p>
          Verified listings, AI valuation, and contract checks grounded in Egyptian
          property law. All in one conversation.
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
              placeholder="Ask Osool anything about real estate in Egypt…"
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
          <span className="osool-nile-pill">CBE Law 194 compliant</span>
          <span className="osool-nile-pill">Civil Code 131</span>
          <span className="osool-nile-pill">FRA 125-ready</span>
          <span className="osool-nile-pill">InstaPay · Fawry escrow</span>
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
      title: 'Verified registry',
      body: 'Every listing is checked against the title registry. Reserved units lock instantly. No double-sells, no surprises at closing.',
      number: '0',
      numberLabel: 'Double-sells, since launch',
    },
    {
      title: 'AI valuation',
      body: 'Fair-price model trained on 412 verified Egyptian transactions, CBE corridor rates, and inflation-adjusted real growth. The number AND the why.',
      number: '±2.4%',
      numberLabel: 'Median accuracy',
    },
    {
      title: 'Contract check',
      body: 'Purchase agreements scanned against Civil Code 131 in seconds. Arbitration venue, escalator clauses, delivery penalties — flagged before you sign.',
      number: '247',
      numberLabel: 'Clauses reviewed per contract',
    },
  ];

  return (
    <section className="osool-section" id="product">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal">
          <div>
            <div className="osool-eyebrow">The product</div>
            <h2 className="osool-section-title">
              Three reasons Egyptian buyers <em>finally</em> trust a listings site.
            </h2>
          </div>
          <p className="osool-section-lead">
            The Egyptian market loses billions a year to unclear titles, contract traps,
            and price inflation. Osool fixes all three — out in the open.
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
            <div className="osool-eyebrow">Watch it work</div>
            <h2 className="osool-section-title">
              <em>Investor-grade</em> answers, in the time it takes to ask.
            </h2>
          </div>
          <p className="osool-section-lead">
            Real questions, real data. Every number Osool gives you traces back to the
            registry, the developer&apos;s disclosure, or the central bank.
          </p>
        </div>

        <div className="osool-preview osool-reveal">
          <div className="osool-preview-bar">
            <i />
            <i />
            <i />
            <span className="osool-preview-url">osool.eg/chat/villas-new-cairo</span>
          </div>
          <div className="osool-preview-body">
            <aside className="osool-preview-side">
              <div className="osool-preview-label">Today</div>
              <div className="osool-preview-item active">Villas in New Cairo under 10M</div>
              <div className="osool-preview-item">Hyde Park vs Mivida — ROI?</div>
              <div className="osool-preview-label">Yesterday</div>
              <div className="osool-preview-item">Mountain View clause 14</div>
              <div className="osool-preview-item">Fawry escrow for 8M unit</div>
            </aside>
            <div className="osool-preview-main">
              <div className="osool-preview-thread">
                <div className="osool-pv-user">
                  I&apos;m looking at apartments in New Cairo around 8M EGP — 3+ bedrooms.
                  What&apos;s the smart pick right now?
                </div>
                <div className="osool-pv-ai">
                  <div className="osool-pv-ai-label">
                    <OsoolAvatar size={20} animated />
                    <b>Osool</b>
                  </div>
                  <div className="osool-pv-ai-think">Reasoning · 4 steps · 1.8s ▾</div>
                  <p>
                    Here&apos;s a snapshot of the <strong>New Cairo</strong> submarket in
                    your budget. The market is up <strong>6.4% YoY</strong> in EGP terms,
                    but inflation-adjusted real growth is closer to{' '}
                    <strong>2.1%</strong>.
                  </p>
                  <div className="osool-pv-summary">
                    <div>
                      <div className="lbl">Median /m²</div>
                      <div className="val">
                        54.2K <span className="trend">↑ 6.4%</span>
                      </div>
                    </div>
                    <div>
                      <div className="lbl">Avg yield</div>
                      <div className="val">
                        5.8% <span className="trend">↑ 0.3pp</span>
                      </div>
                    </div>
                    <div>
                      <div className="lbl">Time on market</div>
                      <div className="val">
                        62d <span className="trend">↓ 9d</span>
                      </div>
                    </div>
                  </div>
                  <div className="osool-pv-cards">
                    <PreviewCard title="Mivida — Lake Residence" loc="EMAAR Misr · New Cairo" price="9.2M EGP" score="91" />
                    <PreviewCard title="Hyde Park — Garden" loc="Hyde Park · 5th Settlement" price="6.9M EGP" score="82" />
                    <PreviewCard title="Mountain View iCity" loc="Mountain View · NC" price="8.4M EGP" score="87" />
                  </div>
                </div>
              </div>
              <div className="osool-preview-composer">
                <div className="osool-preview-composer-box">
                  <span style={{ color: 'var(--osool-muted)', fontSize: 13.5, flex: 1 }}>
                    Ask about properties, market trends, contracts…
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
  score,
}: {
  title: string;
  loc: string;
  price: string;
  score: string;
}) {
  return (
    <div className="osool-pv-card">
      <div className="osool-pv-card-img" />
      <div className="osool-pv-card-body">
        <h5>{title}</h5>
        <div className="osool-pv-card-loc">{loc}</div>
        <div className="osool-pv-card-row">
          <span className="osool-pv-card-price">{price}</span>
          <span className="osool-pv-card-score">
            <b>{score}</b>/100
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── HOW IT WORKS ───────────────────────────────────────────────── */
function HowItWorks() {
  const steps = [
    {
      n: '01',
      t: 'Tell Osool what you need',
      b: 'Budget, neighborhood, bedrooms — or just paste a listing link. Speak or type, in Arabic or English.',
    },
    {
      n: '02',
      t: 'Get verified picks + the math',
      b: 'Osool returns registry-checked units with fair-price valuations and 5-year ROI grounded in actual transactions.',
    },
    {
      n: '03',
      t: 'Reserve safely in EGP',
      b: "When you're ready, reserve via InstaPay or Fawry escrow under CBE Law 194. Funds release on closing — never before.",
    },
  ];

  return (
    <section className="osool-section tight" id="how">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal">
          <div>
            <div className="osool-eyebrow">How it works</div>
            <h2 className="osool-section-title">
              From <em>&ldquo;what&apos;s worth buying&rdquo;</em> to keys in hand.
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

/* ─── NUMBERS BAND ───────────────────────────────────────────────── */
function Numbers() {
  const stats = [
    { val: '412', lbl: 'Verified units across New Cairo & North Coast' },
    { val: '0', lbl: 'Double-sells, ever' },
    { val: '1.8s', lbl: 'Average AI valuation time' },
    { val: 'EGP', lbl: 'Every transaction · CBE Law 194 compliant' },
  ];

  return (
    <section className="osool-section dark">
      <div className="osool-container">
        <div className="osool-section-head osool-reveal" style={{ marginBottom: 32 }}>
          <div>
            <div className="osool-eyebrow">The numbers</div>
            <h2 className="osool-section-title">Built for trust. Measured in receipts.</h2>
          </div>
          <p className="osool-section-lead">
            We publish what most platforms hide. Verification counts, fraud counts, and
            our own valuation accuracy — updated every day.
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
        <div className="osool-devs-label">Trusted listings from Egypt&apos;s leading developers</div>
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
        <h2>Start your search tonight.</h2>
        <p>Three free questions. No account needed. Speak Arabic or English.</p>
        <Link
          href="/chat"
          className="osool-btn osool-btn-primary"
          style={{ padding: '12px 24px', fontSize: 14.5 }}
        >
          Open Osool <IconUp size={14} style={{ transform: 'rotate(45deg)' }} />
        </Link>
        <div className="osool-cta-secondary">
          Or <Link href="/pricing">see Osool Pro plans</Link> · <Link href="/contact">talk to a licensed advisor</Link> · Available 9 AM–11 PM Cairo time
        </div>
      </div>
    </section>
  );
}
