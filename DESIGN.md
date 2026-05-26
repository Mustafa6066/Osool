# Design System — Osool (أصول)

> Last refreshed: 2026-05-27 (Editorial + Cairene direction).
> Always read this before making any visual or UI decision in this repo.

## Product Context

- **What this is:** AI-native Egyptian real-estate broker. Closes deals end-to-end via chat. Not a listings marketplace; not a property-search tool. A services company that uses AI to do the work humans used to do badly.
- **Who it's for:** Egyptian property buyers (primary). Investors evaluating Osool against YC's services-as-AI thesis (secondary).
- **Space / industry:** Real estate; Cairo and the broader Egyptian market; services-as-AI category.
- **Project type:** Web app (chat-driven) + marketing/fundraising landing.

## Memorable Thing

> **"This is built for me, the Egyptian buyer."**

Every typography, color, and layout choice serves this. The product is services-as-AI; the emotional payload is cultural belonging.

## Aesthetic Direction

- **Direction:** Editorial + Cairene
- **Decoration level:** Intentional — Egyptian architectural motifs (arch, mashrabiya), used with restraint
- **Mood:** Confident, grounded, place-specific. Slow-feeling but not soft. Reads as a Cairo company that knows the market, not a global SaaS landing here.
- **Reference vibe:** The Economist meets a high-taste Cairo art studio.

## Typography

- **Display:** Newsreader (italic, 400-500) for Latin; Cairo Display (700) for Arabic. Loaded via Google Fonts in `app/layout.tsx`.
- **Body:** Inter (400-500) Latin; Cairo (400-500) Arabic.
- **Data / numbers:** Inter + Cairo with `font-feature-settings: "tnum"`.
- **Stylistic numerals:** Eastern Arabic (`١٢٣٤٥٦٧٨٩٠`) used as a deliberate cultural accent in select callouts (max one per page). Functional digits stay Latin for global readability.
- **Bilingual hero pattern:** Latin headline in Newsreader italic display; Arabic mirror in Cairo Display 700 below at ~60% opacity (`.osool-bilingual` + `.osool-display-ar` in `osool-theme.css`).

### Scale

| Token | Value | Use |
|---|---|---|
| display | `clamp(48px, 6.5vw, 84px)` | Hero |
| h1 | `clamp(36px, 4.5vw, 56px)` | Section opener |
| h2 | `clamp(28px, 3.2vw, 40px)` | Sub-section |
| h3 | 22px | Card / pillar title |
| body-lg | 17px | Hero subhead, section lead |
| body | 15.5px | Default |
| body-sm | 13.5px | Caption, meta |
| micro | 11.5px | Label, eyebrow, legal |

## Color

**Approach:** Restrained warm — terracotta is the keystone, Nile blue anchors trust, ochre is a rare accent.

### Light theme (`osool-theme.css :root`)

| Token | Value | Role |
|---|---|---|
| `--osool-bg` | `#FCFAF6` | Warm paper background (replaces stark white) |
| `--osool-surface` | `#FFFFFF` | Cards, panels — crisp against the warm bg |
| `--osool-surface-2` | `#F4F1EA` | Subtle panel/well |
| `--osool-text` | `#0E0E10` | Near-black, high contrast |
| `--osool-muted` | `#6E6E73` | Secondary text |
| `--osool-border` | `#E8E2D5` | Paper edge, warmer than metal |
| `--osool-accent` | `#C96442` | **Terracotta** — Egyptian clay; the keystone. Every CTA. |
| `--osool-nile` | `#1B4869` | **Nile blue** — trust + verification badges only |
| `--osool-ochre` | `#C9A66B` | **Egyptian gold** — rarest, stylistic accents only |

### Dark theme (`[data-theme="dark"]`)

Warm near-black `#0B0A08`, lifted terracotta `#D87555`, lifted Nile `#4A7FA8`, lifted ochre `#D4B47A`.

### Semantic

- **success** → terracotta (in this brand, success is the deal closing)
- **warning** → ochre
- **error** → muted red `#A0463D` (warm, on-palette)

### Palette logic

- Terracotta carries every CTA, accent, and "look here" element. Confidence color.
- Nile blue carries trust signals only: verification badges, CBE/FRA compliance callouts. Used sparingly, never adjacent to terracotta CTAs.
- Ochre is the rarest — one decorative element per page. Egyptian-gold quality without kitsch.
- Warm paper background is the silent rebellion against generic-tech bleached white. The page should feel like print.

## Spacing

- **Base unit:** 4px
- **Density:** Comfortable. Editorial pages reward whitespace.
- **Scale:** `2xs(4) xs(8) sm(12) md(16) lg(24) xl(32) 2xl(48) 3xl(64) 4xl(96) 5xl(140)`
- **Section vertical rhythm:** 88px (compact) / 120px (default) / 140px (hero)

## Layout

- **Approach:** Creative-editorial. Asymmetric grids, type-as-image, **dossier blocks** (newspaper-column) instead of icon grids.
- **Max content width:** 1180px
- **Border radius scale:**
  - `sm` 6px (form fields, small chips)
  - `md` 12px (default cards)
  - `lg` 18px (large panels)
  - `arch-top` 24px top corners + 0 bottom — **signature shape**
  - `full` 9999px (pills)

### Hero composition

```
[avatar — arch mascot, animated]
[bilingual stacked headline]
  Latin (Newsreader italic display)
  Arabic (Cairo Display 700, 60% opacity)
[lead paragraph]
[arch-top composer / single CTA]
[chip suggestions]
[Nile-blue compliance pills row]
```

### Section composition

Newspaper-column **dossier blocks** (`.osool-dossier` in `osool-theme.css`) separated by 1px terracotta hairline rules instead of card borders. Each block:

1. Serif italic title (Newsreader)
2. Body paragraph (Inter)
3. One hard number footer (large serif italic + uppercase label)

### Egyptian motifs

| Motif | Usage | Component / class |
|---|---|---|
| Arch (from OsoolAvatar) | Section frame, arch-top card corners, button accent | `<ArchFrame>`, `.osool-arch-top` |
| Mashrabiya pattern | 5%-opacity geometric watermark on section dividers | `<Mashrabiya>`, `.osool-mashrabiya` |
| Eastern Arabic numerals | One stylistic callout per page | `.osool-numeral-ar` |
| Bilingual stacked headlines | Hero, key page openers | `.osool-bilingual` + `.osool-display-ar` |
| Newspaper rule lines | Between dossier blocks, instead of card borders | `border-inline-end` on `.osool-dossier` |

## Motion

- **Approach:** Intentional. Reveal-on-scroll continues; avatar blink/sparkle continues.
- **New:** Arch stroke-draw animation on section reveal (800ms, `cubic-bezier(.22, 1, .36, 1)`, once per session per section).
- **Easing tokens:**
  - `--osool-ease-out-expo: cubic-bezier(.16, 1, .3, 1)` (existing reveal)
  - `--osool-ease-arch: cubic-bezier(.22, 1, .36, 1)` (new — arch draw-in)
- **Duration tokens:** `micro(80ms) short(180ms) medium(280ms) long(560ms) arch(800ms)`
- **Respect:** `@media (prefers-reduced-motion: reduce)` disables all motion always.

## Voice / Copy posture

- **Operator energy in claims:** "412 deals closed." "Three reasons buyers trust us." Numbers over adjectives.
- **Cultural specificity in language:** Egyptian dialect in Arabic copy ("بنقفل صفقتك" — we close your deal), not formal MSA.
- **Anti-hype:** No "revolutionary AI." No "next-generation." Restraint earns trust.

## Anti-patterns (do not do)

- Property image grids as the landing hero (every Egyptian competitor does this; we lead with a number + a question)
- Icon-in-colored-circle 3-pillar grids (replaced by dossier blocks)
- Bleached white `#FFFFFF` backgrounds (use the warm paper `#FCFAF6`)
- Purple/violet gradients
- Arabic-as-translation-afterthought patterns (toggle in nav, English-only hero)
- Generic stock-photo "happy buyer" hero imagery
- Emerald or teal accents (legacy v7 — remapped, but don't re-introduce)

## File map

| Concern | File |
|---|---|
| Tokens + base classes | `web/app/osool-theme.css` |
| Global tailwind token remap (legacy v7 → osool palette) | `web/app/globals.css` |
| Font loading (Inter, Newsreader, Cairo) | `web/app/layout.tsx` |
| Landing page (Editorial + Cairene) | `web/app/page.tsx` |
| Mascot | `web/components/osool/OsoolAvatar.tsx` |
| Arch-top card shape | `web/components/osool/ArchFrame.tsx` |
| Mashrabiya watermark | `web/components/osool/Mashrabiya.tsx` |
| Chat surface (warm-paper compatible) | `web/app/chat/page.tsx` + `web/app/chat/chat.css` |

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-05-27 | Initial DESIGN.md created | `/design-consultation` session. Memorable thing: "built for me, the Egyptian buyer." Theme refines the existing `--osool-*` editorial system rather than replacing it. Added Nile blue + ochre to the palette; shifted background to warm paper; introduced bilingual hero, dossier blocks, arch-top signature, Mashrabiya watermark, Eastern Arabic numeral stylistic accent. |
