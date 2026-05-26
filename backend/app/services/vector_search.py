"""
Vector Search Service
---------------------
Handles semantic search for properties using OpenAI Embeddings and pgvector.
Supports three modes: vector-only, text-only, and hybrid (vector + FTS with RRF).
"""

import os
import logging
from typing import List, Optional
from sqlalchemy import select, or_, text, func as sa_func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import get_db
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# RRF constant (standard value from the original paper)
RRF_K = 60

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Phase 4: Generate embedding for text using OpenAI with circuit breaker and cost monitoring.
    Returns None on failure to allow fallback to text search.
    Uses AsyncOpenAI to avoid blocking the event loop.
    """
    try:
        from app.services.circuit_breaker import openai_breaker
        from app.services.cost_monitor import cost_monitor

        # Async wrapper for circuit breaker
        async def _generate_embedding():
            response = await _async_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )

            # Phase 4: Track token usage and cost
            token_count = response.usage.total_tokens
            cost_monitor.log_usage(
                model="text-embedding-3-small",
                input_tokens=token_count,
                output_tokens=0,
                context="property_search"
            )

            return response.data[0].embedding

        # Execute with circuit breaker protection (async version)
        embedding = await openai_breaker.call_async(_generate_embedding)
        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None

async def search_properties(
    db: AsyncSession,
    query_text: str,
    limit: int = 5,
    similarity_threshold: float = 0.7,
    price_min: int = None,
    price_max: int = None,
    sale_type: str = None,
    is_delivered: bool = None,
    finishing: str = None,
    is_nawy_now: bool = None,
    search_mode: str = "hybrid",
    compound: str = None,
    location: str = None,
    developer: str = None,
) -> List[dict]:
    """
    Search for properties using semantic similarity, full-text search, or hybrid (both + RRF).

    Modes:
    - "hybrid" (default): Runs vector + FTS in parallel, merges via Reciprocal Rank Fusion
    - "vector": Vector-only cosine similarity search
    - "text":   Full-text / keyword search only

    Fallback chain: hybrid → vector-only → text search → keyword split → empty
    """
    try:
        VECTOR_SEARCH_ENABLED = os.getenv("ENABLE_VECTOR_SEARCH", "0") == "1"

        def _build_filters():
            """Build common SQLAlchemy filter conditions."""
            filters = [Property.is_available == True]
            if compound is not None:
                filters.append(Property.compound.ilike(f"%{compound}%"))
            if location is not None:
                filters.append(Property.location.ilike(f"%{location}%"))
            if developer is not None:
                filters.append(Property.developer.ilike(f"%{developer}%"))
            if price_min is not None:
                filters.append(Property.price >= price_min)
            if price_max is not None:
                filters.append(Property.price <= price_max)
            if sale_type is not None:
                filters.append(Property.sale_type == sale_type)
            if is_delivered is not None:
                filters.append(Property.is_delivered == is_delivered)
            if finishing is not None:
                filters.append(Property.finishing.ilike(f"%{finishing}%"))
            if is_nawy_now is not None:
                filters.append(Property.is_nawy_now == is_nawy_now)
            return filters

        # --- Vector search sub-routine ---
        async def _vector_search(embedding, threshold) -> List[tuple]:
            """Returns list of (Property, similarity_score) tuples."""
            similarity_expr = 1 - Property.embedding.cosine_distance(embedding)
            filters = _build_filters() + [similarity_expr >= threshold]
            stmt = (
                select(Property, similarity_expr.label('similarity'))
                .filter(*filters)
                .order_by(similarity_expr.desc())
                .limit(limit * 2)  # fetch extra for RRF merge
            )
            result = await db.execute(stmt)
            return [(row.Property, float(row.similarity)) for row in result.all()]

        # --- Full-text search sub-routine ---
        async def _fts_search() -> List[tuple]:
            """Returns list of (Property, ts_rank_score) tuples using the search_tsv generated column."""
            try:
                # Try English config first (matches stored tsvector stemming)
                ts_query = sa_func.plainto_tsquery('english', query_text)
                rank_expr = sa_func.ts_rank(Property.search_tsv, ts_query)
                filters = _build_filters() + [Property.search_tsv.op('@@')(ts_query)]
                stmt = (
                    select(Property, rank_expr.label('fts_rank'))
                    .filter(*filters)
                    .order_by(rank_expr.desc())
                    .limit(limit * 2)
                )
                result = await db.execute(stmt)
                rows = [(row.Property, float(row.fts_rank)) for row in result.all()]

                # Fallback to 'simple' config for Arabic/mixed-language queries
                if not rows:
                    ts_query_simple = sa_func.plainto_tsquery('simple', query_text)
                    rank_expr_simple = sa_func.ts_rank(Property.search_tsv, ts_query_simple)
                    filters_simple = _build_filters() + [Property.search_tsv.op('@@')(ts_query_simple)]
                    stmt_simple = (
                        select(Property, rank_expr_simple.label('fts_rank'))
                        .filter(*filters_simple)
                        .order_by(rank_expr_simple.desc())
                        .limit(limit * 2)
                    )
                    result_simple = await db.execute(stmt_simple)
                    rows = [(row.Property, float(row.fts_rank)) for row in result_simple.all()]

                return rows
            except Exception as fts_err:
                logger.warning(f"FTS search failed (search_tsv column may not exist yet): {fts_err}")
                return []

        # --- RRF merge ---
        def _rrf_merge(vector_results: List[tuple], fts_results: List[tuple]) -> List[dict]:
            """Merge two ranked lists using Reciprocal Rank Fusion."""
            scores = {}  # property_id -> {rrf_score, property, sources}

            for rank, (prop, sim_score) in enumerate(vector_results, start=1):
                scores[prop.id] = {
                    "property": prop,
                    "rrf_score": 1.0 / (RRF_K + rank),
                    "vector_score": sim_score,
                    "fts_score": None,
                    "sources": ["vector"],
                }

            for rank, (prop, fts_rank) in enumerate(fts_results, start=1):
                if prop.id in scores:
                    scores[prop.id]["rrf_score"] += 1.0 / (RRF_K + rank)
                    scores[prop.id]["fts_score"] = fts_rank
                    scores[prop.id]["sources"].append("fts")
                else:
                    scores[prop.id] = {
                        "property": prop,
                        "rrf_score": 1.0 / (RRF_K + rank),
                        "vector_score": None,
                        "fts_score": fts_rank,
                        "sources": ["fts"],
                    }

            # Sort by RRF score descending, take top `limit`
            ranked = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)[:limit]

            return [
                _prop_to_dict(
                    entry["property"],
                    similarity_score=entry["vector_score"],
                    source="hybrid" if len(entry["sources"]) > 1 else entry["sources"][0],
                )
                for entry in ranked
            ]

        # --- Main search logic ---
        if VECTOR_SEARCH_ENABLED and search_mode in ("hybrid", "vector"):
            try:
                embedding = await get_embedding(query_text)

                if embedding:
                    # Try strict threshold first
                    vector_results = await _vector_search(embedding, similarity_threshold)

                    # Relax threshold if no results
                    if not vector_results and similarity_threshold > 0.5:
                        logger.warning(f"⚠️ No matches at {similarity_threshold}, relaxing to 0.50")
                        vector_results = await _vector_search(embedding, 0.50)

                    if search_mode == "hybrid":
                        # Run FTS in parallel with already-fetched vector results
                        fts_results = await _fts_search()

                        if vector_results or fts_results:
                            merged = _rrf_merge(vector_results, fts_results)
                            logger.info(
                                f"🔀 Hybrid search: {len(vector_results)} vector + {len(fts_results)} FTS → {len(merged)} merged"
                            )
                            return merged

                    elif vector_results:
                        # Vector-only mode
                        logger.info(f"🔎 Vector search: {len(vector_results)} results (best: {vector_results[0][1]:.2f})")
                        return [
                            _prop_to_dict(prop, similarity_score=score, source="vector")
                            for prop, score in vector_results[:limit]
                        ]

                    # Fall through to text search if no results
                    logger.warning("⚠️ No vector/hybrid matches. Falling through to text search.")

            except Exception as vector_error:
                logger.warning(f"Vector search failed, falling back to text search: {vector_error}")

        # TEXT SEARCH FALLBACK
        return await _text_search_fallback(db, query_text, limit, _build_filters)

    except Exception as e:
        logger.error(f"Property search failed: {e}")
        return []


def _prop_to_dict(prop: Property, similarity_score=None, source="database") -> dict:
    """Convert a Property ORM object to a dict with search metadata."""
    return {
        "id": prop.id,
        "title": prop.title,
        "description": prop.description,
        "type": prop.type,
        "location": prop.location,
        "compound": prop.compound,
        "developer": prop.developer,
        "price": prop.price,
        "price_per_sqm": prop.price_per_sqm,
        "size_sqm": prop.size_sqm,
        "bedrooms": prop.bedrooms,
        "bathrooms": prop.bathrooms,
        "finishing": prop.finishing,
        "delivery_date": prop.delivery_date,
        "down_payment": prop.down_payment,
        "installment_years": prop.installment_years,
        "monthly_installment": prop.monthly_installment,
        "image_url": prop.image_url,
        "nawy_url": prop.nawy_url,
        "sale_type": prop.sale_type,
        "is_available": prop.is_available,
        "is_delivered": getattr(prop, 'is_delivered', None),
        "is_cash_only": getattr(prop, 'is_cash_only', None),
        "land_area": getattr(prop, 'land_area', None),
        "nawy_reference": getattr(prop, 'nawy_reference', None),
        "is_nawy_now": getattr(prop, 'is_nawy_now', None),
        "_source": source,
        "_similarity_score": similarity_score,
    }


async def _text_search_fallback(db: AsyncSession, query_text: str, limit: int, build_filters_fn) -> List[dict]:
    """Text search fallback: exact phrase → keyword split → empty."""
    # Strategy 1: Exact phrase match
    logger.info(f"🔍 Text Search Attempt 1: Exact phrase '{query_text}'")
    search_term = f"%{query_text}%"

    base_filters = build_filters_fn() + [
        or_(
            Property.title.ilike(search_term),
            Property.location.ilike(search_term),
            Property.compound.ilike(search_term),
            Property.description.ilike(search_term),
            Property.developer.ilike(search_term),
            Property.type.ilike(search_term),
        )
    ]

    stmt = select(Property).filter(*base_filters).limit(limit)
    result = await db.execute(stmt)
    properties = result.scalars().all()

    # Strategy 2: Split keywords
    if not properties and len(query_text.split()) > 1:
        logger.info(f"🔍 Text Search Attempt 2: Split keywords")
        stop_words = {
            'in', 'at', 'the', 'a', 'an', 'for', 'of', 'with', 'under', 'above', 'below',
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'تحت', 'فوق', 'عند', 'إن', 'أن', 'ال', 'و', 'أو',
        }
        keywords = [k for k in query_text.split() if k.lower() not in stop_words and len(k) > 1]

        if keywords:
            conditions = []
            for word in keywords:
                term = f"%{word}%"
                conditions.append(Property.title.ilike(term))
                conditions.append(Property.location.ilike(term))
                conditions.append(Property.compound.ilike(term))
                conditions.append(Property.developer.ilike(term))
                conditions.append(Property.type.ilike(term))

            filters = build_filters_fn() + [or_(*conditions)]
            stmt = select(Property).filter(*filters).limit(limit)
            result = await db.execute(stmt)
            properties = result.scalars().all()

    if not properties:
        logger.warning(f"No properties found via text search for query: '{query_text}'")
        return []

    return [_prop_to_dict(p, source="text_search_fallback") for p in properties]


async def validate_property_exists(db: AsyncSession, property_id: int) -> bool:
    """
    Phase 1: Hallucination Prevention
    Validates that a property ID actually exists in the database.

    This function is critical for preventing the AI from recommending
    non-existent properties.

    Args:
        db: Database session
        property_id: Property ID to validate

    Returns:
        True if property exists, False otherwise
    """
    try:
        result = await db.execute(
            select(Property).filter(Property.id == property_id)
        )
        exists = result.scalar_one_or_none() is not None

        if not exists:
            logger.warning(f"⚠️ HALLUCINATION BLOCKED: Property {property_id} does not exist in database")

        return exists

    except Exception as e:
        logger.error(f"Property validation failed: {e}")
        return False
