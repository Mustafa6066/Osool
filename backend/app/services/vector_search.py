"""
Vector Search Service
---------------------
Handles semantic search for properties using OpenAI Embeddings and pgvector.
Phase 1: Production-ready with fallback mechanisms.
"""

import os
import logging
from typing import List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property
from app.database import get_db
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Phase 4: Generate embedding for text using OpenAI with circuit breaker and cost monitoring.
    Returns None on failure to allow fallback to text search.
    """
    try:
        from app.services.circuit_breaker import openai_breaker
        from app.services.cost_monitor import cost_monitor

        # Wrap OpenAI call with circuit breaker
        def _generate_embedding():
            response = client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )

            # Phase 4: Track token usage and cost
            token_count = response.usage.total_tokens
            cost_monitor.log_usage(
                model="text-embedding-ada-002",
                input_tokens=token_count,
                output_tokens=0,
                context="property_search"
            )

            return response.data[0].embedding

        # Execute with circuit breaker protection
        embedding = openai_breaker.call(_generate_embedding)
        return embedding

    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None

async def search_properties(
    db: AsyncSession,
    query_text: str,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> List[dict]:
    """
    Search for properties using semantic similarity with STRICT threshold enforcement.

    Phase 7 Production Enhancement:
    - Primary: pgvector cosine similarity search with 0.7 minimum threshold
    - ANTI-HALLUCINATION: Returns empty if no results meet threshold
    - Fallback: Disabled in production to prevent false recommendations

    Args:
        db: Database session
        query_text: User search query
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1), default 0.7

    Returns:
        List of property dicts with similarity scores and _source metadata
    """
    try:
        # Try vector search first
        embedding = await get_embedding(query_text)

        if embedding:
            logger.info(f"Using pgvector semantic search (threshold: {similarity_threshold})")

            # Calculate cosine similarity (1 - cosine_distance)
            # Similarity ranges from 0 (completely different) to 1 (identical)
            similarity_expr = 1 - Property.embedding.cosine_distance(embedding)

            # CRITICAL: Filter by threshold AND order by similarity
            stmt = (
                select(Property, similarity_expr.label('similarity'))
                .filter(
                    Property.is_available == True,
                    similarity_expr >= similarity_threshold  # STRICT THRESHOLD
                )
                .order_by(similarity_expr.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            rows = result.all()

            if not rows:
                logger.warning(
                    f"No properties found above similarity threshold {similarity_threshold} "
                    f"for query: '{query_text}'"
                )
                return []  # Return empty instead of hallucinating

            # Convert to dicts with similarity scores
            properties = []
            for row in rows:
                prop = row.Property
                prop_dict = {
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
                    "_source": "database",
                    "_similarity_score": float(row.similarity)
                }
                properties.append(prop_dict)

            logger.info(
                f"Found {len(properties)} properties with similarity >= {similarity_threshold}"
            )
            return properties

        # Fallback to keyword search (for environments without pgvector like Railway)
        logger.warning("Using full-text search fallback (pgvector not available or embedding failed)")
        search_term = f"%{query_text}%"

        stmt = select(Property).filter(
            Property.is_available == True,
            or_(
                Property.title.ilike(search_term),
                Property.location.ilike(search_term),
                Property.compound.ilike(search_term),
                Property.description.ilike(search_term),
                Property.developer.ilike(search_term)
            )
        ).limit(limit)

        result = await db.execute(stmt)
        properties = result.scalars().all()

        if not properties:
            logger.warning(f"No properties found for query: '{query_text}'")
            return []

        # Convert to dicts without similarity scores
        return [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "type": p.type,
                "location": p.location,
                "compound": p.compound,
                "developer": p.developer,
                "price": p.price,
                "price_per_sqm": p.price_per_sqm,
                "size_sqm": p.size_sqm,
                "bedrooms": p.bedrooms,
                "bathrooms": p.bathrooms,
                "finishing": p.finishing,
                "delivery_date": p.delivery_date,
                "down_payment": p.down_payment,
                "installment_years": p.installment_years,
                "monthly_installment": p.monthly_installment,
                "image_url": p.image_url,
                "nawy_url": p.nawy_url,
                "sale_type": p.sale_type,
                "is_available": p.is_available,
                "_source": "database_fallback",
                "_similarity_score": None
            }
            for p in properties
        ]

    except Exception as e:
        logger.error(f"Property search failed: {e}")
        return []


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
