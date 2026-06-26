"""
Differential Hash Upsert Repository
------------------------------------
Pillar 6: Cost-saving delta mechanism.

Flow per property:
  1. Compute SHA256 hash of the 6 core mutable market attributes
  2. SELECT existing hash from DB by nawy_url
  3a. Hash UNCHANGED → update last_scrape_run_id + scraped_at only (SKIP embedding)
  3b. Hash CHANGED or NEW → generate fresh text-embedding-3-small vector, full upsert

This eliminates redundant OpenAI API calls (embedding + LLM) for the
~80–90% of properties that haven't changed between weekly scrape runs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import AsyncSessionLocal
from app.models import Property, PropertyPriceSnapshot
from app.ingestion.deterministic_normalizer import NormalizedProperty

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Result Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UpsertResult:
    """Counts for one batch of upsert operations."""
    inserted: int = 0   # New nawy_url, full write + embedding
    updated: int = 0    # Existing but hash changed, full write + embedding
    skipped: int = 0    # Existing and hash unchanged, run_id touch only
    errors: int = 0
    error_details: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.inserted + self.updated + self.skipped

    def __add__(self, other: "UpsertResult") -> "UpsertResult":
        return UpsertResult(
            inserted=self.inserted + other.inserted,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
            errors=self.errors + other.errors,
            error_details=self.error_details + other.error_details,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Hash Computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_content_hash(prop: NormalizedProperty) -> str:
    """
    SHA256 over the 6 core market-signal attributes.

    These 6 fields are the "true signal" that warrants re-embedding:
    a price drop, a size correction, a finishing upgrade, etc. NOTE: sale_type
    is deliberately NOT here — adding it would mass-NULL every embedding on the
    first scrape (it changes the hash for the whole catalog at once). A
    Developer→Resale relabel is handled on the cheap path instead, where the
    dev/resale split is recomputed without touching the embedding.

    Deliberately EXCLUDED from hash (cosmetic / narrative changes):
    - title, description  — copywriting updates shouldn't trigger re-embedding
    - image_url           — CDN URL rotation changes these frequently
    - delivery_date       — often shifts by a quarter, low signal-to-noise
    - compound, nawy_reference — identifiers, not market signals

    Returns:
        64-char lowercase hex digest.
    """
    payload = json.dumps(
        {
            "price": float(prop.price) if prop.price else 0.0,
            "size_sqm": int(prop.size_sqm) if prop.size_sqm else 0,
            "type": (prop.type or "").strip(),
            "location": (prop.location or "").strip(),
            "finishing": (prop.finishing or "").strip(),
            "developer": (prop.developer or "").strip(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Embedding generation removed — scraper is zero-token.
# New/updated properties are stored with embedding=NULL.
# Full-text search via search_tsv (tsvector) column remains active.
# To backfill embeddings, run the standalone embed_backfill task.


# ─────────────────────────────────────────────────────────────────────────────
# Core Upsert Function
# ─────────────────────────────────────────────────────────────────────────────

_BATCH_COMMIT_SIZE = 50  # Commit every N properties to bound memory usage


async def upsert_properties(
    properties: Sequence[NormalizedProperty],
    run_id: str,
    skip_anomaly_check: bool = False,
    source: str = "nawy",
) -> UpsertResult:
    """
    Differential hash upsert for a batch of normalized properties.

    Decision per property:
    ┌─────────────────────┬─────────────────────────────────────────────────┐
    │ Condition           │ Action                                          │
    ├─────────────────────┼─────────────────────────────────────────────────┤
    │ New (no nawy_url)   │ INSERT full row + generate embedding            │
    │ Existing, hash ≠    │ UPDATE all fields + regenerate embedding        │
    │ Existing, hash =    │ UPDATE last_scrape_run_id + scraped_at ONLY     │
    └─────────────────────┴─────────────────────────────────────────────────┘

    Args:
        properties: Sequence of NormalizedProperty from llm_normalizer.
        run_id:     UUID string for this scrape run (stale detection).
        skip_anomaly_check: True for curated feeds (Nawy Now etc.) whose
            per-area medians legitimately diverge from the broad-market
            baseline. The anomaly detector compares incoming median price
            against historical median for that area; for niche segments
            (instant-delivery, ultra-luxury) that comparison is structurally
            inflated/deflated and will halt an otherwise-valid scrape.

    Returns:
        UpsertResult with counts for inserted, updated, skipped, errors.
    """
    result = UpsertResult()
    now = datetime.now(timezone.utc)

    # ── Validation gate: reject obviously broken records up front ──
    # The anomaly detector below skips rows without a positive price, so
    # without this gate zero-price / location-less records would be silently
    # upserted and poison valuations and search.
    # Residential price/m² floor — a residential unit below this is almost
    # certainly a captured down-payment / installment rather than the unit
    # price (the El Gouna 416k chalet = 4,521 EGP/m², ~10x below market). Set
    # below the read-time serving floor (8,000) to avoid over-rejecting at the
    # source while the read gate still protects what gets served.
    _MIN_INGEST_PPSQM = 6_000.0
    _RESIDENTIAL_TYPE_TOKENS = (
        "apartment", "villa", "chalet", "studio", "duplex", "penthouse",
        "townhouse", "twin", "loft", "cabin",
    )

    valid_props: list[NormalizedProperty] = []
    for prop in properties:
        reasons = []
        if not prop.price or prop.price <= 0:
            reasons.append("non-positive price")
        if not (prop.location or "").strip():
            reasons.append("missing location")
        # Down-payment-as-price guard (residential only — commercial/land EGP/m²
        # legitimately varies). Cross-checks price against size.
        size = getattr(prop, "size_sqm", 0) or 0
        ptype = str(getattr(prop, "type", "") or "").lower()
        beds = getattr(prop, "bedrooms", 0) or 0
        is_residential = beds > 0 or any(tok in ptype for tok in _RESIDENTIAL_TYPE_TOKENS)
        if not reasons and prop.price and size > 0 and is_residential:
            ppsqm = prop.price / size
            if ppsqm < _MIN_INGEST_PPSQM:
                reasons.append(
                    f"implausible price/m² ({ppsqm:,.0f} EGP/m²) — likely a "
                    f"down-payment/installment captured as the unit price"
                )
        if reasons:
            result.errors += 1
            result.error_details.append(
                f"REJECTED {prop.nawy_url or prop.title}: {', '.join(reasons)}"
            )
        else:
            valid_props.append(prop)

    if result.errors:
        logger.warning(
            "[repo] Validation gate rejected %d/%d records (run=%s). First rejects: %s",
            result.errors, len(properties), run_id, result.error_details[:5],
        )
    properties = valid_props
    if not properties:
        return result

    # ── Anomaly Detection: halt upsert if price data looks corrupted ──
    if skip_anomaly_check:
        logger.info(
            "[repo] Anomaly detector bypassed for run=%s (curated feed)", run_id
        )
    else:
        # I13: don't conflate "intentionally skipped" with "import broke". The old
        # code raised a fake ImportError to skip, then swallowed ALL ImportErrors —
        # so a genuinely broken anomaly_detector silently disabled the integrity
        # guard with zero signal. Now a real import failure is loud (log + Sentry).
        anomaly_detector = None
        send_alert = None
        try:
            from app.ingestion.anomaly_detector import anomaly_detector, send_alert
        except Exception as imp_err:
            # Stay fail-soft (don't abort the whole run on a broken guard), but be
            # LOUD about it — a missing/broken anomaly_detector silently disabling
            # the integrity guard is exactly the I13 bug we're fixing.
            logger.error(
                "[repo] anomaly_detector import FAILED — data-integrity guard is "
                "DISABLED for run=%s: %s", run_id, imp_err,
            )
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    f"anomaly_detector import failed (guard disabled): {imp_err}",
                    level="error",
                )
            except Exception:
                pass
        if anomaly_detector is not None:
            try:
                async with AsyncSessionLocal() as anomaly_db:
                    prop_dicts = [
                        {"location": p.location, "compound": p.compound, "price": p.price}
                        for p in properties
                        if p.price and p.price > 0
                    ]
                    anomaly_result = await anomaly_detector.check_batch(prop_dicts, anomaly_db)
                    if not anomaly_result["safe"]:
                        anomaly_details = "\n".join(
                            f"  • {a['area']}: {a['direction']} {a['deviation_pct']}% "
                            f"(incoming median: {a['incoming_median']:,.0f}, "
                            f"baseline: {a['baseline_median']:,.0f})"
                            for a in anomaly_result["anomalies"]
                        )
                        logger.error(
                            f"🚨 ANOMALY DETECTOR HALTED UPSERT (run={run_id}):\n{anomaly_details}"
                        )
                        await send_alert(
                            title=f"Scrape Anomaly — Upsert Halted (run {run_id[:8]})",
                            message=(
                                f"Anomaly detected in {len(anomaly_result['anomalies'])} area(s):\n"
                                f"{anomaly_details}\n\n"
                                f"Batch of {len(properties)} properties was NOT written to DB."
                            ),
                            severity="critical",
                        )
                        result.errors = len(properties)
                        return result
            except Exception as anomaly_err:
                logger.warning(f"Anomaly detection skipped (non-fatal): {anomaly_err}")

    async with AsyncSessionLocal() as db:
        # Prefetch existing hash/id/price for all URLs in this batch (one round trip)
        urls = [p.nawy_url for p in properties if p.nawy_url]
        existing_hashes: dict[str, str] = {}
        existing_meta: dict[str, tuple[int, Optional[float]]] = {}

        if urls:
            rows = await db.execute(
                select(
                    Property.nawy_url,
                    Property.content_hash,
                    Property.id,
                    Property.price,
                ).where(Property.nawy_url.in_(urls))
            )
            for row in rows:
                existing_hashes[row.nawy_url] = row.content_hash
                existing_meta[row.nawy_url] = (row.id, row.price)

        batch_buffer: list[dict] = []
        price_events: list[dict] = []

        for prop in properties:
            if not prop.nawy_url:
                logger.warning("[repo] Skipping property with no nawy_url: %s", prop.title)
                result.errors += 1
                result.error_details.append(f"Missing nawy_url: {prop.title}")
                continue

            try:
                new_hash = compute_content_hash(prop)
                old_hash = existing_hashes.get(prop.nawy_url)

                # ── Cheap path: hash unchanged ──────────────────────────────
                if old_hash is not None and old_hash == new_hash:
                    # Cheap path: the market hash is unchanged, so skip re-embedding.
                    # Still do two things a hash match would otherwise freeze:
                    #  (a) recompute the developer/resale split so a sale_type relabel
                    #      corrects developer_price/resale_price — this is why sale_type
                    #      is NOT in the hash (adding it would mass-NULL every embedding
                    #      on the first scrape). [I8]
                    #  (b) refresh cosmetic/secondary scalars that move without a market
                    #      signal (delivery, image) and re-list a row delisted during an
                    #      outage that returns unchanged. [I9 + I27]
                    # [Phase 0 / I9 + I31, Phase 2 / I8 + I27]
                    dev_price, resale_price = _split_developer_resale(prop.sale_type, prop.price)
                    await db.execute(
                        text(
                            "UPDATE properties SET "
                            "last_scrape_run_id = :run_id, scraped_at = :now, "
                            "is_available = true, source = :source, "
                            "sale_type = :sale_type, developer_price = :dev_price, "
                            "resale_price = :resale_price, "
                            "delivery_date = :delivery_date, delivery_year = :delivery_year, "
                            "is_delivered = :is_delivered, image_url = :image_url "
                            "WHERE nawy_url = :url"
                        ),
                        {
                            "run_id": run_id,
                            "now": now,
                            "url": prop.nawy_url,
                            "source": source,
                            "sale_type": prop.sale_type,
                            "dev_price": dev_price,
                            "resale_price": resale_price,
                            "delivery_date": prop.delivery_date,
                            "delivery_year": prop.delivery_year,
                            "is_delivered": prop.is_delivered,
                            "image_url": prop.image_url,
                        },
                    )
                    result.skipped += 1
                    logger.debug("[repo] SKIP (hash unchanged) %s", prop.nawy_url)
                    continue

                # ── Expensive path: new or changed ─────────────────────────
                embedding = None  # zero-token: embeddings skipped at scrape time

                row = _build_row(prop, run_id, now, new_hash, embedding, source)
                batch_buffer.append(row)

                if old_hash is None:
                    result.inserted += 1
                    logger.debug("[repo] INSERT %s", prop.nawy_url)
                else:
                    result.updated += 1
                    logger.debug("[repo] UPDATE (hash changed) %s", prop.nawy_url)
                    # Freshness invalidation — drop any cached search results
                    # that included this property so the next chat turn sees
                    # the new price. Best-effort; never raises.
                    try:
                        from app.services.retrieval_cache import on_property_changed
                        # We don't have the row id here; the cache index is by
                        # property_id which we don't know yet for inserts.
                        # For updates, look it up via nawy_url:
                        pid_row = (await db.execute(
                            text("SELECT id FROM properties WHERE nawy_url = :url"),
                            {"url": prop.nawy_url},
                        )).first()
                        if pid_row:
                            on_property_changed(pid_row.id, old_hash, new_hash)
                    except Exception:
                        pass  # never break the upsert over a cache nicety

                    # Capture price movement for alerts/trend analytics
                    prop_id, old_price = existing_meta.get(prop.nawy_url, (None, None))
                    if (
                        old_price is not None
                        and prop.price
                        and float(prop.price) != float(old_price)
                    ):
                        price_events.append({
                            "property_id": prop_id,
                            "nawy_url": prop.nawy_url,
                            "old_price": float(old_price),
                            "new_price": float(prop.price),
                            "pct_change": (float(prop.price) - float(old_price)) / float(old_price),
                            "scrape_run_id": run_id,
                        })

                # Flush batch every N rows to bound memory. Each flush runs in a
                # SAVEPOINT so one bad row/batch rolls back just that batch rather
                # than poisoning the transaction and discarding the entire run.
                if len(batch_buffer) >= _BATCH_COMMIT_SIZE:
                    result.errors += await _flush_batch_safe(db, batch_buffer, now, source)
                    batch_buffer = []

            except Exception as exc:
                logger.error("[repo] Error upserting %s: %s", prop.nawy_url, exc)
                result.errors += 1
                result.error_details.append(f"{prop.nawy_url}: {exc}")

        # Flush remaining rows (also in a SAVEPOINT — see _flush_batch_safe)
        if batch_buffer:
            result.errors += await _flush_batch_safe(db, batch_buffer, now, source)

        if price_events:
            try:
                from app.models import PropertyPriceEvent
                await db.execute(pg_insert(PropertyPriceEvent).values(price_events))
                logger.info(
                    "[repo] Recorded %d price events (run=%s)", len(price_events), run_id
                )
            except Exception as pe_err:
                # Price history is best-effort — never block the upsert
                logger.warning("[repo] Price event capture failed (non-fatal): %s", pe_err)

        await db.commit()

    logger.info(
        "[repo] Upsert complete — inserted=%d updated=%d skipped=%d errors=%d",
        result.inserted,
        result.updated,
        result.skipped,
        result.errors,
    )
    return result


def _split_developer_resale(
    sale_type: Optional[str], price: Optional[float]
) -> tuple[Optional[float], Optional[float]]:
    """Derive the (developer_price, resale_price) split from sale_type + price.

    Mirrors migration 027's backfill semantics, but applied at write time so
    LIVE scrapes keep the split fresh (the migration only touched rows that
    existed in 2026-05). A property is either developer-priced or resale-priced,
    never both — matching how the free-path comparison engine reads the columns.

      sale_type ∈ {Developer, Nawy Now} → developer_price = price
      sale_type == Resale               → resale_price   = price
      unknown / NULL                    → leave both NULL (query-time fallback
                                          still coalesces from sale_type+price)
    """
    st = (sale_type or "").strip().lower()
    if not st or price is None:
        return None, None
    if "resale" in st:
        return None, float(price)
    if "developer" in st or "nawy now" in st or "nawy_now" in st:
        return float(price), None
    return None, None


def _build_row(
    prop: NormalizedProperty,
    run_id: str,
    now: datetime,
    content_hash: str,
    embedding: Optional[List[float]],
    source: str = "nawy",
) -> dict:
    """Maps NormalizedProperty fields to Property table column names."""
    developer_price, resale_price = _split_developer_resale(prop.sale_type, prop.price)
    return {
        "title": prop.title,
        "description": prop.description,
        "type": prop.type,
        "location": prop.location,
        "compound": prop.compound,
        "developer": prop.developer,
        "price": prop.price,
        "developer_price": developer_price,
        "resale_price": resale_price,
        "price_per_sqm": prop.price_per_sqm,
        "size_sqm": prop.size_sqm,
        "bedrooms": prop.bedrooms or 0,
        "bathrooms": prop.bathrooms,
        "finishing": prop.finishing,
        "delivery_date": prop.delivery_date,
        "delivery_year": prop.delivery_year,
        "down_payment": prop.down_payment_percentage,
        "installment_years": prop.installment_years,
        "monthly_installment": prop.monthly_installment,
        "image_url": prop.image_url,
        "nawy_url": prop.nawy_url or None,   # Normalize '' → NULL (avoids unique constraint clash)
        "nawy_reference": prop.nawy_reference,
        "sale_type": prop.sale_type,
        "is_nawy_now": prop.is_nawy_now,
        "is_delivered": prop.is_delivered,
        "is_cash_only": prop.is_cash_only,
        "land_area": prop.land_area,
        "maintenance_fee_pct": prop.maintenance_fee_pct,
        "delivery_payment": prop.delivery_payment,
        "embedding": embedding,
        "content_hash": content_hash,
        "last_scrape_run_id": run_id,
        "source": source,
        "scraped_at": now,
        "is_available": True,
    }


async def _flush_batch_safe(db, rows: list[dict], now: datetime, source: str) -> int:
    """
    Flush one batch inside a SAVEPOINT (db.begin_nested) so a single bad row or
    batch cannot abort the surrounding transaction and discard the entire run.
    On failure the savepoint is rolled back, the offending batch is logged, and
    the run continues. Returns the count of rows that failed (0 on success).
    [Phase 0 / I7]
    """
    if not rows:
        return 0
    try:
        async with db.begin_nested():
            await _flush_batch(db, rows)
            await _flush_snapshots(db, rows, now, source)
        return 0
    except Exception as exc:
        logger.error(
            "[repo] Batch flush failed (%d rows) — rolled back to savepoint, "
            "continuing run: %s",
            len(rows), exc,
        )
        return len(rows)


async def _flush_batch(db, rows: list[dict]) -> None:
    """
    Executes PostgreSQL INSERT ON CONFLICT (nawy_url) DO UPDATE for a batch.

    The partial unique index uq_properties_nawy_url has predicate
        (nawy_url IS NOT NULL AND nawy_url <> '')
    Postgres requires the ON CONFLICT predicate to match the index
    predicate exactly, or it raises InvalidColumnReferenceError.
    """
    if not rows:
        return

    stmt = pg_insert(Property).values(rows)

    # All updatable columns (skip primary key, nawy_url conflict target, created_at,
    # and any GENERATED ALWAYS columns — Postgres rejects assigning to them).
    # search_tsv is a stored tsvector generated from title/description/etc.
    _GENERATED_COLS = {"search_tsv"}
    update_cols = {
        col.key: stmt.excluded[col.key]
        for col in Property.__table__.columns
        if col.key not in ("id", "nawy_url", "created_at")
        and col.key not in _GENERATED_COLS
    }

    # IMPORTANT: Postgres only validates the ON CONFLICT predicate against
    # the partial index when a conflict actually occurs (i.e. an existing
    # row matches). It then requires an EXACT canonicalized match against
    # the index's stored predicate, which is:
    #     ((nawy_url IS NOT NULL) AND (nawy_url <> ''::text))
    # SQLAlchemy expression `col != ""` parameterizes the literal as $param,
    # which Postgres won't match against the stored `<> ''::text`. Emit raw
    # text so the predicate is byte-for-byte equivalent at canonicalization.
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["nawy_url"],
        index_where=text("nawy_url IS NOT NULL AND nawy_url <> ''"),
        set_=update_cols,
    )

    await db.execute(upsert_stmt)


async def _flush_snapshots(db, rows: list[dict], now: datetime, source: str) -> None:
    """
    Record a unit-level price observation for each new/changed property.

    This is the ACCUMULATE pillar of the forecasting feature: property_price_snapshot
    (migration 031) was never written before, so the forecaster had no real history.
    Only the expensive path (insert / hash-changed) reaches here, so we capture a
    point precisely when a property is first seen or its core attributes (incl. price)
    move — exactly the signal a price trend needs. Best-effort: never breaks the upsert.

    Property ids are resolved via the same nawy_url lookup the cache-invalidation path
    already uses (the upsert above has just persisted them).
    """
    if not rows:
        return
    urls = [r["nawy_url"] for r in rows if r.get("nawy_url")]
    if not urls:
        return
    try:
        id_rows = (await db.execute(
            select(Property.id, Property.nawy_url).where(Property.nawy_url.in_(urls))
        )).all()
        url_to_id = {url: pid for pid, url in id_rows}
        snaps: list[dict] = []
        for r in rows:
            pid = url_to_id.get(r.get("nawy_url"))
            if pid is None or r.get("price") is None:
                continue
            run_id = r.get("last_scrape_run_id")
            snaps.append({
                "property_id": pid,
                "observed_at": now,
                "price_egp": r["price"],
                "price_per_sqm": r.get("price_per_sqm"),
                "developer_price": r.get("developer_price"),
                "resale_price": r.get("resale_price"),
                "source": source,
                "scrape_run_id": (run_id[:64] if run_id else None),
            })
        if snaps:
            await db.execute(pg_insert(PropertyPriceSnapshot).values(snaps))
    except Exception:
        logger.warning("[repo] snapshot capture failed (non-fatal)", exc_info=True)
