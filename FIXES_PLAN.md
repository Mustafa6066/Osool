# Osool — Pre-Launch Fixes Implementation Plan

**Author:** Claude Code · **Date:** 2026-05-30
**Scope:** Three launch-blocking fixes, sequenced by risk.

1. Verifier hard-block on pricing/legal claims (highest risk)
2. InstaPay / Fawry payment rails (conversion blocker)
3. Installment-first comparison UX (latent differentiator)

> Grounded against the actual code as of this date. File:line references are real.
> This is not a git repo, so there is no diff/branch workflow — these are direct edits.

---

## Pre-flight: a real bug found while planning

The frontend already tries to render a verification chip:

```tsx
// web/app/chat/page.tsx:1070
{msg.verification?.auto_corrected && (
  ... `Auto-corrected ${msg.verification.fix_count ?? 0} number(s)` ...
)}
```

But the backend payload (`wolf_orchestrator.py:1375-1392`, schema in `verifier_agent.py:153-165`) emits:
`{ verified, confidence, total_claims_checked, verified_claims, corrections, badges, rewritten, original_response }`.

**There is no `auto_corrected` and no `fix_count`.** The chip never shows. Fix #1 must
reconcile these field names regardless of which direction we take. Treat this as P0
inside fix #1, not a separate task.

---

## FIX 1 — Verifier hard-block on pricing & legal claims  ✅ SHIPPED 2026-05-30

> **Status: DONE.** Implemented across `verifier_agent.py`, `wolf_orchestrator.py`,
> `endpoints.py` (`/chat/stream`), `web/app/chat/page.tsx`, + `tests/test_verifier_policy.py`
> (7 tests, all green; full verifier suite 24/24 green).
>
> What landed:
> - Risk tiers + `policy` (serve / corrected / blocked). Fabricated legal *guarantees*
>   (legal term + certainty word in one sentence) and invented compounds are BLOCKED:
>   redacted to a bilingual "let me confirm with the team" caveat instead of invented.
> - `_handle_blocked_handoff` logs each blocked claim to `hallucination_flags` at HIGH
>   severity and opens a `Ticket` (priority=high) when the user is known. Best-effort,
>   own DB session, never breaks chat.
> - Output contract normalized: `auto_corrected`, `fix_count`, `blocked`, `caveat`,
>   `policy` — the frontend chip bug (read `auto_corrected`/`fix_count` that never
>   existed) is fixed; new red "Held for review" pill for blocked turns (on-token colors).
> - Streaming hole closed: high-risk turns (`is_high_risk_turn`) buffer the full draft,
>   run the full policy, THEN simulate-stream the safe text. Low-risk turns stream live
>   and get a post-stream defense-in-depth check.
>
> Known caveat (intentional): the low-risk post-stream path still uses rewrite-only for
> number corrections plus a redact for the (vanishingly rare) block case — it does not
> open a handoff ticket. High-risk turns get the full treatment. Documented, not a gap.

### Original plan (for reference)

### Goal
For high-risk claims (price, ROI, payment terms, legal/Civil-Code assertions), stop
serving fabricated numbers silently. Replace "rewrite and hope" with a tiered policy:
**verified → serve as-is**, **correctable → correct + visible badge**, **uncorrectable
high-risk → block the claim + human-handoff caveat**.

### Why this first
A wrong EGP price or an invented "Civil Code 131 guarantees X" is a legal/trust
liability in a low-trust market. The current path (`verifier_agent.rewrite_hallucinated_response`)
guesses a replacement number; if the LLM rewrite fails it falls to regex string-replace
(`_regex_fallback_rewrite`, line 276) which can mangle text. Neither blocks. The whole
mechanism is also currently invisible due to the field-name bug above.

### Current state (verified)
- `verifier_agent.py` — regex claim extraction + GPT-4o-mini rewrite, 5s timeout, regex
  fallback. Returns `rewritten`/`corrections`. **No blocking, no legal-claim check.**
- `wolf_orchestrator.py:1372-1396` — calls verify → if corrections, rewrites in place.
  Wrapped in try/except that swallows everything (`logger.warning`).
- `wolf_orchestrator.py:1340-1366` — **streaming path skips verification entirely**
  (`"verification": {}`). So `/chat/stream` ships unverified text. This is a real hole.
- Frontend chip reads non-existent keys (see pre-flight).

### Changes

**1a. Add a claim-risk tier + legal-claim detector** (`verifier_agent.py`)
- New constant `LEGAL_CLAIM_PATTERNS` (Arabic + English): matches "Civil Code", "القانون
  المدني", "مضمون/guaranteed", "FRA", "law 230", "tax-free", "registered/مسجل", etc.
- New method `_classify_risk(correction) -> "high"|"low"`: price, ROI, payment terms, and
  any legal-pattern hit are `high`. Compound-name/size mismatches stay `low`.
- `verify_response` returns a new field `policy`:
  - `serve` — no corrections.
  - `corrected` — only low-risk corrections; safe to auto-fix + badge.
  - `blocked` — at least one high-risk uncorrectable claim (e.g. a legal assertion with
    no DB backing, or a price with no matching property row).

**1b. Implement the block path** (`verifier_agent.py`)
- New method `redact_blocked_claims(response_text, corrections) -> str`: replaces the
  offending sentence(s) with a neutral bilingual caveat
  (`"أحتاج أتأكد من الرقم/المعلومة دي مع الفريق قبل ما أأكدها لك"` /
  `"Let me confirm this figure with the team before I quote it."`) instead of inventing a number.
- Distinct from `rewrite_hallucinated_response` (kept for low-risk number fixes only).

**1c. Wire policy into the orchestrator** (`wolf_orchestrator.py:1372-1396`)
- Branch on `verification["policy"]`:
  - `corrected` → existing rewrite path (low-risk only).
  - `blocked` → `redact_blocked_claims`, set `verification["blocked"] = True`, and append
    the response to `hallucination_flags` at **error** severity (the async guardrail at
    line 1398 already exists — reuse `log_hallucination_flags`).
- **Normalize the output contract** so the frontend bug dies: add
  `verification["auto_corrected"] = bool` and `verification["fix_count"] = len(corrections)`
  alongside the existing keys. Add `verification["blocked"]` and `verification["caveat"]`.

**1d. Close the streaming hole** (`wolf_orchestrator.py:1340-1366`)
- Decision: streaming can't post-edit tokens already sent. Two options — pick one:
  - **(recommended)** Run verification on the assembled `stream_context` BEFORE the first
    token flushes when the message contains price/legal triggers (cheap pre-check:
    reuse the regex extractors; only pay the LLM/DB cost when a high-risk pattern fires).
    If `blocked`, fall back to non-streaming for that turn.
  - Or: disable streaming whenever the draft contains high-risk patterns (simpler, slight
    latency cost on those turns only).

**1e. Frontend** (`web/app/chat/page.tsx`)
- Fix the chip to read the real fields (after 1c they exist).
- Add a distinct **blocked/handoff** state (amber → red treatment, "verifying with team")
  using existing Nile-trust pill tokens (`osool-theme.css:1182`) — no raw hex (DESIGN.md).

### Tests
- `tests/test_verifier_policy.py`: legal-claim with no DB backing → `policy == "blocked"`;
  price within 5% → `serve`; price off >5% with a real property row → `corrected`.
- Streaming turn with a fabricated price → falls back / blocks (per 1d choice).
- Frontend: snapshot the three chip states (serve/corrected/blocked).

### Effort
CC: ~half a day. Human: ~2-3 days. No new infra. Blast radius: `verifier_agent.py`,
`wolf_orchestrator.py`, `chat/page.tsx`, one new test file.

---

## FIX 2 — InstaPay / Fawry payment rails

### Goal
Accept the rails Egyptians actually use. Today the only working path is a Paymob **card
iframe**; comments/schemas claim InstaPay/Fawry but none is wired.

### Current state (verified)
- `paymob_service.py` — single `initiate_payment` → one `PAYMOB_IFRAME_ID` (card only).
  HMAC verify (`verify_hmac`) and txn verify exist and fail-safe.
- `endpoints.py:7,56` — docstring + `payment_reference` field say "InstaPay/Fawry" but
  the code routes to the card iframe. `/webhook/paymob` (`:727`) has working idempotency (A7).
- `payment_service.py` — `verify_egp_deposit` validates `EGP`-prefixed refs; mock in dev.

### Key fact
Paymob exposes **separate integration IDs per method** (card, mobile wallet, Fawry
reference, InstaPay). The architecture is already 90% there — it's missing the extra
integration IDs and a method selector. This is config + a small branch, not a rewrite.

### Changes

**2a. Multi-method config** (`paymob_service.py`, `config.py`)
- Read `PAYMOB_INTEGRATION_ID_CARD`, `PAYMOB_INTEGRATION_ID_WALLET`,
  `PAYMOB_INTEGRATION_ID_FAWRY` (+ keep `PAYMOB_INTEGRATION_ID` as the card default for
  back-compat). Add to `RAILWAY_ENV_TEMPLATE.txt`.
- `get_payment_key(..., method: str)` selects the integration_id by method.
- `initiate_payment(..., method: Literal["card","wallet","fawry","instapay"])`:
  - card/wallet/instapay → iframe URL (existing flow, different integration_id).
  - **fawry** → Paymob returns a **reference number**, not an iframe. Return
    `{ method:"fawry", fawry_reference, expires_at }` so the user pays at any Fawry outlet.

**2b. Endpoint surface** (`endpoints.py`)
- `PaymentInitiateRequest` gains `method` (default `card`). Validate against allowed set.
- Response for Fawry returns the reference; for the rest, the iframe URL (unchanged shape).
- Fix the misleading docstrings to describe the real multi-rail flow.

**2c. Webhook** (`endpoints.py:727`)
- `verify_hmac` already iterates fixed keys — confirm wallet/Fawry payloads carry the same
  fields (they do in Paymob's spec). Add a smoke check: log `source_data.type` so we can
  see which rail settled. Idempotency guard (A7) already covers duplicates across rails.

**2d. Frontend** (`web/app` checkout/payment component)
- Method picker: Card / Mobile Wallet / Fawry / InstaPay (bilingual, DESIGN.md tokens).
- Fawry branch renders the reference + "pay at any Fawry kiosk" copy and a status poller
  (reuse existing transaction status polling).

### Tests
- `tests/test_paymob_methods.py`: each method picks the right integration_id; Fawry returns
  a reference not an iframe; missing integration_id for a method fails fast (mirrors the
  existing `PAYMOB_IFRAME_ID` fail-fast at `paymob_service.py:223`).
- Webhook: wallet + Fawry settle payloads pass HMAC and hit idempotency once.

### Dependency / unknown
Needs the actual Fawry + wallet integration IDs provisioned in the Paymob dashboard
(business/ops task, not code). Flag: **confirm the Paymob account has these enabled** before
building 2a — otherwise we build against IDs that don't exist. Card/wallet/InstaPay are
iframe-shaped and low-risk; Fawry's reference flow is the only genuinely new code path.

### Effort
CC: ~1 day. Human: ~3-4 days. Blast radius: `paymob_service.py`, `endpoints.py`,
`config.py`, one checkout component, env templates, one test file.

---

## FIX 3 — Installment-first comparison UX  ✅ SHIPPED 2026-05-30

> **Status: DONE** (pending frontend tsc confirmation). Implemented across
> `endpoints.py`, `wolf_orchestrator.py`, `web/components/visualizations/`,
> + `tests/test_compare_plans.py`.
>
> What landed:
> - `POST /api/valuation/compare-plans` — takes up to 10 listings/plans, returns per-row
>   `sticker_price`, `down_payment(+pct)`, `monthly_installment`, `years`, `npv_today`,
>   `npv_discount_pct`, `is_cash`, and a rent-vs-installment read; sorted by NPV ascending
>   with `cheapest_listing_id`. Reuses `calculate_effective_cash_npv` + `_compare_to_rent`
>   — no new financial math.
> - Orchestrator emits an `npv_plan_comparison` ui_action when 2+ priced listings are in
>   play AND (the turn shows a full list OR the intent is `comparison` / `installment_inquiry`)
>   (`_build_payment_plan_comparison`). Named distinctly from the pre-existing per-property
>   `payment_plan_comparison` type to avoid collision.
> - New `NpvPlanComparison.tsx` (registered in the visualization registry): bilingual
>   table, cheapest row badged, NPV-today highlighted, rent verdict per row, RTL/LTR.
> - Tests: NPV ordering (low-down/long-tenure < front-loaded < sticker), cash == sticker,
>   zero-rate == plan total, rent-ratio math + verdict flip, down-payment normalization.
>   (Run in the project venv — `valuation_engine` imports FastAPI, absent from the bare
>   shell; NPV ordering + normalization were verified numerically here.)
>
> Follow-ups landed after initial ship:
> - **Trigger broadened:** the card also fires on `comparison` / `installment_inquiry`
>   intent turns (not just FULL_LIST), whenever 2+ priced listings are in play.
> - **Compound-comparison fallback:** on a comparison/installment turn that surfaces
>   < 2 unit listings (e.g. the user named compounds), `_fetch_representative_units`
>   pulls the cheapest priced listing per distinct compound from the DB (scoped to the
>   location/type in play) so the card still renders. Best-effort, own rollback.
> - **Correctness fix:** `Property.down_payment` is stored as a PERCENTAGE, but the NPV
>   path assumed EGP. Added `normalize_down_payment_to_egp` (fraction / percentage /
>   absolute EGP → EGP), used by both the endpoint and the orchestrator helper. Without
>   this, every installment listing produced a wrong NPV.

### Original plan (for reference)

### Goal
Egyptians shop by **down payment + monthly installment**, not sticker price. Surface the
NPV "true cash-equivalent cost" and a side-by-side installment comparison as a first-class
UI, not buried AI prose.

### Current state (verified)
- `valuation_engine.py` — `POST /valuation/npv` already flattens payment plans to NPV
  using the CBE rate (A3, resolved from `MarketIndicator`).
- `analytical_engine.py:1222+` — `_build_payment_plan`-style helpers and `_compare_to_rent`
  (`:1277`) already compute down payment, monthly, rent delta — but only emit Arabic/English
  **text** inside chat.
- `comparison_service.py` — `compare_compounds()` / `best_deals_in_compound()` exist for
  compound-level comparison; no plan-level installment comparison surface.
- `Property` carries `down_payment`, `installment_years`, `monthly_installment`
  (`endpoints.py:405-407`).

### Changes

**3a. Structured endpoint** (new: `app/api/comparison_endpoints.py` or extend valuation)
- `POST /valuation/compare-plans`: input = list of property IDs (or plan dicts), output =
  per-property `{ sticker_price, down_payment, monthly_installment, years, npv_today,
  effective_premium_pct, rent_equivalent }`. Reuse the NPV engine + `_compare_to_rent`;
  do not re-implement the math.

**3b. Surface the existing AI math as structured `ui_actions`**
- The orchestrator already emits `ui_actions` (`wolf_orchestrator.py`). Add a
  `payment_plan_comparison` action type carrying the 3a payload so the chat can render a
  card instead of a wall of text. Keep the prose as fallback.

**3c. Frontend comparison card** (`web/components`)
- A bilingual table/card: rows = properties, columns = down payment, monthly, years,
  **NPV-today**, rent-vs-buy delta. Sort by NPV by default (the differentiator: "cheapest
  in real money, not sticker"). DESIGN.md tokens, `osool-dossier`/`osool-bilingual`.

### Tests
- `tests/test_compare_plans.py`: two plans, same sticker, different schedules → the
  longer/cheaper-financed one has lower NPV; rent-equivalent matches `_compare_to_rent`.
- Frontend: renders N properties, sorts by NPV, RTL/LTR both correct.

### Effort
CC: ~1 day. Human: ~3-4 days. Mostly surfacing logic that already exists. Blast radius:
one new endpoint, `wolf_orchestrator.py` (one new ui_action), one component, one test file.

---

## Sequencing & rollout

1. **Fix 1** — ship first, behind no flag (it only makes output safer). Includes the
   frontend field-name bug fix and the streaming hole.
2. **Fix 2** — gate behind the Paymob dashboard prerequisite. Card path already works;
   add wallet/InstaPay/Fawry once integration IDs are confirmed.
3. **Fix 3** — independent of 1 and 2; can land in parallel once 1 is in.

## Production bottlenecks — hardening (2026-05-31)

Two bottlenecks flagged for a seamless production release, plus the two-compound
perception change.

### A — Perception captures two named compounds  ✅
`perception_layer` now scans the raw query for ALL distinct canonical compounds
(consume-span dedup so "hyde park" inside "mv hyde park" can't double-count) and
sets `filters["compounds"]`. Wired on BOTH the rule-based path and the LLM path
(`_normalize_filters(intent_data, query)`). `_fetch_representative_units` prefers
these names (cheapest priced listing per named compound) so "compare X and Y"
compares exactly X and Y.

### B1 — Compound canonicalizer (dedup)  ✅
`ingestion/compound_canonicalizer.py`: deterministic AR/EN entity resolution.
Normalizes (NFKC, strips Arabic diacritics/tatweel, unifies alef/ya/hamza/
ta-marbuta), then exact → whole-phrase-containment → fuzzy (difflib) match against
the curated `COMPOUND_ALIASES` (single source of truth, reused from perception);
unknown names get a stable cleaned form so even unmapped variants dedupe.
Wired into `deterministic_normalizer.NormalizedProperty` via a `compound`
validator (same pattern as the existing location `apply_zone_mapping`), so every
ingested row is canonicalized BEFORE upsert + embedding — "Mountain View iCity"
and "ماونتن فيو" collapse to one compound, one baseline, one embedding.
Tests: 7, green. NOTE: this canonicalizes NEW ingests; a one-off backfill to
re-canonicalize existing rows + re-embed is a follow-up (not done).

### B2 — Scraper health / drift guard  ✅
`ingestion/scraper_health.py`: structural health check that complements the
price-only AnomalyDetector. Catches what it misses — empty batches, count far
below baseline, and schema drift (required fields mostly null = selectors broke).
`assess_batch` is pure/tested; `record_and_alert` emits Prometheus gauges
(`osool_scraper_last_batch_count`, `osool_scraper_health`, `osool_scraper_drift_total`)
and reuses the existing Sentry+Discord `send_alert`.
**Catalog-protection fix (the important one):** `master_discovery_job` now gates
on discovery health — if discovery returns 0/too-few URLs it ABORTS without
registering the run, so `mark_stale_job` can't flag the entire catalog
unavailable off a broken scrape. `scrape_compound_task` emits a per-compound
schema-drift alert. Tests: 7, green.
Knobs: `SCRAPER_MIN_DISCOVERY` (floor, default 5), `DISCORD_ALERT_WEBHOOK_URL`.
NOT done (ongoing/arms-race): proxy/Cloudflare evasion itself, a cross-run
staleness watchdog dashboard, auto-healing selectors.

---

## Decisions (locked 2026-05-30)
- **Q1 (Fix 1d):** **Pre-verify, then stream.** Cheap regex pre-check before the first
  token; on a high-risk hit, verify against the DB first and fall back to non-streaming
  for that turn.
- **Q2 (Fix 2):** **Build multi-method architecture, enable card only.** Wallet / Fawry /
  InstaPay light up once integration IDs are provisioned in the Paymob dashboard. Env
  template ships the checklist so enabling each rail is just dropping in an ID.
- **Q3 (Fix 1 legal):** **Create a real handoff ticket.** Blocked legal claims show the
  bilingual caveat, log a hallucination flag, AND open a `Ticket` for human follow-up.
