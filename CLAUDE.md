# CLAUDE.md

Guidance for Claude Code when working in this repo (the actual Osool product, committed to git).

> The parent `D:\Saas\Osool\CLAUDE.md` has the broader architecture overview. This file is repo-local and the source of truth for code conventions inside `Osool-Platform/`.

## Design System

**Always read `DESIGN.md` (in this same directory) before making any visual or UI decision.**

DESIGN.md defines:
- The aesthetic direction (Editorial + Cairene) and the memorable thing ("built for me, the Egyptian buyer")
- Typography (Newsreader + Cairo Display + Inter + Cairo)
- The full color palette (terracotta + Nile + ochre + warm paper)
- Spacing, layout, motion, and Egyptian visual motifs
- Anti-patterns to avoid

When reviewing diffs that touch CSS, JSX, or any visual surface:
1. Confirm new colors come from `--osool-*` tokens in `web/app/osool-theme.css`. No raw hex codes.
2. Confirm new sections use `osool-dossier`, `osool-bilingual`, `ArchFrame`, or `Mashrabiya` where appropriate — not icon-grid pillars or generic SaaS layouts.
3. Confirm Arabic typography uses `var(--osool-font-arabic)` (Cairo / Tajawal), not Latin fonts.
4. Flag any reintroduction of bleached white `#FFFFFF` as a page background — the warm paper `#FCFAF6` is intentional.

Do not deviate from DESIGN.md without explicit user approval. In QA mode, flag any code that doesn't match it.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas / brainstorming → invoke `/office-hours`
- Strategy / scope → invoke `/plan-ceo-review`
- Architecture → invoke `/plan-eng-review`
- Design system / plan review → invoke `/design-consultation` or `/plan-design-review`
- Full review pipeline → invoke `/autoplan`
- Bugs / errors → invoke `/investigate`
- QA / testing site behavior → invoke `/qa` or `/qa-only`
- Code review / diff check → invoke `/review`
- Visual polish → invoke `/design-review`
- Ship / deploy / PR → invoke `/ship` or `/land-and-deploy`
- Save progress → invoke `/context-save`
- Resume context → invoke `/context-restore`
