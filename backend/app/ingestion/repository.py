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
from app.models import Property
from app.ingestion.llm_normalizer import NormalizedProperty

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

    These 6 fields are the "true signal" of a property changing:
    a price drop, a size correction, a finishing upgrade, etc.

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


# ─────────────────────────────────────────────────────────────────────────────
# Embedding Generation (mirrors vector_search.py exactly)
# ─────────────────────────────────────────────────────────────────────────────

async def _generate_embedding(prop: NormalizedProperty) -> Optional[List[float]]:
    """
    Generates a 1536-dim OpenAI text-embedding-3-small vector.

    Text format is designed to capture the property's investible identity:
    type, location, finishing quality, and price anchoring for cosine similarity.

    Mirrors the pattern in app/services/vector_search.py:get_embedding()
    — uses openai_breaker circuit breaker + cost_monitor tracking.

    Returns:
        List of 1536 floats, or None on failure (upsert proceeds without embedding).
    """
    from openai import AsyncOpenAI

    # circuit_breaker / cost_monitor live in app.services which may not be
    # available in the stripped-down scraper container.
    try:
        from app.services.circuit_breaker import openai_breaker
    except ImportError:
        openai_breaker = None
    try:
        from app.services.cost_monitor import cost_monitor
    except ImportError:
        cost_monitor = None

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    compound_str = f", {prop.compound}" if prop.compound else ""
    desc_snippet = (prop.description or "")[:200].strip()
    desc_part = f" {desc_snippet}" if desc_snippet else ""

    embedding_text = (
        f"{prop.type} in {prop.location}{compound_str}, by {prop.developer or 'Unknown Developer'}. "
        f"Size: {prop.size_sqm}sqm, {prop.bedrooms} bedrooms, {prop.finishing}. "
        f"Price: {prop.price:,.0f} EGP.{desc_part}"
    )

    try:
        async def _call():
            response = await client.embeddings.create(
                input=embedding_text,
                model="text-embedding-3-small",
            )
            token_count = response.usage.total_tokens
            if cost_monitor:
                cost_monitor.log_usage(
                    model="text-embedding-3-small",
                    input_tokens=token_count,
                    output_tokens=0,
                    context="ingestion_embedding",
                )
            return response.data[0].embedding

        if openai_breaker:
            return await openai_breaker.call_async(_call)
        return await _call()

    except Exception as exc:
        logger.warning(
            "[repo] Embedding generation failed for '%s' @ %s — upsert will proceed without vector. Error: %s",
            prop.title,
            prop.nawy_url,
            exc,
        )
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Core Upsert Function
# ─────────────────────────────────────────────────────────────────────────────

_BATCH_COMMIT_SIZE = 50  # Commit every N properties to bound memory usage


async def upsert_properties(
    properties: Sequence[NormalizedProperty],
    run_id: str,
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

    Returns:
        UpsertResult with counts for inserted, updated, skipped, errors.
    """
    result = UpsertResult()
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        # Prefetch existing hashes for all URLs in this batch (one round trip)
        urls = [p.nawy_url for p in properties if p.nawy_url]
        existing_hashes: dict[str, str] = {}

        if urls:
            rows = await db.execute(
                select(Property.nawy_url, Property.content_hash).where(
                    Property.nawy_url.in_(urls)
                )
            )
            existing_hashes = {row.nawy_url: row.content_hash for row in rows}

        batch_buffer: list[dict] = []

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
                    await db.execute(
                        text(
                            "UPDATE properties "
                            "SET last_scrape_run_id = :run_id, scraped_at = :now "
                            "WHERE nawy_url = :url"
                        ),
                        {"run_id": run_id, "now": now, "url": prop.nawy_url},
                    )
                    result.skipped += 1
                    logger.debug("[repo] SKIP (hash unchanged) %s", prop.nawy_url)
                    continue

                # ── Expensive path: new or changed ─────────────────────────
                embedding = await _generate_embedding(prop)

                row = _build_row(prop, run_id, now, new_hash, embedding)
                batch_buffer.append(row)

                if old_hash is None:
                    result.inserted += 1
                    logger.debug("[repo] INSERT %s", prop.nawy_url)
                else:
                    result.updated += 1
                    logger.debug("[repo] UPDATE (hash changed) %s", prop.nawy_url)

                # Flush batch every N rows to bound memory
                if len(batch_buffer) >= _BATCH_COMMIT_SIZE:
                    await _flush_batch(db, batch_buffer)
                    batch_buffer = []

            except Exception as exc:
                logger.error("[repo] Error upserting %s: %s", prop.nawy_url, exc)
                result.errors += 1
                result.error_details.append(f"{prop.nawy_url}: {exc}")

        # Flush remaining rows
        if batch_buffer:
            await _flush_batch(db, batch_buffer)

        await db.commit()

    logger.info(
        "[repo] Upsert complete — inserted=%d updated=%d skipped=%d errors=%d",
        result.inserted,
        result.updated,
        result.skipped,
        result.errors,
    )
    return result


def _build_row(
    prop: NormalizedProperty,
    run_id: str,
    now: datetime,
    content_hash: str,
    embedding: Optional[List[float]],
) -> dict:
    """Maps NormalizedProperty fields to Property table column names."""
    return {
        "title": prop.title,
        "description": prop.description,
        "type": prop.type,
        "location": prop.location,
        "compound": prop.compound,
        "developer": prop.developer,
        "price": prop.price,
        "price_per_sqm": prop.price_per_sqm,
        "size_sqm": prop.size_sqm,
        "bedrooms": prop.bedrooms or 0,
        "bathrooms": prop.bathrooms,
        "finishing": prop.finishing,
        "delivery_date": prop.delivery_date,
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
        "embedding": embedding,
        "content_hash": content_hash,
        "last_scrape_run_id": run_id,
        "scraped_at": now,
        "is_available": True,
    }


async def _flush_batch(db, rows: list[dict]) -> None:
    """
    Executes PostgreSQL INSERT ON CONFLICT (nawy_url) DO UPDATE for a batch.

    The partial unique index uq_properties_nawy_url (WHERE nawy_url IS NOT NULL)
    created by migration 019 powers this conflict target.
    """
    if not rows:
        return

    stmt = pg_insert(Property).values(rows)

    # All updatable columns (skip primary key, nawy_url conflict target, created_at)
    update_cols = {
        col.key: stmt.excluded[col.key]
        for col in Property.__table__.columns
        if col.key not in ("id", "nawy_url", "created_at")
    }

    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["nawy_url"],
        index_where=Property.__table__.c.nawy_url.isnot(None),
        set_=update_cols,
    )

    await db.execute(upsert_stmt)
