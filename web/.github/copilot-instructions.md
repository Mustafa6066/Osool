# Copilot Instructions — Osool Platform Web

## Design Context

### Users
Egyptian property investors and buyers — ranging from expat investors and domestic high-net-worth individuals to first-time buyers. They arrive with high-stakes financial decisions and need clarity, not clutter. Their context is often mobile-first, bilingual (English + Arabic with full RTL), and they're trying to compare developers, evaluate ROI, and make confident investment decisions in the Egyptian real estate market. The AI "CoInvestor" is their expert guide, not a chatbot novelty.

### Brand Personality
**Trustworthy. Modern. Expert.**

Osool is the calm, knowledgeable advisor in the room — never flashy, never gimmicky. It earns trust through data transparency, clear visual hierarchy, and an interface that feels as premium as the investments it facilitates. The tone is warm but professional — confident without being cold, approachable without being casual.

**Primary emotional goal: Confidence** — "I'm making the right investment decision."

### Aesthetic Direction
**Visual tone:** Premium minimalism inspired by Apple.com — liquid glass surfaces, generous whitespace, restrained animation with physics-based motion.

**Visual signature:** The "liquid glass" frosted-panel system — translucent surfaces with subtle blur, soft borders, and inset highlights.

**Anti-reference:** Traditional real estate sites — cluttered listings, stock photos, generic card grids, garish colors.

**Theme:** Dark + Light mode (class-based toggle), dark as default.

### Color System
- **Primary:** Emerald `#10B981` — AI signature, trust, growth
- **Primary light:** `#34D399` — hover states, dark-mode primary
- **Primary dark:** `#059669` — pressed states, emphasis
- **Teal accent:** `#0D9488` — secondary accent, gradient endpoints
- **Surfaces:** Near-white `#FAFAFA` (light) / near-black `#09090B` (dark) with zinc gray spectrum
- Always use CSS custom properties (`var(--color-*)`) — never raw hex in components

### Typography
- **Latin:** Inter (300–700)
- **Arabic:** Cairo (300–700)
- Always use the font stack from `--font-sans` / `--font-display`

### Spacing & Geometry
- 4pt grid system (4, 8, 16, 24, 32, 48, 64px)
- Border radii: 12px (sub-elements) → 16px (cards) → 20–24px (panels) → full (pills)
- Soft layered shadows — never harsh drop shadows

### Motion
- Framer Motion with spring physics (`damping: 28, stiffness: 210–240`)
- Entry: `opacity: 0, y: 10–28` → `opacity: 1, y: 0` with stagger
- Respect `prefers-reduced-motion`

### Design Principles
1. **Clarity over density** — whitespace is a feature, not waste
2. **Earned trust through transparency** — real data, honest states
3. **Premium materiality** — every surface and transition feels considered
4. **AI as expert companion** — emerald accents mark AI presence subtly
5. **Bilingual by design** — RTL is native, not mirrored. Use `start`/`end` logical properties

### Accessibility
- WCAG AA minimum
- 4.5:1 contrast for normal text, 3:1 for large text
- Visible focus indicators, full keyboard nav, semantic HTML
- Full RTL bidirectional support with logical CSS properties
