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

async def search_properties(db: AsyncSession, query_text: str, limit: int = 5) -> List[Property]:
    """
    Search for properties using semantic similarity with fallback to text search.

    Phase 1 Enhancement:
    - Primary: pgvector cosine distance search
    - Fallback: Full-text search on title, location, compound, description

    Args:
        db: Database session
        query_text: User search query
        limit: Maximum number of results

    Returns:
        List of matching Property objects
    """
    try:
        # Try vector search first
        embedding = await get_embedding(query_text)

        if embedding:
            logger.info("Using pgvector semantic search")
            # Cosine distance search using pgvector
            # <=> is cosine distance operator (lower is better, 0 = identical)
            stmt = select(Property).filter(
                Property.is_available == True  # Only available properties
            ).order_by(
                Property.embedding.cosine_distance(embedding)
            ).limit(limit)

            result = await db.execute(stmt)
            properties = result.scalars().all()

            if properties:
                return list(properties)
            else:
                logger.warning("Vector search returned no results, falling back to text search")

        # Fallback to full-text search if vector search fails or returns nothing
        logger.info("Using full-text search fallback")
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

        return list(properties)

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
