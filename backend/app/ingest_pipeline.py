"""
ingest_pipeline.py
==================
Asynchronous property ingestion module for the Osool Egyptian real estate
platform.

Responsibilities
----------------
1. Validate raw scraper streams against the ``PropertyListing`` Pydantic schema.
2. Enrich every record with intrinsic valuation metrics computed by the
   ``ValuationEngine`` (normalized NPV price/sqm, La2ta anomaly flag).
3. Persist structured fields to dedicated indexed columns and store a dense
   1536-dimensional embedding (OpenAI ``text-embedding-3-small``) for
   pgvector ANN retrieval.
4. Expose a ``hybrid_query_engine`` that fuses pgvector cosine similarity
   with PostgreSQL full-text ts_rank scoring under hard SQL constraints.

Isolation contract
------------------
* This module performs **no financial transactions** and **no user mutations**.
* All external I/O is explicitly async (SQLAlchemy asyncpg, openai AsyncClient).
* Schema migrations are declared via SQLAlchemy metadata; call
  ``await create_valuation_tables()`` from your startup hook once.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Final, Optional, Sequence

import openai
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, event, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.database import AsyncSessionLocal, Base, engine, get_db
from app.valuation_engine import (
    NormalizedAssetMetrics,
    PaymentTimeline,
    PropertyListing,
    ValuationEngine,
    ViewOrientation,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"
_EMBEDDING_DIM: Final[int] = 1536

#: Hybrid retrieval score weights (must sum to 1.0)
_SEMANTIC_WEIGHT: Final[float] = 0.70
_LEXICAL_WEIGHT: Final[float] = 0.30

#: La2ta threshold — matches valuation_engine._LA2TA_THRESHOLD
_LA2TA_THRESHOLD: Final[float] = 0.15

#: Minimum secondary listings in a compound to enable La2ta classification.
_LA2TA_MIN_BENCHMARKS: Final[int] = 1

# ---------------------------------------------------------------------------
# pgvector availability guard
# ---------------------------------------------------------------------------

_PGVECTOR_AVAILABLE: bool = False
try:
    from pgvector.sqlalchemy import Vector as _PgVector  # type: ignore[import]

    _PGVECTOR_AVAILABLE = True
except ImportError:
    _PgVector = None  # type: ignore[assignment,misc]
    logger.warning(
        "pgvector SQLAlchemy extension not installed. "
        "Embedding column falls back to Text. "
        "Install with: pip install pgvector"
    )

# ---------------------------------------------------------------------------
# Singleton ValuationEngine — sourced from app.valuation_engine so that
# runtime CBE-rate updates (driven by the FastAPI lifespan handler reading
# MarketIndicator) propagate here without restart.
# ---------------------------------------------------------------------------


def _get_valuation_engine() -> ValuationEngine:
    """Return the process-wide ValuationEngine (rate-current at call time)."""
    from app import valuation_engine as _ve

    return _ve._engine  # noqa: SLF001 — intentional cross-module sharing

# ---------------------------------------------------------------------------
# OpenAI async client
# ---------------------------------------------------------------------------

_OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
_openai_client: Optional[openai.AsyncOpenAI] = (
    openai.AsyncOpenAI(api_key=_OPENAI_API_KEY) if _OPENAI_API_KEY else None
)

# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------


class ValuationListing(Base):
    """
    Persistent store for valuation-enriched property listings.

    Hybrid search is enabled via:
    * ``embedding`` — 1536-dim pgvector column for ANN cosine retrieval.
    * ``asset_profile_text`` — human-readable profile used for inline
      ``to_tsvector`` full-text ranking (no separate generated column required).

    The table is upserted on ``listing_id`` to support idempotent re-ingestion
    from scrapers without duplicating rows.
    """

    __tablename__ = "valuation_listings"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ── Source identifiers ────────────────────────────────────────────────────
    listing_id: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    compound_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    geographic_zone: Mapped[str] = mapped_column(String(128), nullable=False)

    # ── Raw listing fields ────────────────────────────────────────────────────
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    size_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    floor_level: Mapped[int] = mapped_column(Integer, nullable=False)
    has_private_garden: Mapped[bool] = mapped_column(Boolean, nullable=False)
    view_orientation: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    delivery_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_secondary_market: Mapped[bool] = mapped_column(
        Boolean, index=True, nullable=False
    )
    #: JSON-serialised ``PaymentTimeline`` or NULL for outright cash.
    payment_timeline_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Valuation engine outputs (indexed for hard-filter queries) ─────────────
    cash_npv_egp: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    normalized_cash_price_sqm: Mapped[float] = mapped_column(
        Float, index=True, nullable=False
    )
    feature_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_lag_penalty_pp: Mapped[float] = mapped_column(Float, nullable=False)
    effective_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    is_la2ta: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=False)

    # ── Search assets ─────────────────────────────────────────────────────────
    #: Structured plain-text profile used for ts_rank lexical scoring.
    asset_profile_text: Mapped[str] = mapped_column(Text, nullable=False)
    #: Dense 1536-dim embedding vector (NULL until OpenAI call succeeds).
    if _PGVECTOR_AVAILABLE and _PgVector is not None:
        embedding: Mapped[Optional[Any]] = mapped_column(
            _PgVector(_EMBEDDING_DIM), nullable=True
        )
    else:
        embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Audit timestamps ──────────────────────────────────────────────────────
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Response / output schemas
# ---------------------------------------------------------------------------


class IngestResponse(BaseModel):
    """Returned to callers after a successful ingest."""

    listing_id: str
    compound_id: str
    geographic_zone: str
    cash_npv_egp: float
    normalized_cash_price_sqm: float
    is_la2ta: bool
    embedding_generated: bool = Field(
        description="True when the OpenAI embedding was generated and stored."
    )
    ingested_at: datetime


class HybridQueryRow(BaseModel):
    """Single result row from the hybrid retrieval engine."""

    listing_id: str
    compound_id: str
    geographic_zone: str
    total_price: float
    size_sqm: float
    view_orientation: str
    is_secondary_market: bool
    cash_npv_egp: float
    normalized_cash_price_sqm: float
    is_la2ta: bool
    delivery_year: int
    semantic_score: float = Field(
        description="Cosine similarity score [0, 1]; higher is more similar."
    )
    lexical_score: float = Field(
        description="PostgreSQL ts_rank score; higher means stronger keyword overlap."
    )
    hybrid_score: float = Field(
        description=(
            f"Weighted fusion: "
            f"{int(_SEMANTIC_WEIGHT * 100)}% semantic + "
            f"{int(_LEXICAL_WEIGHT * 100)}% lexical."
        )
    )


class HybridQueryResult(BaseModel):
    """Aggregated response from ``hybrid_query_engine``."""

    query_text: str
    compound_id: str
    max_budget_egp: float
    total_returned: int
    results: list[HybridQueryRow]


class StreamIngestRequest(BaseModel):
    """Thin wrapper used by the batch stream endpoint."""

    listings: list[PropertyListing] = Field(..., min_length=1, max_length=500)


class HybridQueryRequest(BaseModel):
    """Request body for the hybrid retrieval endpoint."""

    query_text: str = Field(..., min_length=3, max_length=512)
    compound_id: str = Field(..., min_length=1)
    max_budget_egp: float = Field(..., gt=0)
    limit: int = Field(default=5, ge=1, le=50)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_asset_profile_text(
    listing: PropertyListing,
    metrics: NormalizedAssetMetrics,
    is_la2ta: bool,
) -> str:
    """
    Construct a structured plain-text profile suitable for both embedding
    and lexical full-text search.

    The format is deterministic to ensure that re-ingestion produces an
    identical embedding for unchanged listings (enabling differential upsert
    cost savings at the OpenAI API layer).
    """
    view_label = listing.view_orientation.value.replace("_", " ").title()
    market_label = "Secondary Resale" if listing.is_secondary_market else "Developer Primary"
    garden_label = "Yes" if listing.has_private_garden else "No"
    la2ta_label = "La2ta Opportunity" if is_la2ta else "Standard Listing"

    return (
        f"Compound: {listing.compound_id} | "
        f"Zone: {listing.geographic_zone} | "
        f"Floor: {listing.floor_level} | "
        f"Private Garden: {garden_label} | "
        f"View: {view_label} | "
        f"Size: {listing.size_sqm:.1f} sqm | "
        f"Total Price: {listing.total_price:,.0f} EGP | "
        f"NPV: {metrics.cash_npv_egp:,.0f} EGP | "
        f"Normalised Price per sqm: {metrics.normalized_price_per_sqm:,.0f} EGP | "
        f"Delivery Year: {listing.delivery_year} | "
        f"Market Type: {market_label} | "
        f"Valuation Signal: {la2ta_label}"
    )


async def _embed_text(profile_text: str) -> Optional[list[float]]:
    """
    Generate a 1536-dim embedding vector via OpenAI ``text-embedding-3-small``.

    Returns ``None`` (and logs a warning) if the API key is absent or the
    call fails, allowing the record to be persisted without an embedding.
    Callers should treat ``None`` as a soft degradation: the record remains
    queryable via SQL-only filters but is excluded from vector ANN retrieval.
    """
    if _openai_client is None:
        logger.warning(
            "OPENAI_API_KEY not configured — persisting listing without embedding."
        )
        return None

    try:
        response = await _openai_client.embeddings.create(
            model=_EMBEDDING_MODEL,
            input=profile_text,
            dimensions=_EMBEDDING_DIM,
        )
        return response.data[0].embedding
    except openai.OpenAIError as exc:
        logger.error("OpenAI embedding call failed: %s", exc, exc_info=False)
        return None


async def _classify_la2ta(
    db: AsyncSession,
    listing: PropertyListing,
    candidate_price_sqm: float,
) -> bool:
    """
    Classify whether a listing qualifies as a *La2ta* (لقطة) market anomaly
    by comparing its normalised price/sqm against the live compound mean
    stored in ``valuation_listings``.

    This avoids reconstructing ``PropertyListing`` objects for all compound
    peers and instead leverages the already-computed ``normalized_cash_price_sqm``
    values persisted on prior ingestion runs.

    Returns ``False`` for non-secondary listings or when the compound has
    fewer than ``_LA2TA_MIN_BENCHMARKS`` secondary listings in the store
    (bootstrap scenario — not enough reference data for a meaningful signal).
    """
    if not listing.is_secondary_market:
        return False

    stmt = text(
        """
        SELECT AVG(normalized_cash_price_sqm)
        FROM valuation_listings
        WHERE compound_id = :cid
          AND is_secondary_market = TRUE
          AND normalized_cash_price_sqm > 0
          AND listing_id != :lid
        HAVING COUNT(*) >= :min_bench
        """
    )
    result = await db.execute(
        stmt,
        {
            "cid": listing.compound_id,
            "lid": listing.listing_id,
            "min_bench": _LA2TA_MIN_BENCHMARKS,
        },
    )
    compound_mean: Optional[float] = result.scalar_one_or_none()

    if compound_mean is None or compound_mean <= 0:
        return False

    discount = (compound_mean - candidate_price_sqm) / compound_mean
    return discount >= _LA2TA_THRESHOLD


async def _upsert_listing(
    db: AsyncSession,
    listing: PropertyListing,
    metrics: NormalizedAssetMetrics,
    is_la2ta: bool,
    asset_profile_text: str,
    embedding: Optional[list[float]],
) -> None:
    """
    Idempotent upsert into ``valuation_listings`` keyed on ``listing_id``.

    On conflict (re-ingestion of an existing listing), all mutable columns
    are overwritten and ``updated_at`` is refreshed.  The ``id`` and
    ``ingested_at`` columns are intentionally excluded from the update set
    to preserve the original insertion timestamp.
    """
    now = datetime.now(timezone.utc)

    embedding_value: Any
    if embedding is not None:
        if _PGVECTOR_AVAILABLE:
            embedding_value = embedding  # pgvector natively accepts list[float]
        else:
            embedding_value = json.dumps(embedding)  # degraded: stored as JSON text
    else:
        embedding_value = None

    row: dict[str, Any] = {
        "listing_id": listing.listing_id,
        "compound_id": listing.compound_id,
        "geographic_zone": listing.geographic_zone,
        "total_price": listing.total_price,
        "size_sqm": listing.size_sqm,
        "floor_level": listing.floor_level,
        "has_private_garden": listing.has_private_garden,
        "view_orientation": listing.view_orientation.value,
        "delivery_year": listing.delivery_year,
        "is_secondary_market": listing.is_secondary_market,
        "payment_timeline_json": (
            listing.payment_timeline.model_dump_json()
            if listing.payment_timeline is not None
            else None
        ),
        "cash_npv_egp": metrics.cash_npv_egp,
        "normalized_cash_price_sqm": metrics.normalized_price_per_sqm,
        "feature_multiplier": metrics.feature_multiplier,
        "delivery_lag_penalty_pp": metrics.delivery_lag_penalty_pp,
        "effective_multiplier": metrics.effective_multiplier,
        "is_la2ta": is_la2ta,
        "asset_profile_text": asset_profile_text,
        "embedding": embedding_value,
        "ingested_at": now,
        "updated_at": now,
    }

    stmt = pg_insert(ValuationListing).values(**row)
    update_cols = {
        col: stmt.excluded[col]
        for col in row
        if col not in ("listing_id", "ingested_at")
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=["listing_id"],
        set_=update_cols,
    )
    await db.execute(stmt)
    await db.commit()


# ---------------------------------------------------------------------------
# Core processing function
# ---------------------------------------------------------------------------


async def _process_and_persist(
    db: AsyncSession,
    listing: PropertyListing,
) -> IngestResponse:
    """
    Full processing pipeline for a single ``PropertyListing``:

    1. **Valuation hook** — call ``ValuationEngine.normalize_asset_price_per_sqm``
       synchronously (pure math, no I/O) to compute ``normalized_cash_price_sqm``
       and associated feature metrics.
    2. **La2ta classification** — async DB query to derive compound mean and
       flag the listing as a market anomaly when applicable.
    3. **Profile text construction** — deterministic structured text for both
       embedding and lexical search.
    4. **Embedding generation** — async OpenAI ``text-embedding-3-small`` call.
    5. **Upsert** — idempotent persistence to ``valuation_listings``.

    Parameters
    ----------
    db : AsyncSession
        Active SQLAlchemy async session.
    listing : PropertyListing
        Validated listing from the scraper stream.

    Returns
    -------
    IngestResponse
        Enriched valuation summary returned to the caller.
    """
    # Step 1 — synchronous valuation hook (no I/O, safe to call without await)
    try:
        metrics: NormalizedAssetMetrics = (
            _get_valuation_engine().normalize_asset_price_per_sqm(listing)
        )
    except (ValueError, AssertionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Valuation engine rejected listing {listing.listing_id!r}: {exc}",
        ) from exc

    # Step 2 — La2ta classification (async compound mean query)
    is_la2ta: bool = await _classify_la2ta(
        db, listing, metrics.normalized_price_per_sqm
    )

    # Step 3 — asset profile text
    asset_profile_text: str = _build_asset_profile_text(listing, metrics, is_la2ta)

    # Step 4 — embedding (degraded gracefully on OpenAI failure)
    embedding: Optional[list[float]] = await _embed_text(asset_profile_text)

    # Step 5 — upsert
    await _upsert_listing(db, listing, metrics, is_la2ta, asset_profile_text, embedding)

    logger.info(
        "Ingested listing_id=%s compound=%s npv=%.0f la2ta=%s embedding=%s",
        listing.listing_id,
        listing.compound_id,
        metrics.cash_npv_egp,
        is_la2ta,
        embedding is not None,
    )

    return IngestResponse(
        listing_id=listing.listing_id,
        compound_id=listing.compound_id,
        geographic_zone=listing.geographic_zone,
        cash_npv_egp=metrics.cash_npv_egp,
        normalized_cash_price_sqm=metrics.normalized_price_per_sqm,
        is_la2ta=is_la2ta,
        embedding_generated=embedding is not None,
        ingested_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Hybrid retrieval engine
# ---------------------------------------------------------------------------


async def hybrid_query_engine(
    db: AsyncSession,
    query_text: str,
    compound_id: str,
    max_budget_egp: float,
    limit: int = 5,
) -> HybridQueryResult:
    """
    Execute a dual-pronged hybrid retrieval query over ``valuation_listings``.

    Architecture
    ~~~~~~~~~~~~
    **Hard SQL constraints** (applied as WHERE clauses — no semantic drift):

    * ``compound_id = :compound_id`` — exact compound match.
    * ``cash_npv_egp <= :max_budget_egp`` — NPV-based budget ceiling.
    * ``embedding IS NOT NULL`` — only listings with valid vector entries
      participate in vector ranking.

    **Semantic score** — pgvector cosine distance converted to similarity:

    .. math::

        s_{\\text{sem}} = 1 - (\\text{embedding} \\leftrightarrow \\text{query\\_vec})

    **Lexical score** — PostgreSQL ``ts_rank`` over an inline
    ``to_tsvector('simple', asset_profile_text)`` expression against
    ``plainto_tsquery('simple', :query_text)``.  Uses the ``'simple'``
    configuration for broad language compatibility (Arabic + Latin mixed).

    **Hybrid fusion** — weighted linear combination:

    .. math::

        s_{\\text{hybrid}} =
            0.70 \\cdot s_{\\text{sem}} + 0.30 \\cdot s_{\\text{lex}}

    Results are ordered by ``s_hybrid DESC`` to surface listings that are
    both semantically relevant **and** lexically aligned with the query.

    Parameters
    ----------
    db : AsyncSession
        Active async database session.
    query_text : str
        Natural language query from the user (e.g. "3-bedroom pool view
        under 5M in Marassi").
    compound_id : str
        Exact compound identifier — applied as a hard equality filter.
    max_budget_egp : float
        Maximum cash NPV budget in EGP — applied as a hard upper bound.
    limit : int
        Maximum number of results to return (default 5, range 1–50).

    Returns
    -------
    HybridQueryResult
        Ordered list of validated listings with per-row score breakdowns.

    Raises
    ------
    HTTPException(503)
        When OpenAI embedding for the query text cannot be generated
        (required for vector ranking).
    HTTPException(400)
        When ``compound_id`` or ``max_budget_egp`` constraints produce
        no candidate rows at all.
    """
    if not query_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query_text must be a non-empty string.",
        )

    # Generate query embedding — required for semantic half of hybrid search
    query_embedding: Optional[list[float]] = await _embed_text(query_text.strip())
    if query_embedding is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Embedding service unavailable. Cannot perform vector retrieval. "
                "Verify OPENAI_API_KEY and retry."
            ),
        )

    # Build the parameterised hybrid SQL
    # NOTE: The embedding cast ``::vector`` is required for pgvector to
    # recognise the bound parameter as a vector literal.  ``plainto_tsquery``
    # with 'simple' dictionary works for both Arabic-transliterated and
    # English query terms without requiring an Arabic-specific tsconfig.
    sql = text(
        f"""
        SELECT
            listing_id,
            compound_id,
            geographic_zone,
            total_price,
            size_sqm,
            view_orientation,
            is_secondary_market,
            cash_npv_egp,
            normalized_cash_price_sqm,
            is_la2ta,
            delivery_year,
            (1.0 - (embedding <=> CAST(:query_vec AS vector))) AS semantic_score,
            ts_rank(
                to_tsvector('simple', asset_profile_text),
                plainto_tsquery('simple', :query_text)
            ) AS lexical_score,
            (
                :sem_weight * (1.0 - (embedding <=> CAST(:query_vec AS vector)))
                + :lex_weight * ts_rank(
                    to_tsvector('simple', asset_profile_text),
                    plainto_tsquery('simple', :query_text)
                )
            ) AS hybrid_score
        FROM valuation_listings
        WHERE
            compound_id = :compound_id
            AND cash_npv_egp <= :max_budget_egp
            AND embedding IS NOT NULL
        ORDER BY hybrid_score DESC
        LIMIT :lim
        """
    )

    params: dict[str, Any] = {
        "query_vec": json.dumps(query_embedding),  # pgvector accepts JSON array cast
        "query_text": query_text.strip(),
        "sem_weight": _SEMANTIC_WEIGHT,
        "lex_weight": _LEXICAL_WEIGHT,
        "compound_id": compound_id,
        "max_budget_egp": max_budget_egp,
        "lim": limit,
    }

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    if not rows:
        logger.info(
            "hybrid_query_engine: zero results for compound=%s budget=%.0f",
            compound_id,
            max_budget_egp,
        )

    query_rows: list[HybridQueryRow] = [
        HybridQueryRow(
            listing_id=row["listing_id"],
            compound_id=row["compound_id"],
            geographic_zone=row["geographic_zone"],
            total_price=row["total_price"],
            size_sqm=row["size_sqm"],
            view_orientation=row["view_orientation"],
            is_secondary_market=row["is_secondary_market"],
            cash_npv_egp=round(row["cash_npv_egp"], 2),
            normalized_cash_price_sqm=round(row["normalized_cash_price_sqm"], 2),
            is_la2ta=row["is_la2ta"],
            delivery_year=row["delivery_year"],
            semantic_score=round(float(row["semantic_score"]), 6),
            lexical_score=round(float(row["lexical_score"]), 6),
            hybrid_score=round(float(row["hybrid_score"]), 6),
        )
        for row in rows
    ]

    return HybridQueryResult(
        query_text=query_text,
        compound_id=compound_id,
        max_budget_egp=max_budget_egp,
        total_returned=len(query_rows),
        results=query_rows,
    )


# ---------------------------------------------------------------------------
# Schema initialisation helper
# ---------------------------------------------------------------------------


async def create_valuation_tables() -> None:
    """
    Create the ``valuation_listings`` table (and the pgvector extension if
    missing).  Safe to call repeatedly — uses ``CREATE TABLE IF NOT EXISTS``
    semantics via SQLAlchemy metadata.

    Invoke from your application's startup event handler:

    .. code-block:: python

        @app.on_event("startup")
        async def startup():
            await create_valuation_tables()
    """
    async with engine.begin() as conn:
        advisory_lock_acquired = False
        if conn.dialect.name == "postgresql":
            # Serialize DDL across workers to avoid duplicate extension/type races.
            await conn.execute(
                text("SELECT pg_advisory_lock(hashtext('osool_valuation_schema_init'))")
            )
            advisory_lock_acquired = True

        try:
            # Ensure pgvector extension exists before creating VECTOR columns.
            if conn.dialect.name == "postgresql" and _PGVECTOR_AVAILABLE:
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                except Exception as exc:
                    logger.warning(
                        "pgvector extension unavailable; valuation embedding column may fail if configured as VECTOR: %s",
                        exc,
                    )

            await conn.run_sync(
                Base.metadata.create_all,
                tables=[ValuationListing.__table__],
            )
        finally:
            if advisory_lock_acquired:
                await conn.execute(
                    text("SELECT pg_advisory_unlock(hashtext('osool_valuation_schema_init'))")
                )
    logger.info("valuation_listings table ready.")


# ---------------------------------------------------------------------------
# FastAPI router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/ingest", tags=["Ingest Pipeline"])


@router.get("/health", summary="Ingest pipeline liveness check")
async def ingest_health() -> dict[str, object]:
    """Return service liveness, active CBE rate, and embedding model."""
    return {
        "status": "ok",
        "cbe_rate": _get_valuation_engine().cbe_rate,
        "embedding_model": _EMBEDDING_MODEL,
        "embedding_dim": _EMBEDDING_DIM,
        "pgvector_available": _PGVECTOR_AVAILABLE,
        "openai_configured": _openai_client is not None,
    }


@router.post(
    "/stream",
    response_model=list[IngestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a batch of raw property listings from the scraper stream",
)
async def ingest_stream(
    body: StreamIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> list[IngestResponse]:
    """
    High-throughput ingestion endpoint for raw scraper output.

    **Processing per listing (sequential within batch)**:

    1. Validate against the ``PropertyListing`` schema (Pydantic v2).
    2. Pipe synchronously through ``ValuationEngine`` to compute
       ``normalized_cash_price_sqm`` and associated structural metrics.
    3. Query compound mean from ``valuation_listings`` to classify the
       ``is_la2ta`` market anomaly flag.
    4. Generate a 1536-dim embedding via OpenAI ``text-embedding-3-small``.
    5. Upsert to ``valuation_listings`` with dedicated indexed metadata columns.

    **Idempotency**: re-ingesting a listing with the same ``listing_id``
    overwrites all mutable columns and refreshes ``updated_at``.

    **Partial failure**: if one listing fails valuation (e.g. malformed
    payment plan), that listing returns HTTP 422 and the batch is aborted.
    Callers should implement retry logic per listing in the scraper worker.
    """
    responses: list[IngestResponse] = []
    for listing in body.listings:
        result = await _process_and_persist(db, listing)
        responses.append(result)
    return responses


@router.post(
    "/stream/single",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single raw property listing",
)
async def ingest_single(
    listing: PropertyListing,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """
    Convenience endpoint for ingesting one listing at a time.

    Semantically identical to ``/stream`` with a one-element batch.
    Preferred for low-latency incremental scraper pipelines.
    """
    return await _process_and_persist(db, listing)


@router.post(
    "/hybrid-query",
    response_model=HybridQueryResult,
    summary="Hybrid vector + lexical property search within budget constraints",
)
async def api_hybrid_query(
    body: HybridQueryRequest,
    db: AsyncSession = Depends(get_db),
) -> HybridQueryResult:
    """
    Execute a hybrid search combining pgvector ANN retrieval and PostgreSQL
    full-text ranking under hard SQL budget and compound constraints.

    Hard filters applied **before** any scoring:
    - ``compound_id`` exact match.
    - ``cash_npv_egp ≤ max_budget_egp``.

    Results are ranked by a 70 % semantic / 30 % lexical weighted score.
    Only listings with a stored embedding participate in vector ranking.
    """
    return await hybrid_query_engine(
        db=db,
        query_text=body.query_text,
        compound_id=body.compound_id,
        max_budget_egp=body.max_budget_egp,
        limit=body.limit,
    )
