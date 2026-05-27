"""
Zero-Token Property Retrieval — L2 + L3 + L4 + L5 orchestrator.

This is the single entry point for property search. It takes a buyer
prompt + context, extracts a StructuredQuery (L1, via zero_token_intent),
runs 3-4 parallel SQL retrievals (L2), fuses them with Reciprocal Rank
Fusion (L3), augments the top-K with decision-support math (L4), and
caches the result (L5).

No LLM calls. No embedding generation. Every byte of cost in the chat
turn is the narrative LLM that wraps these results — never the
retrieval itself.

Public API:
    retrieve(RetrievalRequest) -> RetrievalResponse

Latency targets:
    p50 cold:  <= 80ms
    p99 cold:  <= 200ms
    warm hit:  <= 10ms (Redis HGET)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.zero_token_intent import StructuredQuery, extract_query

logger = logging.getLogger(__name__)

# Tunable knobs — exposed for easy A/B testing without code change.
RRF_K = 60
SET_WEIGHTS = {
    "structured": 1.0,
    "bm25": 0.6,
    "trigram": 0.5,
    "more_like_this": 0.8,
}
TOP_K_AUGMENT = 8        # how many hits we augment with NPV/La2ta/etc.
DEFAULT_CAP = 5          # how many we return to the caller (rest held as reserve)
PER_SET_LIMIT = 50       # rows per sub-query


# ─────────────────────────────────────────────────────────────────────────────
# Public contract
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RetrievalRequest:
    prompt: str
    session_id: str = ""
    user_id: Optional[int] = None
    lead_profile: Optional[dict] = None
    locale: str = "en"
    ref_property_id: Optional[int] = None  # "more like this" anchor (zero-token)
    cap_results: int = DEFAULT_CAP


@dataclass
class RankedHit:
    """A property after L3 fusion + boost. No augmentation yet."""
    property_id: int
    rrf_score: float
    boosted_score: float
    matched_sets: list[str] = field(default_factory=list)
    sub_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class DecisionAugmentedHit:
    """A property after L4 — what the user actually sees, or the LLM narrates."""
    property_id: int
    boosted_score: float
    matched_sets: list[str]
    # Decision-support fields
    npv_egp: Optional[float] = None
    la2ta_flag: Optional[str] = None
    payment_fit_score: Optional[float] = None
    delivery_fit: Optional[bool] = None
    why_matched: str = ""
    # Pass-through (for the LLM narrative + frontend cards)
    row: dict = field(default_factory=dict)  # selected DB row fields


@dataclass
class RetrievalResponse:
    structured_query: StructuredQuery
    hits: list[DecisionAugmentedHit]            # ≤ cap_results
    reserve: list[RankedHit]                     # held for follow-ups
    diagnostics: dict                            # per-layer latency, cache_hit
    used_zero_token_path: bool = True            # always True; invariant guard


# ─────────────────────────────────────────────────────────────────────────────
# L2 — SQL retrieval (4 parallel queries)
# ─────────────────────────────────────────────────────────────────────────────

# Hard-filter SQL fragment shared by L2a (structured), L2b (BM25), L2d (mlt).
# Built dynamically from the StructuredQuery so we only emit the WHEREs that
# actually have values — keeps the planner choosing the right index.
def _build_hard_filters(q: StructuredQuery) -> tuple[list[str], dict]:
    wheres: list[str] = ["p.is_available = true"]
    params: dict = {}

    def add(clause: str, **kwargs):
        wheres.append(clause)
        params.update(kwargs)

    if q.price_min is not None:
        add("p.price >= :price_min", price_min=q.price_min)
    if q.price_max is not None:
        add("p.price <= :price_max", price_max=q.price_max)
    if q.bedrooms_min is not None:
        add("p.bedrooms >= :beds_min", beds_min=q.bedrooms_min)
    if q.bedrooms_max is not None:
        add("p.bedrooms <= :beds_max", beds_max=q.bedrooms_max)
    if q.size_sqm_min is not None:
        add("p.size_sqm >= :size_min", size_min=q.size_sqm_min)
    if q.size_sqm_max is not None:
        add("p.size_sqm <= :size_max", size_max=q.size_sqm_max)
    if q.locations:
        add("p.location = ANY(:locations)", locations=q.locations)
    if q.compounds:
        add("p.compound = ANY(:compounds)", compounds=q.compounds)
    if q.developers:
        add("p.developer = ANY(:developers)", developers=q.developers)
    if q.property_types:
        add("p.type = ANY(:types)", types=q.property_types)
    if q.finishing_levels:
        add("p.finishing = ANY(:finishing)", finishing=q.finishing_levels)
    if q.ready_by_year_max is not None:
        # delivery_year is added by migration 033; fallback to is_delivered if NULL
        add(
            "(p.delivery_year IS NULL OR p.delivery_year <= :ready_year)",
            ready_year=q.ready_by_year_max,
        )
    if q.is_delivered is not None:
        add("p.is_delivered = :is_delivered", is_delivered=q.is_delivered)
    if q.is_nawy_now is not None:
        add("p.is_nawy_now = :is_nawy_now", is_nawy_now=q.is_nawy_now)
    if q.is_cash_only is not None:
        add("p.is_cash_only = :is_cash_only", is_cash_only=q.is_cash_only)
    if q.installment_years_min is not None:
        add("p.installment_years >= :iy_min", iy_min=q.installment_years_min)
    if q.down_payment_pct_max is not None:
        add("(p.down_payment IS NULL OR p.down_payment <= :dp_max)", dp_max=q.down_payment_pct_max)
    if q.sale_types:
        add("p.sale_type = ANY(:sale_types)", sale_types=q.sale_types)

    return wheres, params


async def _retrieve_structured(db: AsyncSession, q: StructuredQuery) -> list[tuple[int, float]]:
    """L2a — structured WHERE on indexed columns. Returns [(property_id, neutral_score)]."""
    wheres, params = _build_hard_filters(q)
    where_sql = " AND ".join(wheres)
    sql = (
        f"SELECT p.id "
        f"FROM properties p "
        f"WHERE {where_sql} "
        f"ORDER BY p.scraped_at DESC NULLS LAST, p.price ASC "
        f"LIMIT :limit"
    )
    params["limit"] = PER_SET_LIMIT
    rows = (await db.execute(text(sql), params)).fetchall()
    # Structured set has no inherent score gradient — use rank as the score
    # so RRF treats earlier rows as stronger evidence.
    return [(r.id, 1.0) for r in rows]


async def _retrieve_bm25(db: AsyncSession, q: StructuredQuery) -> list[tuple[int, float]]:
    """L2b — BM25 over search_tsv. Only runs if semantic_text is non-empty."""
    if not q.semantic_text or len(q.semantic_text) < 2:
        return []
    wheres, params = _build_hard_filters(q)
    where_sql = " AND ".join(wheres)
    sql = (
        f"SELECT p.id, ts_rank_cd(p.search_tsv, plainto_tsquery('simple', :semantic)) AS bm25 "
        f"FROM properties p "
        f"WHERE {where_sql} "
        f"  AND p.search_tsv @@ plainto_tsquery('simple', :semantic) "
        f"ORDER BY bm25 DESC "
        f"LIMIT :limit"
    )
    params["semantic"] = q.semantic_text
    params["limit"] = PER_SET_LIMIT
    rows = (await db.execute(text(sql), params)).fetchall()
    return [(r.id, float(r.bm25)) for r in rows]


async def _retrieve_trigram(db: AsyncSession, q: StructuredQuery) -> list[tuple[int, float]]:
    """L2c — trigram fuzzy on compound/developer when exact filters returned few hits."""
    # Only run when a compound or developer was mentioned but might have typos.
    candidates: list[str] = []
    candidates.extend(q.compounds)
    candidates.extend(q.developers)
    if not candidates:
        return []
    # Build OR of similarity matches
    fragments = []
    params: dict = {}
    for i, name in enumerate(candidates):
        key = f"name_{i}"
        fragments.append(
            f"(p.compound %% :{key} OR p.developer %% :{key})"
        )
        params[key] = name
    where_clause = " OR ".join(fragments)
    sql = (
        f"SELECT p.id, "
        f"  GREATEST({', '.join(f'similarity(p.compound, :{k}), similarity(p.developer, :{k})' for k in params)}) AS trgm "
        f"FROM properties p "
        f"WHERE p.is_available = true AND ({where_clause}) "
        f"ORDER BY trgm DESC "
        f"LIMIT :limit"
    )
    params["limit"] = 20
    try:
        rows = (await db.execute(text(sql), params)).fetchall()
        return [(r.id, float(r.trgm)) for r in rows]
    except Exception as exc:
        # pg_trgm extension may be off; trigram is a nice-to-have, not load-bearing
        logger.debug("[retrieval] trigram query failed (non-fatal): %s", exc)
        return []


async def _retrieve_more_like_this(
    db: AsyncSession, q: StructuredQuery, ref_property_id: int,
) -> list[tuple[int, float]]:
    """
    L2d — pgvector cosine similarity to a REFERENCE property's embedding.

    Crucially this NEVER generates a new embedding. Both vectors are read
    from the DB. If the reference property has no embedding (embedding IS NULL),
    we return an empty list rather than calling OpenAI.
    """
    wheres, params = _build_hard_filters(q)
    where_sql = " AND ".join(wheres)
    sql = (
        f"WITH ref AS (SELECT embedding FROM properties WHERE id = :ref_id) "
        f"SELECT p.id, 1 - (p.embedding <=> (SELECT embedding FROM ref)) AS cosine "
        f"FROM properties p "
        f"WHERE {where_sql} "
        f"  AND p.id != :ref_id "
        f"  AND p.embedding IS NOT NULL "
        f"  AND (SELECT embedding FROM ref) IS NOT NULL "
        f"ORDER BY p.embedding <=> (SELECT embedding FROM ref) "
        f"LIMIT :limit"
    )
    params["ref_id"] = ref_property_id
    params["limit"] = PER_SET_LIMIT
    try:
        rows = (await db.execute(text(sql), params)).fetchall()
        return [(r.id, float(r.cosine)) for r in rows]
    except Exception as exc:
        logger.debug("[retrieval] more-like-this failed (non-fatal): %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# L3 — Reciprocal Rank Fusion + decision-fit boosts
# ─────────────────────────────────────────────────────────────────────────────

def _rrf_fuse(
    sets: dict[str, list[tuple[int, float]]],
) -> dict[int, tuple[float, list[str], dict[str, float]]]:
    """
    Reciprocal Rank Fusion. Returns {property_id: (rrf_score, matched_sets, sub_scores)}.

    Each set contributes  weight × 1 / (RRF_K + rank_in_set)  for properties it ranks.
    """
    out: dict[int, tuple[float, list[str], dict[str, float]]] = {}
    for set_name, hits in sets.items():
        weight = SET_WEIGHTS.get(set_name, 0.5)
        for rank, (pid, sub_score) in enumerate(hits, start=1):
            contribution = weight * (1.0 / (RRF_K + rank))
            if pid not in out:
                out[pid] = (0.0, [], {})
            cur_score, cur_sets, cur_sub = out[pid]
            cur_sets.append(set_name)
            cur_sub[set_name] = sub_score
            out[pid] = (cur_score + contribution, cur_sets, cur_sub)
    return out


def _apply_boosts(
    fused: dict[int, tuple[float, list[str], dict[str, float]]],
    rows_by_id: dict[int, dict],
    q: StructuredQuery,
) -> list[RankedHit]:
    """
    Multiplicative boosts on top of RRF score, using the buyer's StructuredQuery
    + row attributes. Pure math; no I/O.
    """
    ranked: list[RankedHit] = []
    for pid, (rrf_score, matched_sets, sub_scores) in fused.items():
        row = rows_by_id.get(pid, {})
        boost = 1.0

        # Budget fit (when buyer set a max)
        if q.buyer_budget_cap or q.price_max:
            target = q.buyer_budget_cap or q.price_max
            price = row.get("price") or 0
            if price > 0 and target:
                lo = target * 0.85
                hi = target * 1.05
                if lo <= price <= hi:
                    boost *= 1.15

        # Down-payment fit
        if q.down_payment_pct_max is not None:
            dp = row.get("down_payment")
            if dp is not None and dp <= q.down_payment_pct_max:
                boost *= 1.10

        # Nawy Now + needs-delivery match
        if row.get("is_nawy_now") and any(t.startswith("needs_delivery_by_") for t in q.intent_tags):
            boost *= 1.20

        # Freshness — content_hash updated in last 7 days
        scraped_at = row.get("scraped_at")
        if scraped_at is not None:
            try:
                from datetime import datetime, timezone, timedelta
                if isinstance(scraped_at, str):
                    scraped_at = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
                if scraped_at.tzinfo is None:
                    scraped_at = scraped_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - scraped_at < timedelta(days=7):
                    boost *= 1.05
            except Exception:
                pass

        # La2ta + investor persona
        if row.get("price_flag") == "below_area_avg" and "investor" in q.intent_tags:
            boost *= 1.25

        # Penalty for un-embedded rows (only ranked via L2a/b/c, no semantic signal)
        if row.get("embedding") is None:
            boost *= 0.95

        ranked.append(
            RankedHit(
                property_id=pid,
                rrf_score=rrf_score,
                boosted_score=rrf_score * boost,
                matched_sets=list(dict.fromkeys(matched_sets)),  # dedup, preserve order
                sub_scores=sub_scores,
            )
        )
    ranked.sort(key=lambda h: h.boosted_score, reverse=True)
    return ranked


# ─────────────────────────────────────────────────────────────────────────────
# L4 — Decision augmentation (pure math)
# ─────────────────────────────────────────────────────────────────────────────

def _augment_hit(hit: RankedHit, row: dict, q: StructuredQuery) -> DecisionAugmentedHit:
    """
    Adds NPV, La2ta flag, payment-fit, delivery-fit, why_matched template.
    Every field is computed from row data + StructuredQuery. No I/O.
    """
    # NPV — guarded compute; valuation_engine has its own contract.
    npv_egp: Optional[float] = None
    try:
        price = row.get("price") or 0
        if price > 0:
            dp_pct = row.get("down_payment") or 0
            years = row.get("installment_years") or 0
            monthly = row.get("monthly_installment") or 0
            if years > 0 and monthly > 0 and dp_pct >= 0:
                # Rough NPV: down payment + PV of monthly installments at CBE rate.
                # Real impl would call valuation_engine.compute_npv(...) once it
                # accepts a row dict — for now, a cheap approximation that still
                # ranks correctly.
                cbe_rate = 0.22  # placeholder; valuation_engine.get_cbe_rate() ideally
                monthly_rate = cbe_rate / 12
                n_months = years * 12
                down_payment = price * (dp_pct / 100.0)
                if monthly_rate > 0:
                    pv_installments = monthly * ((1 - (1 + monthly_rate) ** -n_months) / monthly_rate)
                else:
                    pv_installments = monthly * n_months
                npv_egp = float(down_payment + pv_installments)
            else:
                npv_egp = float(price)
    except Exception as exc:
        logger.debug("[retrieval] npv compute failed for property %s: %s", hit.property_id, exc)

    la2ta_flag = row.get("price_flag")

    payment_fit_score: Optional[float] = None
    if q.down_payment_pct_max is not None and row.get("down_payment") is not None:
        try:
            payment_fit_score = max(
                -1.0,
                min(1.0, (q.down_payment_pct_max - row["down_payment"]) / 100.0),
            )
        except Exception:
            payment_fit_score = None

    delivery_fit: Optional[bool] = None
    if q.ready_by_year_max is not None and row.get("delivery_year") is not None:
        delivery_fit = row["delivery_year"] <= q.ready_by_year_max

    # why_matched — template-only, no LLM
    reasons: list[str] = []
    if "structured" in hit.matched_sets:
        if q.locations and row.get("location") in q.locations:
            reasons.append(f"in {row['location']}")
        if q.price_max is not None and row.get("price"):
            reasons.append(f"within budget ({int(row['price']):,} EGP)")
        if q.installment_years_min and (row.get("installment_years") or 0) >= q.installment_years_min:
            reasons.append(f"{row['installment_years']}-year payment plan")
        if q.bedrooms_min and row.get("bedrooms") == q.bedrooms_min:
            reasons.append(f"{row['bedrooms']} bedrooms")
    if "bm25" in hit.matched_sets and q.semantic_text:
        reasons.append(f"matches '{q.semantic_text[:40]}'")
    if la2ta_flag == "below_area_avg":
        reasons.append("priced below area average")
    if row.get("is_nawy_now"):
        reasons.append("instant delivery (Nawy Now)")

    why_matched = " · ".join(reasons[:3]) if reasons else ""

    return DecisionAugmentedHit(
        property_id=hit.property_id,
        boosted_score=hit.boosted_score,
        matched_sets=hit.matched_sets,
        npv_egp=npv_egp,
        la2ta_flag=la2ta_flag,
        payment_fit_score=payment_fit_score,
        delivery_fit=delivery_fit,
        why_matched=why_matched,
        row={
            k: row.get(k) for k in (
                "id", "title", "compound", "developer", "location", "type",
                "price", "size_sqm", "bedrooms", "bathrooms", "finishing",
                "delivery_date", "delivery_year", "down_payment",
                "installment_years", "monthly_installment", "is_nawy_now",
                "is_delivered", "sale_type", "image_url", "nawy_url",
            )
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cache key helper
# ─────────────────────────────────────────────────────────────────────────────

def canonical_query_hash(q: StructuredQuery, ref_property_id: Optional[int] = None) -> str:
    """
    Deterministic hash over the *normalized* StructuredQuery shape, so two
    semantically identical queries hit the same cache entry regardless of
    prompt phrasing.
    """
    payload = asdict(q)
    payload["_ref_property_id"] = ref_property_id
    # Sort lists for stable hashing
    for k, v in payload.items():
        if isinstance(v, list):
            payload[k] = sorted(v)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point — retrieve()
# ─────────────────────────────────────────────────────────────────────────────

async def retrieve(req: RetrievalRequest, db: AsyncSession) -> RetrievalResponse:
    """
    The single zero-token retrieval entry point.

    Pipeline:
        L1 (extract_query)
        L5 cache lookup — bail with cached response on hit
        L2 (parallel SQL: structured + BM25 + trigram + more-like-this)
        L3 (RRF fuse + boosts)
        L4 (NPV / La2ta / payment-fit / why_matched augmentation on top-K)
        L5 cache set — write result for next caller

    Returns RetrievalResponse with diagnostics.
    """
    t0 = time.perf_counter()
    diagnostics: dict = {"layer_ms": {}, "cache_hit": False}

    # L1
    q = extract_query(
        req.prompt,
        buyer_budget_cap=(req.lead_profile or {}).get("budget_max"),
        buyer_persona=(req.lead_profile or {}).get("persona"),
    )
    diagnostics["layer_ms"]["l1_intent"] = round((time.perf_counter() - t0) * 1000, 2)

    if q.is_empty() and req.ref_property_id is None:
        # Nothing to search; caller (Wolf) will ask a clarifying question.
        return RetrievalResponse(
            structured_query=q, hits=[], reserve=[], diagnostics=diagnostics,
        )

    # L5 — cache lookup. Imported lazily to avoid circular import at module load.
    try:
        from app.services.retrieval_cache import get_cached_response, set_cached_response
        cached = get_cached_response(q, req.ref_property_id)
        if cached is not None:
            cached.diagnostics["layer_ms"] = {"cache_lookup_ms": round((time.perf_counter() - t0) * 1000, 2)}
            cached.diagnostics["cache_hit"] = True
            # Honor cap_results in case the cached entry had a different cap
            cached.hits = cached.hits[: max(1, min(req.cap_results, len(cached.hits) or 1))]
            return cached
    except Exception as exc:
        logger.debug("[retrieval] cache lookup failed: %s", exc)
        set_cached_response = None  # so the post-write block is a no-op

    # L2 — parallel sub-queries
    t1 = time.perf_counter()
    tasks = [
        _retrieve_structured(db, q),
        _retrieve_bm25(db, q),
        _retrieve_trigram(db, q),
    ]
    if req.ref_property_id is not None:
        tasks.append(_retrieve_more_like_this(db, q, req.ref_property_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    sets: dict[str, list[tuple[int, float]]] = {}
    set_names = ["structured", "bm25", "trigram"]
    if req.ref_property_id is not None:
        set_names.append("more_like_this")
    for name, res in zip(set_names, results):
        if isinstance(res, Exception):
            logger.warning("[retrieval] L2 %s failed: %s", name, res)
            sets[name] = []
        else:
            sets[name] = res
    diagnostics["layer_ms"]["l2_retrieval"] = round((time.perf_counter() - t1) * 1000, 2)
    diagnostics["set_sizes"] = {k: len(v) for k, v in sets.items()}

    # Hydrate rows for the union of property_ids — one round trip
    all_ids = {pid for hits in sets.values() for pid, _ in hits}
    if not all_ids:
        return RetrievalResponse(
            structured_query=q, hits=[], reserve=[], diagnostics=diagnostics,
        )

    t2 = time.perf_counter()
    hydrate_sql = (
        "SELECT id, title, compound, developer, location, type, price, "
        "       size_sqm, bedrooms, bathrooms, finishing, delivery_date, "
        "       delivery_year, down_payment, installment_years, "
        "       monthly_installment, is_nawy_now, is_delivered, sale_type, "
        "       image_url, nawy_url, scraped_at, price_flag, embedding "
        "FROM properties WHERE id = ANY(:ids)"
    )
    rows = (await db.execute(text(hydrate_sql), {"ids": list(all_ids)})).mappings().all()
    rows_by_id = {r["id"]: dict(r) for r in rows}
    diagnostics["layer_ms"]["hydrate"] = round((time.perf_counter() - t2) * 1000, 2)

    # L3 — fuse + boost
    t3 = time.perf_counter()
    fused = _rrf_fuse(sets)
    ranked = _apply_boosts(fused, rows_by_id, q)
    diagnostics["layer_ms"]["l3_rrf_boost"] = round((time.perf_counter() - t3) * 1000, 2)

    # L4 — augment top-K
    t4 = time.perf_counter()
    top = ranked[:TOP_K_AUGMENT]
    augmented = [_augment_hit(h, rows_by_id.get(h.property_id, {}), q) for h in top]
    diagnostics["layer_ms"]["l4_augment"] = round((time.perf_counter() - t4) * 1000, 2)

    cap = max(1, min(req.cap_results, TOP_K_AUGMENT))
    hits = augmented[:cap]
    reserve = ranked[cap:TOP_K_AUGMENT]  # ranked, not augmented

    diagnostics["layer_ms"]["total"] = round((time.perf_counter() - t0) * 1000, 2)
    diagnostics["query_hash"] = canonical_query_hash(q, req.ref_property_id)

    response = RetrievalResponse(
        structured_query=q,
        hits=hits,
        reserve=reserve,
        diagnostics=diagnostics,
    )

    # L5 — write through to cache for next caller. Best-effort, never raises.
    if set_cached_response is not None and hits:
        try:
            set_cached_response(q, response, req.ref_property_id)
        except Exception as exc:
            logger.debug("[retrieval] cache set failed: %s", exc)

    return response
